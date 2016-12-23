import requests
import simplejson
from flask import redirect, url_for, request, jsonify, flash
from flask.ext.security import current_user
from werkzeug.datastructures import MultiDict

from emotiv.app import app
from emotiv.helpers import attempt_emotiv_login, login_or_token_required, \
    templated, set_user_attributes_helper
from emotiv.models import Attribute
from emotiv.user import user
from forms import ChangePasswordForm
from itertools import groupby

json_headers = {'Content-Type': 'application/json'}


# Used for remote api
@user.route('/<username>/modify', methods=['POST'])
@login_or_token_required
def modify_user(username=None):
    """Change password for current user.

    TODO: This code should not be in use anymore and can probably be deleted.
    Password resets are now handled by emotivcloud.
    """
    form = ChangePasswordForm()
    change_password_helper(form)
    return render_form_to_json(form)


@app.route('/profile', methods=['GET', 'POST'])
@templated('profile.html')
@login_or_token_required
def profile():
    """Display or update user profile.

    GET: render user profile
    POST: update user profile

    Parameters (for POST):
        new attributes, keyed by parameter name. see parsing code in set_user_attributes_helper.

    Returns:
        (possibly updated) user profile page
    """
    if request.method == 'POST':
        set_user_attributes_helper(request.form)
        flash("Attributes Saved")
        return redirect(url_for('profile'))

    return {
        "attributes": attributes_with_user_attribute(),
        "password_link": app.config["FORGOT_PASSWORD_ENDPOINT"],
    }


def attributes_with_user_attribute():
    attributes = Attribute.query.all()
    user_attributes = sorted(current_user.attributes, key=lambda x: x.attribute_id)
    for attribute in attributes:
        # set attribute.user_attribute to user_attribute or None
        for k, g in groupby(user_attributes, key=lambda x: x.attribute_id):
            user_attribute = list(map(lambda x: x.value, g))
            if k == attribute.id:
                attribute = setattr(attribute, 'user_attribute', user_attribute)
                break
        else:
            setattr(attribute, 'user_attribute', [])
    return attributes


# To set multiple at a time
@user.route('/<username>/attributes', methods=['PUT', 'GET'])
@login_or_token_required
def set_attributes(username=None):
    """Get or set user attributes, as a JSON API.

    GET: retrieve current user attributes
    PUT: update current user attributes

    Parameters (for PUT):
        new attributes, keyed by parameter name. see parsing code in set_user_attributes_helper.
    """
    if request.method == 'GET':
        return jsonify(attributes=user_attributes_jsonify(attributes_with_user_attribute()))
    else:
        if not current_user.username == username:
            return jsonify({"error": "Can't change attributes for that user"}), 200
        if request.json:
            form_data = MultiDict(request.json)
        else:
            form_data = request.form
        set_user_attributes_helper(form_data)
        if not request.json:
            return redirect(url_for('profile'))
        response_json = jsonify(response='attribute added')
        return response_json, 200


def change_password_helper(form):
    if form.validate_on_submit():
        success, response = attempt_emotiv_login(current_user.username,
                                                 form.current_password.data)
        if not success:
            form.current_password.errors.append('Incorrect password')
            return (form)
        change_password_data = {'old_password': form.current_password.data,
                                'password': form.new_password.data}
        response = requests.put(
            app.config["CHANGE_PASSWORD_ENDPOINT"].format(
                response["access_token"]),
            data=simplejson.dumps(change_password_data),
            json=simplejson.dumps(change_password_data),
            headers=json_headers)
        if response.status_code is not requests.codes.ok:
            form.errors.append('There was an error')
            return (form)
    return (form)


def set_items(inner_items, inner_item_name, outer_item, inner_item_value=None):
    if outer_item is not None:
        for item in inner_items:
            if getattr(item, "id") == outer_item.id:
                if inner_item_value is None:
                    setattr(outer_item, inner_item_name, item)
                else:
                    setattr(outer_item, inner_item_name,
                            getattr(item, inner_item_value))
                break
        else:
            setattr(outer_item, inner_item_name, None)
    return outer_item


def user_attributes_jsonify(attributes):
    list_to_jsonify = []
    for attribute in attributes:
        user_possible_options = []
        if hasattr(attribute, 'possible_options'):
            if attribute.possible_options is not None:
                for option in attribute.possible_options:
                    user_possible_options.append(option.value)
        list_to_jsonify.append({
            'name': attribute.name.lower(),
            'values': attribute.user_attribute,
            'possible_values': user_possible_options,
            'type': attribute.input_type,
        })
    return list_to_jsonify


def render_form_to_json(form):
    has_errors = len(form.errors) > 0
    if has_errors:
        code = 400
        response = {"errors": form.errors}
    else:
        code = 200
        response = {}

    return jsonify({"meta": {"code": code}, "response": response})
