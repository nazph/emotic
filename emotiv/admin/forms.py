from flask.ext.wtf import Form
from wtforms import StringField, validators, \
    SelectField, TextAreaField, FieldList, ValidationError, FormField, HiddenField

class OptionForm(Form):
    value = StringField('Value')
    content_type = HiddenField('Content Type')

class AttributeForm(Form):
    """Form encoding for new attributes. """

    # If you update the max name length, also update it in emotiv/models.py
    name = StringField('Question', [validators.DataRequired(),
                                validators.Length(min=1, max=64)])
    input_type = SelectField('Input Type',
                             choices=[
                                 ('ss', 'Single Select Multiple Choice'),
                                 ('ms', 'Multi Select Multiple Choice'),
                                 ('ot', 'Open Text'),
                                 ('nm', 'Numeric'),
                                 ('dt', 'Date')
                             ])
    criteria_options = FieldList(HiddenField('Criteria Options'))
    content_types = FieldList(HiddenField('Content Type'))

    def validate_criteria_option(form, field):
        if form.input_type.data in ['ss', 'ms']:
            if len(field.entries) == 0:
                raise ValidationError('Must have at least one option.')


class CommentForm(Form):
    """Form for approving/denying things."""
    comment = TextAreaField('Comment')
