"""Load pipeline command"""
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_io


@lazyobject
def PARSER():
    parser = ArgumentParser('load')
    parser.add_argument('path',
                        help='path to local file or URL.',
                        nargs="?",
                        default=None,)
    parser.add_argument('--no-norm', '--dont-norm', dest='norm',
                        action='store_false', default=True,
                        help="don't normalize output."
                        )
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Loads an audio file"""
    ns = PARSER.parse_args(args)
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print_color('{YELLOW}Reducing noise{NO_COLOR}', file=stderr, flush=True)
    print('  - audio in:', audio_in, file=stderr, flush=True)
    import umdone.noise_reduction
    audio_out = umdone.noise_reduction.reduce_noise(audio_in, norm=ns.norm)
    print('  - audio out:', audio_out, file=stderr, flush=True)
    return audio_out
