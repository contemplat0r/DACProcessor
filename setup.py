from setuptools import setup, find_packages
#from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
        scheme['data'] = scheme['purelib']

setup(name='dacconnector',
    version='0.1',
    description='Web application for manipulating with Apple devices and provisional profiles',
    author='Nikolay Golikov',
    install_requires=[
        'flask-wtf',
        'flask-login',
        'flask-script',
        'flask-principal',
        'flask-sqlalchemy',
        'flask-bootstrap',
        'flask',
        'celery',
        'python-ldap',
        'mechanize',
        'lxml'
    ],
    #packages=find_packages(),
    packages = [
        'dac',
        'dac/users',
        'dac/dacbrowser'
    ],
    py_modules = [
        'manage',
        'config'
    ],
    package_data = {
        'dac' : 
             [
                'templates/*.html',
                'templates/forms/*.html',
                'templates/users/*.html',
                'templates/dacbrowser/*.html',
                'static/css/*.css',
        ]
    },
    package_dir = {
        'dac': 'dac'
    },
    data_files = [('', ['README.txt'])],
    zip_safe=False
)
