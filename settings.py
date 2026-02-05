PORT = 8999


FLASK_RUN_ARGS = {
    'host':  '127.0.0.1',
    'port':  PORT,
    'debug': True,
}


MAX_RECORDINGS_IN_FLIGHT = 5


BROWSER = 'firefox'


FFMPEG = 'ffmpeg'
FFMPEG_INPUT_ARGS = '-f pulse -i default'.split()
FFMPEG_QUIET = False


MODEL_PATH = '/home/v/repo/vosk-app/vosk-model-small-ru-0.22/'


SAMPLE_RATE = 16000
