from flask import Blueprint, request, render_template, flash, session, redirect, url_for, current_app, g, jsonify
from werkzeug import check_password_hash, generate_password_hash
from flask.ext.login import login_user , logout_user , current_user , login_required
from flask.ext.principal import Identity, AnonymousIdentity, Permission, UserNeed, RoleNeed, identity_changed, identity_loaded

from wtforms import TextField, PasswordField, BooleanField, SelectField, FormField, FieldList
import hashlib

from sqlalchemy import inspect

from . import app, db, login_manager
from dac import SQLAlchemyError
from ldap_utils import get_ldap_objects
from dac.users.forms import LoginForm, RegisterForm, ListUsersForm, LDAPSyncForm
from dac.users.models import User
from dac.users.constants import CUSTOMER, MEMBER, ADMIN, ROLE, LOCAL, LDAP, AUTH_TYPE
from ldap import initialize, LDAPError as LdapError, INVALID_CREDENTIALS as LdapInvalidCredentialsException
import ldap
from celery import Celery


WTF_CSRF_ENABLED = False

mod_users = Blueprint('users', __name__)

login_manager.login_view = 'auth_progress'

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

@celery.task
def ldap_sync():
    sqlalchemy_session = db.session
    result_message = 'Sync done'
    ldap_search_result = get_ldap_objects()
    if ldap_search_result != None:
        new_users = []
        users_to_delete = []
        exists_users = []
        ldap_users_dict = dict()
        ldap_users_dict_by_uid = dict()
        for distinguished_name, object_description in ldap_search_result:
            ldap_user_description = object_description
            if ldap_user_description != None:
                ldap_user_uid_list = ldap_user_description.get('uid')
                ldap_user_cn_list = ldap_user_description.get('cn')
                ldap_user_given_name_list = ldap_user_description.get('givenName')
                ldap_user_surname_list = ldap_user_description.get('sn')
                ldap_user_mail_list = ldap_user_description.get('mail')
                ldap_user_password_list = ldap_user_description.get('sambaNTPassword')
                if ldap_user_cn_list != None and ldap_user_uid_list != None and ldap_user_given_name_list != None and ldap_user_surname_list != None and  ldap_user_mail_list != None:
                    ldap_user_cn = ldap_user_cn_list[0]
                    ldap_user_uid = ldap_user_uid_list[0]
                    ldap_user_given_name = ldap_user_given_name_list[0]
                    ldap_user_surname = ldap_user_surname_list[0]
                    ldap_user_mail = ldap_user_mail_list[0]
                    ldap_user_password = ldap_user_password_list[0]
                    ldap_users_dict[ldap_user_cn] = {'ldap_user_uid' : ldap_user_uid, 'ldap_user_given_name' : ldap_user_given_name, 'ldap_user_surname'  : ldap_user_surname, 'ldap_user_mail' : ldap_user_mail, 'ldap_user_password' : ldap_user_password }
                    ldap_users_dict_by_uid[ldap_user_uid] = {'ldap_user_cn' : ldap_user_cn, 'ldap_user_given_name' : ldap_user_given_name, 'ldap_user_surname'  : ldap_user_surname, 'ldap_user_mail' : ldap_user_mail, 'ldap_user_password' : ldap_user_password }
        all_ldap_auth_local_users = User.query.filter_by(auth_type=LDAP).all()
        ldap_auth_local_users_dict = {user.common_name : user for user in all_ldap_auth_local_users}
        local_users_cn_set = set(ldap_auth_local_users_dict.keys())
        ldap_users_cn_set = set(ldap_users_dict.keys())
        cn_to_delete_set = local_users_cn_set.difference(ldap_users_cn_set)
        cn_to_add_set = ldap_users_cn_set.difference(local_users_cn_set)
        for cn_to_delete in list(cn_to_delete_set):
            sqlalchemy_session.delete(ldap_auth_local_users_dict[cn_to_delete])
        all_local_auth_users = User.query.filter_by(auth_type=LOCAL).all()
        local_auth_users_dict = {user.uid : user for user in all_local_auth_users}
        local_users_uid_set = set(local_auth_users_dict.keys())
        ldap_users_uid_set = set(ldap_users_dict_by_uid.keys())
        local_uids_to_delete_set = local_users_uid_set.intersection(ldap_users_uid_set)
        for uid_to_delete in list(local_uids_to_delete_set):
            sqlalchemy_session.delete(local_auth_users_dict[uid_to_delete])
        sqlalchemy_session.commit()
        for cn_to_add in list(cn_to_add_set):
            ldap_user = ldap_users_dict[cn_to_add]
            sqlalchemy_session.add(User(common_name=cn_to_add, uid=ldap_user['ldap_user_uid'], given_name=ldap_user['ldap_user_given_name'], surname=ldap_user['ldap_user_surname'], mail=ldap_user['ldap_user_mail'], role=CUSTOMER, auth_type=LDAP, password=ldap_user['ldap_user_password']))
            
        sqlalchemy_session.commit()
    return result_message 

def nonlocal_ldap_user_auth_and_sync(uid, password):
    sqlalchemy_session = db.session
    print 'Call nonlocal_ldap_user_auth_and_sync'
    auth_success = False
    ldap_search_result = get_ldap_objects()
    if ldap_search_result != None:
        user_found = False
        for distinguished_name, object_description in ldap_search_result:
            ldap_user_description = object_description
            if ldap_user_description != None:
                ldap_user_uid_list = ldap_user_description.get('uid')
                ldap_user_cn_list = ldap_user_description.get('cn')
                ldap_user_given_name_list = ldap_user_description.get('givenName')
                ldap_user_surname_list = ldap_user_description.get('sn')
                ldap_user_mail_list = ldap_user_description.get('mail')
                ldap_user_password_list = ldap_user_description.get('sambaNTPassword')
                if ldap_user_cn_list != None and ldap_user_uid_list != None and ldap_user_given_name_list != None and ldap_user_surname_list != None and  ldap_user_mail_list != None:
                    ldap_user_cn = ldap_user_cn_list[0]
                    ldap_user_uid = ldap_user_uid_list[0]
                    ldap_user_given_name = ldap_user_given_name_list[0]
                    ldap_user_surname = ldap_user_surname_list[0]
                    ldap_user_mail = ldap_user_mail_list[0]
                    ldap_user_password = ldap_user_password_list[0]
                    if ldap_user_uid == uid and ldap_auth(ldap_user_password, password):
                        print 'User found'
                        auth_success = True
                        sqlalchemy_session.add(User(common_name=ldap_user_cn, uid=ldap_user_uid, given_name=ldap_user_given_name, surname=ldap_user_surname, mail=ldap_user_mail, role=CUSTOMER, auth_type=LDAP, password=hashlib.new( 'md4', password.encode('utf-16le')).digest().encode('hex').upper()))
                        sqlalchemy_session.commit()
                        break
                else:
                    # Wrong LDAP user record. Is this real case?
                    pass
    return auth_success

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return redirect(url_for('users.login'))

@mod_users.route('/profileredirect/')
@customer_permission.require(http_exception=403)
@login_required
def profile_redirect():
    return redirect(url_for('users.home'))

@mod_users.route('/profile/')
@customer_permission.require(http_exception=403)
@login_required
def home():
    return render_template('users/profile.html', user=g.user)

@app.before_request
def before_request():
    g.user = None
    g.role = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        g.user = user
        g.role = user.get_role()

@app.errorhandler(403)
def authorisation_failed(exception):
    if hasattr(current_user, 'role'):
        flash(('Your current role is {id}. You need special privileges to access this page').format(id=current_user.get_role()))
    else:
        flash('You not authentificated. Login please')
    return redirect(url_for('users.login'))

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'role'):
        if current_user.get_role() == customer:
            identity.provides.add(customer_role)
        if current_user.get_role() == member:
            identity.provides.add(customer_role)
            identity.provides.add(member_role)
        if current_user.get_role() == admin:
            identity.provides.add(customer_role)
            identity.provides.add(member_role)
            identity.provides.add(admin_role)


@mod_users.route('/logout/')
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return redirect(url_for('users.login')) 

def ldap_auth(stored_password, password):
    print 'Call ldap_auth'
    auth_success = False
    nt_password = hashlib.new( 'md4', password.encode('utf-16le')).digest().encode('hex').upper()
    if stored_password == nt_password:
        print 'ldap_auth: stored_password == nt_password'
        auth_success = True
    else:
        print 'ldap_auth: stored_password != nt_password'
    return auth_success

@celery.task
def auth(user, uid, password):
    auth_success = False
    if user:
        stored_password = user.password
        if user.auth_type == LOCAL:
            auth_success = check_password_hash(stored_password, password)
        if user.auth_type == LDAP:
            auth_success = ldap_auth(stored_password, password)
    else:
        print 'User is None'
        auth_success = nonlocal_ldap_user_auth_and_sync(uid, password)
    return auth_success

def user_auth(user, uid, password):
    auth_success = False
    if user:
        stored_password = user.password
        if user.auth_type == LOCAL:
            auth_success = check_password_hash(stored_password, password)
        if user.auth_type == LDAP:
            auth_success = ldap_auth(stored_password, password)
    else:
        print 'User is None'
        auth_success = nonlocal_ldap_user_auth_and_sync(uid, password)
    return auth_success


@mod_users.route('/login/', methods=['GET', 'POST'])
def login():
    auth_success = False
    ldap_invalid_credentials = False
    ldap_server_down = False
    form = LoginForm(request.form)
    if form.validate_on_submit():
        uid = form.uid.data
        user = User.query.filter_by(uid=uid).first()
        print user
        auth_success = user_auth(user, uid, form.password.data)
        if auth_success:
            if user == None:
                user = User.query.filter_by(uid=uid).first()
            session['user_id'] = user.id
            flash('Welcome %s' % user.common_name)
            login_user(user)
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
            return redirect(url_for('users.home'))
        flash('Wrong UID', 'error-message')
    return render_template('users/login.html', form=form)

@mod_users.route('/startauth/', methods=['POST'])
def start_auth():
    user_auth_task_id = ''
    auth_success = False
    user_uid = ''
    form = LoginForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        user_uid = form.uid.data
        user = User.query.filter_by(uid=user_uid).first()
        print user
        user_auth_task = auth.delay(user, user_uid, form.password.data)
        user_auth_task_id = user_auth_task.task_id
    return jsonify(task_id=user_auth_task_id, user_uid=user_uid)

@mod_users.route('/authprogress/', methods=['GET'])
#@admin_permission.require(http_exception=404)
def auth_progress():
    print 'Call auth_progress'
    state = 'notready'
    auth_result = ''
    args = request.args
    auth_task_id = args.get('task_id')
    uid = args.get('user_id')
    auth_task_async_result = auth.AsyncResult(auth_task_id)
    if auth_task_async_result.ready():
        print 'Task %s ready!' % auth_task_id 
        state = 'ready'
        task_result_value = auth_task_async_result.result
        print 'task_result_value: ', task_result_value
        if task_result_value == False:
            auth_result = 'not authorised'
        else:
            auth_result = 'auth success'
        #return jsonify(state=state, result_value=task_result_value)
            user = User.query.filter_by(uid=uid).first()
            session['user_id'] = user.id
            flash('Welcome %s' % user.common_name)
            login_user(user)
            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
    else:
        print 'Task %s is not ready!' % auth_task_id
    print 'auth_result: ', auth_result
    return_value = jsonify(state=state, result_value='')
    try:
        return_value = jsonify(state=state, value=auth_result)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value

class UserDescription(object):
    def __init__(self, user):
        self.identifier = user.id
        self.uid = user.uid
        self.given_name = user.given_name
        self.surname = user.surname
        self.mail = user.mail
        self.auth_type = user.get_auth_type()
        self.role = user.role

@mod_users.route('/administration/', methods=['GET', 'POST'])
#@login_required
@admin_permission.require(http_exception=404)
def administration():
    ldap_sync_form = LDAPSyncForm(csrf_enabled=False, prefix='ldap_sync')
    register_form = RegisterForm(csrf_enabled=False, prefix='register')

    return render_template('users/administration.html', register_form=register_form, ldap_sync_form=ldap_sync_form)


@mod_users.route('/adduser/', methods=['POST'])
#@login_required
@admin_permission.require(http_exception=404)
def add_user():
    sqlalchemy_session = db.session
    print request.form
    page=1

    register_form = RegisterForm(request.form, csrf_enabled=False, prefix='register')
    result = 'fail'
    if request.method == 'POST' and  register_form.validate():
        uid = register_form.uid.data
        given_name = register_form.given_name.data
        surname = register_form.surname.data

        if sqlalchemy_session.query(User).filter_by(uid=uid).count() == 0:
            user = User(uid=register_form.uid.data, common_name='%s %s' % (given_name, surname), given_name=given_name, surname=surname,  mail=register_form.mail.data, role=register_form.role.data, auth_type=LOCAL, password=generate_password_hash(register_form.password.data))
            print user
            sqlalchemy_session.add(user)
            try:
                sqlalchemy_session.commit()
                result = 'success'
            except SQLAlchemyError as sqlalchemy_error:
                app.logger.error(sqlalchemy_error)
        else:
            result = 'exists'
    return jsonify(completion_code=result)


@mod_users.route('/getuserslist/', methods=['GET'])
@admin_permission.require(http_exception=404)
def get_users_list():
    users_per_page = 3
    page = 1
    args = request.args
    page_num = args.get('page_num')
    if page_num == '':
        page_num = '1'

    if args.get('per_page') != None and page_num != None:
        users_per_page = int(args.get('per_page'))
        page = int(page_num)

    paginated_users = User.query.order_by(User.common_name).paginate(page, users_per_page, False)
    if page > paginated_users.pages:
        page = paginated_users.pages
        paginated_users = User.query.order_by(User.common_name).paginate(page, users_per_page, False)
    list_users_form = ListUsersForm(csrf_enabled=False, prefix='users_list')
    for user in paginated_users.items:
        list_users_form.users.append_entry(UserDescription(user))
    users_list = render_template('users/userstable.html', list_users_form = list_users_form)
    pagination_links_html = render_template('render_pagination.html', pagination=paginated_users)
    return jsonify(item_list=users_list, pagination=pagination_links_html)


@mod_users.route('/updateuserslist/', methods=['POST'])
@admin_permission.require(http_exception=404)
def update_users_list():
    list_users_form = ListUsersForm(request.form, csrf_enabled=False, prefix='users_list')
    sqlalchemy_session = db.session
    if request.method == 'POST' and  list_users_form.validate():
        users_to_delete = []
        for user_update_info in list_users_form.users.data:
            user_id = user_update_info.get('identifier')
            role = user_update_info.get('role')
            delete = user_update_info.get('delete')
            if user_id != None:
                user = User.query.get(user_id)
                if user != None:
                    if delete and user.auth_type == LOCAL:
                        sqlalchemy_session.delete(user)
                    if user.role != role:
                        user.role = role
        result = 'fail'
        try:
            sqlalchemy_session.commit()
            result = 'success'
        except SQLAlchemyError as sqlalchemy_error:
            app.logger.error(sqlalchemy_error)

    return jsonify(completion_code=result)

@mod_users.route('/startldapsync/', methods=['POST'])
@admin_permission.require(http_exception=404)
def start_ldap_sync():
    ldap_sync_task_id = ''
    if request.method == 'POST':
        ldap_sync_task = ldap_sync.delay()
        ldap_sync_task_id = ldap_sync_task.task_id
        return jsonify(task_id=ldap_sync_task_id)


@mod_users.route('/ldapsyncprogress/', methods=['POST'])
@admin_permission.require(http_exception=404)
def ldap_sync_progress():
    state = 'notready'
    task_result_value = 'ldap sync error'
    ldap_sync_task_id = request.data
    print 'ldap_sync_progress, task_id: ', ldap_sync_task_id
    ldap_sync_task_async_result = ldap_sync.AsyncResult(ldap_sync_task_id)
    if ldap_sync_task_async_result.ready():
        print 'Task %s ready!' % ldap_sync_task_id 
        state = 'ready'
        task_result_value = ldap_sync_task_async_result.result
        if task_result_value == None:
            task_result_value = 'ldap sync error'
    else:
        print 'Task %s is not ready!' % ldap_sync_task_id
    return_value = jsonify(state=state, result_value='add device error')
    try:
        return_value = jsonify(state=state, result_value=task_result_value)
    except TypeError as json_type_error:
        app.logger.error(json_type_error)
    return return_value
