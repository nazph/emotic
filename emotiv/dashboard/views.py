import flask
import os
import pdb
import boto
import io
import csv
from datetime import datetime, timedelta
from pydash import py_ as _
from funcy import flatten, merge
from boto.s3.key import Key
from emotiv.app import app
from emotiv.dashboard import dashboard
from emotiv.experiment.views import builder_validation
from emotiv.helpers import templated, login_or_token_required
from emotiv.models import Experiment, Phase, PhaseElement, PhaseElementAnswerUser, PhaseElementAnswer
from emotiv.experiment.views import serialize_phase_element, download_csv

@dashboard.route('/mock_data/<media>')
def mock_data(media):
    """Return mock emotion data."""
    return flask.send_file('dashboard/' + media)


@dashboard.route('/<int:experiment_id>')
@templated('result_dashboard.html')
@login_or_token_required
@builder_validation
def for_experiment(experiment_id=None):
    """Render the dashboard for an experiment."""
    experiment = Experiment.query.get_or_404(experiment_id)
    answers = PhaseElementAnswerUser.query.\
        join(PhaseElementAnswerUser.phase).\
        filter(Phase.experiment_id == experiment_id).\
        all()

    def unique(things):
      seen = set()
      def unseen(thing):
        r = thing.id not in seen
        seen.add(thing.id)
        return r
      return (thing for thing in things if unseen(thing))

    #TODO: Link up correct CSV data from EEG readings of the emotiv headset
    media = []
    for phase in experiment.phases:
        media.extend([{
            'key': idx - 1,
            'file_name': element.material.file_name,
            'content_type': element.material.content_type,
            'name': element.material.name,
            'eventMarkers': [],
            'data': [],
            'file': element.recording_data[-1].file_name if len(element.recording_data) > 0 else [],
            'duration_ms': element.duration_ms,
            'gaze_data': serialize_gaze_data_from_element(element)
        } for idx, element in enumerate(filter(lambda x: x.material != None, phase.elements), 1)])

    # TODO: Average data
    users = unique((a.user for a in answers))
    users_result = []

    collected_ids = [a.id for a in experiment.attributes_collected]
    for u in users:
      attrs = [{
        'id': a.attribute.id,
        'value': a.value,
        'user_id': u.id,
      } for a in u.attributes if a.attribute.id in collected_ids]
      responses = [{
        'id': a.phase_element_id,
        'value': a.value if a.value is not None else a.phase_element_answer.value,
        'user_id': u.id,
      } for a in answers if a.user_id == u.id]
      users_result.append({
        'attributes': attrs,
        'responses': responses,
      })

    return {
        'dashboard_props': {
            'experimentName': experiment.name,
            'users': users_result,
            'media': media,
            'attributes': [{
              'id': a.id,
              'name': a.name,
              'input_type': a.input_type,
            } for a in experiment.attributes_collected],
            'questions': [{
              'id': e.id,
              'name': e.text,
              'input_type': e.input_type,
              'position': e.position,
              'phase_element': serialize_phase_element(e)
            } for e in unique(a.phase_element for a in answers)]
        }
    }

def iso_to_epoch(time):
    utc_dt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%f')
    # convert UTC datetime to seconds since the Epoch
    timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds()
    return round(timestamp, 1)


def csvs_to_array(filenames):
    """
    takes filename array, reads from s3, and returns data
    input: []
    output: [
        {
            'timestamp': String,
            'gazeDataX': String,
            'gazeDataY': String
        }
    ]
    """
    total_gaze_data = []
    for data in filenames:
        file = read_csv(data['filename'])
        user_gaze_data = csv.DictReader(io.StringIO(file.decode('utf-8')))
        for row in user_gaze_data:
            total_gaze_data.append(row)
    return total_gaze_data

def read_csv(filename):
    # Makes use of AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables
    conn = boto.connect_s3()
    bucket = conn.get_bucket(app.config['S3_BUCKET_NAME'])
    k = Key(bucket)
    URL = 'http:/emotiv-omniscience-dev.s3.amazonaws.com/'
    k.key = filename[len(URL) + 1:]
    return k.get_contents_as_string()

def serialize_gaze_data_from_element(element):
    """
        Downloads the gaze data from S3 and converts to usable data for heatmap
        Note - this can take several seconds. We can consider doing it async if necessary
        The data will be grouped by one-second intervals - any more granularity and the heat map can't re render fast enough
        The media players also update at non deterministic intervals
        output:
        {
            data: {
                timestamp: [{x: 1, y: 1, count: 5}, ...]
                }
            min_count: 0,
            max_count: ?
        }
    """
    duration_data = PhaseElement.query.filter_by(id=element.id).first().duration_data
    data = flatten([{'files': [g.file_name for g in d.recording_data.gaze_data], 'user_id': d.recording_data.user.id} for d in duration_data])
    gaze_data_files = []
    for d in data:
        gaze_data_files.append([{'filename': f, 'user_id': d['user_id']} for f in d['files']])
    filenames = flatten(gaze_data_files)
    total_gaze_data = csvs_to_array(filenames)

    # divide the data by time stamp
    by_timestamp = {}
    count = {}
    max_count = 0
    # find starting time
    if not _.is_empty(total_gaze_data):
        start_time = _(total_gaze_data).pluck('timestamp').uniq().map(lambda t: iso_to_epoch(t)).min().value()
        # group into unique timestamps
        for data in total_gaze_data:
            time = int(iso_to_epoch(data['timestamp']) - start_time)
            # reduce level of specificity to get more meaningful groupings
            round_x = round(float(data['gazeDataX']) * 181, 1)
            round_y = round(float(data['gazeDataY']) * 227, 1)
            count_key = str(round_x) + str(round_y)
            if by_timestamp.get(time, None) is None:
                by_timestamp[time] = []

            if count.get(count_key, None) is None:
                count[count_key] = 0

            count[count_key] += 1
            if count[count_key] > max_count:
                max_count = count[count_key]
            by_timestamp[time].append({'x': round_x, 'y': round_y, 'value': count[count_key]})

        # create a prettier array to send back to the front end
        serialized_data = {}
        serialized_data['data'] = by_timestamp
        serialized_data['max'] = max_count
        serialized_data['min'] = 0
        return serialized_data
    return []
