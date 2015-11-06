import cookielib
import json
import codecs
import os
import sys
import logging
import urllib
import mechanize
import ast
from lxml import etree
from StringIO import StringIO
from urllib2 import HTTPError, URLError

from mechanize import Browser, Request, FormNotFoundError, BrowserStateError, urlopen
from dac import app


#mechanize._sockettimeout._GLOBAL_DEFAULT_TIMEOUT = 100
browser_url_open_timeout = app.config.get('BROWSER_TIMEOUT')

if browser_url_open_timeout == None:
    browser_url_open_timeout = 60

class ResponseDataWrapper(object):
    
    def __init__(self, response_data=None, headers=None, url_error_occured=False, http_error_occured=False, http_code=None):

        self.response_data = response_data
        self.headers = headers
        self.url_error_occured = url_error_occured
        self.url_error_description = None
        self.http_error_occured = http_error_occured
        self.http_code = http_code
    
    def read(self):
        return self.response_data

    def get_data(self):
        return self.response_data

    def get_headers(self):
        return self.headers

    def get_url_error_decription(self):
        return self.url_error_description
    
    def get_http_code(self):
        return self.http_code
    
    def is_http_errors(self):
        return self.http_error_occured

    def no_url_errors(self):
        return not self.url_error_occured

    def close(self):
        return True

class DACBrowser(object):

    def __init__(self, username, password, useragent='Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1', cookiesfile=os.path.join(os.path.expanduser('~'), '.dacconnectorcookies.lwp')):
        self.auth_form_variants = [
            {'form_name' : 'form2', 'username_field' : 'appleId', 'password_field' : 'accountPassword'},
            {'form_name' : 'appleConnectForm', 'username_field' : 'theAccountName', 'password_field' : 'theAccountPW'}
        ]
        self.username = username
        self.password = password
        self.useragent = useragent
        self.auth_success = True
        self.devices_list_file_name = 'devices_list_file.txt'
        self.current_form = None
        self.csrf = None
        self.csrf_ts = None

        cookies_jar = cookielib.LWPCookieJar(cookiesfile)
        if os.path.exists(cookiesfile) and os.path.getsize(cookiesfile) > 0:
            try:
                cookies_jar.load(ignore_discard=True, ignore_expires=True)
            except cookielib.LoadError as cookie_load_error:
                app.logger.error(cookie_load_error)
                pass
        self.cookies_jar = cookies_jar

        browser = Browser()
        browser.set_cookiejar(cookies_jar)
        browser.addheaders = [('User-agent', useragent)]

        #browser.set_debug_responses(True)
        #browser.set_debug_http(True)

        browser.set_handle_referer(True)
        browser.set_handle_redirect(True)
        browser.set_handle_equiv(True)
        browser.set_handle_robots(False)

        self.browser = browser

    def __login__(self, login_form_attributes):
        print 'call __login__'
        browser = self.browser


        self.select_form_by_name(login_form_attributes['form_name'])

        browser.form[login_form_attributes['username_field']] = self.username
        browser.form[login_form_attributes['password_field']] = self.password
        #request = browser.click()
        #print '__login__, dir(request): ', dir(request)
        response = browser.submit()
        #request.timeout = browser_url_open_timeout
        #print '__login__ request.timeout after assign: ', request.timeout
        #response = browser.open(request)
        if response.info().get('x-frame-options') == 'DENY':
            self.auth_success = False
            print 'Authentication error. Please check login and password, and delete dacconnector cookies file (by default ~/.dacconnector.lwp).'
        else:
            print 'Authentication succcess'
            self.cookies_jar.save(ignore_discard=True, ignore_expires=True)
            browser.set_cookiejar(self.cookies_jar)
        return response
    
    def __detect_login_form__(self, response_html):
        detected_form_attributes = None

        parser = etree.HTMLParser()
        response_html_tree = etree.parse(StringIO(response_html), parser)

        for form_attributes in self.auth_form_variants:
            login_form_container = response_html_tree.xpath('//form[@name="%s"]' % form_attributes['form_name'])
            if login_form_container != []:
                detected_form_attributes = form_attributes
                break
        return detected_form_attributes

    def __save_csrf__(self, headers):
        if 'csrf' in headers.keys() and 'csrf_ts' in headers.keys():
            self.csrf = headers['csrf']
            self.csrf_ts = headers['csrf_ts']
   
    def __open__(self, url_or_request):

        response = None
        response_data = None
        headers = None
        url_error_occured = False
        http_error_occured = False
        http_code = None

        browser = self.browser

        try:
            response = browser.open(url_or_request, timeout=browser_url_open_timeout)
            response_data = response.read()
            headers = response.info()
            #print '__open__ first try block http response code: ', response.code
            http_code = response.code
            self.__save_csrf__(headers)
        except HTTPError as http_error:
            #print 'dir(http_error): ', dir(http_error)
            #print 'http_error, geturl: ', http_error.geturl()
            app.logger.error('__open__ HTTPError: %s' % str(http_error))
            headers = response.info()
            http_code = response.code
            http_error_occured = True
            self.__save_csrf__(headers)
        except URLError as url_error:
            print '__open__ URLError: ', url_error
            app.logger.error('__open__ URLError: %s' % str(url_error))
            url_error_occured = True
        
        if not url_error_occured and not http_error_occured:
            login_form_attributes = self.__detect_login_form__(response.get_data())
            if login_form_attributes != None:
                print '__open__: detected login form'
                #self.__login__(login_form_attributes)
                try:
                    response = self.__login__(login_form_attributes)
                    #response = browser.open(url_or_request, timeout=browser_url_open_timeout)
                    response_data = response.read()
                    headers = response.info()
                    print '__open__ second try block http response code: ', response.code
                    http_code = response.code
                    self.__save_csrf__(headers)
                except HTTPError as http_error:
                    print '__open__ HTTPError: ', http_error
                    app.logger.error('__open__ HTTPError: %s' % str(http_error))
                    http_error_occured = True
                except URLError as url_error:
                    print '__open__ URLError: ', url_error
                    app.logger.error('__open__ URLError: %s' % str(url_error))
                    url_error_occured = True
        return ResponseDataWrapper(response_data=response_data, headers=headers, url_error_occured=url_error_occured, http_error_occured=http_error_occured, http_code=http_code)

        #return response


    def add_headers(self, headers_dict):
        self.browser.addheaders = headers_dict.items()

    '''
    def submit_selected_form(self):
        error_occured = True
        response_data = None
        try:
            #self.browser.submit()
            request = self.browser.click()
            #self.__open__(request)
            self.browser.open(request, timeout=browser_url_open_timeout)
            error_occured = False
        except HTTPError as http_error:
            print 'submit_selected_form HTTPError: ', http_error
            app.logger.error('submit_selected_form HTTPError: %s' % str(http_error))
        except URLError as url_error:
            print 'submit_selected_form URLError: ', url_error
            app.logger.error('submit_selected_form URLError: %s' % str(url_error))

        original_response = self.browser.response()
        if error_occured == False:
            response_data = original_response.get_data()
        headers = original_response.info()
        self.__save_csrf__(headers)
        return ResponseDataWrapper(response_data, headers, error_occured)
        '''
    
    def submit_selected_form(self):
        browser = self.browser
        request = browser.click()
        return self.__open__(request)

    def get_response():
        orIginal_response = self.browser.response()
        return ResponseDataWrapper(original_response.get_data(), original_response.info())

    def select_form_by_name(self, form_name):
        form_found = False
        browser = self.browser
        try:
            browser.select_form(name=form_name)
            form_found = True
            self.current_form = browser.form
        except FormNotFoundError as form_not_found_error:
            app.logger.error('Form with name %s not found, rise exception: %s' % (form_name, form_not_found_error))
            print 'Form with name %s not found, rise exception:' % form_name, form_not_found_error
            self.current_form = None
        except BrowserStateError as browser_state_error:
            app.logger.error('select_form_by_name, form_name %s rise exception: %s' % (form_name, browser_state_error))
            print 'select_form_by_name, form_name %s rise exception: %s' % (form_name, browser_state_error)
            self.current_form = None

        return form_found

    def select_form_by_id(self, form_id):
        form_found = False
        browser = self.browser
        try:
            browser.select_form(predicate=lambda form: 'id' in form.attrs and form.attrs['id'] == form_id)
            form_found = True
            self.current_form = browser.form
        except FormNotFoundError as form_not_found_error:
            app.logger.error('Form with id %s not found, rise exception: %s' % (form_id, form_not_found_error))
            print 'Form with id %s not found, rise exception:' % form_id, form_not_found_error
            self.current_form = None
        except BrowserStateError as browser_state_error:
            app.logger.error('select_form_by_id, form_id %s rise exception: %s' % (form_id, browser_state_error))
            print 'select_form_by_id, form_id %s rise exception: %s' % (form_id, browser_state_error)
            self.current_form = None

        return form_found

    def get(self, url):
        print 'call get'
        return self.__open__(url)

    def post(self, url, post_params={}):
        request = Request(url, urllib.urlencode(post_params), timeout=browser_url_open_timeout)
        print 'dacbrowser post call'
        #print 'post, type(request): ', type(request)
        #print 'dir(request): ', dir(request)
        #print 'request timeout: ', request.timeout
        #print 'dir(request.timeout): ', dir(request.timeout)
        request.add_header('User-agent', self.useragent) 
        return self.__open__(request)

    def set_value_by_key(self, key, value):
        self.browser[key] = value

    def add_adssuv_field_to_form(self):
        form_exists = False
        form = self.current_form
        if form != None:
            form_exists = True
            adssuv_value = None
            for cookie in self.cookies_jar:
                if cookie.name == 'adssuv':
                    adssuv_value = cookie.value
                    break
            if adssuv_value != None:
                form.new_control('text','adssuv-value',{'value':''})
                form.fixup()
                adssuv_control = form.find_control('adssuv-value')
                self.set_value_by_key('adssuv-value', adssuv_value)
        return form_exists

    def prepare_csrf_headers(self):
        headers_dict = {'Accept' : '*/*', 'X-Requested-With' : 'XMLHttpRequest', 'Accept-Encoding' : 'gzip, deflate'}
        csrf = self.csrf
        csrf_ts = self.csrf_ts
        csrf_dict = {'csrf' : False, 'csrf_ts' : False}
        if csrf != None and csrf_ts != None:
            csrf_dict = {'csrf' : csrf, 'csrf_ts' : csrf_ts}
        headers_dict.update(csrf_dict)
        self.add_headers(headers_dict)

    def clean_credentials(self):
        self.cookies_jar.clear()
        self.cookies_jar.save()
