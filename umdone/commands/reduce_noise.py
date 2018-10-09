"""Load pipeline command"""
from argparse import ArgumentParser

from lazyasd import lazyobject

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
    from umdone.noise_reduction import reduce_noise
    audio_out = reduce_noise(audio_in, norm=ns.norm)
    return audio_out
