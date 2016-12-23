from flask import Blueprint

material = Blueprint('material', __name__,
                     template_folder='templates',
                     static_folder='static')

from emotiv.material import views
