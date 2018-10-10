"""Commands subpackage for umdone"""
from ast import literal_eval
import os
import sys
import glob
import time
import builtins
import functools
import importlib
from contextlib import contextmanager

from xonsh.proc import QueueReader, NonBlockingFDReader

from umdone.sound import Audio


AUDIO_PIPELINE_STASH = {}


def _stash_get_audio(stdin, spec):
    if stdin is None:
        return None
    #for line in stdin.readlines():
    for line in stdin:
        #line = stdin.readline().decode()
        #if not line.strip():
        #    time.sleep(1e-3)
        #    continue
        print('line: ', line, stdin, file=sys.stderr)

        if line.startswith('{"UMDONE_AUDIO_PIPELINE_STASH_ID":'):
            aid = literal_eval(line)["UMDONE_AUDIO_PIPELINE_STASH_ID"]
            audio = AUDIO_PIPELINE_STASH[aid]
            break
    else:
        audio = None
        print('no audio in pipeline', file=sys.stderr)
        print("stash:", AUDIO_PIPELINE_STASH, file=sys.stderr)
    if spec.last_in_pipeline:
        AUDIO_PIPELINE_STASH.clear()
    return audio


def audio_in(f):
    """Decorated a main pipeline command function and declares that
    the command accepts audio input
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        audio = _stash_get_audio(stdin, spec)
        return f(audio, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
    return dec


def _stash_set_audio(audio, stdout, spec):
    if not isinstance(audio, Audio) or spec.last_in_pipeline:
        #AUDIO_PIPELINE_STASH.clear()
        return 0 if isinstance(audio, Audio) else audio
    aid = audio.hash_str()
    AUDIO_PIPELINE_STASH[aid] = audio
    print(spec, stdout, file=sys.stderr)
    print('\n{"UMDONE_AUDIO_PIPELINE_STASH_ID":' + repr(aid) + '}', file=stdout,
          flush=True)
    return 0


def audio_out(f):
    """Decorates a main pipeline command function and declares that
    the command returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        audio = f(args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(audio, stdout, spec)
        return rtn
    return dec


def audio_io(f):
    """Decorates a main pipeline command function and declares that
    the command both accepts and returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        ain = _stash_get_audio(stdin, spec)
        aout = f(ain, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(aout, stdout, spec)
        return rtn
        #return _stash_set_audio(aout, stdout, spec)
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
