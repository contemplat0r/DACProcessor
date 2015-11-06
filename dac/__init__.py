import os, sys
from flask import Flask, render_template
from werkzeug import generate_password_hash
from flask_bootstrap import Bootstrap, StaticCDN

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.principal import Principal
from sqlalchemy.exc import SQLAlchemyError

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

#from celery import Celery

app = Flask(__name__)

'''
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
'''

file_handler = RotatingFileHandler('dac.log', maxBytes=100000, backupCount=1)
file_handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s ' '[in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.config.from_object('config')

Bootstrap(app)

app.extensions['bootstrap']['cdns']['jquery'] = StaticCDN()

db = SQLAlchemy(app)

Principal(app)

login_manager = LoginManager()
login_manager.init_app(app)


from dac.users.views import mod_users
from dac.dacbrowser.controllers import mod_browser

app.register_blueprint(mod_users, url_prefix='/users')
app.register_blueprint(mod_browser, url_prefix='/browser')
db.create_all()

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

