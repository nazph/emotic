from flask import Blueprint

organization = Blueprint('organization', __name__,
                         template_folder='templates',
                         static_folder='static')

from emotiv.organization import views
