import os
import subprocess

from flask import Flask

# module level
app = Flask(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

def compile_jsx(filename):
    return unicode(subprocess.check_output(['npm', 'run', '-s', 'babel', filename]), 'utf-8')

app.jinja_env.globals['compile_jsx'] = compile_jsx

app.config.from_envvar('application.cfg')
app.jinja_env.globals['production'] = app.config.get('PRODUCTION', False)
app.jinja_env.globals['allowed_image_extensions'] = list(app.config.get(
    'ALLOWED_IMAGE_EXTENSIONS'))
app.jinja_env.globals['allowed_audio_extensions'] = list(app.config.get(
    'ALLOWED_AUDIO_EXTENSIONS'))
app.jinja_env.globals['allowed_video_extensions'] = list(app.config.get(
    'ALLOWED_VIDEO_EXTENSIONS'))

if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

basedir = os.path.abspath(os.path.dirname(__file__))

if app.config['DEV']:
    # Delete the DB
    try:
        os.remove(basedir + '/emotiv-builder.db')
    except Exception as ex:
        print(ex.args[1])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
