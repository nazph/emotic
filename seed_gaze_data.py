import os
import datetime
import iso8601
from uuid import uuid4 as uuid
from random import random
import boto
from dateutil import tz
from boto.s3.key import Key
from emotiv.database import db
from emotiv.app import app
from emotiv.models import ExperimentGazeData, User, ExperimentRecordingData, Experiment, PhaseElement, PhaseElementDurationData
# Seed gaze data to expedite development of heat map
def gaze_data_to_csv(gaze_data):
    return "\n".join(map(lambda x: "{},{},{}".format(x['gazeDataX'], x['gazeDataY'], x['timestamp']), gaze_data))

def upload_csv(filename, data):
    # Makes use of AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables
    conn = boto.connect_s3()
    bucket = conn.get_bucket(app.config['S3_BUCKET_NAME'])
    k = Key(bucket)
    k.key = filename
    k.set_contents_from_string(data)
    return filename
# session_obj = ExperimentRecordingData.query.get_or_404(session_id)
# gaze_data = request.json['gazeData']

def upload_gaze_tracking_data(gaze_data, user_id):
    """
    Method for testing only. Adds a new set of gaze_data for an image object

    Parameters:
        session_id: The session_id of the user who is viewing the experiment
        gazeData: array of gaze data information
        durationData: array of timestamps for when a particular phase element was being viewed

    Returns:
        success: boolean indicating whether the gaze data was successfully saved
    """
    current_dir_gaze_data = os.path.join(os.getcwd(), "tmp_gaze_data")
    if not os.path.exists(current_dir_gaze_data):
        os.mkdir(current_dir_gaze_data)

    csv_gaze_data = gaze_data_to_csv(gaze_data)
    file_name = "gaze_data_{}.csv".format(uuid())
    print('file_name is {}'.format(file_name))
    csv_gaze_data = 'gazeDataX,gazeDataY,timestamp\n' + csv_gaze_data
    print('data is is \n{}'.format(csv_gaze_data))

    with open(os.path.join(current_dir_gaze_data, file_name), 'w') as f:
        f.write(csv_gaze_data)

    session_obj = ExperimentRecordingData(
        user=User.query.filter_by(id=user_id).first(),
        experiment=Experiment.query.filter_by(id=1456).first(), # has a lot of media associated with it
    )
    start_time = datetime.datetime.fromtimestamp(1472075283.940)
    duration = {
        'startTimestamp': start_time.isoformat(),
        'endTimestamp': (start_time + datetime.timedelta(0,4)).isoformat()
    }
    new_duration = PhaseElementDurationData(
        phase_element=PhaseElement.query.filter_by(id=1403).first(), #image on experiment 1456
        recording_data=session_obj,
        view_start=iso8601.parse_date(duration['startTimestamp']).astimezone(tz.gettz('UTC')),
        view_end=iso8601.parse_date(duration['endTimestamp']).astimezone(tz.gettz('UTC')),
    )

    upload_csv(file_name, csv_gaze_data)
    new_gaze_data = ExperimentGazeData(
        recording_data=session_obj,
        file_name="http://{}.s3.amazonaws.com/{}".format(app.config['S3_BUCKET_NAME'], file_name),
        name=file_name
    )
    db.session.add(session_obj)
    db.session.add(new_duration)
    db.session.add(new_gaze_data)
    db.session.commit()
    return True

now = datetime.datetime.fromtimestamp(1472075283.940)
# print(gaze_data)

for i in range(1, 6):
    gaze_data = [{'gazeDataX': random(), 'gazeDataY': random(), 'timestamp': (now + datetime.timedelta(0,d)).isoformat()} for d in [x / 10.0 for x in range(0, 41)]]
    upload_gaze_tracking_data(gaze_data, i)
