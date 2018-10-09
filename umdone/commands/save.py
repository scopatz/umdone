"""Save pipeline command"""
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_in


@lazyobject
def PARSER():
    parser = ArgumentParser('save')
    parser.add_argument('infile', help='path to local file or URL.',
                        nargs="?",
                        default=None)
    parser.add_argument('outfile', help='path to local file or URL.',
                        default=None)
    return parser


@audio_in
def main(ain, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Saves an audio file"""
    ns = PARSER.parse_args(args)
    print_color('Saving audio to {GREEN}' + ns.outfile + '{NO_COLOR}',
                file=sys.stderr, flush=True)
    if ain is None and ns.infile is not None:
        ain = Audio(ns.infile)
    ain.save(ns.outfile)
    return 0
