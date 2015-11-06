from dac import db
from dac.users import constants
from dac.sqltypes import Model, Column, String, Integer, LargeBinary, ForeignKey, relationship, backref
from sqlalchemy.engine import Engine
from sqlalchemy import event

device_id_len = 40

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    print 'call set_sqlite_pragma'
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class DeviceProfileAssociation(Model):
    __tablename__ = 'device_profile_association'
    device_number = Column(String(device_id_len), ForeignKey('devices.number'), primary_key=True)
    profile_id = Column(String(10), ForeignKey('profiles.id'), primary_key=True)

    def __init__(self, device_number, profile_id):
        self.device_number = device_number
        self.profile_id = profile_id

class Device(Model):
    __tablename__ = 'devices'
    number = Column(String(device_id_len), primary_key=True)
    id = Column(String(10), nullable=True)
    name = Column(String(200), nullable=True)
    status = Column(String(1), nullable=True)
    platform = Column(String(10), nullable=True)
    device_profiles = relationship('DeviceProfileAssociation', cascade="all, delete-orphan", backref=backref('devices'))

    def __init__(self, device_number, device_dict={}):
        self.number = device_number
        self.id = device_dict.get('deviceId')
        self.name = device_dict.get('name')
        self.status = device_dict.get('status')
        self.platform = device_dict.get('devicePlatform')

    def __repr__(self):
        return 'name: %s\tid: %s\tnumber: %s\tstatus: %s\tplatform: %s' % (self.name, self.id, self.number, self.status, self.platform)

class Profile(Model):
    __tablename__ = 'profiles'

    id = Column(String(10), primary_key=True)
    name = Column(String(100))
    uuid = Column(String(36))
    certificate_count = Column(Integer)
    device_count = Column(Integer)
    date_expire = Column(String(20))
    distribution_method = Column(String(10))
    platform = Column(String(10))
    status = Column(String(7))
    type = Column(String(12))
    version = Column(String(21))
    profile_binary = Column(LargeBinary)
    #profile_devices = relationship('DeviceProfileAssociation', cascade="all, delete-orphan", backref=backref('profiles'), lazy='dynamic')
    profile_devices = relationship('DeviceProfileAssociation', cascade="all, delete-orphan", backref=backref('profiles'))

    def __init__(self, profile_dict):
        self.name = profile_dict.get('name')
        self.id = profile_dict.get('provisioningProfileId')
        self.uuid = profile_dict.get('UUID')
        self.certificate_count = profile_dict.get('certificateCount')
        self.device_count = profile_dict.get('deviceCount')
        self.date_expire = profile_dict.get('dateExpire')
        self.distribution_method = profile_dict.get('distributionMethod')
        self.platform = profile_dict.get('proProPlatform')
        self.status = profile_dict.get('status')
        self.type = profile_dict.get('type')
        self.version = profile_dict.get('version')

