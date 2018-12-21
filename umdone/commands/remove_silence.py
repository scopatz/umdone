"""Remove silence command"""
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio
from umdone.commands import audio_io


@lazyobject
def PARSER():
    parser = ArgumentParser("remove-silence")
    parser.add_argument(
        "path", help="path to local file or URL.", nargs="?", default=None
    )
    parser.add_argument(
        "-t",
        "--reduce-to",
        dest="reduce_to",
        type=float,
        default=0.0,
        help="length of time (in sec) to reduce silences to",
    )
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """removes silence from an audio file"""
    ns = PARSER.parse_args(args)
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print_color("{YELLOW}Removing silences{NO_COLOR}", file=stderr, flush=True)
    print("  - audio in:", audio_in, file=stderr, flush=True)
    print("  - reducing silence to:", ns.reduce_to, file=stderr, flush=True)
    import umdone.basic_filters

    audio_out = umdone.basic_filters.remove_silence(audio_in, reduce_to=ns.reduce_to)
    print("  - audio out:", audio_out, file=stderr, flush=True)
    return audio_out
