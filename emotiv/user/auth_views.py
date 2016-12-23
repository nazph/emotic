import requests
import simplejson
from flask import flash, current_app, redirect, request, url_for, jsonify
from flask.ext.security import Security, current_user, login_user, logout_user
from flask.ext.security.decorators import anonymous_user_required
from flask.ext.security.recoverable import reset_password_token_status
from flask.ext.security.utils import get_post_register_redirect, \
    get_hmac, encrypt_password
from flask.ext.security.views import config_value
from werkzeug.datastructures import MultiDict

from emotiv import models
from emotiv.app import app
from emotiv.database import db
from emotiv.forms import ExtendedRegisterForm
from emotiv.helpers import attempt_emotiv_login, get_user, json_headers, register_viewer_user, \
    register_builder_user, render_json, render_form_json_errors, templated
from emotiv.user.forms import LoginForm

security = Security(app, models.user_datastore,
                    register_form=ExtendedRegisterForm,
                    confirm_register_form=ExtendedRegisterForm)

# Get rid of that pesky Flask-Security register URL so we can override it.
# Accesses protected member I know... If you know of a better way let me know.
register_url = None
for url in app.url_map.iter_rules():
    if str(url) == '/register':
        register_url = url
app.url_map._rules.remove(register_url)
# same with reset
reset_url = None
for url in app.url_map.iter_rules():
    if str(url) == '/reset/<token>':
        reset_url = url
app.url_map._rules.remove(reset_url)
reset_url = None
for url in app.url_map.iter_rules():
    if str(url) == '/reset':
        reset_url = url
app.url_map._rules.remove(reset_url)
login_url = None
for url in app.url_map.iter_rules():
    if str(url) == '/login':
        login_url = url
app.url_map._rules.remove(login_url)


@security.context_processor
def security_context_processor():
    return {'user': current_user}


def _ctx(endpoint):
    # Yes I know. This accesses a protected member.
    return current_app.extensions['security']._run_ctx_processor(endpoint)


@anonymous_user_required
@app.route('/login', methods=['GET', 'POST'])
@templated('security/login_user.html')
def login():
    """Handle login request.

    Users must have created an account for this app using their EmotivID credentials.

    Parameters:
        username: EmotivID username
        password: EmotivID password

    Returns:
        Redirect to home page on success, failure message on failure.
    """
    form = LoginForm()
    if request.method == 'GET':
        return {
            'reset_password_link': app.config["FORGOT_PASSWORD_ENDPOINT"],
            'form': form,
        }
    if request.content_type == 'application/json':
        form_data = MultiDict(request.json)
        form = LoginForm(form_data)
        if 'email' in form_data.keys():
            form.username.data = form_data['email']
        success, error = get_user(True, form.username.data, form.password.data, True)
        if success:
            response_json = jsonify({"response": {"user": {"authorization_token": success[0], "refresh_token": success[1],
                                                  "expires_at": success[2], "id": success[3]}},
                                    "meta": {"code": 200}})
            return response_json, 200
        if error:
            return jsonify({"error": error}), 200
    if form.validate_on_submit():
        success, error = get_user(False, form.username.data, form.password.data)
        if success:
            return redirect(url_for('experiment.list_all'))
        flash(error, 'error')
    return {
        'reset_password_link': app.config["FORGOT_PASSWORD_ENDPOINT"],
        'form': form,
    }


@anonymous_user_required
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles a user registration request.

    Adds organization if it does not exist and user is builder.
    Submits an invitation request if it does exist.
    Maintains Flask-Security integration, just in case we want to use some of that.
    """
    if current_user.is_authenticated():
        logout_user()
    organization_list = models.Organization.query.all()
    _security = current_app.extensions['security']
    if _security.confirmable or request.json:
        form_class = _security.confirm_register_form
    else:
        form_class = _security.register_form

    if request.json:
        form_data = MultiDict(request.json)
    else:
        form_data = request.form

    form = form_class(form_data)
    registered = False
    has_errors = False
    emotiv_error = False
    if request.method == 'GET':
        return _security.render_template(config_value('REGISTER_USER_TEMPLATE'),
                                         register_user_form=form, organizations=organization_list,
                                         **_ctx('register'))

    if form.validate_on_submit():
        user_existing = models.User.query. \
            filter(models.User.username == form.username.data).first()
        if user_existing is None:
            # This is viewer
            if form.builder.data == 0:
                registered, emotiv_error = register_viewer_user(form)
            elif form.builder.data == 1:
                if len(form.organization_name.data) > 0:
                    registered, emotiv_error = register_builder_user(form)
                else:
                    form.organization_name.errors.append("You must specify an organization name when registering"
                                                         " as a builder.")
            else:
                # User tried to signup as a participant to a new organization?
                form.organization_name.errors.append("Organization does not exist")
            if registered:
                if 'access_token' in emotiv_error.keys(): 
                     login_user(registered)
                if not request.json:
                    if 'next' in form:
                        redirect_url = get_post_register_redirect(form.next.data)
                    else:
                        redirect_url = get_post_register_redirect()
                        if 'access_token' not in emotiv_error.keys(): 
                            flash('Please confirm your email address first.', 'info')
                    return redirect(redirect_url)
                form.user = registered
                return render_json(form, include_auth_token=True)
        else:
            form.username.errors.append("Username already in use.")
        has_errors = True
    if request.json:
        if not has_errors:
            return render_json(form)
        else:
            return render_form_json_errors(form, emotiv_error), 200, {'Content-Type': 'application/json; charset=utf-8'}
    return _security.render_template(config_value('REGISTER_USER_TEMPLATE'),
                                     register_user_form=form, organizations=organization_list,
                                     **_ctx('register'))


@anonymous_user_required
@app.route('/reset')
@anonymous_user_required
def forgot_password():
    """Handle password reset request.

    We just render a page with a link to emotivcloud's password reset.
    """
    _security = current_app.extensions['security']

    return _security.render_template(config_value('FORGOT_PASSWORD_TEMPLATE'),
                                     resetUrl=app.config["FORGOT_PASSWORD_ENDPOINT"]
                                     **_ctx('forgot_password'))


@anonymous_user_required
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token=None):
    """Handle password reset.

    TODO: This code should not be in use anymore and can probably be deleted.
    Password resets are now handled by emotivcloud.
    """
    _security = current_app.extensions['security']

    expired, invalid, user = reset_password_token_status(token)
    if invalid:
        flash("Invalid reset password token.", "error")
    if expired:
        flash("Token Expired", "error")
    if invalid or expired:
        return redirect(url_for('forgot_password'))

    form = security.reset_password_form()
    if request.method == 'GET':
        return _security.render_template(config_value('RESET_PASSWORD_TEMPLATE'),
                                         reset_password_form=form,
                                         reset_password_token=token,
                                         **_ctx('reset_password'))
    if form.validate_on_submit():
        current_hmac_password = user.emotiv_hash
        new_hmac_password = get_hmac(form.password.data)
        user.password = encrypt_password(form.password.data)
        user.emotiv_hash = new_hmac_password
        success, response = attempt_emotiv_login(
            user.username,
            current_hmac_password, True)
        if success:

            change_password_data = {'old_password': current_hmac_password,
                                    'password': new_hmac_password}
            response = requests.put(
                app.config["CHANGE_PASSWORD_ENDPOINT"].format(
                    response["access_token"]),
                data=change_password_data,
                json=simplejson.loads(
                    change_password_data),
                headers=json_headers)

            if "Password mismatch" in response.text:
                form.errors.append('Mismatched')
            else:
                db.session.commit()
                login_user(user)
                return redirect(url_for('experiment.list_all'))

    return _security.render_template(config_value('RESET_PASSWORD_TEMPLATE'),
                                     reset_password_form=form,
                                     reset_password_token=token,
                                     **_ctx('reset_password'))
