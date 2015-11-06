from dac import db
from dac.users import constants
from dac.sqltypes import Model, Column, String, Integer, SmallInteger, LargeBinary, ForeignKey, relationship, backref

class User(Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    uid = Column(String(128), nullable=False, unique=True)
    common_name = Column(String(128), nullable=False)
    surname = Column(String(64), nullable=False)
    given_name = Column(String(64), nullable=False)
    mail = Column(String(128), nullable=False)
    role = Column(SmallInteger, default=constants.CUSTOMER)
    auth_type = Column(SmallInteger, default=constants.LOCAL)
    password = Column(String(192), nullable=False)

    #def __init__(self, uid, given_name, surname, mail, role, auth_type, password):
    def __init__(self, uid, common_name, given_name, surname, mail, role, auth_type, password):
        self.uid = uid 
        #self.common_name = '%s %s' % (given_name, surname)
        self.common_name = common_name
        self.given_name = given_name
        self.surname = surname
        self.mail = mail
        self.role = role
        self.auth_type = auth_type
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def get_status(self):
        return constants.STATUS[self.status]

    def get_role(self):
        return constants.ROLE[self.role]

    def get_auth_type(self):
        return constants.AUTH_TYPE[self.auth_type]

    def __repr__(self):
        return '<User: %s>' % self.common_name
