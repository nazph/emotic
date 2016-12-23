from flask import Blueprint

phase = Blueprint('phase', __name__,
                  template_folder='templates',
                  static_folder='static')

from emotiv.phase import views
