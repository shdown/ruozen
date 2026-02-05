# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

import vosk
import subprocess
import contextlib


_READ_SIZE = 4000


class RecorderError(BaseException):
    pass


def _error_wrap(ex):
    return RecorderError(f'{type(ex).__name__}: {str(ex)}')


class RecorderModel:
    def __init__(self, model_path):
        self.model = vosk.Model(model_path=model_path)


class RecorderSettings:
    def __init__(self, sample_rate, ffmpeg, ffmpeg_input_args, ffmpeg_quiet):
        self.sample_rate = sample_rate
        self.ffmpeg = ffmpeg
        self.ffmpeg_input_args = ffmpeg_input_args
        self.ffmpeg_quiet = ffmpeg_quiet


class Recorder:
    def __init__(self, rec_model, rec_settings):
        self.rec_model = rec_model
        self.rec_settings = rec_settings
        self.recognizer = None
        self.proc = None
        self.state = 'inited'

    def realize(self):
        assert self.state == 'inited'

        self.recognizer = vosk.KaldiRecognizer(
            self.rec_model.model,
            self.rec_settings.sample_rate)

        self.state = 'realized'

    def start(self):
        assert self.state == 'realized'

        quiet_args = []
        if self.rec_settings.ffmpeg_quiet:
            quiet_args = ['-loglevel', 'quiet']

        argv = [
            self.rec_settings.ffmpeg,
            *quiet_args,
            *self.rec_settings.ffmpeg_input_args,
            '-ar', str(self.rec_settings.sample_rate),
            '-ac', '1',
            '-f', 's16le',
            '-',
        ]

        try:
            self.proc = subprocess.Popen(argv, stdout=subprocess.PIPE)
        except subprocess.SubprocessError as ex:
            raise _error_wrap(ex)

        self.state = 'started'

    def run_loop(self, callback):
        assert self.state == 'started'

        r = self.recognizer
        is_eof = False
        while True:
            data = self.proc.stdout.read(_READ_SIZE)
            if not data:
                is_eof = True
                break
            if r.AcceptWaveform(data):
                should_continue = callback(r.Result(), 'whole')
            else:
                should_continue = callback(r.PartialResult(), 'partial')

            if not should_continue:
                break

        if is_eof:
            callback(r.FinalResult(), 'final')

        self.state = 'waiting_to_be_done'

    def done(self):
        if self.proc is not None:
            self.proc.kill()
            self.proc.wait()
            self.proc = None
        self.state = 'done'


@contextlib.contextmanager
def record(recorder):
    recorder.start()
    try:
        yield
    finally:
        recorder.done()
