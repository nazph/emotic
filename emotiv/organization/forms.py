from flask.ext.wtf import Form
from wtforms import StringField, validators


class NewOrganizationForm(Form):
    name = StringField('Organization Name', [validators.DataRequired()])
