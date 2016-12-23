from datetime import datetime
from functools import wraps
from hashlib import md5
import itertools
import urllib
import base64
import json
import csv
import StringIO
import requests
import os
import iso8601
import boto

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for, send_file
from flask.ext.security import current_user
from flask_mail import Message
from flask_sqlalchemy import Pagination
from sqlalchemy import and_, asc, desc, or_
from dateutil import tz
from boto.s3.key import Key

from emotiv.app import app
from emotiv.helpers import set_user_attributes_helper
from emotiv.database import db
from emotiv.experiment import experiment, filters
from emotiv.experiment.forms import ExperimentFormStep1, ExperimentFormStep2, ExperimentFormStep3, \
    ExperimentFormStep4, ExperimentFormStep5, ExperimentFormStep6
from emotiv.helpers import login_or_token_required, templated
from emotiv.material.views import _record_filestack_upload
from emotiv.models import Attribute, AttributeSuggestion, Experiment, Filter, Invitation, Material, Phase, PhaseCondition, RequestOrganization, User, \
    PhaseElement, PhaseElementAnswerUser, ExperimentRecordingData, ExperimentGazeData, PhaseElementDurationData
from emotiv.phase.forms import PhaseForm


def builder_validation(func):
    """Enforce that the current user is allowed to build this experiment."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if 'admin' in [r.name for r in current_user.roles]:
            flash('Admins cannot build experiments.', 'error')
            return redirect(url_for('admin.dashboard'))
        if current_user.builder:
            exp_id = kwargs.get('experiment_id', None)
            if exp_id != None:
                org_id = Experiment.query.get_or_404(exp_id).organization_id
            if exp_id is None or org_id == current_user.organization_id:
                return func(*args, **kwargs)
        flash('You do not have permission to build experiments for that organization', 'error')
        return redirect(url_for('experiment.list_all'))
    return decorated_function


def update_last_step(experiment_obj, step):
    prev = experiment_obj.last_setup_step_completed
    if not prev or prev < step:
        experiment_obj.last_setup_step_completed = step
        db.session.commit()


def allowed_to_view_experiment(f):
    """Enforce that the current user is allowed to view this experiment."""
    @wraps(f)
    def decorated_function(experiment_id, *args, **kwargs):
        if current_user.builder:
            flash("Builders can not participate in experiments", 'error')
            return redirect(url_for('experiment.list_all'))

        experiment_obj = Experiment.query.get_or_404(experiment_id)
        if experiment_obj.private:
            invitation_obj = Invitation.query.filter(Invitation.user_id == current_user.id). \
                filter(Invitation.experiment_id == experiment_obj.id).first()
            if not invitation_obj:
                flash("You have not been invited to that experiment", 'error')
                return redirect(url_for('experiment.list_all'))

        return f(experiment_id, *args, **kwargs)
    return decorated_function


@experiment.route('/new', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_experiment.html')
@builder_validation
def new_experiment():
    """Handles step 1 of new experiment flow.

    The web UI for creating experiments is divided into several steps,
    so there are multiple corresponding handlers in this file. This
    is the first.

    GET: render the HTML form
    POST: take ExperimentFormStep1 params in the body, creates experiment object in db
    """
    form = ExperimentFormStep1()
    if request.method == 'GET':
        return {'organization': current_user.organization, 'form': form}
    if form.validate_on_submit():
        try:
            new_experiment_obj = Experiment(name=form.name.data,
                                            description=form.description.data,
                                            organization_id=current_user.organization.id,
                                            user_id=current_user.id)
            db.session.add(new_experiment_obj)
            new_exp_calibration_phase = Phase(name="Calibration",
                                              experiment=new_experiment_obj,
                                              organization_id=current_user.organization.id,
                                              rank=1)
            db.session.add(new_exp_calibration_phase)
            new_exp_start_phase = Phase(name="Introduction",
                                        experiment=new_experiment_obj,
                                        previous_phase=new_exp_calibration_phase,
                                        organization_id=current_user.organization.id,
                                        rank=2)
            db.session.add(new_exp_start_phase)
            new_exp_calibration_phase_default_condition = PhaseCondition(next_phase=new_exp_start_phase,
                                                                         phase=new_exp_calibration_phase,
                                                                         operation="default")
            db.session.add(new_exp_calibration_phase_default_condition)
            new_exp_calibration_phase.default_condition = new_exp_calibration_phase_default_condition
            new_exp_end_phase = Phase(name="Conclusion",
                                      experiment=new_experiment_obj,
                                      previous_phase=new_exp_start_phase,
                                      organization_id=current_user.organization.id,
                                      rank=3)
            db.session.add(new_exp_end_phase)
            new_exp_start_phase_default_condition = PhaseCondition(next_phase=new_exp_end_phase,
                                                                   phase=new_exp_start_phase,
                                                                   operation="default")
            db.session.add(new_exp_start_phase_default_condition)
            new_exp_start_phase.default_condition = new_exp_start_phase_default_condition

            new_experiment_obj.calibration_phase = new_exp_calibration_phase
            new_experiment_obj.start_phase = new_exp_start_phase
            new_experiment_obj.end_phase = new_exp_end_phase
            db.session.commit()
        except Exception, ex:
            print ex
            db.session.rollback()
            flash('There was a problem inserting into the database, please try again.', 'error')
            return {'organization': current_user.organization, 'form': form}
        update_last_step(new_experiment_obj, 1)
        return redirect(url_for('experiment.new_experiment_step_2', experiment_id=new_experiment_obj.id))
    return {'organization': current_user.organization, 'form': form}


@experiment.route('/new/step_2/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_experiment_step_2.html')
@builder_validation
def new_experiment_step_2(experiment_id=None):
    """Handles step 2 of new experiment flow.

    Step 2 allows you to select an experiment template.

    GET: render the HTML form
    POST: take ExperimentFormStep2 params in the body, updates experiment based on template if present
    """

    experiment_obj = Experiment.query.get_or_404(experiment_id)
    form = ExperimentFormStep2()
    past_experiments = Experiment.query.filter(Experiment.organization_id == experiment_obj.organization_id). \
        filter(Experiment.id < experiment_obj.id).all()
    template_choices = [(int(item.id), item.name) for item in past_experiments]
    template_choices.insert(0, (0, 'Blank'))
    form.template.choices = template_choices
    if request.method == 'GET':
        return {'organization': current_user.organization, 'experiment': experiment_obj, 'form': form}
    if form.validate_on_submit():
        if int(form.template.data) != 0:
            existing_template = Experiment.query.get_or_404(form.template.data)
            experiment_obj.allow_repeats = existing_template.allow_repeats
            experiment_obj.eye_tracking_enabeld = existing_template.eye_tracking_enabled
            experiment_obj.web_tracking_enabled = existing_template.web_tracking_enabled
            experiment_obj.status = 'e'
            experiment_obj.image = existing_template.image
            # experiment_obj.attributes_collected = existing_template.attributes_collected
            db.session.commit()
            existing_template_phases = Phase.query.filter(Phase.experiment_id == existing_template.id). \
                filter(Phase.name != "Introduction").filter(Phase.name != "Conclusion"). \
                filter(Phase.name != "Calibration").all()
            end_phase = Phase.query.filter(Phase.experiment_id == experiment_obj.id). \
                filter(Phase.name == "Conclusion").first()
            end_phase.rank += len(existing_template_phases)
            for phase in existing_template_phases:
                new_phase_obj = Phase(rank=phase.rank, experiment=experiment_obj, name=phase.name,
                                      organization_id=current_user.organization.id)
                new_phase_obj.condition = phase.condition
                db.session.add(new_phase_obj)
            db.session.commit()
            update_last_step(experiment_obj, 2)
            return redirect(url_for('experiment.new_experiment_step_3', experiment_id=experiment_obj.id))
        else:
            update_last_step(experiment_obj, 2)
            return redirect(url_for('experiment.new_experiment_step_3', experiment_id=experiment_obj.id))
    return {'organization': current_user.organization, 'experiment': experiment_obj, 'form': form}


@experiment.route('/new/step_3/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('edit_experiment_criteria.html')
@builder_validation
def new_experiment_step_3(experiment_id=None):
    """Handles step 3 of new experiment flow.

    Step 3 is setting up filtering based on user attributes. Note that the web UI
    lets you edit this step in particular after an experiment has already been created,
    so most of this implementation is shared with that other view.

    GET: render the HTML form
    POST: take ExperimentFormStep3 params in the body, set filters based on it

    Note that the ExperimentFormStep3 params uses a somewhat complicated data structure.
    For context on it, see:
        experiment/forms.py - FilterField class
        experiment/filters.py
        this file - _edit_criteria
    """
    template_data = _edit_criteria(experiment_id, True)
    if template_data:
        return template_data
    update_last_step(Experiment.query.get_or_404(experiment_id), 3)
    return redirect(url_for('experiment.new_experiment_step_4', experiment_id=experiment_id))


@experiment.route('/edit/criteria/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('edit_experiment_criteria.html')
@builder_validation
def edit_criteria(experiment_id=None):
    """Handles the edit criteria view.

    This view is almost identical to step 3 of the new experiment flow.
    It exists to provide an easy way for builders to edit those settings
    after creating an experiment. See notes on new_experiment_step_3.

    GET: render the HTML form
    POST: take ExperimentFormStep3 params in the body, set filters based on it
    """
    template_data = _edit_criteria(experiment_id, False)
    if template_data:
        return template_data
    flash('Criteria updated!', 'success')
    if request.args.get('search'):
        return redirect(url_for('experiment.list_all', term=request.args.get('search')))
    return redirect(url_for('experiment.list_all'))


def _edit_criteria(experiment_id, is_new_experiment):
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    form = ExperimentFormStep3()
    exp_filters = []
    suggestion = request.form.get('criteria_suggestion')
    if not form.validate_on_submit() or suggestion:
        if request.method == 'GET':
            for attribute in Attribute.query.all():
                for f in experiment_obj.filters:
                    if f.attribute_id == attribute.id:
                      form.filters.append_entry((attribute.id, f.parameters))
                      break
        elif suggestion:
            send_new_suggestions(suggestion, False, experiment_obj)
        else:
            flash('Double-check your inputs.', 'error')

        # Convert filter values to a JSON-able structure.
        exp_filters = []
        def add_filter(params, attribute):
            opts = [
                {
                    'id': o.id,
                    'value': o.value,
                } for o in attribute.possible_options
            ]
            exp_filters.append({
                'params': params,
                'attribute': {
                    'id': attribute.id,
                    'input_type': attribute.input_type,
                    'name': attribute.name,
                    'possible_options': opts,
                }
            })
        for f in form.filters:
            add_filter(f.parameters, Attribute.query.get(f.attribute_id))
        for a in Attribute.query.all():
          for f in experiment_obj.filters:
            if f.attribute_id == a.id:
              break
          else:
            add_filter(filters.default_filter(a), a)

        return {
            'form': form,
            'new_experiment': is_new_experiment,
            'experiment': experiment_obj,
            'filters': exp_filters,
            'selected': [f.attribute_id for f in form.filters],
        }
    experiment_obj.filters = []
    for f in form.filters:
        db.session.add(Filter(experiment=experiment_obj,
                              attribute_id=f.attribute_id,
                              parameters=f.parameters))
    db.session.commit()
    return None


def send_new_suggestions(suggestion, is_attribute, experiment_obj):
    """If suggestion is new, record it and notify admins."""
    if not suggestion:
        return
    suggestion = suggestion.strip()
    kind = 'Attribute' if is_attribute else 'Criteria'
    if len(suggestion) > 0:
        # Don't accept duplicate attribute suggestions.
        if AttributeSuggestion.query.filter(and_(
                AttributeSuggestion.text == suggestion,
                AttributeSuggestion.user == current_user)).first():
            flash(kind + ' suggestion sent successfully.', 'success')
            return
        new_suggestion = AttributeSuggestion(user=current_user, text=suggestion)
        db.session.add(new_suggestion)
        db.session.commit()
        try:
            subject = 'Attribute Request' if is_attribute else 'Acceptable Criteria Request'
            send_mail(subject, app.config['CRITERIA_REQUEST_EMAIL'],
                      app.config['SECURITY_EMAIL_SENDER'], 'criteria_suggestion',
                      name=current_user.first_name,
                      organization=current_user.organization.name, email=current_user.email,
                      suggestion=new_suggestion.text, experiment=experiment_obj)
            new_suggestion.email_sent = True
            db.session.commit()
            flash(kind + ' suggestion sent successfully.', 'success')
        except Exception as ex:
            flash(kind + ' suggestion was not able to send.', 'error')
            print(ex.message)


@experiment.route('/new/step_4/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_experiment_step_4.html')
@builder_validation
def new_experiment_step_4(experiment_id=None):
    """Handles step 4 of new experiment flow.

    Step 4 is selecting which user attributes to collect.

    GET: render the HTML form
    POST: take ExperimentStep4 params in the body, set attributes_collected based on it.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    form = ExperimentFormStep4()
    attribute_list = Attribute.query.all()
    form.attributes.choices = [(int(item.id), item.name,) for item in attribute_list]

    if form.validate_on_submit():
        attributes_selected = request.form.getlist('attributes')
        for value in attributes_selected:
            attribute_collected = Attribute.query.get(int(value))
            if attribute_collected not in experiment_obj.attributes_collected:
                experiment_obj.attributes_collected.append(attribute_collected)
        db.session.commit()
        for attribute in experiment_obj.attributes_collected:
            if str(attribute.id) not in attributes_selected:
                experiment_obj.attributes_collected.remove(attribute)
        db.session.commit()

        send_new_suggestions(request.form.get('attribute_suggestion'), True, experiment_obj)

        update_last_step(experiment_obj, 4)
        return redirect(url_for('experiment.new_experiment_step_5', experiment_id=experiment_obj.id))

    if request.method == 'GET':
        selected = [a.id for a in experiment_obj.attributes_collected]
    else:
        selected = request.form.getlist('attributes')

    attributes = [{'id': a.id, 'name': a.name} for a in attribute_list]

    return {
        'experiment': experiment_obj,
        'form': form,
        'attributes': attributes,
        'selected': selected
    }


@experiment.route('/new/step_5/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_experiment_step_5.html')
@builder_validation
def new_experiment_step_5(experiment_id=None):
    """Handles step 5 of new experiment flow.

    Step 5 is a few miscellaneous settings, including an optional image to represent
    the experiment. Note that updating the image is handled by a separate handler: upload_image.

    GET: render the HTML form
    POST: take ExperimentFormStep5 params in the body, update settings based on it
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    form = ExperimentFormStep5()
    image_list = Material.query.filter(Material.content_type == 'i'). \
        filter(Material.organization_id == experiment_obj.organization_id).all()
    if request.method == 'GET':
        return {'experiment': experiment_obj, 'available_images': image_list, 'form': form}
    if form.validate_on_submit():
        experiment_obj.allow_repeats = bool(form.allow_repeats.data)
        experiment_obj.private = bool(form.private.data)
        email = request.form.get('participant_email')
        if len(email) > 6:
            email = email.replace('\r\n', '')
            email = email.replace(' ', '')
            split_emails = email.split(',')
            for email in split_emails:
                m = md5()
                m.update(email)
                m.update(experiment_obj.organization.name)
                m.update(experiment_obj.name)
                m.update(str(experiment_obj.id))
                m.update(str(datetime.now()))
                token = m.hexdigest()
                new_invitation = Invitation(email=email, experiment_id=experiment_obj.id, token=token)
                try:
                    send_mail('Experiment Invitation', email,
                              app.config['SECURITY_EMAIL_SENDER'], 'invitation', user=current_user,
                              experiment=experiment_obj, token=token, url=app.config['ROOT_URL'])
                    new_invitation.email_sent = True
                except Exception as ex:
                    print(ex.message)
                existing_user = User.query.filter(User.email == email).first()
                if existing_user:
                    new_invitation.user_id = existing_user.id
                else:
                    new_invitation.user_id = None
                db.session.add(new_invitation)
                db.session.commit()
        db.session.commit()
        update_last_step(experiment_obj, 5)
        return redirect(url_for('experiment.new_experiment_step_6', experiment_id=experiment_obj.id))
    return {'experiment': experiment_obj, 'available_images': image_list, 'form': form}


@experiment.route('/new/step_6/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_experiment_step_6.html')
@builder_validation
def new_experiment_step_6(experiment_id=None):
    """Handles step 6 of new experiment flow.

    Step 6 is a few more miscellaneous settings.

    GET: render the HTML form
    POST: take ExperimentFormStep6 params in the body, update settings based on it.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    form = ExperimentFormStep6()
    if request.method == 'GET':
        return {'experiment': experiment_obj, 'form': form, 'recording_cost': app.config['RECORDING_COST']}
    if form.validate_on_submit():
        experiment_obj.recordings_to_collect = form.recordings_collected.data
        experiment_obj.launch_date = form.start_date.data
        experiment_obj.end_date = form.end_date.data
        experiment_obj.eye_tracking_enabled = bool(form.eye_tracking.data)
        experiment_obj.web_tracking_enabled = bool(form.web_tracking.data)
        db.session.commit()
        update_last_step(experiment_obj, 6)
        return redirect(url_for('experiment.edit_roadmap', experiment_id=experiment_obj.id))
    return {'experiment': experiment_obj, 'form': form, 'recording_cost': app.config['RECORDING_COST']}


@experiment.route('/submit/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@builder_validation
def submit(experiment_id=None):
    """Handle builders submitting an experiment for review.

    Does some validation of the experiment and, if validation passes, marks the experiment's status
    as "p" (pending). This will cause it to show up in the admin dashboard.

    If validation fails, flashes an error message explaining why.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    if experiment_obj.launch_date is None or (
            experiment_obj.end_date is None and
            experiment_obj.recordings_to_collect == 0):
        flash('Experiment has incomplete data.', 'error')
    elif experiment_obj.status == 'e':
        errors = []
        if len(valid_phases(experiment_obj)) == 0:
            errors.append('Can\'t submit. All of this experiment\'s phases are empty.')
        for phase in experiment_obj.phases:
            for element in phase.elements:
                if element.category_type == 'q' and \
                        element.input_type in ['ss', 'ms'] and \
                        not element.answers:
                    errors.append('Phase "{}" has a question with no answers'
                                  .format(phase.name))
                    break
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for(
                'experiment.edit_roadmap', experiment_id=experiment_id))
        experiment_obj.status = 'p'
        experiment_obj.submitted_date = datetime.now()
        db.session.commit()
        flash('Experiment submitted for review.', 'success')
    else:
        flash('Experiment was not in the editing state.', 'error')
    return redirect(url_for('experiment.list_all'))


@experiment.route('/accept/<string:token>', methods=['GET', 'POST'])
@login_or_token_required
def accept_token(token=None):
    """Handle a viewer submitting a token to view a private experiment.

    For private expriments, we send emails to any email addresses the builder wants, containing
    unique links to this endpoint. When a logged-in viewer clicks the link and ends up here, we
    associate the corresponding invitation with the user, which provides them access to the experiment.
    """
    if current_user.builder:
        flash('Must be logged in as a viewer to accept an experiment invitation', 'error')
    else:
        invitation = Invitation.query.filter(Invitation.token == token).first_or_404()
        invitation.user_id = current_user.id
        db.session.commit()
    return redirect(url_for('experiment.list_all'))


@experiment.route('/delete/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@builder_validation
def delete(experiment_id=None):
    """Handle an experiment delete request.

    Deletes the experiment, if it exists.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    db.session.delete(experiment_obj)
    db.session.commit()
    return redirect(url_for('experiment.list_all'))


def valid_phases(experiment_obj):
    return filter(lambda phase: len(phase.elements) > 0, experiment_obj.phases)

@experiment.route('/start_experiment/<int:experiment_id>', methods=['POST'])
@login_or_token_required
@allowed_to_view_experiment
def start_experiment(experiment_id=None):
    """Starts one user view of an experiment

    Parameters:
        experiment_id: An id of the experiment that the user is participating in

    Returns:
        sesssion_id: An id of the session for which the user is assigned.
        accepted: boolean representing whether the user was accepted for the experiment
        experiment:
            phase: The starting phase for the experiment
            phase_element: The starting phase element for the experiment.
            finished: Whether the experiment is finished or not
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    screen_width = request.json['screenWidth']
    screen_height = request.json['screenHeight']
    valid = valid_phases(experiment_obj)

    first_phase = valid[0]
    first_element = first_phase.elements[0]


    new_session = ExperimentRecordingData(
        user=current_user,
        experiment=experiment_obj,
        screen_width=screen_width,
        screen_height=screen_height,
    )

    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'session_id': new_session.id,
        'accepted':True,
        'experiment':{
            'id': experiment_obj.id,
            'phase': serialize_phase(first_phase),
            'phase_element': serialize_phase_element(first_element),
            'finished': False,
        }
    })



@experiment.route('/detail/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('experiment_detail.html')
def detail(experiment_id=None):
    """Handles a request to take an experiment

    Parameters:
        experiment_id: An id of the experiment that the user is participating in

    Returns:
        need_criteria: Criteria that the user is required to have to view the experiment.
        experiment: Experiment model in the database
        organization: The organization that the logged in user belongs to
        experiment_view_props: props needed for the experiment view react component
        visage_liscence_file: name of the visage liscence file
    """
    if current_user.builder:
        flash("Builders can not participate in experiments", 'error')
        return redirect(url_for('experiment.list_all'))
    if request.method == 'POST':
        form_data = request.form
        form_data = set_user_attributes_helper(form_data)
        flash("Attributes Saved")
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    valid = valid_phases(experiment_obj)

    if len(valid) == 0:
        flash("The experiment has no valid phases!", 'error')
        return redirect(url_for('experiment.list_all'))

    first_phase = valid[0]
    first_element = first_phase.elements[0]

    if not current_user.builder:
        if experiment_obj.private:
            invitation_obj = Invitation.query.filter(Invitation.user_id == current_user.id). \
                filter(Invitation.experiment_id == experiment_obj.id).first()
            if not invitation_obj:
                flash("You have not been invited to that experiment", 'error')
                return redirect(url_for('experiment.list_all'))
        need_criteria = []
        attributes = Attribute.query.all()
        def find_by_id(list, id, field='id'):
            return next((x for x in list if getattr(x, field) == id), None)

        def collect_needed_criteria(more_criteria):
            for criteria_id in more_criteria:
                if not find_by_id(need_criteria, criteria_id):
                    item = find_by_id(attributes, criteria_id)
                    item.user_attribute = []
                    need_criteria.append(item)

        for _filter in experiment_obj.filters:
            accept, _need_criteria = filters.apply_filter(
                _filter, current_user.attributes)
            if _need_criteria:
                collect_needed_criteria(_need_criteria)
            elif not accept:
                if request.content_type == 'application/json':
                    return {'api_response': jsonify(accepted=False,
                                                    need_criteria=[])}
                flash("Your attributes don't match the experiment's criteria", 'error')
                return redirect(url_for('experiment.list_all'))

        for attribute in experiment_obj.attributes_collected:
            id = attribute.id
            if not find_by_id(current_user.attributes, id, field='attribute_id'):
                collect_needed_criteria([id])



        if request.content_type == 'application/json':
            return {
                'api_response': jsonify(
                    accepted=True,
                    need_criteria=experiment_need_criteria_jsonify(need_criteria),
                    experiment={
                        'id': experiment_obj.id,
                        'phase': serialize_phase(first_phase),
                        'phase_element': serialize_phase_element(first_element),
                        'finished': False,
                    },
                ),
            }
        return {'organization': current_user.organization,
                'experiment': experiment_obj,
                'need_criteria': need_criteria,
                'visage_license_file': app.config['VISAGE_LICENSE_FILE'],
                'experiment_view_props': {
                    'experiment_id': experiment_obj.id,
                    'phase': serialize_phase(first_phase),
                    'phase_element': serialize_phase_element(first_element),
                    'finished': False,
                }
        }
    else:
        flash("You do not have access to that organization's experiments", 'error')
        return redirect(url_for('experiment.list_all'))

def serialize_phase(phase):
    return {
        'name': phase.name,
        'id': phase.id,
    }

def serialize_phase_element(phase_element):
    category_type = phase_element.category_type
    if category_type == 'v':
        return {
            'category_type': category_type,
            'file_name': phase_element.material.file_name,
            'id': phase_element.id
        }

    if category_type == 'a':
        return {
            'category_type': category_type,
            'file_name': phase_element.material.file_name,
            'id': phase_element.id
        }

    if category_type == 'i':
        return {
            'category_type': category_type,
            'file_name': phase_element.material.file_name,
            'id': phase_element.id,
            'duration_ms': phase_element.duration_ms
        }

    if category_type == 't':
        return {
            'category_type': category_type,
            'text': phase_element.text,
            'id': phase_element.id,
        }

    if category_type == 'q':
        return {
            'category_type': category_type,
            'text': phase_element.text,
            'id': phase_element.id,
            'input_type': phase_element.input_type,
            'answers': map(lambda x: x.value, phase_element.answers),
        }

def save_answers(user, phase, element, answers):
    if element.input_type == 'ss':
        phase_answer = filter(lambda p_answer: p_answer.value == answers[0], element.answers)
        if len(phase_answer) == 0:
            return False

        user_answer = PhaseElementAnswerUser(user=user, phase=phase, phase_element_answer=phase_answer[0], phase_element=element)
        db.session.add(user_answer)
    elif element.input_type == 'ms':
        valid_answers = {p_answer.value : p_answer for p_answer in element.answers}
        for answer in answers:
            if not answer in valid_answers:
                return False

            user_answer = PhaseElementAnswerUser(user=user, phase=phase, phase_element_answer=valid_answers[answer], phase_element=element)
            db.session.add(user_answer)
    elif element.input_type == 'dt':
        try:
            answer = datetime.strptime(answers[0], '%Y-%m-%d')
        except ValueError:
            return False

        user_answer = PhaseElementAnswerUser(user=user, phase=phase, value=answers[0], phase_element=element)
        db.session.add(user_answer)
    elif element.input_type == 'nv':
        if not answers[0].isdigit():
            return False

        user_answer = PhaseElementAnswerUser(user=user, phase=phase, value=answers[0], phase_element=element)
        db.session.add(user_answer)
    elif element.input_type == 'ot':
        user_answer = PhaseElementAnswerUser(user=user, phase=phase, value=answers[0], phase_element=element)
        db.session.add(user_answer)

    return True

@experiment.route('/next_phase_element/<int:experiment_id>', methods=['POST'])
@login_or_token_required
@allowed_to_view_experiment
def next_phase_element(experiment_id):
    """Logic that runs when the user submits an answer and proceeds to a new phase element in an experiment.

    Parameters:
        experiment_id: An id of the experiment that the user is participating in
        current_phase_id: the phase id that the user is in
        current_phase_element_id: the current phase element id that the user is in
        answer: the answers to the phase element if the category type is question

    Returns:
        phase: the next phase
        phase_element: the next phase element
        finished: boolean indicating whether the experiment is finished or not
    """
    current_phase_id = request.json['currentPhaseId']
    current_element_id = request.json['currentElementId']
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    phase = Phase.query.filter(Phase.id == current_phase_id, Phase.experiment_id==experiment_id).first_or_404()
    element = PhaseElement.query.filter(PhaseElement.id == current_element_id, PhaseElement.phase_id == phase.id).first_or_404()
    position = element.position

    if element.category_type == 'q':
        answer = request.json['answers']
        if len(answer) <= 0 or not save_answers(current_user, phase, element, answer):
            return jsonify({'phase': serialize_phase(phase), 'phase_element': serialize_phase_element(element), 'finished': False })
        db.session.commit()

    #TODO: Still need to do the conditional logic
    valid_next_elements = filter(lambda element: element.position > position, phase.elements)
    if phase.id == experiment_obj.end_phase.id and len(valid_next_elements) == 0:
        return jsonify({'phase': serialize_phase(phase), 'finished': True})

    if len(valid_next_elements) == 0:
        next_phase = phase.default_condition.next_phase
        if len(next_phase.elements) == 0:
            return jsonify({ 'phase': serialize_phase(next_phase), 'finished': True })
        next_element = next_phase.elements[0]
    else:
        next_phase = phase
        next_element = valid_next_elements[0]

    return jsonify({'phase': serialize_phase(next_phase), 'phase_element': serialize_phase_element(next_element),'finished': False })

@experiment.route('/edit/roadmap/<int:experiment_id>')
@login_or_token_required
@templated('edit_experiment_roadmap.html')
@builder_validation
def edit_roadmap(experiment_id=None):
    """Handle a request to edit the experiment roadmap.

    If the new experiment flow has not been completed for this experiment, redirect to
    the next unfinished step of the flow. Otherwise, render the edit roadmap page.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    prev_step = experiment_obj.last_setup_step_completed
    if prev_step and prev_step < 6:
        # We could do:
        #
        #   next_step = 'experiment.new_experiment_step_{}'.format(prev_step+1)
        #
        # but that could easily be missed by any future refactoring that changes these function names.
        if prev_step == 1:
            next_step = 'experiment.new_experiment_step_2'
        elif prev_step == 2:
            next_step = 'experiment.new_experiment_step_3'
        elif prev_step == 3:
            next_step = 'experiment.new_experiment_step_4'
        elif prev_step == 4:
            next_step = 'experiment.new_experiment_step_5'
        else:
            next_step = 'experiment.new_experiment_step_6'
        return redirect(url_for(next_step, experiment_id=experiment_id))
    form = PhaseForm()
    return {'organization': current_user.organization, 'experiment': experiment_obj, 'form': form}


@experiment.route('/set/image/<int:experiment_id>/<int:material_id>', methods=['GET', 'POST'])
@login_or_token_required
@builder_validation
def set_image(experiment_id=None, material_id=None):
    """Handle a request to set the title image for an experiment.

    Parameters:
        experiment_id: ID of experiment to update
        material_id: ID of image to use.

    Note that the image represented by material_id should have already been
    uploaded to filestack and its filestack url recorded by a POST to
    /material/record_filestack_upload

    Returns:
        redirect to new experiment step 5 (the image-editing step)
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    material_obj = Material.query.filter(Material.organization_id == experiment_obj.organization_id). \
        filter(Material.id == material_id).first_or_404()
    experiment_obj.image_id = material_obj.id
    db.session.commit()
    return redirect(url_for('experiment.new_experiment_step_5', experiment_id=experiment_obj.id))


@experiment.route('/delete/image/<int:experiment_id>', methods=['POST'])
@login_or_token_required
@builder_validation
def delete_image(experiment_id=None):
    """Handle a request to remove the title image for an experiment.

    Deletes the title image for an experiment, if any.
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    experiment_obj.image_id = None
    db.session.commit()
    return redirect(url_for('experiment.new_experiment_step_5', experiment_id=experiment_obj.id))


@experiment.route('/upload/image/<int:experiment_id>', methods=['POST'])
@login_or_token_required
@builder_validation
def upload_image(experiment_id=None):
    """Handle a request to upload and set the title image for an experiment.

    Parameters:
        experiment_id: ID of the experiment to update
        filestack_url (form value): The URL returned by filestack after using their API to upload the image

    This endpoint does the same thing as using

        /material/record_filestack_upload

    followed by

        /experiment/set_image

    See comments on both handlers.

    Returns:
        redirect to new experiment step 5 (the image-editing step)
    """
    experiment_obj = Experiment.query.get_or_404(experiment_id)
    material = _record_filestack_upload('i', request.form['filestack_url'])
    if material:
        experiment_obj.image_id = material.id
        db.session.commit()
        flash('File uploaded successfully!', 'success')
    else:
        flash('There was a problem uploading the file.', 'error')
    return redirect(url_for('experiment.new_experiment_step_5', experiment_id=experiment_obj.id))


app.jinja_env.filters['urlescape'] = urllib.quote

#This request is hardcoded into the visage sdk
@experiment.route('/detail/visageSDK.data', methods=['GET'])
@login_or_token_required
def proxy_visage_data():
    """Return visageSDK.data."""
    return send_file(os.path.join(os.getcwd(),"emotiv/static/visageSDK.data"))

def gaze_data_to_csv(gaze_data):
    return "\n".join(map(lambda x: "{},{},{}".format(x['gazeDataX'], x['gazeDataY'], x['timestamp']), gaze_data))

@experiment.route('/gaze_tracking/<int:session_id>', methods=['POST'])
@login_or_token_required
def upload_gaze_tracking(session_id=None):
    """Endpoint to save Gaze Tracking Data into the database.

    Parameters:
        session_id: The session_id of the user who is viewing the experiment
        gazeData: array of gaze data information
        durationData: array of timestamps for when a particular phase element was being viewed

    Returns:
        success: boolean indicating whether the gaze data was successfully saved
    """
    session_obj = ExperimentRecordingData.query.get_or_404(session_id)
    gaze_data = request.json['gazeData']

    current_dir_gaze_data = os.path.join(os.getcwd(), "tmp_gaze_data")
    if not os.path.exists(current_dir_gaze_data):
        os.mkdir(current_dir_gaze_data)

    existing_gaze_data = session_obj.gaze_data[0] if session_obj.gaze_data else None
    csv_gaze_data = gaze_data_to_csv(gaze_data)
    file_name = "gaze_data_{}.csv".format(session_id)

    if existing_gaze_data:
        local_filepath = os.path.join(current_dir_gaze_data, existing_gaze_data.name)
        if not os.path.exists(current_dir_gaze_data, existing_gaze_data.name):
           download_csv(existing_gaze_data.file_name, local_filepath)

        with open(local_filepath, 'a') as f:
            f.write(csv_gaze_data)
    else:
        csv_gaze_data = 'gazeDataX,gazeDataY,timestamp\n' + csv_gaze_data
        with open(os.path.join(current_dir_gaze_data, file_name), 'w') as f:
            f.write(csv_gaze_data)

        upload_csv(file_name, csv_gaze_data)
        new_gaze_data = ExperimentGazeData(
            recording_data=session_obj,
            file_name="http://{}.s3.amazonaws.com/{}".format(app.config['S3_BUCKET_NAME'], file_name),
            name=file_name
        )

        db.session.add(new_gaze_data)
        db.session.commit()

    return jsonify({'success': True})

@experiment.route('/gaze_tracking/phase_element_timestamp/<int:session_id>', methods=['POST'])
@login_or_token_required
def update_duration_information(session_id=None):
    """Endpoint to save information about when a user was viewing a particular phase element.

    Parameters:
        session_id: The session_id of the user who is viewing the experiment
        phaseElementTimestamps: Array containing information pertaining to timestamp data for a specific phase element.
    """
    session_obj = ExperimentRecordingData.query.get_or_404(session_id)
    duration_information = request.json['phaseElementTimestamps']
    for duration in duration_information:
        phase_element = PhaseElement.query.filter(PhaseElement.id == duration['elementId']).one_or_none()
        if not phase_element:
            return jsonify({'success': False})

        new_duration = PhaseElementDurationData(
            phase_element=phase_element,
            recording_data=session_obj,
            view_start=iso8601.parse_date(duration['startTimestamp']).astimezone(tz.gettz('UTC')),
            view_end=iso8601.parse_date(duration['endTimestamp']).astimezone(tz.gettz('UTC')),
        )
        db.session.add(new_duration)
    db.session.commit()
    return jsonify({'success': True})

def upload_csv(filename, data):
    # Makes use of AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables
    conn = boto.connect_s3()
    bucket = conn.get_bucket(app.config['S3_BUCKET_NAME'])
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_string(data)
    return filename

def download_csv(filename, local_filename):
    # Makes use of AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables
    conn = boto.connect_s3()
    bucket = conn.get_bucket(app.config['S3_BUCKET_NAME'])
    k = bucket.get_key(filename)
    k.set_contents_to_filename(local_filename)


@experiment.route('/', methods=['GET', 'POST'])
@experiment.route('/search/<string:term>', methods=['GET', 'POST'])
@experiment.route('/sort_by/<string:sort_by>', methods=['GET', 'POST'])
@experiment.route('/sort_by/<string:sort_by>/<int:sort_page>', methods=['GET', 'POST'])
@experiment.route('/sort_by/<string:sort_by>/<string:term>', methods=['GET', 'POST'])
@experiment.route('/sort_by/<string:sort_by>/<int:sort_page>/<string:term>', methods=['GET', 'POST'])
@templated('experiment_list.html')
@login_or_token_required
def list_all(sort_by="date", sort_page=1, term=None, filter_on="any"):
    """Render experiment list view.

    Parameters:
        sort_by: field to sort by - "date", "status", or "name"
        sort_page: which page of search results to view
        term: optional search term, matches experiment name or description
        filter_on: filter experiments by status - "editing", "pending review", "scheduled", "onging", "finished", or "any"
        current_user (implicit param): always filter to show only experiments visible to the user

    Returns:
        rendered HTML of experiment list view (or json blob if Content-Type is "application/json")
    """
    # Check for experiments with status 'Scheduled' that should be 'Ongoing'
    # instead. It would be more precise to do this in something like a cron
    # job, but for now the only thing that hinges on 'Scheduled' vs 'Ongoing'
    # is the view we are about to render right now. So it is sufficient to
    # do it here, and it is simpler to not deal with external cron jobs.
    now = datetime.now()
    for experiment_obj in Experiment.query.filter(
            or_(Experiment.status == 'o', Experiment.status == 's')):
        if experiment_obj.launch_date and experiment_obj.launch_date < now:
            experiment_obj.status = 'o'
        if experiment_obj.end_date and experiment_obj.end_date < now:
            experiment_obj.status = 'f'
        db.session.commit()

    filter_on = request.args.get('filter_on')

    if request.method == 'POST':
        term = request.form.get('search')
        sort_page = 1
    if current_user.has_role('admin'):
        return redirect(url_for('admin.dashboard'))
    if request.content_type == 'application/json':
        if current_user.builder and not current_user.organization_id:
            return {'api_response': jsonify(items=[])}
        return {'api_response': jsonify(items=experiment_list_query(True, sort_by, sort_page, term, filter_on))}
    if current_user.builder and not current_user.organization_id:
        return {
            'organization': current_user.organization,
            'experiments': empty_experiments_paginate(),
            'pending_requests': [],
            'sort_page': sort_page,
            'sort_by': sort_by,
            'filter_on': filter_on,
            'is_builder': True,
            'search': term
        }
    if current_user.builder:
        pending_requests = RequestOrganization.query. \
            filter(RequestOrganization.organization_id == current_user.organization_id). \
            filter(RequestOrganization.response == "p").all()
        experiments_list = experiment_list_query(False, sort_by, sort_page, term, filter_on)
    else:
        experiments_list = experiment_list_query(False, sort_by, sort_page, term, filter_on)
        pending_requests = []
    return {
        'organization': current_user.organization,
        'experiments': experiments_list,
        'pending_requests': pending_requests,
        'sort_page': sort_page,
        'sort_by': sort_by,
        'filter_on': filter_on,
        'is_builder': current_user.builder,
        'search': term
    }


# Using a builder instead of all that mess.
def experiment_list_query(api=False, sort_by="date", sort_page=1, term=None, filter_on='any'):
    experiment_list = Experiment.query
    if current_user.builder:
        experiment_list = experiment_list.filter(Experiment.organization_id == current_user.organization_id)
        statuses = {
            'editing': 'e',
            'pending review': 'p',
            'scheduled': 's',
            'ongoing': 'o',
            'finished': 'f'
        }
        if filter_on in statuses:
            experiment_list = experiment_list.filter(Experiment.status == statuses[filter_on])
    else:
        experiment_list = experiment_list.outerjoin(Invitation). \
            filter(or_(Invitation.user_id == current_user.id, Experiment.private == False)). \
            filter(Experiment.launch_date != None). \
            filter(or_(Experiment.status == 'o', Experiment.status == 's'))  # noqa
    if sort_by == "date":
        experiment_list = experiment_list.order_by(desc(Experiment.created_at))
    elif sort_by == "status":
        experiment_list = experiment_list.order_by(asc(Experiment.status))
    else:
        experiment_list = experiment_list.order_by(asc(Experiment.name))
    if term:
        experiment_list = experiment_list.filter(or_(
            Experiment.name.ilike("""%{0}%""".format(term)),
            Experiment.description.ilike("""%{0}%""".format(term))))

    if current_user.builder:
        if api:
            return experiment_list_jsonify(experiment_list.all())
        return experiment_list.paginate(sort_page, app.config['EXPERIMENTS_PER_PAGE'] - 1, True)
    experiments_matched = filter_experiments_user_attributes(experiment_list.all())
    if api:
        return experiment_list_jsonify(experiments_matched)
    return Pagination(experiment_list, sort_page, app.config['EXPERIMENTS_PER_PAGE'] - 1,
                      len(experiments_matched), get_page(experiments_matched, sort_page))


def get_page(items, page, per_page=app.config['EXPERIMENTS_PER_PAGE'] - 1):
    start = (page - 1) * per_page
    return list(itertools.islice(items, start, start + per_page))


def filter_experiments_user_attributes(experiments):
    experiments_matched = []
    for experiment_obj in experiments:
        for _filter in experiment_obj.filters:
            accept, need_info = filters.apply_filter(_filter, current_user.attributes)
            if accept or need_info:
                continue
            else:
                break
        else:
            experiments_matched.append(experiment_obj)
    return experiments_matched


def empty_experiments_paginate():
    return Experiment.query.filter(Experiment.id == 0).paginate(1, 1, True)


# Couldn't serialize the native object so this is the workaround.
def experiment_list_jsonify(experiment_list):
    list_to_jsonify = []
    for experiment_obj in experiment_list:
        end_date = None
        if experiment_obj.end_date is not None:
            end_date = experiment_obj.end_date.date()
        this_experiment = {'id': experiment_obj.id,
                           'name': experiment_obj.name,
                           'description': experiment_obj.description,
                           'status': experiment_obj.status,
                           'private': experiment_obj.private,
                           'allow_repeats': experiment_obj.allow_repeats,
                           'web_tracking': experiment_obj.web_tracking_enabled,
                           'eye_tracking': experiment_obj.eye_tracking_enabled,
                           'recordings_to_collect': experiment_obj.recordings_to_collect,
                           'recordings_collected': experiment_obj.recordings_collected,
                           'organization': experiment_obj.organization_id,
                           'launch_date': str(experiment_obj.launch_date.date()),
                           'image': None,
                           'end_date': str(end_date),
                           'created_at': experiment_obj.created_at,
                           'change_at': experiment_obj.changed_at}
        if experiment_obj.image_id:
            this_experiment['image'] = experiment_obj.image.file_name
        list_to_jsonify.append(this_experiment)
    return list_to_jsonify


def experiment_need_criteria_jsonify(need_criteria):
    list_to_jsonify = []
    for criteria in need_criteria:
        needed_data = {'name': criteria.name}
        list_to_jsonify.append(needed_data)
    return list_to_jsonify


def send_mail(subject, recipient, sender, template, **context):
    msg = Message(subject, sender=sender, recipients=[recipient])

    ctx = ('email', template)
    msg.body = render_template('%s/%s.txt' % ctx, **context)
    msg.html = render_template('%s/%s.html' % ctx, **context)

    mail = current_app.extensions.get('mail')
    mail.send(msg)
