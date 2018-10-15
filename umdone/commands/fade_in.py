"""Fade-in pipeline command"""
import sys
from argparse import ArgumentParser

import numpy as np

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_io


@lazyobject
def PARSER():
    parser = ArgumentParser('fade-in')
    parser.add_argument('path',
                        help='path to local file or URL.',
                        nargs="?",
                        default=None,)
    parser.add_argument('-t', '--time', dest='t',
                        type=float, default=3.0,
                        help="length of time (in sec) to fade in over"
                        )
    parser.add_argument('-b', '--base', dest='base',
                        type=float, default=10.0,
                        help="base of cross-fade power"
                        )
    parser.add_argument('-p', '--prefix', dest='prefix',
                        default=None,
                        help="path to local file of URL to prefix with, and fade in from"
                        )
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Fades in this audio stream"""
    ns = PARSER.parse_args(args)
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print_color('{YELLOW}Fading in{NO_COLOR}', file=stderr, flush=True)
    print('  - audio in:', audio_in, file=stderr, flush=True)
    if ns.prefix is None:
        prefix = Audio(np.zeros(int(ns.t*audio_in.sr)), audio_in.sr)
    else:
        print(f'  - fading in {ns.prefix}', file=stderr, flush=True)
        prefix = Audio(ns.prefix)
    print(f'  - fading in over {ns.t} seconds', file=stderr, flush=True)
    import umdone.basic_filters
    audio_out = umdone.basic_filters.cross_fade(prefix, audio_in, t=ns.t, base=ns.base)
    print('  - audio out:', audio_out, file=stderr, flush=True)
    return audio_out
