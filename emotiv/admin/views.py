from flask import current_app, flash, redirect, render_template, request, url_for
from flask.ext.security import roles_required
from flask_mail import Message
from sqlalchemy import asc
from sqlalchemy.sql.expression import nullsfirst
import pdb
from emotiv.admin import admin
from emotiv.admin.forms import AttributeForm, CommentForm
from emotiv.app import app
from emotiv.database import db
from emotiv.helpers import login_or_token_required, templated
from emotiv.models import Attribute, AttributeSuggestion, Experiment, SelectOption, Phase
from emotiv.phase.views import serialize_phase_elements
import json


@admin.route('/', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('dashboard.html')
def dashboard():
    """Main admin page.

    Renders HTML for attribute requests and experiments that need admin attention.
    """
    sessions = []
    attributes = AttributeSuggestion.query.filter(AttributeSuggestion.status == 'p').all()
    nulls = nullsfirst
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        nulls = lambda x: x
    experiments = Experiment.query \
        .filter(Experiment.status == 'p') \
        .order_by(
            nulls(asc(Experiment.submitted_date)), asc(Experiment.created_at)
        ).all()
    return {'attributes': attributes, 'experiments': experiments, 'sessions': sessions}


@admin.route('/new_attribute', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('edit_attribute.html')
def new_attribute():
    """Attribute creation page.

    GET: render the HTML form
    POST: take AttributeForm params in the body and create attribute if they pass validation
    """
    return _new_attribute(None)


@admin.route('/view_attributes', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('edit_attributes.html')
def view_attributes():
    """Attribute list view page.

    Renders an HTML view of the current attributes.
    """
    return {'attributes': available_attributes()}


@app.template_filter('single_quote_escape')
def single_quote_escape(s):
    """Escape single quotes."""
    return s.replace("'", "\\'")


@admin.route('/view_attribute/<int:attribute_id>', methods=['GET'])
@login_or_token_required
@roles_required('admin')
@templated('edit_attribute.html')
def view_attribute(attribute_id=None):
    """Render the view for a single attribute

    Renders an HTML view.
    """
    attribute = Attribute.query.get_or_404(attribute_id)
    form = AttributeForm()
    form.input_type.data = attribute.input_type
    form.name.data = attribute.name
    for o in attribute.possible_options:
        form.criteria_options.append_entry(o.value)
        form.content_types.append_entry(o.content_type)
    return {
        'form': form,
        'options': attribute.possible_options,
        # View settings
        'view': True,
        'type': next(c[1] for c in form.input_type.choices if c[0] == attribute.input_type),
    }


@admin.route('/delete_attribute/<int:attribute_id>', methods=['POST'])
@login_or_token_required
@roles_required('admin')
def delete_attribute(attribute_id=None):
    """Handle delete attribute API requests.

    Deletes the attribute if it exists, and flashes a confirmation message.
    """
    attribute = Attribute.query.get_or_404(attribute_id)
    db.session.delete(attribute)
    db.session.commit()
    flash('Deleted attribute "{}"'.format(attribute.name), 'success')
    return 'success'


@admin.route('/new_attribute/render_options', methods=['GET'])
@login_or_token_required
@roles_required('admin')
@templated('criteria_options.html')
def render_criteria_options():
    """Render list of criteria options to HTML.

    Now that we are using React, it would be nice to render this on the client
    instead. But it hasn't been worth it to move this logic yet.
    """
    seen = set()

    def unique(x):
        u = x not in seen
        seen.add(x)
        return u

    options = [json.loads(option) for option in filter(unique, request.args.getlist('o'))]
    # pdb.set_trace()
    # options = [o['data'] for o in options]
    return {'options': options, 'view': False}


def available_attributes():
    all_attributes = Attribute.query.all()
    return [(int(item.id), item.name,) for item in all_attributes]


@admin.route('/new_attribute/<int:id>', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('edit_attribute.html')
def new_attribute_from_suggestion(id=None):
    """Attribute creation page with suggestion.

    Parameters:
        id: ID of an AttributeSuggestion, to be rendered at the top of the page

    GET: render the HTML form
    POST: take AttributeForm params in the body and create attribute if they pass validation
    """
    return _new_attribute(id)


def _new_attribute(id=None):
    form = AttributeForm()
    suggestion = AttributeSuggestion.query.get_or_404(id) if id else None
    if not form.validate_on_submit():
        if request.method == 'POST':
            flash('Invalid form. Check error messages below.', 'error')
        return {'form': form, 'suggestion': suggestion, 'edit': False}
    if Attribute.query.filter(Attribute.name == form.name.data).first():
        flash('An attribute with this name already exists.', 'error')
        return {'form': form, 'suggestion': suggestion, 'edit': False}
    attribute = Attribute(name=form.name.data, input_type=form.input_type.data)
    db.session.add(attribute)
    for i, opt in enumerate(form.criteria_options):
        new_opt = SelectOption(attribute=attribute, value=opt.data, content_type=form.content_types[i].data)
        db.session.add(new_opt)
        attribute.possible_options.append(new_opt)
    db.session.commit()
    flash('New attribute created', 'success')
    if suggestion:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('admin.view_attribute', attribute_id=attribute.id))


@admin.route('/approve/attribute/<int:suggestion_id>', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('response.html')
def approve_attribute(suggestion_id=None):
    """Approve an attribute and redirect to attribute creation page.

    GET: just render the HTML approval form
    POST: approve the attribute and notify requester

    Parameters:
        suggestion_id: ID of an AttributeSuggestion. The builder who suggested it will be notified by email.
    """
    form = CommentForm()
    suggestion = AttributeSuggestion.query.get_or_404(suggestion_id)
    if request.method == "GET":
        return {'form': form, 'approve_or_deny': 'Approve', 'type': 'Attribute', 'suggestion': suggestion.text}
    if response_post_helper(form, approve=True, suggestion=suggestion):
        flash("We emailed the requester to let them know Emotiv has approved their criteria request. \
        Please actually create their requested criteria here.", 'success')
        return redirect(url_for('admin.new_attribute_from_suggestion', id=suggestion.id))
    return {'form': form, 'approve_or_deny': 'Approve', 'type': 'Attribute', 'suggestion': suggestion.text}


def response_post_helper(form, approve, suggestion=None, experiment=None):
    """Approve or deny a criteria suggestion or experiment.

    Also notify the requester by email.
    """
    if not form.validate_on_submit():
        return False

    if not len(form.comment.data):
        form.comment.data = "No reason given."
    try:
        def send(subject, to, requested):
            result = 'approved' if approve else 'denied'
            send_mail(
                subject,
                to,
                app.config['SECURITY_EMAIL_SENDER'],
                'response',
                suggestion=suggestion,
                experiment=experiment,
                message='Your request for {} was {}.'.format(requested, result),
                comment=form.comment.data
            )
        if suggestion is not None:
            send('Emotiv Attribute Suggestion', suggestion.user.email, 'a new attribute')
        if experiment is not None:
            send('Emotiv Experiment', experiment.user.email, 'an experiment')
    except Exception, ex:
        print ex.message
        flash('There was a problem sending the email.', 'error')
    if approve:
        if suggestion is not None:
            suggestion.status = 'a'
            flash('Attribute request approved.', 'success')
        if experiment is not None:
            experiment.status = 's'
            flash('Experiment request approved.', 'success')
    else:
        if suggestion is not None:
            suggestion.status = 'd'
            flash('Attribute request denied.', 'success')
        if experiment is not None:
            experiment.status = 'e'
            flash('Experiment request denied.', 'success')
    db.session.commit()
    return True


@admin.route('/deny/attribute/<int:suggestion_id>', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('response.html')
def deny_attribute(suggestion_id=None):
    """Deny an attribute and redirect to the admin dashboard.

    GET: just render the HTML denial form
    POST: deny the attribute and notify requester

    Parameters:
        suggestion_id: ID of an AttributeSuggestion. The builder who suggested it will be notified by email.
    """
    form = CommentForm()
    suggestion = AttributeSuggestion.query.get_or_404(suggestion_id)
    if request.method == "GET":
        return {'form': form, 'approve_or_deny': 'Deny', 'type': 'Attribute', 'suggestion': suggestion.text}
    if response_post_helper(form, approve=False, suggestion=suggestion):
        return redirect(url_for('admin.dashboard'))
    return {'form': form, 'approve_or_deny': 'Deny', 'type': 'Attribute', 'suggestion': suggestion.text}


@admin.route('/approve/experiment/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('response.html')
def approve_experiment(experiment_id=None):
    """Approve an experiment and redirect to the admin dashboard.

    GET: just render the HTML approval form
    POST: approve the experiment and notify builder

    The user who created the experiment will be notified by email.
    """
    form = CommentForm()
    experiment = Experiment.query.get_or_404(experiment_id)
    if request.method == "GET":
        return {
            'form': form,
            'approve_or_deny': 'Approve',
            'type': 'Experiment',
            'experiment': experiment.name,
            'organization': experiment.organization.name,
        }
    if response_post_helper(form, approve=True, experiment=experiment):
        return redirect(url_for('admin.dashboard'))
    return {
        'form': form,
        'approve_or_deny': 'Approve',
        'type': 'Experiment',
        'experiment': experiment.name,
        'organization': experiment.organization.name,
    }


@admin.route('/deny/experiment/<int:experiment_id>', methods=['GET', 'POST'])
@login_or_token_required
@roles_required('admin')
@templated('response.html')
def deny_experiment(experiment_id=None):
    """Deny an experiment and redirect to the admin dashboard.

    GET: just render the HTML approval form
    POST: deny the experiment and notify builder

    The user who created the experiment will be notified by email.
    """
    form = CommentForm()
    experiment = Experiment.query.get_or_404(experiment_id)
    if request.method == "GET":
        return {
            'form': form,
            'approve_or_deny': 'Deny',
            'type': 'Experiment',
            'experiment': experiment.name,
            'organization': experiment.organization.name,
        }
    if response_post_helper(form, approve=False, experiment=experiment):
        return redirect(url_for('admin.dashboard'))
    return {
        'form': form,
        'approve_or_deny': 'Deny',
        'type': 'Attribute',
        'experiment': experiment.name,
        'organization': experiment.organization.name,
    }


@admin.route('/review/experiment/<int:experiment_id>')
@login_or_token_required
@roles_required('admin')
@templated('review_experiment.html')
def review_experiment(experiment_id=None):
    """Render the review page for an experiment."""
    return {
        'experiment': Experiment.query.get_or_404(experiment_id),
        'SelectOption': SelectOption,
    }


@admin.route('/review/experiment/roadmap/<int:experiment_id>')
@login_or_token_required
@roles_required('admin')
@templated('review_experiment_roadmap.html')
def review_experiment_roadmap(experiment_id=None):
    """Render the review page for an experiment roadmap."""
    return {
        'experiment': Experiment.query.get_or_404(experiment_id),
    }


@admin.route('/review/experiment/phase/<int:phase_id>')
@login_or_token_required
@roles_required('admin')
@templated('review_experiment_phase.html')
def review_experiment_phase(phase_id=None):
    """Render the review page for an experiment phase."""
    phase = Phase.query.get_or_404(phase_id)
    return {
        'phase': phase,
        'elements': serialize_phase_elements(phase),
    }


def send_mail(subject, recipient, sender, template, **context):
    """Send an email."""
    msg = Message(subject, sender=sender, recipients=[recipient])

    ctx = ('email', template)
    msg.body = render_template('%s/%s.txt' % ctx, **context)
    msg.html = render_template('%s/%s.html' % ctx, **context)

    mail = current_app.extensions.get('mail')
    mail.send(msg)
