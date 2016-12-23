from datetime import datetime, timedelta
from functools import wraps

import requests
import simplejson
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask.ext.security import login_user, current_user
from htmlmin.main import minify

# module level import
from emotiv.app import app
from emotiv.database import db
from models import Organization, RequestOrganization, User, \
    Attribute, UserAttribute

# All this stuff only needs to be declared a single time.
# No point in creating it in every call. Maybe put in a separate file?
json_headers = {'Content-Type': 'application/json'}
form_headers = {'Content-Type': 'application/x-www-form-urlencoded'}


def attempt_emotiv_registration(username=None, password=None, first_name=None,
                                last_name=None, email=None):
    # Try to process EmotivID registration
    new_user_data = {
        "client_id": app.config["CLIENT_ID"],
        "client_secret": app.config["CLIENT_SECRET"],
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "date_joined": None,
        "last_login": None,
        "citizenship": "US",
        "resident_country": "US",
        "country": "US",
        "medical_record_id": None,
        "external_user_id": None,
        "date_of_birth": "1900-01-01",
        "sex": "M",
        "state": "",
        "city": ""
    }
    success, response = attempt_emotiv_login(username, password)
    if success:
        # User logged in to emotiv, get the profile.
        success, emotiv_profile = get_emotiv_profile(response['access_token'])
        emotiv_profile['access_token'] = response['access_token']
        emotiv_profile['refresh_token'] = response['refresh_token']
        emotiv_profile['expires'] = datetime.now() + timedelta(minutes=int(response['expires_in']))
        return success, emotiv_profile
    response = requests.post(app.config["NEW_USER_ENDPOINT"],
                             data=simplejson.dumps(new_user_data),
                             json=simplejson.dumps(new_user_data),
                             headers=json_headers)
    for s in [
            'Email has already been registered!',
            'A user with that username already exists.',
            'A user with that username is already existed']:
        if s in response.text:
            return False, ["""There is an EmotivID associated with that email account. Please register using its"""
                           """ username and password. If you need help with your account, please visit"""
                           """ <a href="https://id.emotivcloud.com/">https://id.emotivcloud.com/</a>."""]
    if response.text.startswith('{"id":'):
        emotiv_profile = simplejson.loads(response.text)
        return True, emotiv_profile
    result = []
    for field, errors in simplejson.loads(response.text).iteritems():
        for error in errors:
            result.append(field + ': ' + error)
    return False, result


def attempt_emotiv_login(username=None, password=None):
    # Try to process EmotivID login
    login_user_data = {
        "grant_type": "password",
        "client_id": app.config["CLIENT_ID"],
        "client_secret": app.config["CLIENT_SECRET"],
        "username": username,
        "password": password
    }
    response = requests.post(app.config["LOGIN_ENDPOINT"],
                             data=login_user_data,
                             headers=form_headers)
    if '"access_token"' in response.text:
        response_json = simplejson.loads(response.text)
        return True, response_json
    return False, "Emotiv Login Failed"


def get_user(api=False, username=None, password=None, json=False):
    success, response = attempt_emotiv_login(username, password)
    if success:
        access_token = response['access_token']
        refresh_token = response['refresh_token']
        expires = datetime.now() + timedelta(minutes=int(response['expires_in']))

        success, emotiv_profile = get_emotiv_profile(response['access_token'])
        if success:
            user = User.query.filter(User.emotiv_eoidc_id == emotiv_profile['user']['id']).first()
            if user:
                # Below disables builders from logging into app if builder
                if user.builder and json:
                    return False, "Builders can only login on web app."
                login_user(user)
                user.access_token = access_token
                user.refresh_token = refresh_token
                user.token_expires = expires
                db.session.commit()
                if json:
                    return (access_token, refresh_token, expires, user.id), None
                return True, None
            if api:
                return False, "There is an EmotivID associated with that username."
            return False, """There is an EmotivID associated with that username. Please register using its""" \
                          """ username and password <a href="/register">here</a>."""
        return False, "Login failed."
    return False, "Login failed. Please confirm your email address first."


def get_emotiv_profile(token=None):
    if token:
        response = requests.get(app.config["USER_ME_ENDPOINT"].format(token))
        if response.text.startswith('{"id":'):
            response_json = simplejson.loads(response.text)
            return True, response_json
    return False, ['Emotiv Login Failed or Invalid Token Used']


def register_viewer_user(form):
    success, stuff = attempt_emotiv_registration(form.username.data, form.password.data,
                                                 form.first_name.data, form.last_name.data,
                                                 form.email.data)
    if not success:
        for line in stuff:
            flash(line, 'error')
    else:
        if dict == type(stuff):
            form.builder.data = False
            user = register_user_in_db(form, stuff)
            return user, stuff
        flash('Request could not be processed.', 'error')
    return False, stuff


def register_builder_user(form):
    existing_organization = Organization.query. \
        filter(Organization.name == form.organization_name.data).first()
    if existing_organization:
        # If user is a builder do we need to process stripe info again?
        # Where is it stored???
        success, stuff = attempt_emotiv_registration(form.username.data, form.password.data, form.first_name.data,
                                                     form.last_name.data, form.email.data)
        if not success:
            for line in stuff:
                flash(line, 'error')
        else:
            if dict == type(stuff):
                form.builder.data = True
                user = register_user_in_db(form, stuff)
                new_request = RequestOrganization(organization_id=existing_organization.id,
                                                  requester_id=user.id, response="p")
                db.session.add(new_request)
                db.session.commit()
                return form.user, stuff
            else:
                flash('Request could not be processed.', 'error')
    else:
        # Organization does not exist
        # TODO: Need to process payment and do this in a call back of course.
        success, stuff = attempt_emotiv_registration(form.username.data, form.password.data, form.first_name.data,
                                                     form.last_name.data, form.email.data)
        if not success:
            for line in stuff:
                flash(line, 'error')
        else:
            if dict == type(stuff):
                form.builder.data = True
                user = register_user_in_db(form, stuff)
                new_organization = Organization(name=form.organization_name.data, owner_id=form.user.id)
                db.session.add(new_organization)
                db.session.commit()
                user.organization_id = new_organization.id
                new_request = RequestOrganization(organization_id=new_organization.id, requester_id=user.id,
                                                  responder_id=user.id, response="a")
                db.session.add(new_request)
                db.session.commit()
                return form.user, stuff
            else:
                flash('Request could not be processed.', 'error')
    return False, stuff


def register_user_in_db(form, stuff):
    values = form.to_dict()
    user = User(username=values['username'], first_name=values['first_name'], last_name=values['last_name'],
                builder=values['builder'], email=values['email'], emotiv_dbapi_id=stuff['id'],
                emotiv_eoidc_id=stuff['user']['id'],
                emotiv_eoidc_username=stuff['user']['username'])
    if 'access_token' in stuff.keys(): 
        user.access_token=stuff['access_token']
        user.refresh_token=stuff['refresh_token']
        user.token_expires=stuff['expires']
    db.session.add(user)
    db.session.commit()
    form.user = user
    return user


def render_form_json_errors(form, other=None):
    json_errors = {}
    for field in form:
        if len(field.errors) > 0:
            json_errors[field.short_name] = {'errors': []}
            for error in field.errors:
                json_errors[field.short_name]['errors'].append(error)
    if other:
        json_errors['error'] = other.replace('<a href="https://id.emotivcloud.com/">', '').replace('</a>', '')
    return jsonify(json_errors)


# What is this here for you ask?
# So, I don't have to include the current user to
# every functions response manually.
#
# Calling render_from_template, etc, it cuts out
# quite a bit of the tedious coding.
#
# Any functionality I want to process for every response that has a template
# can also be done in here.
def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint.replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            ctx['url'] = app.config['ROOT_URL'] + request.path
            ctx['user'] = current_user
            if ctx.get('api_response'):
                return ctx['api_response']
            if template_name == "401.html":
                return render_template(template_name, **ctx), 401
            elif template_name == "402.html":
                return render_template(template_name, **ctx), 402
            elif template_name == "403.html":
                return render_template(template_name, **ctx), 403
            elif template_name == "404.html":
                return render_template(template_name, **ctx), 404
            # An easter egg! They can minify the response, if desired.
            if app.config['MINIFY']:
                return minify(render_template(template_name, **ctx))
            else:
                return render_template(template_name, **ctx)

        return decorated_function

    return decorator


# Custom auth decorator...
def login_or_token_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated():
            token = request.form.get('auth_token')
            if token:
                get_user_by_token(token)
                return func(*args, **kwargs)
            token = request.headers.get('Authentication-Token')
            if token:
                get_user_by_token(token)
                return func(*args, **kwargs)
            return redirect(url_for('not_authorized'))
        return func(*args, **kwargs)
    return decorated_function


def get_user_by_token(token=None):
    if token:
        user = User.query.filter(User.access_token == token).first()
        if user:
            login_user(user)
            return user
        return False
    return False


def render_json(form, include_user=True, include_auth_token=False):
    has_errors = len(form.errors) > 0

    if has_errors:
        code = 400
        response = {"errors": form.errors}
    else:
        code = 200
        response = {}
        if include_user:
            response['user'] = {"id": form.user.id}
        if include_auth_token:
            response['user']['authentication_token'] = form.user.access_token

    return jsonify({'meta': {'code': code}, 'response': response})

# Multidict throws an error if you try to index into an empty list.
# See https://github.com/pallets/werkzeug/issues/944
def is_nonempty(form_data, key):
    try:
        data = form_data.get(key)
        return len(data) > 0
    except IndexError:
        return False
    return True

# This functions removes some code which is used by both
# api and web view
def set_user_attributes_helper(form_data):
    attributes = Attribute.query.all()
    for x in form_data:
        for attribute in attributes:
            if attribute.name.lower() == x:
                existing_user_attributes = UserAttribute.query. \
                    filter(UserAttribute.attribute_id == attribute.id). \
                    filter(UserAttribute.user_id == current_user.id).all()

                if existing_user_attributes:
                    for existing_user_attribute in existing_user_attributes:
                        db.session.delete(existing_user_attribute)

                if is_nonempty(form_data, x):
                    for value in form_data.getlist(x):
                        new_user_attribute = UserAttribute(
                                user_id=current_user.id,
                                attribute_id=attribute.id,
                                value=value,
                                )
                        db.session.add(new_user_attribute)
    db.session.commit()
