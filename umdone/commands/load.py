"""Load pipeline command"""
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_out


@lazyobject
def PARSER():
    parser = ArgumentParser('load')
    parser.add_argument('path', help='path to local file or URL.')
    return parser


@audio_out
def main(args, stdin=None, stdout=None, stderr=None, spec=None):
    """Loads an audio file"""
    ns = PARSER.parse_args(args)
    print_color('Loading {GREEN}' + ns.path + '{NO_COLOR}',
                file=stderr)
    return Audio(ns.path)
