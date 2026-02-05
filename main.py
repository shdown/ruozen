#!/usr/bin/env python3

# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

import os
import re
import json
import threading

import flask

import uid_utils
import recorder
import settings
import commands
import commands_db


global_rec_model = None
global_rec_settings = None


ERRORS = [
    (0, 'E_OK', ''),
    (1001, 'E_INVALID_UID', 'invalid uid'),
    (1002, 'E_CAS_FAILED', 'compare-and-swap failed'),
    (1003, 'E_REC_ALREADY', 'this recording is already in flight'),
    (1004, 'E_REC_NOT_FOUND', 'recording with this uid was not found'),
    (1005, 'E_REC_TOO_MANY', 'too many recordings in flight'),
    (1006, 'E_COMMAND_NOT_FOUND', 'command not found'),
    (1007, 'E_NO_TEXT', 'no text passed'),
    (1008, 'E_INTERNAL_ERROR', 'internal error'),
]


def mkresult(err_token='E_OK', other_fields=None):
    other_fields = other_fields or {}
    for cur_code, cur_token, cur_msg in ERRORS:
        if cur_token == err_token:
            return {
                'ok': (err_token == 'E_OK'),
                'error_code': cur_code,
                'error_msg': cur_msg,
                **other_fields,
            }
    raise ValueError(f'unknown err_token "{err_token}"')


def result_from_ex(ex):
    return {
        'ok': False,
        'error_code': -1,
        'error_msg': str(ex),
    }


FLASK_RUN_ARGS = {
    **settings.FLASK_RUN_ARGS,
    'use_reloader': False,
}


app = flask.Flask(__name__)


pending_uid = uid_utils.empty()


recordings = {}


@app.route('/')
@app.route('/index.html')
def handler_for_index_page():
    return app.send_static_file('index.html')


@app.route('/api/uid/new', methods=['POST'])
def handler_for_uid_new():
    return mkresult(other_fields={
        'uid': uid_utils.gen_random(),
    })


@app.route('/api/uid/pending/get', methods=['POST'])
def handler_for_uid_pending_get():
    return mkresult(other_fields={
        'uid': pending_uid,
    })


@app.route('/api/uid/pending/cas', methods=['POST'])
def handler_for_uid_pending_cas():
    old_uid = flask.request.form.get('old_uid', '')
    new_uid = flask.request.form.get('new_uid', '')

    if not uid_utils.is_valid_uid(old_uid, accept_empty=True):
        return mkresult('E_INVALID_UID')

    if not uid_utils.is_valid_uid(new_uid, accept_empty=True):
        return mkresult('E_INVALID_UID')

    global pending_uid
    if pending_uid == old_uid:
        pending_uid = new_uid
        return mkresult()
    else:
        return mkresult('E_CAS_FAILED')


@app.route('/api/uid/pending/set', methods=['POST'])
def handler_for_uid_pending_set():
    new_uid = flask.request.form.get('new_uid', '')

    if not uid_utils.is_valid_uid(new_uid, accept_empty=True):
        return mkresult('E_INVALID_UID')

    global pending_uid
    pending_uid = new_uid
    return mkresult()


class InFlightRecording:
    def __init__(self, thr):
        self.thr = thr
        self.result = (False, None)

    def set_result_ok(self, text):
        self.result = (True, text)

    def set_result_error(self, ex):
        self.result = (False, ex)


def recorder_thread(rec, uid):
    result = ''

    def callback(json_str, kind):
        data = json.loads(json_str)
        if 'text' in data:
            nonlocal result
            result = data['text']
            return False
        return True

    try:
        rec.realize()
        with recorder.record(rec):
            rec.run_loop(callback)
    except BaseException as ex:
        recordings[uid].set_result_error(ex)
        return

    recordings[uid].set_result_ok(result)


@app.route('/api/recording/new', methods=['POST'])
def handler_for_recoding_new():
    uid = flask.request.form.get('uid', '')

    if not uid_utils.is_valid_uid(uid):
        return mkresult('E_INVALID_UID')

    if uid in recordings:
        return mkresult('E_REC_ALREADY')

    if len(recordings) == settings.MAX_RECORDINGS_IN_FLIGHT:
        return mkresult('E_REC_TOO_MANY')

    rec = recorder.Recorder(
        rec_model=global_rec_model,
        rec_settings=global_rec_settings)

    thr = threading.Thread(target=recorder_thread, args=(rec, uid))
    recordings[uid] = InFlightRecording(thr)
    thr.start()

    return mkresult()


@app.route('/api/recording/wait', methods=['POST'])
def handler_for_recording_wait():
    uid = flask.request.form.get('uid', '')

    if not uid_utils.is_valid_uid(uid):
        return mkresult('E_INVALID_UID')

    recording = recordings.get(uid)
    if recording is None:
        return mkresult('E_REC_NOT_FOUND')

    recording.thr.join()

    is_ok, res = recording.result

    if is_ok:
        return mkresult(other_fields={
            'text': res.strip(),
        })
    else:
        if res is None:
            return mkresult('E_INTERNAL_ERROR')
        else:
            return result_from_ex(res)


@app.route('/api/command', methods=['POST'])
def handler_for_command():
    text = flask.request.form.get('text', '')
    text = text.strip()

    if not text:
        return mkresult('E_NO_TEXT')

    found, result = commands.find_and_exec_command(text)

    return mkresult(other_fields={
        'found': found,
        'result': result,
    })


@app.route('/api/ping')
def handler_for_ping():
    return mkresult()


def main():
    global global_rec_model
    global_rec_model = recorder.RecorderModel(settings.MODEL_PATH)

    global global_rec_settings
    global_rec_settings = recorder.RecorderSettings(
        sample_rate=settings.SAMPLE_RATE,
        ffmpeg=settings.FFMPEG,
        ffmpeg_input_args=settings.FFMPEG_INPUT_ARGS,
        ffmpeg_quiet=settings.FFMPEG_QUIET)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app.run(**FLASK_RUN_ARGS)


if __name__ == '__main__':
    main()
