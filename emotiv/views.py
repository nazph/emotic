from flask import jsonify, redirect, request, url_for, send_from_directory
from flask.ext.security import current_user

# module level imports
from emotiv.app import app
from emotiv.helpers import templated


@app.errorhandler(401)
@app.route('/401')
@templated('401.html')
def not_authorized():
    """Custom 401 page"""
    return {}


@app.errorhandler(404)
@templated('404.html')
def page_not_found(e):
    """Custom 404 page"""
    return {}


@app.route('/')
def web_root():
    """Root page.

    If the current user is not logged in, redirect to login.
    If the current user is an admin, redirect to admin dashboard.
    Otherwise, redirect to experiment list view.
    """
    if request.content_type == 'application/json':
        return jsonify({"meta": {"code": 200, },
                        "response": {"success": True, }, }), 200
    if not current_user.is_authenticated():
        return redirect(url_for('login'))
    else:
        if current_user.has_role('admin'):
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('experiment.list_all'))

# @app.route('/bower_components/<path:path>')
# def serve_bower_components(path):
#     import pdb
#     pdb.set_trace()
#     return send_from_directory('static/bower_components/', path)
