from dacbrowser import DACBrowser
import re
import json
import os
from tempfile import NamedTemporaryFile
from lxml import etree
from StringIO import StringIO
from sqlalchemy.exc import SQLAlchemyError
import urllib
from urllib2 import HTTPError

from time import sleep

from models import DeviceProfileAssociation, Device, Profile

class AppleConnectionState(object):
    pass

class AppleAccountProcessor(object):

    def __init__(self, username, password, sqlalchemy_db, useragent=None):
        if useragent != None:
            self.dacbrowser = DACBrowser(username, password, useragent)
        else:
            self.dacbrowser = DACBrowser(username, password)
        self.sqlalchemy_db = sqlalchemy_db
        self.devices_url = 'https://developer.apple.com/account/ios/device/deviceList.action'
        self.devices_data = None
        self.devices_descriptions = None
        self.profiles_url = 'https://developer.apple.com/account/ios/profile/profileList.action'
        self.profile_download_url = 'https://developer.apple.com/account/ios/profile/profileContentDownload.action?displayId=%s'
        self.profiles_data = None
        self.profiles_descriptions = None
        self.certificates_url = 'https://developer.apple.com/account/ios/certificate/certificateList.action'
        self.certificates_data = None
        self.certificates_descriptions = None
        self.add_device_url = 'https://developer.apple.com/account/ios/device/deviceCreate.action'
        self.profile_edit_url = 'https://developer.apple.com/account/ios/profile/profileEdit.action'
        self.add_device_success_mesage = 'device with number success' # Fake message, I don't know right message
        self.add_device_already_exist = 'already exists'
        self.add_device_invalid = 'An invalid value (this is device number) was provided for the parameter'
        # An invalid value '5fd5ddcd7f3248c2b385d51c8548db4acd02f6e9 ' was provided for the parameter 'deviceNumber'."
        self.add_device_error = 'device with number' # Fake message, I don't know right message
        self.refresh_devices_descriptions_success = False
        self.refresh_profiles_descriptions_success = False
        self.url_error_detected = False
        self.url_error_had_occured = False
        self.required_csrf_http_code = 421

    def set_devices_url(self, devices_url=None):
        if devices_url != None:
            self.devices_url = devices_url

    def set_profiles_url(self, profiles_url):
        if profiles_url != None:
            self.profiles_url = profiles_url

    def set_certificates_url(self, certificates_url):
        if certificates_url != None:
            self.certificates_url = certificates_url

    def extract_data_url_component(self, response_data, data_regex_pattern):
        data_url_component = None
        data_url_component_regex = re.compile(data_regex_pattern)
        regex_search_result = data_url_component_regex.search(response_data)
        if regex_search_result != None:
            data_url_component = regex_search_result.group(1)
        return data_url_component


    def get_data(self, data_url, post_params={}):
        data = None
        data_response = self.dacbrowser.post(data_url, post_params)
        #if data_response != None:
        if data_response.no_url_errors():
            data = json.loads(data_response.read())
            data_response.close()
        else:
            pass
            #print 'get_data, are url errors'
        return data

    def get_devices_data(self):
        response = self.dacbrowser.get(self.devices_url)
        #if response != None:
        if response.no_url_errors():
            print 'get_devices_data, no url errors'
            response_context = response.read()
            #print 'get_devices_data, response_context: ', response_context
            data_url = self.extract_data_url_component(response_context, 'deviceDataURL = "([^"]*)"')
            response.close()
            if data_url != None:
                self.devices_data = self.get_data(data_url)
            else:
                print 'get_devices_data, data_url is None'
        else:
            self.devices_data = None
            print 'get_devices_data, present url errors'
        return self.devices_data

    def get_devices_descriptions(self):
        self.get_devices_data()
        devices_data = self.devices_data
        if devices_data != None and devices_data != {}:
            self.devices_descriptions = [Device(device['deviceNumber'], device) for device in devices_data.get('devices')]
        return self.devices_descriptions

    def print_devices(self):
        devices_descriptions = self.devices_descriptions
        if devices_descriptions == None:
            devices_descriptions = self.get_devices_descriptions()
        for device in devices_descriptions:
            device.display()

    def get_provisioning_profiles_data(self):
        response = self.dacbrowser.get(self.profiles_url)
        if response.no_url_errors():
            data_url = self.extract_data_url_component(response.read(), 'profileDataURL = "([^"]*)"')
            print 'get_provisioning_profiles_data, data_url: ', data_url
            response.close()
            if data_url != None:
                self.profiles_data = self.get_data(data_url)
        else:
            print 'get_provisioning_profiles_data: are url errors'
            self.profiles_data = None
        return self.profiles_data

    def get_provisioning_profiles_descriptions(self):
        self.get_provisioning_profiles_data()
        profiles_data = self.profiles_data

        if profiles_data != None and profiles_data != {}:
            self.profiles_descriptions = [Profile(profile_description) for profile_description in profiles_data.get('provisioningProfiles')]
        return self.profiles_descriptions

    def download_provisioning_profile(self, url):
        profile_binary = None
        response = self.dacbrowser.get(url)
        #if response != None:
        if response.no_url_errors():
            profile_binary = response.read()
            response.close()
        return profile_binary

    def extract_devices_from_profile(self, profile_binary):
        devices_id_list = None
        profile_str = str(profile_binary)
        xml_begin_index = profile_str.find('<?xml')
        xml_end_index = profile_str.rfind('</plist>')
        profile_xml = profile_binary[xml_begin_index:xml_end_index + len('</plist>')]

        parser = etree.XMLParser()
        xml_tree = etree.parse(StringIO(profile_xml), parser)
        tag_keyword_elements = xml_tree.xpath('//key')
        for tag_keyword_element in tag_keyword_elements:
            if tag_keyword_element.text == 'ProvisionedDevices':
                succeeding_siblings = tag_keyword_element.itersiblings(preceding=False)
                devices_id_array = succeeding_siblings.next()
                devices_id_list = [id_string_element.text for id_string_element in devices_id_array.getchildren()]
        return devices_id_list
    
    def update_profile_and_device_tables(self):
        #sqlalchemy_session = self.sqlalchemy_db.session(expire_on_commit=False)
        sqlalchemy_session = self.sqlalchemy_db.session()
        present_devices = sqlalchemy_session.query(Device).all()
        present_devices_count = len(present_devices)

        retrieved_devices_count = -1
        new_devices_count = 0
        retrieved_profiles_count = -1
        new_profiles_count = 0
    
        url_error_detected = False
        devices_descriptions = self.get_devices_descriptions()
        if devices_descriptions == None:
            url_error_detected = True

        if url_error_detected == False:
            profiles_descriptions = self.get_provisioning_profiles_descriptions()
            if profiles_descriptions == None:
                url_error_detected == True

        all_downloaded_profiles_devices_numbers = set()
        profiles_with_associates_devices_numbers = list()

        #if self.refresh_profiles_descriptions_success and self.refresh_devices_descriptions_success:
        all_downloaded_profiles_devices_numbers_list = list()

        if url_error_detected == False:
            for profile in self.profiles_descriptions:
                profile_id = profile.id
                profile_devices_numbers = []
                profile_binary = self.download_provisioning_profile(self.profile_download_url % profile_id)
                if profile_binary != None:
                    profile.profile_binary = profile_binary
                    profile_devices_numbers = self.extract_devices_from_profile(profile_binary)
                    if profile_devices_numbers != None:
                        all_downloaded_profiles_devices_numbers.update(set(profile_devices_numbers))
                else:
                    url_error_detected = True
                    break
                profiles_with_associates_devices_numbers.append((profile, profile_devices_numbers))
            
            if url_error_detected == False:
                all_downloaded_profiles_devices_numbers_list = list(all_downloaded_profiles_devices_numbers)

        if url_error_detected == False:
            retrieved_devices_numbers = [device.number for device in self.devices_descriptions]
            retrieved_devices_count = len(retrieved_devices_numbers)

            # devices_delete_result = sqlalchemy_session.query(Device).filter(~Device.number.in_(retrieved_devices_numbers)).delete(synchronize_session='fetch')
            devices_to_delete = [device for device in present_devices if device.number not in retrieved_devices_numbers]
            for device_to_delete in devices_to_delete:
                sqlalchemy_session.delete(device_to_delete)
            sqlalchemy_session.commit()

            present_devices = sqlalchemy_session.query(Device).all()
            present_devices_numbers = [device.number for device in present_devices]

            new_devices = [device for device in self.devices_descriptions if device.number not in present_devices_numbers]
            new_devices_numbers = [device.number for device in new_devices]

            present_profiles = sqlalchemy_session.query(Profile).all()
            present_profiles_ids = [profile.id for profile in present_profiles]
            retrieved_profiles_ids = [profile.id for profile in self.profiles_descriptions]
            retrieved_profiles_count = len(retrieved_profiles_ids)

            profiles_to_delete = [profile for profile in present_profiles if profile.id not in retrieved_profiles_ids]
            for profile_to_delete in profiles_to_delete:
                sqlalchemy_session.delete(profile_to_delete)
            sqlalchemy_session.commit()

            present_profiles = sqlalchemy_session.query(Profile).all()
            present_profiles_ids = [profile.id for profile in present_profiles]

            new_devices_numbers_from_profiles = [device_number for device_number in all_downloaded_profiles_devices_numbers_list if (device_number not in present_devices_numbers and device_number not in new_devices_numbers)]

            new_devices_from_profiles = [Device(device_number) for device_number in new_devices_numbers_from_profiles]
            new_devices.extend(new_devices_from_profiles)

            sqlalchemy_session.add_all(new_devices)
            sqlalchemy_session.commit()
           
            devices_after_add = sqlalchemy_session.query(Device).all()
            
            new_profiles_with_associated_devices_numbers = [profile_numbers_pair for profile_numbers_pair in profiles_with_associates_devices_numbers if profile_numbers_pair[0].id not in present_profiles_ids]
            new_profiles_count = len(new_profiles_with_associated_devices_numbers)
            for present_profile in present_profiles:
                print 'Present profile id: ', present_profile.id
                for profile_numbers_pair in profiles_with_associates_devices_numbers:
                    retrieved_profile, devices_numbers = profile_numbers_pair
                    if present_profile.id == retrieved_profile.id:
                        if retrieved_profile.profile_binary != None:
                            present_profile.profile_binary = retrieved_profile.profile_binary
                        if devices_numbers != None:
                            present_profile.profile_devices = [DeviceProfileAssociation(device_number, present_profile.id) for device_number in devices_numbers]
                        else:
                            present_profile.profile_devices = []

            for profile_numbers_pair in new_profiles_with_associated_devices_numbers:
                profile, devices_numbers = profile_numbers_pair
                if devices_numbers != None and devices_numbers != {}:
                    profile.profile_devices = [DeviceProfileAssociation(number, profile.id) for number in devices_numbers]
                sqlalchemy_session.add(profile)
            sqlalchemy_session.commit()

            new_devices_count = len(new_devices_numbers)


        sqlalchemy_session.close()
        return {'retrieved_devices_count' : retrieved_devices_count, 'new_devices_count' : new_devices_count, 'retrieved_profiles_count' : retrieved_profiles_count, 'new_profiles_count' : new_profiles_count}


    def get_new_old_profiles_ids_map(self, edited_profiles):
        #print 'get_new_old_profiles_ids_map: ', edited_profiles.items()
        #return { profile_item[0] : profile_item[1]['new_profile_id'] for profile_item in edited_profiles.items() if profile_item[1]['success'] == True}
        return edited_profiles

    #def get_old_profiles_ids(self. edited_profiles):
    #    return 

    def replace_edited_profiles(self, edited_profiles):
        result = False
        url_error_detected = False
        profiles_data = self.get_provisioning_profiles_data()

        if profiles_data == None:
            url_error_detected == True
        if not url_error_detected:
            all_profiles_list = profiles_data.get('provisioningProfiles')
            new_old_profiles_ids_map = self.get_new_old_profiles_ids_map(edited_profiles)
            old_profiles_ids = new_old_profiles_ids_map.keys()
            new_profiles_ids = new_old_profiles_ids_map.values()

            new_profiles_with_associated_devices_numbers = list()
           
            sqlalchemy_session = self.sqlalchemy_db.session()
            associations_delete_result = sqlalchemy_session.query(DeviceProfileAssociation).filter(DeviceProfileAssociation.profile_id.in_(old_profiles_ids)).delete(synchronize_session='fetch')
            old_profiles_delete_result = sqlalchemy_session.query(Profile).filter(Profile.id.in_(old_profiles_ids)).delete(synchronize_session='fetch')

            sqlalchemy_session.flush()

            new_profiles = [Profile(profile_description) for profile_description in all_profiles_list if profile_description.get('provisioningProfileId') in new_profiles_ids]

            for profile in new_profiles:
                profile_id = profile.id
                profile_devices_numbers = []
                profile_binary = self.download_provisioning_profile(self.profile_download_url % profile_id)
                if profile_binary != None:
                    profile.profile_binary = profile_binary
                    profile_devices_numbers = self.extract_devices_from_profile(profile_binary)
                    new_profiles_with_associated_devices_numbers.append((profile, profile_devices_numbers))
                else:
                    url_error_detected = True
                    break
            if not url_error_detected:
                for profile_numbers_pair in new_profiles_with_associated_devices_numbers:
                    profile, devices_numbers = profile_numbers_pair
                    if devices_numbers != None and devices_numbers != {}:
                        profile.profile_devices = [DeviceProfileAssociation(number, profile.id) for number in devices_numbers]
                    sqlalchemy_session.add(profile)
                    
                result = True     
                sqlalchemy_session.commit()
        return result

    def add_multiple_devices(self, devices_file_context):

        result_message = 'unknow result'
        response_html = ''

        dacbrowser = self.dacbrowser
        url = self.add_device_url
        
        response = dacbrowser.get(url)
        #if dacbrowser.get(url) != None:
        if response.no_url_errors():
            device_import_form_found = dacbrowser.select_form_by_name('deviceImport')
            if device_import_form_found == False:
                print 'Device import form not found. Cleaning cookies'
                dacbrowser.clean_credentials()
                print 'Done. Try login with current login and password again'
                device_import_form_found = dacbrowser.select_form_by_name('deviceImport')
            if device_import_form_found:

                form = dacbrowser.current_form
                form.method = 'POST'
    
                devices_list_file = NamedTemporaryFile(prefix='apple_devices_list_', suffix='.txt')
                devices_list_file.write(devices_file_context)
                devices_list_file.flush()
                devices_list_file_name = devices_list_file.name

                for control in form.controls:
                    if control.type == 'file':
                        control.add_file(open(devices_list_file_name), 'text/plain', devices_list_file_name)
                        control.disabled=False
                        break
                
                response = dacbrowser.submit_selected_form()
                devices_list_file.close()

                response_data = response.get_data()
                if response_data != None and response_data != '':
                    parser = etree.HTMLParser()
                    html_tree = etree.parse(StringIO(response_data), parser)
                    error_message_container = html_tree.xpath('//ul[@class="errorMessage"]')
                    if error_message_container != [] and len(error_message_container) == 1:
                        error_message = etree.tostring(error_message_container[0])
                        print error_message
                        response_html = error_message
                        result_message = 'devices description error'
                    else:
                        device_import_save_form_found = dacbrowser.select_form_by_id('deviceImportSave')
                        if device_import_save_form_found:
                            form = dacbrowser.current_form
                            form.method = 'POST'
                            
                            #response = dacbrowser.submit_selected_form() ##-- Don't delete this line! This is for reall add devices!

                            if response_data != None and response_data != '':
                                html_tree = etree.parse(StringIO(response_data), parser)

                                '''
                                # Lines below - for real add devices.

                                success_message_container = html_tree.xpath('//<success tag xpath')
                                if success_message_container != [] and len(success_message_container) == 1:
                                    success_message = etree.tostring(success_message_container[0])
                                    result_messages = 'devices added successfuly'
                                    response_html = success_message
                                    '''

                            result_messages = 'devices added successfuly'
            else:
                result_message = 'Add multiple devices form not found. Probably your permissions not enough to add multiple devices. Try change login or/and password'
        else:
            result_message = 'cannot open url'

        print 'add_multiple_devices, result_message: ', result_message, ' response_html: ', response_html

        return result_message, response_html

    def select_devices_in_edit_form(self, device_ids_control, device_ids_list):
        for item in device_ids_control.items:
            for device_id in device_ids_list:
                if item.name == device_id:
                    if item.selected == True:
                        item.selected = False
                    else:
                        item.selected = True
                    break

    def select_and_prepare_profile_edit_form(self, profile_id, device_ids_list):
        profile_edit_response = self.dacbrowser.post(self.profile_edit_url, {'type' : '', 'provisioningProfileId' : profile_id, 'clientToken' : 'undefined'})
        dacbrowser = self.dacbrowser
        profile_edit_form_found = dacbrowser.select_form_by_name('profileEdit')
        if profile_edit_form_found:
            dacbrowser.add_adssuv_field_to_form()
            dacbrowser.prepare_csrf_headers()
          
            form = dacbrowser.current_form
            device_ids_control = form.find_control(name='deviceIds')
            self.select_devices_in_edit_form(device_ids_control, device_ids_list)

            form.method = 'POST'

        return profile_edit_form_found

    def get_profiles_ids(self, profiles_name_list, profiles_data_list):
        profile_ids = list()
        for profile_data in profiles_data_list:
            for profile_name in profiles_name_list:
                if profile_name == profile_data['name']:
                    profile_ids.append(profile_data['provisioningProfileId'])
                    print 'Profile id: ', profile_data['provisioningProfileId']
                    break
        return profile_ids

    def edit_profile(self, profile_id, devices_ids_list):
        dacbrowser = self.dacbrowser
        edit_success = False
        profile_edit_form_found = self.select_and_prepare_profile_edit_form(profile_id, devices_ids_list)
        
        new_profile_id = None
        profile_name = None
        submit_profile_edit_form_response = None
        if profile_edit_form_found:
            submit_profile_edit_form_response = dacbrowser.submit_selected_form()
            http_error_occured = submit_profile_edit_form_response.is_http_errors()
            http_code = submit_profile_edit_form_response.get_http_code()
            #print 'edit_profile, http_code: ', http_code, ' http_code type: ', type(http_code)
            if submit_profile_edit_form_response.no_url_errors():
                if http_error_occured and http_code == self.required_csrf_http_code:
                    profile_edit_form_found = self.select_and_prepare_profile_edit_form(profile_id, devices_ids_list)
                    if profile_edit_form_found:
                        submit_profile_edit_form_response = dacbrowser.submit_selected_form()

                if not http_error_occured:

                    profile_regeneration_result = submit_profile_edit_form_response.read()
                    result_dictionary = json.loads(profile_regeneration_result)

                    creation_timestamp = result_dictionary.get('creationTimestamp')
                    result_code = result_dictionary.get('resultCode')
                    new_profile_id = None
                    profile_name = None
                    profile_description = result_dictionary.get('provisioningProfile')

                    if profile_description != None:
                        #print 'name in profile_description.keys(): ', 'name' in profile_description.keys()
                        new_profile_id = profile_description.get('provisioningProfileId')
                        profile_name = profile_description.get('name')
                    else:
                        pass
                        #print 'profile_description is None'

                    print 'new_profile_id: ', new_profile_id, 'profile_name: ', profile_name

                    if creation_timestamp != None and result_code == 0 and new_profile_id != None:
                        edit_success = True
                else:
                    pass
                    print 'submit_profile_edit_form_response: ', submit_profile_edit_form_response
            else:
                pass
                print 'url error occured'
        else:
            pass
            print 'Profile with id %s not found!' % profile_id

        return edit_success, new_profile_id, profile_name
                   
    def edit_profiles(self, devices_ids_list, profiles_ids_list):
        edit_profiles_result_data = dict()
        dacbrowser = self.dacbrowser
        response = dacbrowser.get(self.profiles_url)
        self.get_provisioning_profiles_data()
        if self.profiles_data != None and self.profiles_data != {}:
            for profile_id in profiles_ids_list:
                print 'edit_profiles, profile_id: ', profile_id
                profile_edit_success, new_profile_id, profile_name = self.edit_profile(profile_id, devices_ids_list)
                edit_profiles_result_data[profile_id] = {'success' : profile_edit_success, 'new_profile_id' : new_profile_id, 'profile_name' : profile_name}
        return edit_profiles_result_data

