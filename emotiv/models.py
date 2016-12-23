from datetime import datetime
from itertools import chain
import json

from flask.ext.security import SQLAlchemyUserDatastore, UserMixin, RoleMixin
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import TypeDecorator, LargeBinary

from emotiv.database import db


class BaseMixin(object):
    """
        Applies base columns to models.
    """
    id = db.Column(db.Integer(), primary_key=True)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    changed_at = db.Column(db.DateTime(), onupdate=datetime.now)


class OrganizationMixin(object):
    """
        Applies organization relationship to models.
    """

    @declared_attr
    def organization(cls):
        return db.relationship('Organization')

    @declared_attr
    def organization_id(cls):
        return db.Column(db.Integer(), db.ForeignKey('organization.id'))


class Attribute(db.Model, BaseMixin):
    # If you update the max length here, also update emotiv/admin/forms.py
    name = db.Column(db.String(64), index=True, unique=True, nullable=False)
    input_type = db.Column(db.String(2), nullable=False)

    # For inputs of type 'ms' or 'ss'.
    possible_options = db.relationship('SelectOption', back_populates='attribute', cascade='all, delete-orphan')


class SelectOption(db.Model, BaseMixin):
    attribute = db.relationship('Attribute', back_populates='possible_options')
    attribute_id = db.Column(db.Integer(), db.ForeignKey('attribute.id'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(1))


# Based on
# http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html#marshal-json-strings
class JSONDict(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Filter(db.Model, BaseMixin):
    """A filter for an attribute.

    Experiment builders can filter users by the values of their attributes.
    This is represented in the database as a Filter object, with parameters
    that are passed to an appropriate filtering function for the attribute.

    See emotiv/experiments/filters.py
    """

    attribute_id = db.Column(db.Integer(), db.ForeignKey('attribute.id'), nullable=False)
    attribute = db.relationship('Attribute', backref=db.backref('_filters', cascade='all, delete-orphan'))
    parameters = db.Column(JSONDict)
    experiment_id = db.Column(db.Integer(), db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', back_populates='filters')


# Input Types = (
#     ('ss', 'Single-Select Multiple Choice'),
#     ('ms', 'Multi-Select Multiple Choice'),
#     ('sv', 'Single View'),
#     ('ot', 'Open Text'),
#     ('dt', 'Datetime'),
# )

class AttributeSuggestion(db.Model, BaseMixin):
    text = db.Column(db.TEXT(), nullable=False)
    email_sent = db.Column(db.Boolean(), default=False)
    status = db.Column(db.String, default='p')
    user = db.relationship('User')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


experiments_attributes = db.Table('experiments_attributes',
                                  db.Column('experiment_id', db.Integer(),
                                            db.ForeignKey('experiment.id')),
                                  db.Column('attribute_id', db.Integer(),
                                            db.ForeignKey('attribute.id')))


class Experiment(db.Model, BaseMixin, OrganizationMixin):
    allow_repeats = db.Column(db.Boolean(), default=False)
    attributes_collected = db.relationship('Attribute', secondary=experiments_attributes,
                                           backref=db.backref('experiments', lazy='dynamic'))
    filters = db.relationship('Filter', back_populates='experiment', cascade='all, delete-orphan')
    description = db.Column(db.String(255), index=True, nullable=True)
    end_date = db.Column(db.DateTime(), nullable=True)
    # Date submitted for review.
    submitted_date = db.Column(db.DateTime(), nullable=True)
    eye_tracking_enabled = db.Column(db.Boolean(), default=False)
    image = db.relationship('Material')
    image_id = db.Column(db.Integer(), db.ForeignKey('material.id'))
    launch_date = db.Column(db.DateTime())
    name = db.Column(db.String(255), index=True, nullable=False)
    recordings_collected = db.Column(db.Integer(), default=0)
    # 0 == Unlimited
    recordings_to_collect = db.Column(db.Integer(), default=0)
    private = db.Column(db.Boolean(), default=False)
    status = db.Column(db.String(1), default='e', nullable=False)
    web_tracking_enabled = db.Column(db.Boolean(), default=False)
    phases = db.relationship('Phase', foreign_keys='Phase.experiment_id', cascade='all, delete-orphan')
    calibration_phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    calibration_phase = db.relationship('Phase', foreign_keys='Experiment.calibration_phase_id', uselist=False,
                                        post_update=True)
    start_phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    start_phase = db.relationship('Phase', foreign_keys='Experiment.start_phase_id', uselist=False,
                                  post_update=True)
    end_phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    end_phase = db.relationship('Phase', foreign_keys='Experiment.end_phase_id', uselist=False,
                                post_update=True)
    calibration_length = db.Column(db.Integer(), default=120)
    user = db.relationship('User')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_setup_step_completed = db.Column(db.Integer, default=0)
    recording_data = db.relationship('ExperimentRecordingData')
    def get_phase_elements(self):
        return list(chain.from_iterable([p.elements for p in self.phases]))

# Experiment Status = (
#     ('e', 'Editing'),
#     ('p', 'Pending Review'),
#     ('s', 'Scheduled'),
#     ('o', 'Ongoing'),
#     ('f', 'Finished'),
# )


class Invitation(db.Model, BaseMixin):
    email = db.Column(db.String(30), nullable=False)
    email_sent = db.Column(db.Boolean(), default=False)
    experiment = db.relationship('Experiment')
    experiment_id = db.Column(db.Integer(), db.ForeignKey('experiment.id'), nullable=False)
    token = db.Column(db.String(255))
    user = db.relationship('User')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))


# These are just for reference at the moment.
# I assume this is for experiment filter criteria answers?
# it wasn't used before...

# ANSWER_OPTION_CHOICES = (
#     ('i', 'ints'),
#     ('d', 'datetime'),
#     ('s', 'strings'),
# )

class Material(db.Model, BaseMixin, OrganizationMixin):
    content_type = db.Column(db.String(1), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)


# content_type = (
#     ('a', 'Audio'),
#     ('i', 'Image'),
#     ('v', 'Video'),
#     ('t', 'Text'),
#     ('q', 'Question'),
# )


class Organization(db.Model, BaseMixin):
    auto_deploy = db.Column(db.Boolean())
    description = db.Column(db.String(1024))
    name = db.Column(db.String(255), nullable=False, unique=True)
    # SQLAlchemy does not like setting this as a foreign key for some reason, but it doesn't matter.
    # Used to allow who can revoke access.
    owner_id = db.Column(db.Integer())
    phases = db.relationship('Phase')


class Phase(db.Model, BaseMixin, OrganizationMixin):
    experiment = db.relationship('Experiment', foreign_keys='Phase.experiment_id')
    experiment_id = db.Column(db.Integer(), db.ForeignKey('experiment.id', use_alter=True), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    previous_phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id', use_alter=True))
    previous_phase = db.relationship('Phase', foreign_keys='Phase.previous_phase_id', uselist=False, post_update=True, remote_side='[Phase.id]')
    default_condition = db.relationship('PhaseCondition', foreign_keys='Phase.default_condition_id', uselist=False,
                                        post_update=True)
    default_condition_id = db.Column(db.Integer(), db.ForeignKey('phase_condition.id', use_alter=True))
    conditions = db.relationship('PhaseCondition', foreign_keys='PhaseCondition.phase_id', cascade='all, delete-orphan')
    elements = db.relationship('PhaseElement', cascade='all, delete-orphan', order_by='PhaseElement.position')
    rank = db.Column(db.Integer(), nullable=False)


class PhaseCondition(db.Model, BaseMixin):
    attribute = db.relationship('Attribute')
    attribute_id = db.Column(db.Integer(), db.ForeignKey('attribute.id'))
    match_attribute = db.Column(db.Boolean(), default=False)
    operation = db.Column(db.String(7))
    phase = db.relationship('Phase', foreign_keys='PhaseCondition.phase_id')
    phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    next_phase = db.relationship('Phase', foreign_keys='PhaseCondition.next_phase_id', uselist=False)
    next_phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    phase_element = db.relationship('PhaseElement')
    phase_element_id = db.Column(db.Integer(), db.ForeignKey('phase_element.id'))
    value_1 = db.Column(db.String(255))
    value_2 = db.Column(db.String(255))
    order = db.Column(db.Integer())


# Operations
# > Greater Than
# < Less Than
# == Equal
# != Not Equal
# >= Greater Than Equal
# <= Less Than Equal
# >< Greater Than AND Less Than
# >||< Greater Than OR Less Than
# >&&< Greater Than AND Less Than
# >=||<= Greater Than Equal OR Less Than Equal
# >=&&<= Greater Than Equal OR Less Than Equal
# Default


class PhaseElement(db.Model, BaseMixin, OrganizationMixin):
    text = db.Column(db.TEXT())
    description = db.Column(db.TEXT())
    lower_limit = db.Column(db.Integer())
    upper_limit = db.Column(db.Integer())
    material = db.relationship('Material')
    material_id = db.Column(db.Integer(), db.ForeignKey('material.id'))
    phase = db.relationship('Phase')
    phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'), nullable=False)
    answers = db.relationship('PhaseElementAnswer', cascade='all, delete-orphan', order_by='PhaseElementAnswer.position')
    input_type = db.Column(db.String(2), nullable=True)
    category_type = db.Column(db.String(1), nullable=False)
    position = db.Column(db.Integer(), nullable=False)
    recording_data = db.relationship('PhaseElementRecordingData')
    duration_data = db.relationship('PhaseElementDurationData')
    # How long an image should be displayed for, in milliseconds.
    duration_ms = db.Column(db.Integer())


class PhaseElementAnswer(db.Model, BaseMixin, OrganizationMixin):
    value = db.Column(db.String(255))
    label = db.Column(db.String(255))
    content_type = db.Column(db.String(2), nullable=True)
    material = db.relationship('Material')
    material_id = db.Column(db.Integer(), db.ForeignKey('material.id'))
    phase = db.relationship('Phase')
    phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'))
    phase_element = db.relationship('PhaseElement')
    phase_element_id = db.Column(db.Integer(), db.ForeignKey('phase_element.id'))
    position = db.Column(db.Integer(), nullable=False)


class PhaseElementAnswerUser(db.Model, BaseMixin):
    phase = db.relationship('Phase', uselist=False)
    phase_id = db.Column(db.Integer(), db.ForeignKey('phase.id'), nullable=False)
    phase_element = db.relationship('PhaseElement')
    phase_element_id = db.Column(db.Integer(), db.ForeignKey('phase_element.id'), nullable=False)
    phase_element_answer = db.relationship('PhaseElementAnswer')
    phase_element_answer_id = db.Column(db.Integer(), db.ForeignKey('phase_element_answer.id'))
    value = db.Column(db.TEXT())
    user = db.relationship('User')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)

# The CSV data from the emotiv headset during the duration of a particular phase element.
class PhaseElementRecordingData(db.Model, BaseMixin):
    phase_element = db.relationship('PhaseElement', back_populates='recording_data')
    phase_element_id = db.Column(db.Integer(), db.ForeignKey('phase_element.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    data_type = db.Column(db.String(1), nullable=False)

# Represents a single experiment view of a user
# combines headset and eye data
class ExperimentRecordingData(db.Model, BaseMixin):
    experiment_id = db.Column(db.Integer(), db.ForeignKey('experiment.id'), nullable=False)
    experiment = db.relationship('Experiment', back_populates='recording_data')
    user = db.relationship('User')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    screen_width = db.Column(db.Integer())
    screen_height = db.Column(db.Integer())
    emotiv_data = db.relationship('ExperimentEmotivData')
    gaze_data = db.relationship('ExperimentGazeData')
    duration_data = db.relationship('PhaseElementDurationData')

# headset data
class ExperimentEmotivData(db.Model, BaseMixin):
    file_name = db.Column(db.String(255), nullable=False)
    data_type = db.Column(db.String(1), nullable=False)
    recording_data_id = db.Column(db.Integer(), db.ForeignKey('experiment_recording_data.id'))
    recording_data = db.relationship('ExperimentRecordingData', back_populates='emotiv_data')

# data_type = (
#     ('e', 'Raw EEG Data'),
#     ('a', 'Affectiv Performance Metrics'),
#     ('m', 'Motion Data'),
# )

#The gaze data given from the Visage SDK
class ExperimentGazeData(db.Model, BaseMixin):
    file_name = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    recording_data_id = db.Column(db.Integer(), db.ForeignKey('experiment_recording_data.id'))
    recording_data = db.relationship('ExperimentRecordingData', back_populates='gaze_data')

class PhaseElementDurationData(db.Model, BaseMixin):
    recording_data_id = db.Column(db.Integer(), db.ForeignKey('experiment_recording_data.id'))
    recording_data = db.relationship('ExperimentRecordingData', back_populates='duration_data')
    phase_element_id = db.Column(db.Integer(), db.ForeignKey('phase_element.id'))
    phase_element = db.relationship('PhaseElement')
    view_start = db.Column(db.DateTime(), nullable=False)
    view_end = db.Column(db.DateTime(), nullable=False)

groups_phases = db.Table('groups_phases',
                         db.Column('phase_id', db.Integer(), db.ForeignKey('phase.id')),
                         db.Column('group_id', db.Integer(), db.ForeignKey('phase_group.id')))


class PhaseGroup(db.Model, BaseMixin, OrganizationMixin):
    name = db.Column(db.String(255), nullable=False)
    phases = db.relationship('Phase', secondary=groups_phases,
                             backref=db.backref('groups', lazy='dynamic'))


class RequestOrganization(db.Model, BaseMixin, OrganizationMixin):
    requester = db.relationship('User', foreign_keys='RequestOrganization.requester_id')
    requester_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    responder = db.relationship('User', foreign_keys='RequestOrganization.responder_id')
    responder_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    response = db.Column(db.String(1), default='p', nullable=False)


# Request Response = (
#     ('a', 'Accepted'),
#     ('r', 'Rejected'),
#     ('p', 'Pending'),
# )


# Required for Flask-Security
class Role(db.Model, RoleMixin, BaseMixin):
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


# Required for Flask-Security
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class User(db.Model, BaseMixin, UserMixin):
    # EmotivID Last access token - for subsequent requests
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    builder = db.Column(db.Boolean(), default=False, nullable=False)
    email = db.Column(db.String(30), index=True, unique=True, nullable=False)
    emotiv_dbapi_id = db.Column(db.Integer)
    emotiv_eoidc_id = db.Column(db.Integer)
    emotiv_eoidc_username = db.Column(db.String(255))
    defaults_updated = False
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    organization = db.relationship('Organization')
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    # EmotivID Token expires field - to make sure we don't try using an expired token.
    token_expires = db.Column(db.DateTime())
    username = db.Column(db.String(30), index=True, unique=True, nullable=False)
    # Flask-Security fields
    active = db.Column(db.Boolean(), default=True)
    confirmed_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    current_login_ip = db.Column(db.String(45))
    first_ip = db.Column(db.String(45))
    last_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


class UserAttribute(db.Model, BaseMixin):
    attribute = db.relationship('Attribute', backref=db.backref('_user_attributes', cascade='all, delete-orphan'))
    attribute_id = db.Column(db.ForeignKey('attribute.id'), nullable=False)
    user = db.relationship('User', backref='attributes')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.String(255))
