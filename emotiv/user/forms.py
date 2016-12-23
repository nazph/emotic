from flask.ext.wtf import Form
from wtforms import validators, PasswordField, StringField

from emotiv.forms import complexity_check


class ChangePasswordForm(Form):
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', [validators.DataRequired(), validators.length(min=8, max=32),
                                                  complexity_check, validators.EqualTo('confirm_password',
                                                                                       message="Passwords must match")])
    confirm_password = PasswordField('Confirm Password')


class LoginForm(Form):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
