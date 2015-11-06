import os
from datetime import timedelta

from ldap import SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE, SCOPE_SUBORDINATE

_basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_basedir, 'dac.db')
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 4
CSRF_ENABLED = True
CSRF_SESSION_KEY = 'abc'
SECRET_KEY = 'abc'

#APPLE_USER_LOGIN = '<Apple user login>'
#APPLE_USER_PASSWORD = '<Apple user password>'
APPLE_USER_LOGIN = ''
APPLE_USER_PASSWORD = ''


LDAP_SERVER = 'ldap://192.168.1.125'
LDAP_BASE_DN = 'ou=people,dc=local'
LDAP_SEARCH_FILTER = '(objectclass=inetorgperson)'
LDAP_SEARCH_SCOPE = SCOPE_ONELEVEL
LDAP_CONNECTION_TIMEOUT = '4.0'
LDAP_CHIEF_USER_NAME = 'Ldapchief Ldap0'
LDAP_CHIEF_USER_PASSWORD = 'ldapchief'

ADMIN_UID = 'admin.coderivium'
ADMIN_GIVEN_NAME = 'Admin'
ADMIN_SURNAME = 'Coderivium'
ADMIN_MAIL = 'dacadmin@coderivium.com'
ADMIN_PASSWORD = 'admin'

#CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
#BROKER_URL = 'sqla+sqlite:///celerydb.sqlite'
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_SCHEDULE_PERIOD = 1800 # in seconds
CELERYBEAT_SCHEDULE = {
    'periodic-dac-update' : {
        'task' : 'dac.dacbrowser.controllers.dacupdate',
        'schedule' : timedelta(seconds=CELERY_SCHEDULE_PERIOD),
    }
}

BROWSER_TIMEOUT = 10
