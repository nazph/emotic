import logging
from logging.handlers import WatchedFileHandler

from flask import current_app, render_template
from flask_mail import Mail
from flask_mail import Message

# Import Module
from emotiv.app import app
from emotiv.db_setup import init_db
from emotiv.admin import admin
from emotiv.experiment import experiment
from emotiv.material import material
from emotiv.organization import organization
from emotiv.phase import phase
from emotiv.user import user
from emotiv.dashboard import dashboard

from emotiv import views

# Not really doing anything with this yet, but maybe in the future?
mail = Mail(app)


@app.template_filter('minus_time')
def minus_time(value):
    value = str(value).replace("00:00:00", "")
    return value.strip()


@app.template_filter('not_token')
def not_token(value):
    return value.text != "Csrf Token"


@app.before_first_request
def setup_logging():
    """
    Setup logging - not required for production but makes
    troubleshooting easier.
    """
    handler = WatchedFileHandler("/tmp/emotiv-builder_app.log")
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def send_mail(subject, recipient, sender, template, **context):
    msg = Message(subject, sender=sender, recipients=[recipient])

    ctx = ('email', template)
    msg.body = render_template('%s/%s.txt' % ctx, **context)
    msg.html = render_template('%s/%s.html' % ctx, **context)

    mail_ext = current_app.extensions.get('mail')
    mail_ext.send(msg)


if app.config['DEV']:
    init_db()

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(experiment, url_prefix='/experiments')
app.register_blueprint(material, url_prefix='/material')
app.register_blueprint(organization, url_prefix='/organization')
app.register_blueprint(phase, url_prefix='/phases')
app.register_blueprint(user, url_prefix='/users')
app.register_blueprint(dashboard, url_prefix='/dashboard')
