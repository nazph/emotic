from datetime import date, timedelta
import itertools

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, DateField, IntegerField, validators, \
    SubmitField, RadioField, SelectMultipleField, TextAreaField, FieldList, Field
from wtforms.validators import ValidationError

from emotiv.experiment import filters
from emotiv.models import Attribute


class GreaterThan(object):
    """
    Compares the value of two fields the value of self is to be greater than the supplied field.

    :param fieldname:
        The name of the other field to compare to.
    :param message:
        Error message to raise in case of a validation error. Can be
        interpolated with `%(other_label)s` and `%(other_name)s` to provide a
        more helpful error.
    """

    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(field.gettext(u"Invalid field name '%s'.") % self.fieldname)
        if field.data != '' and field.data < other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname
            }
            if self.message is None:
                self.message = field.gettext(u'Field must be greater than %(other_name)s.')

            raise ValidationError(self.message % d)


class ExperimentFormStep1(Form):
    name = StringField('Name of Experiment', [validators.DataRequired(), validators.Length(min=1, max=255)])
    description = StringField('Short description of Experiment', [validators.Length(min=0, max=1024)])
    next_button = SubmitField('Next')


class PhaseForm(Form):
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=1, max=255)])


class ExperimentFormStep2(Form):
    template = RadioField('', coerce=int, default=0)


class FilterField(Field):
    def __init__(self, label='', validators=None, **kwargs):
        super(FilterField, self).__init__(label, validators, **kwargs)
        self.validators = list(
            itertools.chain(
                self.validators,
                [lambda form, field: filters.validate(*self.data)]))

    @property
    def data(self):
        return (self.attribute_id, self.parameters)

    def process(self, formdata, data=None):
        self.process_errors = []
        if data:
            try:
                self.attribute_id, self.parameters = data
            except TypeError:
                self.process_errors.append('Must pass name and parameters of filter')

        if not formdata:
            return

        def first_or_none(key, param=True, coerce=lambda x: x):
            key = self.name + ('-p-' if param else '-') + key
            if key in formdata:
                return coerce(formdata.getlist(key)[0])
            return None

        self.attribute_id = first_or_none('attribute_id', coerce=int, param=False)
        attribute = Attribute.query.get(self.attribute_id)
        if not attribute:
            self.process_errors.append('invalid attribute_id: {}'.format(self.attribute_id))
            return
        _type = attribute.input_type
        self.label = attribute.name
        if _type in ['ss', 'ms']:
            self.parameters = {
                'selected': map(int, formdata.getlist(self.name + '-p-selected'))
            }
        elif _type == 'dt':
            self.parameters = {
                'low': first_or_none('low'),
                'high': first_or_none('high'),
            }
        elif _type == 'nm':
            def parseNum(s):
                return int(s) if s and s.strip() else None
            self.parameters = {
                'low': first_or_none('low', coerce=parseNum),
                'high': first_or_none('high', coerce=parseNum),
            }
        elif _type == 'ot':
            self.parameters = {'text': first_or_none('text')}


class ExperimentFormStep3(Form):
    filters = FieldList(FilterField())
    criteria_suggestion = TextAreaField()


class ExperimentFormStep4(Form):
    attributes = SelectMultipleField('', coerce=int)
    attribute_suggestion = TextAreaField()


class ExperimentFormStep5(Form):
    private = BooleanField('Private')
    allow_repeats = BooleanField('Allow Repeats')


class CalibrationLength(Form):
    length = IntegerField('Length', [validators.DataRequired(), validators.NumberRange(min=120, max=1200)])


def _end_date_or_record_limit(form, field):
    if not form.end_date.data and not form.recordings_collected.data:
        field.errors[:] = []
        raise validators.StopValidation('Must set an end date or a maximum number of recordings.')


class ExperimentFormStep6(Form):
    recordings_collected = IntegerField(
        'Number to collect',
        [_end_date_or_record_limit,
            validators.Optional(),
            validators.NumberRange(min=0, max=10**9)],
        default=0)

    start_date = DateField('Start Date', [validators.DataRequired()])
    end_date = DateField(
        'End Date', [_end_date_or_record_limit, validators.Optional()])
    eye_tracking = BooleanField('Enable Eye-tracking')
    web_tracking = BooleanField('Enable Web-tracking')

    def validate_start_date(form, field):
        if field.data < date.today() - timedelta(days=1):
            raise ValidationError('Experiment cannot start in the past.')

    def validate_end_date(form, field):
        if field.data is not None and form.start_date is not None:
            if field.data != '' and field.data < form.start_date.data:
                raise ValidationError('Experiment cannot end before it has started')

