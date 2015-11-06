from flask.ext.script import Manager, Server
from dac import app, db
from dac.users.models import User
from dac.users.constants import LOCAL, AUTH_TYPE, ADMIN, ROLE
from dac.users.views import generate_password_hash
from dac.dacbrowser.appleaccountprocessor import AppleAccountProcessor

apple_user_login = app.config.get('APPLE_USER_LOGIN')
apple_user_password = app.config.get('APPLE_USER_PASSWORD')

manager = Manager(app)
manager.add_command('runserver', Server(use_debugger=True, use_reloader=True, host='0.0.0.0'))

apple_account_processor = AppleAccountProcessor(apple_user_login, apple_user_password, db.session)

@manager.command
def create_database():
    db.create_all()
    no_admin = (User.query.filter_by(role=ADMIN).first() == None)
    if no_admin:
        admin_uid = app.config.get('ADMIN_UID')
        admin_given_name = app.config.get('ADMIN_GIVEN_NAME')
        admin_surname = app.config.get('ADMIN_SURNAME')
        admin_mail = app.config.get('ADMIN_MAIL')
        admin_password = app.config.get('ADMIN_PASSWORD')
        if admin_uid != None and admin_given_name != None and admin_surname != None and admin_mail != None and admin_password != None:
            print admin_uid, admin_given_name, admin_surname
            user = User(uid=admin_uid, common_name='%s %s' % (admin_given_name, admin_surname), given_name=admin_given_name, surname=admin_surname, mail=admin_mail, role=ADMIN, auth_type=LOCAL, password=generate_password_hash(admin_password))
            db.session.add(user)
            db.session.commit()
    #apple_account_processor.update_profile_and_device_tables()

if __name__ == '__main__':
    manager.run()
