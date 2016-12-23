from flask.ext.wtf import Form
from wtforms import StringField, validators


class PhaseForm(Form):
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=1, max=30)])


class PhaseDetailForm(Form):
    data = StringField('data', [validators.DataRequired()])
