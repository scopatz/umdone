"""Remove umms pipeline command"""
import os
import sys
import glob
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone import cli
from umdone.sound import Audio, CLIPS_CACHE_DIR
from umdone.commands import audio_io



@lazyobject
def PARSER():
    parser = ArgumentParser("remove-clips")
    parser.add_argument(
        "path", help="path to local file or URL.", nargs="?", default=None
    )
    parser.add_argument(
        "--dbfile",
        dest="dbfile",
        default=None,
        help="training database file to load",
    )
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """removes clips from an audio file"""
    print_color("{YELLOW}Removing clips{NO_COLOR}", file=stderr, flush=True)
    ns = PARSER.parse_args(args)
    # ensure audio
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print("  - audio in:", audio_in, file=stderr, flush=True)
    # get and verify dbfiles
    if ns.dbfile is None:
        prefix = (
            audio_in.hash()
            if ns.path is None
            else os.path.splitext(os.path.basename(ns.path))[0]
        )
        ns.dbfile = os.path.join(CLIPS_CACHE_DIR, prefix + "-clips.h5")
    if not ns.dbfile:
        print_color(
            "{RED}No clip database file found!{NO_COLOR}", file=stderr, flush=True
        )
        return 1
    print(
        "  - training database file: " + ns.dbfile,
        file=stderr,
        flush=True,
    )
    from umdone.basic_filters import remove_marked_clips
    audio_out = remove_marked_clips(audio_in, dbfile=ns.dbfile)
    print("  - audio out:", audio_out, file=stderr, flush=True)
    return audio_out
