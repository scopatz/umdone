"""Label training data pipeline command"""
import os
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color, unthreadable

from umdone import cli
from umdone.sound import Audio, CLIPS_CACHE_DIR
from umdone.commands import audio_in


@lazyobject
def PARSER():
    parser = ArgumentParser("mark-clips")
    parser.add_argument(
        "infile", help="path to local file or URL.", nargs="?", default=None
    )
    parser.add_argument(
        "--db", help="path to local database file or URL.", default=None, dest="dbfile"
    )
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    return parser


@unthreadable
@audio_in
def main(ain, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Marks clip audio"""
    ns = PARSER.parse_args(args)
    if ain is None and ns.infile is not None:
        ain = Audio(ns.infile)
    if ns.dbfile is None:
        prefix = (
            ain.hash()
            if ns.infile is None
            else os.path.splitext(os.path.basename(ns.infile))[0]
        )
        ns.dbfile = os.path.join(CLIPS_CACHE_DIR, prefix + "-clips.h5")
    print_color(
        "{YELLOW}Marking clips {GREEN}" + str(ain) + "{NO_COLOR}",
        file=stderr,
        flush=True,
    )
    from umdone.clipper import ClipperDisplay

    td = ClipperDisplay(
        ain,
        ns.dbfile,
        window_length=ns.window_length,
        noise_threshold=ns.noise_threshold,
    )
    td.main()
    print(f"  - saved clips database to {ns.dbfile}", ain, file=stderr)
    return 0
