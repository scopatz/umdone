"""Commands subpackage for umdone"""
from ast import literal_eval
import builtins
import functools

from umdone.sound import Audio


AUDIO_PIPELINE_STASH = {}


def _stash_get_audio(stdin, spec):
    if stdin is None:
        return None
    for line in stdin:
        if line.startswith('{"UMDONE_AUDIO_PIPELINE_STASH_ID":'):
            aid = literal_eval(line)["UMDONE_AUDIO_PIPELINE_STASH_ID"]
            audio = AUDIO_PIPELINE_STASH[aid]
            break
    else:
        audio = None
    if spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
    return audio


def audio_in(f):
    """Decorated a main pipeline command function and declares that
    the command accepts audio input
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None):
        audio = _stash_get_audio(stdin, spec)
        return f(audio, args, stdin=stdin, stdout=stdin, stderr=stderr, spec=spec)
    return dec


def _stash_set_audio(audio, stdout, spec):
    if not isinstance(audio, Audio) or spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
        return 0 if isinstance(audio, Audio) else audio
    aid = id(a)
    AUDIO_PIPELINE_STASH[aid] = a
    print('\n{"UMDONE_AUDIO_PIPELINE_STASH_ID":' + str(aid) + '}', file=stdout)
    return 0


def audio_out(f):
    """Decorates a main pipeline command function and declares that
    the command returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None):
        audio = f(args, stdin=stdin, stdout=stdin, stderr=stderr, spec=spec)
        return _stash_set_audio(audio, stdout, spec)
    return dec


def audio_io(f):
    """Decorates a main pipeline command function and declares that
    the command both accepts and returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None):
        ain = _stash_get_audio(stdin, spec)
        aout = f(ain, args, stdin=stdin, stdout=stdin, stderr=stderr, spec=spec)
        return _stash_set_audio(aout, stdout, spec)
    return dec
