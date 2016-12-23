from collections import defaultdict
from functools import wraps
import re

from wtforms.validators import ValidationError

from emotiv.models import Attribute


_known_filters = {}
_validators = defaultdict(list)


def apply_filter(f, attributes):
    """Report whether the given set of attributes conforms to the given filter.

    Parameters:
      f: An emotiv.models.Filter to apply.
      attributes: A list of emotive.models.UserAttribute to filter against.

    Returns two values:
        accept: A boolen that is True iff the attributes pass the filter.
        need_attributes: A list of attribute ids that the User does not have
            values for that this filter needs in order to work.
    """
    attributes = [a for a in attributes if a.attribute_id == f.attribute_id and a.value != '']
    if not attributes:
        return False, [f.attribute_id]
    return _known_filters[f.attribute.input_type](f.parameters, attributes), []


def validate(attribute_id, params):
    """Check that params has correct structure for this attribute's filter."""
    attribute = Attribute.query.get(attribute_id)
    if not attribute:
        raise ValidationError('No such attribute: {}'.format(attribute_id))
    _type = attribute.input_type
    if _type not in _known_filters:
        raise ValidationError('Unrecognized filter name: "{}"'.format(_type))
    if _type in _validators:
        _validators[_type](params)


def default_filter(attribute):
    """Create a filter that accepts everything for this attribute."""
    return {
        'ss': {'selected': [o.id for o in attribute.possible_options]},
        'ms': {'selected': [o.id for o in attribute.possible_options]},
        'nm': {'low': None, 'high': None},
        'dt': {'low': None, 'high': None},
        'ot': {'text': None},
    }[attribute.input_type]


def _filter(f):
    def validate(expr, msg):
        if not expr:
            raise ValidationError(msg)
    _validators[f.__name__] = lambda(params): f(params, [], validate)

    @wraps(f)
    def wrapper(params, attributes):
        return f(params, attributes, lambda *args, **kwargs: None)

    _known_filters[f.__name__] = wrapper
    return wrapper


def option_value(attribute, option_id):
    return next(
        (o.value for o in attribute.possible_options if o.id == option_id),
        None)


@_filter
def ss(params, attributes, validate):
    validate(params['selected'], 'Must select at least one option. Otherwise this filter will exclude everyone.')
    selected = (option_value(attributes[0].attribute, id) for id in params['selected'])
    return any(x.value in selected for x in attributes)


@_filter
def ms(params, attributes, validate):
    validate(params['selected'], 'Must select at least one option. Otherwise this filter will exclude everyone.')
    selected = (option_value(attributes[0].attribute, id) for id in params['selected'])
    return any(x.value in selected for x in attributes)


@_filter
def nm(params, attributes, validate):
    low, high = params['low'], params['high']
    if low is not None and high is not None:
        validate(low < high, "Can't have end of range before start of range")
    for attribute in attributes:
        v = int(attribute.value)
        if (low is None or low < v) and (high is None or high > v):
            return True
    return False


@_filter
def ot(params, attributes, validate):
    return True


@_filter
def dt(params, attributes, validate):
    low, high = params['low'], params['high']
    validate(not low or dt.regex.match(low), 'Format dates as YYYY-MM-DD')
    validate(not high or dt.regex.match(high), 'Format dates as YYYY-MM-DD')
    if low and high:
        validate(low < high, "Can't have an ending date before the beginning date")
    for attribute in attributes:
        v = attribute.value
        if (not low or low < v) and (not high or high > v):
            return True
    return False
dt.regex = re.compile('\d\d\d\d-\d\d-\d\d')
