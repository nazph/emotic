from flask import Blueprint

user = Blueprint('user', __name__,
                 template_folder='templates',
                 static_folder='static')

from emotiv.user import views, auth_views
