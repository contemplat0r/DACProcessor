import os
import sys
import tempfile
#sys.path.append('../dac/dacbrowser')
#sys.path.append('dac')
import config
import dac
from dac.dacbrowser.controllers import *
from flask.ext.principal import Identity, AnonymousIdentity, Permission, UserNeed, RoleNeed, identity_changed, identity_loaded
from flask import request, flash, session, redirect, url_for, current_app, g, jsonify
from flask.ext.login import login_user , logout_user , current_user , login_required
from dac.users.models import User
import unittest
import mock
import json
from dac.users.constants import CUSTOMER, MEMBER, ADMIN, ROLE, LOCAL, LDAP, AUTH_TYPE

#print apple_account_processor, '\n' * 4

print 'dir(dac.app): ', dir(dac.app)

#print dac.app.config

customer = ROLE[CUSTOMER]
member = ROLE[MEMBER]
admin = ROLE[ADMIN]

customer_role = RoleNeed(customer)
member_role = RoleNeed(member)
admin_role = RoleNeed(admin)

customer_permission = Permission(customer_role)
member_permission = Permission(member_role)
admin_permission = Permission(admin_role)

roles = [customer_role, member_role, admin_role]
permissions = [customer_permission, member_permission, admin_permission]


def _on_identity_init(sender, identity):
    identity.provides.add(customer_role)
    identity.provides.add(member_role)
    identity.provides.add(admin_role)



class Test(unittest.TestCase):

    def setUp(self):
        _, temp_database_file = tempfile.mkstemp()
        #print dac.app.config
        #dac.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % temp_database_file
        print dac.app.config['SQLALCHEMY_DATABASE_URI']
        self.app = dac.app.test_client()
        print 'dir(self.app): ', dir(self.app)
        print 'self.app.application: ', self.app.application
        print 'self.app.trace: ', self.app.trace
        self.app.trace()
        dac.app.config['TESTING'] = True
        app = dac.app
        '''
        admin_uid = app.config.get('ADMIN_UID')
        admin_given_name = app.config.get('ADMIN_GIVEN_NAME')
        admin_surname = app.config.get('ADMIN_SURNAME')
        admin_mail = app.config.get('ADMIN_MAIL')
        admin_password = app.config.get('ADMIN_PASSWORD')
        if admin_uid != None and admin_given_name != None and admin_surname != None and admin_mail != None and admin_password != None:
            print admin_uid, admin_given_name, admin_surname
            user = User(uid=admin_uid, common_name='%s %s' % (admin_given_name, admin_surname), given_name=admin_given_name, surname=admin_surname, mail=admin_mail, role=ADMIN, auth_type=LOCAL, password=generate_password_hash(admin_password))
            '''


    def tearDown(self):
        pass
    
    def test_app_config(self):
        #print dac.app.config['SQLALCHEMY_DATABASE_URI']
        assert True
    
    def test_add_device(self):
        result_json = self.app.get('/browser/adddevice/', data = {'name' : 'New device', 'udid' : '2lsalls'}, follow_redirects=True)
        print 'test_add_device', result_json
        #print result_json.data
        #result = json.loads(result_json)
        #print result
        assert True

    def test_start_auth(self):
        #result_json = self.app.post('/users/startauth/', data = {'uid' : 'admin.coderivium', 'password' : 'admin' }, headers={'content-type' : 'application/x-www-form-urlencoded'}, follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', data='uid=admin.coderivium&password=admin', headers={'content-type' : 'application/x-www-form-urlencoded'}, follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', query_string='uid=admin.coderivium&password=admin', headers={'content-type' : 'application/x-www-form-urlencoded'}, follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', query_string='uid=admin.coderivium&password=admin', content_type='application/x-www-form-urlencoded; charset=UTF-8', follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', data='uid=admin.coderivium&password=admin', content_type='application/x-www-form-urlencoded; charset=UTF-8', follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', data='uid=admin.coderivium&password=admin', content_type='application/x-www-form-urlencoded; charset=UTF-8', follow_redirects=True)
        #result_json = self.app.post('/users/startauth/', data = dict(uid='admin.coderivium', password='admin'), content_type='application/x-www-form-urlencoded; charset=UTF-8', follow_redirects=True)
        result_json = self.app.post('/users/startauth/', data = {'password' : 'admin', 'uid' : 'admin.coderivium'}, content_type='application/x-www-form-urlencoded; charset=UTF-8', follow_redirects=True)
        print result_json
        print result_json.data
        assert True

