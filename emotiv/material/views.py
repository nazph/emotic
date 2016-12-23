import json

from flask import abort, request, jsonify
from flask.ext.security import current_user
import requests

from emotiv.database import db
from emotiv.helpers import login_or_token_required
from emotiv.models import Material
from emotiv.material import material


@material.route('/record_filestack_upload', methods=['POST'])
@login_or_token_required
def record_filestack_upload():
  """Record the metadata for a file in filestack.

  Our media files (images, video, and audio for experiments) are hosted on Filestack,
  but we also store metadata about each file (most importantly, the organization that
  uploaded the file) in our application database. This endpoint stores that metadata
  given the URL of a file in Filstack.

  So the flow for uploading new files is:
      1. Use Filestack's API to upload the file and get a URL back.
      2. Pass that URL to this endpoint.

  Parameters (json fields in POST body):
      content_type: 'a', 'i', or 'v' for audio, image, or video, respectively
      url: URL of file from Filestack API

  Returns:
      JSON blob of the new Material object in our application database
  """
  new_material = _record_filestack_upload(
      request.json['content_type'], request.json['url'])
  return jsonify(as_dict(new_material))


def _record_filestack_upload(content_type, url):
    resp = requests.get(url + '/metadata')
    if resp.status_code != requests.codes.ok:
        print 'Failed to get metadata from Filestack for {}. Response from Filestack: {}'.format(url, resp.text)
        return None
    data = json.loads(resp.text)
    new_material = Material(organization=current_user.organization,
                            content_type=content_type,
                            file_name=url,
                            name=data['filename'])
    db.session.add(new_material)
    db.session.commit()
    return new_material


@material.route('/available/<string:content_type>')
@login_or_token_required
def available_media(content_type):
    """Return the media uploaded by the current user's organization.

    Parameters (url string):
        content_type: the type of media to return - 'a', 'i', or 'v' for audio, image, or video, respectively

    Returns (json blob):
        media: list of json-serialized Material objects
    """
    media = Material.query.filter(Material.content_type == content_type). \
        filter(Material.organization_id == current_user.organization.id).all()
    # Note that Flask 0.10 does not support top-level lists in jsonify (Flask 0.11 does),
    # so we wrap the media list in an object.
    # https://github.com/pallets/flask/commit/431db2874b242316051963d9bc4d5653b3647acc
    # https://stackoverflow.com/questions/7907596/json-dumps-vs-flask-jsonify
    return jsonify({'media': [as_dict(m) for m in media]})


# http://stackoverflow.com/a/11884806/3072514
def as_dict(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _get_material(material_id, do_404=False):
    m = Material.query.filter(Material.organization_id == current_user.organization_id).\
        filter(Material.id == material_id).first()
    return as_dict(m) if m else {}


@material.route('/filename')
@login_or_token_required
def get_material():
    """Get material metadata by id.

    See comment above on record_filestack_upload about how we track media.

    Parameters (url query):
        id: ID of Material object

    Returns:
        JSON-serialized Material object
    """
    m = _get_material(request.args.get('id', ''))
    if not m:
      abort(404)
    return jsonify(m)
