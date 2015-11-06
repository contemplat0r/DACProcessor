from ldap import initialize, LDAPError as LdapError, INVALID_CREDENTIALS as LdapInvalidCredentialsException
import ldap
from dac import app
ldap_server = app.config.get('LDAP_SERVER')
ldap_base_dn = app.config.get('LDAP_BASE_DN')
ldap_connection_timeout = app.config.get('LDAP_CONNECTION_TIMEOUT')
ldap_chief_user_name = app.config.get('LDAP_CHIEF_USER_NAME')
ldap_chief_user_password = app.config.get('LDAP_CHIEF_USER_PASSWORD')

ldap_search_filter = app.config.get('LDAP_SEARCH_FILTER')
if ldap_search_filter == None:
    ldap_search_filter = '(objectclass=inetorgperson)'

ldap_search_scope = app.config.get('LDAP_SEARCH_SCOPE')
if ldap_search_scope == None:
    ldap_search_scope = ldap.SCOPE_ONELEVEL

def create_ldap_connection(ldap_server, ldap_connection_timeout):
    ldap_connection = None
    timeout = None
    try:
        timeout = float(ldap_connection_timeout)
    except ValueError:
        pass
    print 'Timeout', timeout
    if ldap_server != None:
        if timeout != None:
            ldap_connection = initialize(ldap_server, timeout)
        else:
            ldap_connection = initialize(ldap_server)
    print 'create_ldap_connection: ', ldap_connection
    return ldap_connection

def connect_to_ldap():
    message = ''
    ldap_distinguished_name = 'cn=' + ldap_chief_user_name + ',' + ldap_base_dn
    ldap_connection = create_ldap_connection(ldap_server, ldap_connection_timeout)
    if ldap_connection != None:
        try:
            ldap_connection.simple_bind_s(ldap_distinguished_name, ldap_chief_user_password)
            message = 'LDAP auth success'
        except LdapInvalidCredentialsException as ldap_invalid_credentials_exception:
            app.logger.info(ldap_invalid_credentials_exception)
            message = 'LDAP invalid credentials'
            ldap_connection = None
        except LdapError:
            message = 'LDAP server error'
            ldap_connection = None
    return ldap_connection, message


def unconnect_from_ldap(ldap_connection):
    success = True
    try:
        ldap_connection.unbind_s()
    except LDAPError as ldap_error:
        app.logger.info(ldap_error)
        success = False
    return success

def get_ldap_objects():
    ldap_search_result = None
    ldap_connection, ldap_connect_message = connect_to_ldap()
    if ldap_connection != None:
        if ldap_connect_message == 'LDAP auth success':
            try:
                ldap_search_result = ldap_connection.search_s(ldap_base_dn, ldap_search_scope, ldap_search_filter)
            except LdapError as ldap_error:
                app.logger.error(ldap_error)
                print 'LdapError: ', ldap_error
                pass
            unconnect_from_ldap(ldap_connection)
    return ldap_search_result
