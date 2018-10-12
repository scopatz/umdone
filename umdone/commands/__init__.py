"""Commands subpackage for umdone"""
from ast import literal_eval
import os
import sys
import glob
import time
import builtins
import functools
import importlib
from threading import RLock
from contextlib import contextmanager

from xonsh.proc import QueueReader, NonBlockingFDReader

from umdone.sound import Audio


AUDIO_PIPELINE_STASH = {}
LOCK = RLock()


def _stash_get_audio(stdin, stderr, spec):
    if stdin is None:
        return None
    #for line in stdin:
    stdin = NonBlockingFDReader(stdin.fileno())
    while not stdin.closed:
        line = stdin.readline().decode().strip()
        stderr.write('line: ' + repr(line) + ' ' + repr(stdin) + '\n')
        if not line:
            time.sleep(1e-3)
            continue
        if line.startswith('{"UMDONE_AUDIO_PIPELINE_STASH_ID":'):
            aid = literal_eval(line)["UMDONE_AUDIO_PIPELINE_STASH_ID"]
            audio = AUDIO_PIPELINE_STASH[aid]
            break
    else:
        audio = None
        print('no audio in pipeline', file=stderr)
        print('stdin closed:', stdin.closed, file=stderr)
        print("stash:", AUDIO_PIPELINE_STASH, file=stderr)
    if spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
    return audio


def _stash_get_audio(stdin, stderr, spec):
    global NEXT_IN_PIPELINE
    while NEXT_IN_PIPELINE is None:
        time.sleep(1e-3)
    aid = NEXT_IN_PIPELINE
    audio = AUDIO_PIPELINE_STASH[aid]
    NEXT_IN_PIPELINE = None
    if spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
    return audio


def _stash_get_audio(stdin, stderr, spec):
    while len(AUDIO_PIPELINE_STASH) < spec.pipeline_index:
        time.sleep(1e-3)
    audio = AUDIO_PIPELINE_STASH[spec.pipeline_index]
    if spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
    return audio


def audio_in(f):
    """Decorated a main pipeline command function and declares that
    the command accepts audio input
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
      #with LOCK:
        audio = _stash_get_audio(stdin, stderr, spec)
        return f(audio, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
    #dec.__xonsh_threadable__ = False
    return dec


def _stash_set_audio(audio, stdout, stderr, spec):
    if not isinstance(audio, Audio) or spec.last_in_pipeline:
        print('failed to set stash: ', audio, file=stderr)
        AUDIO_PIPELINE_STASH.clear()
        return 0 if isinstance(audio, Audio) else audio
    aid = audio.hash_str()
    AUDIO_PIPELINE_STASH[aid] = audio
    time.sleep(5e-3)
    line = '\n{"UMDONE_AUDIO_PIPELINE_STASH_ID":' + repr(aid) + '}'
    print(line, file=stdout, flush=True)
    print(line, file=stderr, flush=True)
    return 0


def _stash_set_audio(audio, stdout, stderr, spec):
    global NEXT_IN_PIPELINE
    NEXT_IN_PIPELINE = aid = audio.hash_str()
    AUDIO_PIPELINE_STASH[aid] = audio
    return 0

def _stash_set_audio(audio, stdout, stderr, spec):
    AUDIO_PIPELINE_STASH[spec.pipeline_index+1] = audio
    return 0


def audio_out(f):
    """Decorates a main pipeline command function and declares that
    the command returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
      #with LOCK:
        audio = f(args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(audio, stdout, stderr, spec)
        return rtn
    #dec.__xonsh_threadable__ = False
    return dec


def audio_io(f):
    """Decorates a main pipeline command function and declares that
    the command both accepts and returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
      #with LOCK:
        ain = _stash_get_audio(stdin, stderr, spec)
        aout = f(ain, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(aout, stdout, stderr, spec)
        return rtn
    #dec.__xonsh_threadable__ = False
    return dec


COMMANDS = tuple([os.path.basename(_)[:-3] for _ in
                  glob.iglob(os.path.join(os.path.dirname(__file__), '*.py'))
                  if not os.path.basename(_).startswith('_')])


def load_alias(name):
    """Loads an alias for a command name."""
    mod = importlib.import_module('umdone.commands.' + name)
    main = getattr(mod, 'main')
    builtins.aliases[name] = main
    builtins.aliases[name.replace('_', '-')] = main


def load_aliases():
    """Loads all command name aliases"""
    for name in COMMANDS:
        load_alias(name)


def unload_aliases():
    """Removes all command name aliases"""
    for name in COMMANDS:
        del builtins.aliases[name]
        alt_name = name.replace('_', '-')
        if alt_name in builtins.aliases:
            del builtins.aliases[alt_name]


@contextmanager
def swap_aliases():
    """Context manager for swapping in/out command aliases."""
    # store existing aliases, so we can restore them.
    existing = {}
    for name in COMMANDS:
        if name in builtins.aliases:
            existing[name] = builtins.aliases[name]
        alt_name = name.replace('_', '-')
        if alt_name in builtins.aliases:
            existing[alt_name] = builtins.aliases[alt_name]
    load_aliases()
    yield
    unload_aliases()
    builtins.aliases.update(existing)
