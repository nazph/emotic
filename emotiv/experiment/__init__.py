from flask import Blueprint

experiment = Blueprint('experiment', __name__,
                       template_folder='templates',
                       static_folder='static')

from emotiv.experiment import views
