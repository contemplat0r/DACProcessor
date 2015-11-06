from flask import Blueprint, request, render_template, flash, session, redirect, url_for, current_app, g, jsonify

from dac import app
#from dac import celery
from dac import db, login_manager
from dac.dacbrowser.models import DeviceProfileAssociation, Device, Profile
from dac.dacbrowser.appleaccountprocessor import AppleAccountProcessor
from dac.dacbrowser.forms import UpdateAllForm, AddDeviceForm, AddDeviceToProfileForm, AddMultipleDevicesForm, ProfileDescriptionForm, EditProfilesForm, DeviceIdForm, EditProfileForm, DeviceDescriptionForm

from dac.users.views import customer_permission, member_permission, admin_permission
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import not_
from urllib2 import URLError

from celery import Celery
from time import sleep
from StringIO import StringIO
import json


## begin make celery section

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

## end make celery section

mod_browser = Blueprint('browser', __name__)


## begin create apple_account_processor seciton

apple_user_login = app.config.get('APPLE_USER_LOGIN')
apple_user_password = app.config.get('APPLE_USER_PASSWORD')

apple_account_processor = AppleAccountProcessor(apple_user_login, apple_user_password, db)

## end create apple_account_processor section


@mod_browser.route('/')
def index():
    return redirect(url_for('devices'))


## begin check task progress function section

def check_task_progress(request, celery_task):
    state = 'notready'
    result_value = None
    task_id = request.data
    task_result = add_device.AsyncResult(add_device_task_id)
    if add_device_result.ready():
        print 'Task %s ready!' % add_device_task_id
        state = 'ready'
        result_value = add_device_result.result
        print 'add_device_result.result: ', add_device_result.result
        if result_value == None:
            result_value = 'add device error'
        return jsonify(state=state, result_msg=add_device_result.result)
        print 'result_value: ', result_value
    else:
        print 'Task %s is not ready!' % add_device_task_id
    return_value = jsonify(state=state, result_value='add device error')
    print 'before try, return_value: ', return_value
    try:
        return_value = jsonify(state=state, result_value=result_value)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    print 'before return, return_value: ', return_value
    return return_value

## end check task progress function section


## begin devices page section

@mod_browser.route('/devices/', methods=['GET'])
@customer_permission.require(http_exception=403)
def devices():
    if request.query_string != '':
        return redirect(url_for('browser.devices'))
    add_device_form = AddDeviceForm(request.form, csrf_enabled=False)
    add_multiple_devices_form = AddMultipleDevicesForm()
    return render_template('dacbrowser/devices.html', add_device_form=add_device_form, add_multiple_devices_form=add_multiple_devices_form)

@mod_browser.route('/getdeviceslist/', methods=['GET'])
@customer_permission.require(http_exception=403)
def get_devices_list():
    page = 1
    records_per_page = 3
    args = request.args
    page_num = args.get('page_num')
    if page_num == '':
        page_num = '1'
    if args.get('per_page') != None and page_num != None:
        records_per_page = int(args.get('per_page'))
        page = int(page_num)

    devices = Device.query.paginate(page, records_per_page, False)
    if page > devices.pages:
        page = devices.pages
        devices = Device.query.paginate(page, records_per_page, False)
    devices_info = []

    i = 1
    for device in devices.items:
        devices_info.append({'number' : str((page - 1) * records_per_page + i), 'name' : device.name, 'udid' : device.number})
        i = i + 1
    devices_list = render_template('dacbrowser/devicestable.html', devices_info = devices_info)
    pagination_links_html = render_template('render_pagination.html', pagination=devices) 
    return jsonify(item_list=devices_list,  pagination=pagination_links_html)

@mod_browser.route('/startadddevice/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_add_device():
    add_device_task_id = ''
    add_device_form = AddDeviceForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and add_device_form.validate():
        device_name = add_device_form.name.data.strip()
        device_udid = add_device_form.udid.data.strip()
        device_file_content = 'Device ID\tDevice Name\n%s\t%s' % (device_udid, device_name)
        print 'start_add_device, device_file_content: ', device_file_content
        add_device_task = add_multiple_devices.delay(device_file_content)
        add_device_task_id = add_device_task.task_id
    return jsonify(task_id=add_device_task_id)

@mod_browser.route('/startaddmultipledevices/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_add_multiple_devices():
    add_multiple_devices_task_id = ''
    add_multiple_devices_form = AddMultipleDevicesForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and add_multiple_devices_form.validate():
        devices_list_file = request.files['devices_list_file']
        file_content = devices_list_file.read()
        add_multiple_devices_task = add_multiple_devices.delay(file_content)
        add_multiple_devices_task_id = add_multiple_devices_task.task_id
    
    return jsonify(task_id=add_multiple_devices_task_id)

@mod_browser.route('/addmultipledevicesprogress/', methods=['POST'])
@customer_permission.require(http_exception=403)
def add_multiple_devices_progress():
    print 'Call add_device_progress'
    state = 'notready'
    add_devices_result_state = 'add devices fail'
    result_html = ''
    add_multiple_devices_task_id = request.data
    add_multiple_devices_result = add_multiple_devices.AsyncResult(add_multiple_devices_task_id)
    if add_multiple_devices_result.ready():
        print 'Task %s ready!' % add_multiple_devices_task_id
        state = 'ready'
        result = add_multiple_devices_result.result
        add_devices_result_state, result_html = result
        print add_devices_result_state
    else:
        print 'Task %s is not ready!' % add_multiple_devices_task_id
    return_value = jsonify(state=state, result_value='add devices fail', result_html = '')
    try:
        return_value = jsonify(state=state, result_value=add_devices_result_state, result_html = '<strong>' + result_html + '</strong>')
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value


@celery.task
def add_multiple_devices(devices_list_file_context):
    result = ('add devices fail', 'task execution error')
    try:
        result = apple_account_processor.add_multiple_devices(devices_list_file_context)
    except (IOError, URLError, TypeError) as add_device_error:
        app.logger.error(add_device_error)
    #Do not delete this rows! This for emulating device adding.
    '''
    result = ('add devices success', '')
    sleep(5)
    print '5 sec add_devices_list. Flight is normal'
    sleep(5)
    print '10 sec add_devices_list. Flight is normal'
    sleep(5)
    print '15 sec add_devices_list. Flight is normal'
    '''
    return result

## end devices page section


## begin device page section

class DeviceIdDescription(object):
    
    def __init__(self, device_id):
        self.device_id = device_id

class AddDeviceToProfileFormValues(object):
    def __init__(self, name, udid):
        self.name = name
        self.udid = udid

@mod_browser.route('/device/<devicenumber>', methods=['GET'])
@customer_permission.require(http_exception=403)
def device(devicenumber):
    #add_device_to_profile_form = AddDeviceToProfileForm(request.form, csrf_enabled=False)
    device = db.session.query(Device).filter_by(number=devicenumber).first()
    device_id_form = DeviceIdForm(obj=DeviceIdDescription(device.id))
    add_device_to_profile_form = AddDeviceToProfileForm(obj=AddDeviceToProfileFormValues(device.name, device.number), csrf_enabled=False)
    return render_template('dacbrowser/device.html', device=device, add_device_to_profile_form=add_device_to_profile_form, device_id_form=device_id_form)

class ProfileDescription(object):
    def __init__(self, number, profile):
        profile_id = profile.id
        self.profile_id = profile_id
        self.number = number
        profile_name = profile.name
        self.profile_name = profile_name
        self.team = 'Unknown'
        self.devices_number = len(profile.profile_devices)

@mod_browser.route('/getdeviceprofileslist/', methods=['GET'])
@customer_permission.require(http_exception=403)
def get_device_profiles_list():
    page = 1
    records_per_page = 3
    args = request.args
    per_page = args.get('per_page')
    page_num = args.get('page_num')
    if page_num == '':
        page_num = '1'
    filter_predicate = args.get('filter_predicate')
    device_id = args.get('device_id')
    if per_page != None and page_num != None and filter_predicate != None:
        records_per_page = int(per_page)
        page = int(page_num)
        devicenumber = filter_predicate
        device_id = args.get('device_id')
        select_profiles_condition = int(args.get('select_profiles_condition'))
    
    edit_profiles_form = EditProfilesForm(obj=DeviceIdDescription(device_id), csrf_enabled=False)

    profiles = None
    paginated_profiles = []

    associations_containing_this_device = DeviceProfileAssociation.query.filter(DeviceProfileAssociation.device_number.in_((devicenumber,)))
    containing_this_device_profiles_ids = [association.profile_id for association in associations_containing_this_device]
    submit_edit_button_text = '- Remove from profiles'

    if select_profiles_condition == 0:
        profiles = Profile.query.filter(Profile.id.in_(containing_this_device_profiles_ids))
    if select_profiles_condition == 1:
        profiles = Profile.query.filter(not_(Profile.id.in_(containing_this_device_profiles_ids)))
        submit_edit_button_text = '+ Add to profiles'

    if profiles != None:
        paginated_profiles = profiles.paginate(page, records_per_page, False)

        if page > paginated_profiles.pages:
            page = paginated_profiles.pages
            paginated_profiles = profiles.paginate(page, records_per_page, False)

        i = 1
        for profile in paginated_profiles.items:
            edit_profiles_form.profiles.append_entry(ProfileDescription(str((page - 1) * records_per_page + i), profile))
            i = i + 1

    profiles_list = render_template('dacbrowser/deviceprofilestable.html', submit_edit_button_text=submit_edit_button_text, edit_profiles_form=edit_profiles_form)
    pagination_links_html = render_template('render_pagination.html', pagination=paginated_profiles) 
    return jsonify(item_list=profiles_list,  pagination=pagination_links_html)

@mod_browser.route('/starteditprofiles/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_edit_profiles():
    edit_profiles_form = EditProfilesForm(request.form, csrf_enabled=False)

    profiles_ids_list = [] 
    device_id = edit_profiles_form.device_id.data
    for profile_info in edit_profiles_form.profiles.data:
        profile_id = profile_info.get('profile_id')
        select_to_edit = profile_info.get('select_to_edit')
        if select_to_edit:
            profiles_ids_list.append(profile_id)
    edit_profiles_task = edit_profiles.delay([device_id], profiles_ids_list)
    edit_profiles_task_id = edit_profiles_task.task_id
    return jsonify(task_id=edit_profiles_task_id)

@mod_browser.route('/editprofilesprogress/', methods=['POST'])
@customer_permission.require(http_exception=403)
def edit_profiles_progress():
    print 'Call edit_profiles_progress'
    state = 'notready'
    edit_profiles_result_data = {}
    edit_profiles_task_id = request.data
    edit_profiles_result = edit_profiles.AsyncResult(edit_profiles_task_id)
    if edit_profiles_result.ready():
        print 'Task %s ready!' % edit_profiles_task_id
        state = 'ready'
        edit_profiles_result_data = edit_profiles_result.result
    else:
        print 'Task %s is not ready!' % edit_profiles_task_id
    return_value = jsonify(state=state, result_value={})
    print 'edit_profiles_result_data: ', edit_profiles_result_data
    try:
        return_value = jsonify(state=state, result_value=edit_profiles_result_data)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value

@celery.task
def edit_profiles(devices_ids_list, profiles_ids_list):
    result = None
    try:
        result = apple_account_processor.edit_profiles(devices_ids_list, profiles_ids_list)
    except (IOError, URLError, TypeError) as edit_profiles_error:
        app.logger.error(edit_profiles_error)

    return result

## end device page section


## begin profile page section

class ProfileIdDescription(object):
    def __init__(self, profile_id):
        self.profile_id = profile_id

class DeviceDescription(object):
    def __init__(self, number, device):
        self.number = number
        self.device_number = device.number
        self.device_name = device.name
        self.device_id = device.id

@mod_browser.route('/profile/<profileid>')
@member_permission.require(http_exception=403)
def profile(profileid):
    profile = db.session.query(Profile).filter_by(id=profileid).one()
    return render_template('dacbrowser/profile.html', profile=profile)

@mod_browser.route('/starteditprofile/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_edit_profile():
    edit_profile_form = EditProfileForm(request.form, csrf_enabled=False)
    devices_ids_list = [] 
    profile_id = edit_profile_form.profile_id.data
    for device_description in edit_profile_form.devices.data:
        device_id = device_description.get('device_id')
        select_to_edit = device_description.get('select_to_edit')
        if select_to_edit:
            devices_ids_list.append(device_id)
    edit_profile_task = edit_profiles.delay(devices_ids_list, [profile_id])
    edit_profile_task_id = edit_profile_task.task_id
    return jsonify(task_id=edit_profile_task_id)

@mod_browser.route('/editprofileprogress/', methods=['POST'])
@customer_permission.require(http_exception=403)
def edit_profile_progress():
    print 'Call edit_profile_progress'
    state = 'notready'
    edit_profile_result_data = {}
    edit_profile_task_id = request.data
    edit_profile_result = edit_profiles.AsyncResult(edit_profile_task_id)
    if edit_profile_result.ready():
        print 'Task %s ready!' % edit_profile_task_id
        state = 'ready'
        edit_profile_result_data = edit_profile_result.result
    else:
        print 'Task %s is not ready!' % edit_profile_task_id
    return_value = jsonify(state=state, result_value={})
    print 'edit_profile_result_data: ', edit_profile_result_data
    try:
        return_value = jsonify(state=state, result_value=edit_profile_result_data)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value

@mod_browser.route('/getprofiledeviceslist/')
@member_permission.require(http_exception=403)
def get_profile_devices_list():
    page = 1
    records_per_page = 3
    args = request.args
    page_num = args.get('page_num')
    per_page = args.get('per_page')
    if page_num == '':
        page_num = '1'
    filter_predicate = args.get('filter_predicate')
    select_devices_condition_str = args.get('select_devices_condition')
    if select_devices_condition_str == '':
        select_devices_condition_str = '0'
    devices_list = ''
    pagination_links_html = ''
    if per_page != None and page_num != None and filter_predicate != None:
        records_per_page = int(per_page)
        page = int(page_num)
        profile_id = filter_predicate
        select_devices_condition = int(select_devices_condition_str)
        
    edit_profile_form = EditProfileForm(obj=ProfileIdDescription(profile_id), csrf_enabled=False)

    devices = None
    paginated_devices = []

    associations_containing_this_profile = DeviceProfileAssociation.query.filter(DeviceProfileAssociation.profile_id.in_((profile_id,)))
    belong_to_this_profile_devices_numbers = [association.device_number for association in associations_containing_this_profile]
    submit_edit_button_text = '- Remove from profile'

    if select_devices_condition == 0:
        devices = Device.query.filter(Device.number.in_(belong_to_this_profile_devices_numbers))
    
    if select_devices_condition == 1:
        devices = Device.query.filter(not_(Device.number.in_(belong_to_this_profile_devices_numbers)))
        submit_edit_button_text = '+ Add to profile'

    if devices != None:
        paginated_devices = devices.paginate(page, records_per_page, False)

        if page > paginated_devices.pages:
            page = paginated_devices.pages
            paginated_devices = devices.paginate(page, records_per_page, False)

        i = 1
        for device in paginated_devices.items:
            edit_profile_form.devices.append_entry(DeviceDescription(str((page - 1) * records_per_page + i), device))
            i = i + 1
    pagination_links_html = render_template('render_pagination.html', pagination=paginated_devices) 
    devices_list = render_template('dacbrowser/profiledevicestable.html', edit_profile_form=edit_profile_form, submit_edit_button_text=submit_edit_button_text)
    return jsonify(item_list=devices_list, pagination=pagination_links_html)

## end profile page section


## begin profiles page section

@mod_browser.route('/profiles/')
@member_permission.require(http_exception=403)
def profiles():
    return render_template('dacbrowser/profiles.html')

@mod_browser.route('/getprofileslist/')
@member_permission.require(http_exception=403)
def get_profiles_list():
    page=1
    records_per_page = 3 
    args = request.args
    page_num = args.get('page_num')
    if page_num == '':
        page_num = '1'
    if args.get('per_page') != None and page_num != None:
        records_per_page = int(args.get('per_page'))
        page = int(page_num)
    displayed_records = []
    profiles = Profile.query.paginate(page, records_per_page, False)
    if page > profiles.pages:
        page = profiles.pages
        profiles = Profile.query.paginate(page, records_per_page, False)
    i = 1
    for profile in profiles.items:
        displayed_records.append({'number' : str((page - 1) * records_per_page + i), 'profile_id' : profile.id , 'name' : profile.name, 'total' : len(profile.profile_devices)})
        i = i + 1
    profiles_list = render_template('dacbrowser/profilestable.html', profiles_descriptions = displayed_records)
    pagination_links_html = render_template('render_pagination.html', pagination=profiles) 
    return jsonify(item_list=profiles_list,  pagination=pagination_links_html)

## end profile page section


## begin all update page section

@mod_browser.route('/update/', methods=['GET'])
@customer_permission.require(http_exception=403)
def update():
    present_devices_num = None
    new_devices_num = None
    update_all_form = UpdateAllForm(request.form, csrf_enabled=False)
    return render_template('dacbrowser/update.html', update_all_form=update_all_form, present_devices_num=present_devices_num, new_devices_num=new_devices_num)

@mod_browser.route('/startallupdate/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_all_update():
    all_update_task_id = ''
    if request.method == 'POST':
        all_update_task = dacupdate.delay()
        all_update_task_id = all_update_task.task_id
    return jsonify(task_id=all_update_task_id)

@mod_browser.route('/allupdateprogress/', methods=['POST'])
@customer_permission.require(http_exception=403)
def all_update_progress():
    print 'call all_update_progress'
    state = 'notready'
    result_value = ()
    all_update_task_id = request.data
    print 'all_update task_id: ', all_update_task_id
    all_update_result = dacupdate.AsyncResult(all_update_task_id)
    if all_update_result.ready():
        print 'All update task %s ready!' % all_update_task_id
        state = 'ready'
        print 'All update result: ', all_update_result.result
        result_value = all_update_result.result
        if result_value == None:
            result_value = {}
    else:
        print 'All update task %s not ready!' % all_update_task_id
    return_value = jsonify(state=state, result_value={})
    try:
        return_value = jsonify(state=state, result_value=result_value)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value

@celery.task
def dacupdate():
    result = None
    try:
        result = apple_account_processor.update_profile_and_device_tables()
    except (SQLAlchemyError, URLError, IOError) as update_error:
        print 'update error: ', update_error
        app.logger.error(update_error)
    return result

## end all update page section


## being replace edited profiles section

@mod_browser.route('/startreplaceeditedprofiles/', methods=['POST'])
@customer_permission.require(http_exception=403)
def start_replace_edited_profiles():
    replace_edited_profiles_task_id = ''
    if request.method == 'POST':
        print 'json.loads(request.data): ', json.loads(request.data)

        replace_edited_profiles_task = replace_edited_profiles.delay(json.loads(request.data))
        replace_edited_profiles_task_id = replace_edited_profiles_task.task_id

    return jsonify(task_id=replace_edited_profiles_task_id)
    #return jsonify(task_id='fake_task_id')

@mod_browser.route('/replaceeditedprofilesprogress/', methods=['POST'])
@customer_permission.require(http_exception=403)
def replace_edited_profiles_progress():
    print 'call replaceeditprofilesprogress'
    state = 'notready'
    result_value = ()
    replace_edited_profiles_task_id = request.data
    print 'replace_edited_profiles_task_id task_id: ', replace_edited_profiles_task_id
    replace_edited_profiles_result = dacupdate.AsyncResult(replace_edited_profiles_task_id)
    if replace_edited_profiles_result.ready():
        print 'Replace edited profiles task %s ready!' % replace_edited_profiles_task_id
        state = 'ready'
        print 'Replace edited profiles result: ', replace_edited_profiles_result.result
        result_value = replace_edited_profiles_result.result
        if result_value == None:
            result_value = {}
    else:
        print 'Replace edited profiles task %s not ready!' % replace_edited_profiles_task_id
    return_value = jsonify(state=state, result_value={})
    try:
        return_value = jsonify(state=state, result_value=result_value)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value


@celery.task
def replace_edited_profiles(edited_profiles):
    result = None
    try:
        result = apple_account_processor.replace_edited_profiles(edited_profiles)
    except (SQLAlchemyError, URLError, IOError) as replace_error:
        print 'replace error: ', replace_error
        app.logger.error(replace_error)
    return result

## end replace edited profiles section
