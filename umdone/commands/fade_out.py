"""Fade-out pipeline command"""
import sys
from argparse import ArgumentParser

import numpy as np

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_io


@lazyobject
def PARSER():
    parser = ArgumentParser('fade-out')
    parser.add_argument('path',
                        help='path to local file or URL.',
                        nargs="?",
                        default=None,)
    parser.add_argument('-t', '--time', dest='t',
                        type=float, default=3.0,
                        help="length of time (in sec) to fade out over"
                        )
    parser.add_argument('-b', '--base', dest='base',
                        type=float, default=10.0,
                        help="base of cross-fade power"
                        )
    parser.add_argument('-p', '--postfix', dest='postfix',
                        default=None,
                        help="path to local file of URL to postfix with, and fade out to"
                        )
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Fades out this audio stream"""
    ns = PARSER.parse_args(args)
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print_color('{YELLOW}Fading out{NO_COLOR}', file=stderr, flush=True)
    print('  - audio in:', audio_in, file=stderr, flush=True)
    if ns.postfix is None:
        postfix = Audio(np.zeros(int(ns.t*audio_in.sr)), audio_in.sr)
    else:
        print(f'  - fading out to {ns.postfix}', file=stderr, flush=True)
        postfix = Audio(ns.postfix)
    print(f'  - fading out over {ns.t} seconds', file=stderr, flush=True)
    import umdone.basic_filters
    audio_out = umdone.basic_filters.cross_fade(audio_in, postfix, t=ns.t, base=ns.base)
    print('  - audio out:', audio_out, file=stderr, flush=True)
    return audio_out
