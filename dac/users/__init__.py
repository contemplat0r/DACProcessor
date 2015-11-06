from dac import app, db, login_manager
from ldap import initialize, LDAPError as LdapError, INVALID_CREDENTIALS as LdapInvalidCredentialsException
ldap_server = app.config.get('LDAP_SERVER')
ldap_base_dn = app.config.get('LDAP_BASE_DN')
ldap_connection_timeout = app.config.get('LDAP_CONNECTION_TIMEOUT')
ldap_chief_user_name = app.config.get('LDAP_CHIEF_USER_NAME')
ldap_chief_user_password = app.config.get('LDAP_CHIEF_USER_PASSWORD')

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
    return ldap_connection

def connect_to_ldap(ldap_chief_user_name, ldap_base_dn, ldap_chief_user_password):
    message = ''
    ldap_distinguished_name = 'cn=' + ldap_chief_user_name + ',' + ldap_base_dn
    print ldap_distinguished_name
    ldap_connection = create_ldap_connection(ldap_server, ldap_connection_timeout)
    if ldap_connection != None:
        try:
            ldap_connection.simple_bind_s(ldap_distinguished_name, ldap_chief_user_password)
            message = 'LDAP auth success'
        except LdapInvalidCredentialsException:
            message = 'LDAP invalid credentials'
            ldap_connection = None
        except LdapError:
            message = 'LDAP server error'
            ldap_connection = None
    return ldap_connection, message

