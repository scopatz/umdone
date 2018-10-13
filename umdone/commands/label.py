"""Label training data pipeline command"""
import os
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color, unthreadable

from umdone import cli
from umdone.sound import Audio, LABEL_CACHE_DIR
from umdone.commands import audio_in


@lazyobject
def PARSER():
    parser = ArgumentParser('label')
    parser.add_argument('infile', help='path to local file or URL.',
                        nargs="?",
                        default=None)
    parser.add_argument('--db', help='path to local database file or URL.',
                        default=None, dest='dbfile')
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    cli.add_n_mfcc(parser)
    return parser


@unthreadable
@audio_in
def main(ain, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Labels audio"""
    ns = PARSER.parse_args(args)
    if ain is None and ns.infile is not None:
        ain = Audio(ns.infile)
    if ns.dbfile is None:
        prefix = ain.hash() if ns.infile is None else \
                 os.path.splitext(os.path.basename(ns.infile))[0]
        ns.dbfile = os.path.join(LABEL_CACHE_DIR, prefix + '-training.h5')
    print_color('{YELLOW}Labeling {GREEN}' + str(ain) + '{NO_COLOR}',
                file=stderr, flush=True)
    from umdone.trainer import TrainerDisplay
    td = TrainerDisplay(ain, ns.dbfile, window_length=ns.window_length,
                        noise_threshold=ns.noise_threshold, n_mfcc=ns.n_mfcc)
    td.main()
    print(f'  - saved label database to {ns.dbfile}', ain, file=stderr)
    return 0
