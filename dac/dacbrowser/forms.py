from flask.ext.wtf import Form
from wtforms import SubmitField, TextField, HiddenField, FileField, BooleanField, FieldList, FormField
from wtforms.validators import Required, EqualTo

class UpdateAllForm(Form):
    submit = SubmitField('Update all')

class AddDeviceForm(Form):
    name = TextField('Name', [Required()])
    udid = TextField('UDID', [Required()])
    submit = SubmitField('Add')

class AddDeviceToProfileForm(Form):
    name = HiddenField('Name')
    udid = HiddenField('UDID')
    submit = SubmitField('+ Add to profile')

class AddMultipleDevicesForm(Form):
    devices_list_file = FileField(label='Devices list file', id='deviceslistfile')
    #another_file = FileField(label='Another file', id='anotherfile')
    submit = SubmitField('Send')

class DeviceIdForm(Form):
    device_id = HiddenField('DeviceID')

class ProfileDescriptionForm(Form):
    profile_id = HiddenField('ProfileID')
    number = HiddenField('Number')
    profile_name = HiddenField('Name')
    team = HiddenField('Team')
    devices_number = HiddenField('DevicesNumber')
    select_to_edit = BooleanField()

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(ProfileDescriptionForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class EditProfilesForm(Form):
    device_id = HiddenField('DeviceID')
    profiles = FieldList(FormField(ProfileDescriptionForm))
    #submit_edit_command = SubmitField('+ Add to profiles')

class DeviceDescriptionForm(Form):
    number = HiddenField('Number')
    device_name = HiddenField('Name')
    device_number = HiddenField('DeviceNumber')
    device_id = HiddenField('DeviceID')
    select_to_edit = BooleanField()

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(DeviceDescriptionForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)


class EditProfileForm(Form):
    profile_id = HiddenField('ProfileID')
    devices = FieldList(FormField(DeviceDescriptionForm))
