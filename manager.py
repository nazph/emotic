#!/usr/bin/python
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager

from emotiv import app
from emotiv.models import *
from emotiv.database import db

app.config.from_envvar('/emotiv/application.cfg')

migrate = Migrate(app, db)

manager = Manager(app)

manager.add_command('db', MigrateCommand)

# manager.add_command('shell', open_shell)


if __name__ == '__main__':
    manager.run()
