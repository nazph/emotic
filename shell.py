import os
import readline
from pprint import pprint

from flask import *

from emotiv.database import *
from emotiv.models import *


os.environ['PYTHONINSPECT'] = 'True'
