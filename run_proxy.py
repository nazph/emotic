#!/usr/bin/python
from werkzeug.contrib.fixers import ProxyFix

from emotiv import app

app.wsgi_app = ProxyFix(app.wsgi_app)
