from flask.ext.wtf import Form
from flask_security.forms import RegisterFormMixin
from wtforms import StringField, validators, PasswordField, \
    RadioField, ValidationError


def complexity_check(form, field):
    has_upper = False
    has_lower = False
    for character in field.data:
        if character.isupper():
            has_upper = True
        if character.islower():
            has_lower = True
    if not has_upper or not has_lower:
        raise ValidationError('Password must have a lower and upper case character.')


class ChangePasswordForm(Form):
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', [validators.DataRequired(), validators.length(min=8, max=32),
                                                  complexity_check, validators.EqualTo('confirm_password', message="Passwords must match")])
    confirm_password = PasswordField('Confirm Password')


class ExtendedRegisterForm(RegisterFormMixin, Form):
    username = StringField('Username', [validators.Regexp(r'^[\w.@+-]+$'), validators.DataRequired(), validators.length(min=1, max=30)])
    password = PasswordField('Password', [validators.DataRequired(), validators.length(min=8, max=32),
                                          complexity_check])
    first_name = StringField('First Name', [validators.DataRequired(), validators.length(min=1, max=30)])
    last_name = StringField('Last Name', [validators.DataRequired(), validators.length(min=1, max=30)])
    email = StringField('Email Address', [validators.DataRequired(), validators.length(min=6, max=30),
                                          validators.Email()])
    organization_name = StringField('Organization', [validators.length(min=0, max=255)])
    builder = RadioField('', choices=[(0, 'Participate only'), (1, 'Build and participate')], default=0,
                         coerce=int)
