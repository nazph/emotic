from collections import defaultdict
import json

from flask import abort, render_template, request, url_for, redirect, flash
from flask.ext.security import current_user
from wtforms.validators import ValidationError

from emotiv.database import db
from emotiv.experiment.forms import CalibrationLength
from emotiv.helpers import login_or_token_required, templated
from emotiv.material.views import _get_material
from emotiv.models import Experiment, Material, Phase, PhaseCondition, PhaseElement, PhaseElementAnswer
from emotiv.phase import phase
from emotiv.phase.forms import PhaseForm, PhaseDetailForm


def builder_validation(experiment_org_id=None):
    if current_user.builder:
        if experiment_org_id is None:
            return True
        if experiment_org_id == current_user.organization_id:
            return True
    return False


@phase.route('/set/calibration/<int:experiment_id>', methods=['POST'])
@login_or_token_required
@templated('phase_detail.html')
def set_calibration(experiment_id=None):
    """Set how long to run calibration for this experiment.

    Parameters:
        experiment_id: ID of experiment to update
        length (form field): length in seconds for calibration
    """
    experiment = Experiment.query.get_or_404(experiment_id)
    if not builder_validation(experiment_org_id=experiment.organization_id):
        return "Not authorized for this experiment", 401
    form = CalibrationLength()
    if form.validate_on_submit():
        experiment.calibration_length = form.length.data
        db.session.commit()
        flash('Updated calibration length', 'success')
        return redirect(url_for('experiment.edit_roadmap', experiment_id=experiment_id))
    return {
        'phase': experiment.calibration_phase,
        'calibration_form': form,
        'allow_delete': False,
    }


@phase.route('/new/<int:experiment_id>', methods=['POST'])
@login_or_token_required
def new_phase(experiment_id=None):
    """Create a new phase for this experiment.

    Parameters:
        experiment_id: ID of experiment to update
        name (form field): name of new phase - must be unique in this experiment
        insert_id: ids of previous phases to insert new phase in between, separated by an underscore - "<prev phase id>_<new phase id>"
    """
    experiment = Experiment.query.get_or_404(experiment_id)
    if not builder_validation(experiment_org_id=experiment.organization_id):
        return "Not authorized for this experiment", 401
    form = PhaseForm()
    if form.validate_on_submit():
        for e_phase in experiment.phases:
            if form.name.data == e_phase.name:
                form.name.errors.append("Phase already exists with that name.")
                return render_template('phase_form.html', form=form, insert_id=request.form.get('insert_id')), 422
        prev_id, next_id = request.form.get('insert_id').split('_')
        previous_phase = Phase.query.filter(Phase.experiment_id == experiment.id).filter(Phase.id == prev_id).first()
        next_phase = Phase.query.filter(Phase.experiment_id == experiment.id).filter(Phase.id == next_id).first()

        new_phase_obj = Phase(name=form.name.data, rank=1, experiment_id=experiment.id,
                              organization_id=experiment.organization_id, previous_phase=previous_phase)

        db.session.add(new_phase_obj)
        new_phase_default_condition = PhaseCondition(operation="default", phase=new_phase_obj, next_phase=next_phase)
        db.session.add(new_phase_default_condition)
        new_phase_obj.default_condition = new_phase_default_condition
        previous_phase.default_condition.next_phase = new_phase_obj
        if next_phase:
            next_phase.previous_phase = new_phase_obj
        db.session.commit()
    else:
        return render_template('phase_form.html', form=form, insert_id=request.form.get('insert_id')), 422
    return render_template('phases.html', experiment=experiment)


@phase.route('/<int:phase_id>', methods=['GET', 'POST'])
@login_or_token_required
@templated('phase_detail.html')
def detail(phase_id=None):
    """Render or update a phase.

    GET: render HTML for a phase
    POST: update the entire phase object

    Parameters:
        data: JSON-serialized phase data

    Check the code here and in phase_detail.js for an authoritative version, but the
    structure of `data` currently looks like this:
        {
            "elements": [
                "text": text for this phase element, if applicable
                "input_type": for question elements. 'ss', 'ms', 'sv', 'ot', or 'dt'. see models.py
                "duration_ms": for images, how long to display the image, in milliseconds
                "category_type": type of element. 'a', 'i', 'v', 't', or 'q'. see models.py
                "material": for media elements, the corresponding Material id

                "answers": [ // answers only present for multi-choice question elements
                    "material_id": if an image answer, the corresponding Material id
                    "value": text answer
                ]
            ]
        }
    """
    phase_obj = Phase.query.get_or_404(phase_id)
    organization = phase_obj.organization
    if not builder_validation(experiment_org_id=organization.id):
        return redirect(url_for('not_authorized'))

    if request.method == 'POST':
        for element in PhaseElement.query.filter(PhaseElement.phase_id == phase_id).all():
            db.session.delete(element)

        for answer in PhaseElementAnswer.query.filter(PhaseElementAnswer.phase_id == phase_id).all():
            db.session.delete(answer)

        def check_material_id(material_id):
            if material_id and not Material.query.filter(Material.organization_id == organization.id). \
                    filter(Material.id == element['material_id']).first():
                raise ValidationError()

        form = PhaseDetailForm()
        data = json.loads(form.data.data)

        for (i, element) in enumerate(data['elements']):
            element = defaultdict(lambda: None, **element)
            check_material_id(element['material_id'])
            element_obj = PhaseElement(
                phase=phase_obj,
                text=element['text'],
                input_type=element['input_type'],
                duration_ms=element['duration_ms'],
                organization=organization,
                position=i,
                category_type=element['category_type'],
                material_id=element['material'],
                description=element['description']
            )
            db.session.add(element_obj)
            for (j, answer) in enumerate(element.get('answers', [])):
                answer = defaultdict(lambda: None, **answer)
                check_material_id(answer['material_id'])
                db.session.add(PhaseElementAnswer(
                    value=answer['value'],
                    label=answer.get('label', None),
                    phase=phase_obj,
                    organization=organization,
                    position=j,
                    phase_element=element_obj,
                    material_id=answer['material_id'],
                    content_type=answer['content_type']
                ))
        db.session.commit()
        flash('Updated phase', 'success')
        return redirect(url_for('experiment.edit_roadmap', experiment_id=phase_obj.experiment.id))

    return {
        'phase': phase_obj,
        'elements': serialize_phase_elements(phase_obj),
        'calibration_form': CalibrationLength(),
        'allow_delete': not is_required_phase(phase_obj),
        'token': current_user.access_token,
    }


def serialize_phase_elements(phase_obj):
    return [{
      'id': e.id,
      'category_type': e.category_type,
      'input_type': e.input_type,
      'text': e.text,
      'material_data': _get_material(e.material_id),
      'duration_ms': e.duration_ms,
      'material': e.material_id,
      'description': e.description,
      'answers': [{
        'value': a.value,
        'id': a.id,
        'label': a.label,
        'content_type': a.content_type
      } for a in e.answers]
    } for e in phase_obj.elements]


def is_required_phase(phase_obj):
    exp = phase_obj.experiment
    return phase_obj in [exp.calibration_phase, exp.start_phase, exp.end_phase]


@phase.route('/delete/<int:phase_id>', methods=['GET', 'POST'])
@login_or_token_required
def delete(phase_id=None):
    """Delete a phase.

    Also unlink the phase from the previous and next phases.
    """
    phase_obj = Phase.query.get_or_404(phase_id)
    if not builder_validation(experiment_org_id=phase_obj.experiment.organization_id):
        return redirect(url_for('not_authorized'))
    experiment_id = phase_obj.experiment.id

    if is_required_phase(phase_obj):
        flash('Cannot delete that phase', 'error')
        return redirect(url_for('experiment.edit_roadmap', experiment_id=experiment_id))

    # Assume for now that there is only one successor phase. This will not be true in the future,
    # but dealing with it requires the same logic as dealing with phase reordering, which will
    # happen in the next milestone.
    if len(phase_obj.conditions) != 1:
        abort(500, 'Deleting a phase with multiple successor phases is not implemented')
    next_phase = phase_obj.conditions[0].next_phase
    previous_phase = phase_obj.previous_phase
    if len(previous_phase.conditions) != 1:
        abort(500, 'Deleting a phase with multiple sibling phases is not implemented')

    # Update previous phase and next phase.
    next_phase.previous_phase = previous_phase
    previous_phase.default_condition.next_phase = next_phase

    # Remove phase_obj from the database.
    db.session.delete(phase_obj)

    db.session.commit()

    flash('Phase deleted.', 'success')
    return redirect(url_for('experiment.edit_roadmap', experiment_id=experiment_id))
