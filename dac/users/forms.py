from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, BooleanField, SelectField, FormField, FieldList, HiddenField, SubmitField
from wtforms.validators import Required, Email, EqualTo
from dac.users.constants import ROLE, CUSTOMER, MEMBER, ADMIN

class LoginForm(Form):
    uid = TextField('UID', [Required(message='Forgot your UID?')])
    password = PasswordField('Password', [Required(message='Must provide a password')])
    submit = SubmitField('Login')

class RegisterForm(Form):
    uid = TextField('UID', [Required()])
    given_name = TextField('Name', [Required()])
    surname = TextField('Surname', [Required()])
    mail = TextField('Mail', [Required(), Email()])
    role = SelectField('Role', choices=[(CUSTOMER, ROLE[CUSTOMER]), (MEMBER, ROLE[MEMBER]), (ADMIN, ROLE[ADMIN])], coerce=int)
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Confirm password', [Required(), EqualTo('password', message='Password must match')])
    submit = SubmitField('Register')

class UserDescriptionForm(Form):
    identifier = HiddenField('UserID')

    #uid = TextField('UID')
    uid = HiddenField('UID')
    #given_name = TextField('Name')
    given_name = HiddenField('Name')
    #surname = TextField('Surname')
    surname = HiddenField('Surname')
    #mail = TextField('mail')
    mail = HiddenField('mail')
    #auth_type = TextField('AuthType')
    auth_type = HiddenField('AuthType')
    role = SelectField('Role', choices=[(CUSTOMER, ROLE[CUSTOMER]), (MEMBER, ROLE[MEMBER]), (ADMIN, ROLE[ADMIN])], coerce=int)
    delete = BooleanField()

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserDescriptionForm, self).__init__(csrf_enabled=csrf_enabled, *args, **kwargs)

class ListUsersForm(Form):
    users = FieldList(FormField(UserDescriptionForm))
    submit = SubmitField('Update')

class LDAPSyncForm(Form):
    submit = SubmitField('LDAP Sync')
