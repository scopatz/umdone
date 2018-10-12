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
from queue import LifoQueue
from contextlib import contextmanager

from xonsh.proc import QueueReader, NonBlockingFDReader

from umdone.sound import Audio


NEXT_IN_PIPELINE = None


def _stash_get_audio(stdin, stderr, spec):
    global NEXT_IN_PIPELINE
    audio, NEXT_IN_PIPELINE = NEXT_IN_PIPELINE, None
    return audio


def audio_in(f):
    """Decorated a main pipeline command function and declares that
    the command accepts audio input
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        audio = _stash_get_audio(stdin, stderr, spec)
        return f(audio, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
    return dec


def _stash_set_audio(audio, stdout, stderr, spec):
    global NEXT_IN_PIPELINE
    NEXT_IN_PIPELINE = audio
    return 0


def audio_out(f):
    """Decorates a main pipeline command function and declares that
    the command returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        audio = f(args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(audio, stdout, stderr, spec)
        return rtn
    return dec


def audio_io(f):
    """Decorates a main pipeline command function and declares that
    the command both accepts and returns an audio file.
    """
    @functools.wraps(f)
    def dec(args, stdin=None, stdout=None, stderr=None, spec=None, stack=None):
        ain = _stash_get_audio(stdin, stderr, spec)
        aout = f(ain, args, stdin=stdin, stdout=stdout, stderr=stderr, spec=spec)
        rtn = _stash_set_audio(aout, stdout, stderr, spec)
        return rtn
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
