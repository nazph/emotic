from flask import flash, redirect, request, url_for
from sqlalchemy import asc

from flask.ext.security import current_user
from emotiv.helpers import login_or_token_required, templated
from emotiv.models import db, Organization, RequestOrganization
from emotiv.organization import organization
from emotiv.organization.forms import NewOrganizationForm


def builder_validation():
    if current_user.builder and current_user.organization_id:
        return
    flash("You do not have permission for %s's organization" %
          current_user.organization.name, 'error')
    return redirect(url_for('experiment.list_all'))


@organization.route('/request/approve/<int:request_id>')
@login_or_token_required
def approve_request(request_id=None):
    """Approve a request to join the current user's organization.

    When someone requests to join an organization, any member of that organization can
    click the generated link to this endpoint to approve the request.

    Parameters:
        request_id: ID of the RequestOrganization object generated for this request

    Returns:
        redirect to the current user's organization settings
    """
    builder_validation()
    request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.id == request_id).first_or_404()
    request_obj.response = "a"
    request_obj.responder_id = current_user.id
    request_obj.requester.organization_id = request_obj.organization_id
    db.session.commit()
    flash("%s's request has been approved for %s" %
          (request_obj.requester.username, current_user.organization.name), 'success')
    return redirect(url_for('organization.settings'))


@organization.route('/request/approve/ajax/<int:request_id>')
@login_or_token_required
def approve_request_ajax(request_id=None):
    """Approve a request to join the current user's organization, ajax version.

    Like approve_request, but for API use.

    Parameters:
        request_id: ID of the RequestOrganization object generated for this request

    Returns:
        the id of another request to join this organization, or "0" if there are none
    """
    builder_validation()
    request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.id == request_id).first()
    if request_obj:
        request_obj.response = "a"
        request_obj.responder_id = current_user.id
        request_obj.requester.organization_id = request_obj.organization_id
        db.session.commit()
    next_request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.response == 'p').first()
    if next_request_obj is not None:
        return str(next_request_obj.id)
    return "0"


@organization.route('/new', methods=['GET', 'POST'])
@login_or_token_required
@templated('new_org.html')
def new():
    """Create a new organization.

    GET: just render the form
    POST: validate and then create the organization

    Parameters (for POST):
        name: The name of the new organization. Must not match an existing name.
    """
    if current_user.builder:
        form = NewOrganizationForm()
        if request.method == "GET":
            return {"form": form}
        if form.validate_on_submit():
            if not (255 > len(form.name.data) > 0):
                form.name.errors.append('Must be greater than 0 and less than 255 characters.')
            else:
                existing_organization = Organization.query. \
                    filter(Organization.name == form.name.data).first()
                if existing_organization:
                    form.name.errors.append('Organization already exists.', 'error')
                else:
                    org_request = RequestOrganization.query.filter(
                        RequestOrganization.requester_id == current_user.id).first()
                    db.session.delete(org_request)
                    db.session.flush()
                    db.session.commit()
                    new_organization = Organization(name=form.name.data,
                                                    owner_id=current_user.id)
                    db.session.add(new_organization)
                    db.session.commit()
                    current_user.organization_id = new_organization.id
                    new_request = RequestOrganization(organization_id=new_organization.id,
                                                      requester_id=current_user.id,
                                                      responder_id=current_user.id,
                                                      response="a")
                    db.session.add(new_request)
                    db.session.commit()
                    return redirect(url_for('experiment.list_all'))
        return {"form": form}
    else:
        flash("Only builders may create new organizations", 'error')
        return redirect(url_for('experiment.list_all'))


@organization.route('/request/next/ajax/<int:request_id>')
@login_or_token_required
def next_request_ajax(request_id=None):
    """Render the HTML UI to approve or reject a request to join the current user's organization.

    Parameters:
        request_id: The ID of the request to render a UI for.

    Returns:
        Request approval form as an HTML string 
    """
    builder_validation()
    next_request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.response == 'p'). \
        filter(RequestOrganization.id == request_id).first_or_404()
    if next_request_obj is not None:
        if next_request_obj.requester.builder:
            access_level = "Builder"
        else:
            access_level = "Viewer"
        return "Username: %s<br>Access Level: %s<br>Requested at: %s" % \
               (next_request_obj.requester.username, access_level,
                next_request_obj.requester.created_at)
    return "Request not found..."


@organization.route('/request/reject/<int:request_id>')
@login_or_token_required
@templated('experiments.html')
def reject_request(request_id=None):
    """Reject a request to join the current user's organization.

    When someone requests to join an organization, any member of that organization can
    click the generated link to this endpoint to reject the request.

    Parameters:
        request_id: ID of the RequestOrganization object generated for this request

    Returns:
        redirect to the current user's organization settings
    """
    builder_validation()
    request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.id == request_id).first_or_404()
    if request_obj:
        request_obj.response = "r"
        request_obj.responder_id = current_user.id
    db.session.commit()
    flash("%s's request has been rejected for %s" %
          (request_obj.requester.username, current_user.organization.name), 'success')
    return redirect(url_for('organization.settings'))


@organization.route('/request/reject/ajax/<int:request_id>')
@login_or_token_required
def reject_request_ajax(request_id=None):
    """Reject a request to join the current user's organization, ajax version.

    Like reject_request, but for API use.

    Parameters:
        request_id: ID of the RequestOrganization object generated for this request

    Returns:
        the id of another request to join this organization, or "0" if there are none
    """
    builder_validation()
    request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.id == request_id).first()
    if request_obj:
        request_obj.response = "r"
        request_obj.responder_id = current_user.id
        db.session.commit()
    next_request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.response == 'p').first()
    if next_request_obj is not None:
        return str(next_request_obj.id)
    return "0"


@organization.route('/request/revoke/<int:request_id>')
@login_or_token_required
@templated('experiments.html')
def revoke_request(request_id=None):
    """Remove a user from the current user's organization.

    Parameters:
        request_id: The ID of the user's original request to join the organization.

    Returns:
        redirect to current user's organization settings
    """
    builder_validation()
    request_obj = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.id == request_id).first_or_404()
    if request_obj:
        request_obj.response = "r"
        request_obj.responder_id = current_user.id
        request_obj.requester.organization_id = None
    db.session.commit()
    flash("%s's access has been revoked for %s" %
          (request_obj.requester.username, current_user.organization.name), 'success')
    return redirect(url_for('organization.settings'))


@organization.route('/settings')
@login_or_token_required
@templated('org_settings.html')
def settings():
    """Organization dashboard page.

    From the organization dashboard, users can manage requests to join their organization.

    Returns:
        dashboard for current user's organization
    """
    builder_validation()
    pending_requests = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.response == "p").all()
    other_requests = RequestOrganization.query. \
        filter(RequestOrganization.organization_id == current_user.organization_id). \
        filter(RequestOrganization.response != "p"). \
        order_by(asc(RequestOrganization.response)).all()
    return {'organization': current_user.organization,
            'pending_requests': pending_requests,
            'other_requests': other_requests}
