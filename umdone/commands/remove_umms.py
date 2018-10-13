"""Remove umms pipeline command"""
import os
import sys
import glob
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone import cli
from umdone.sound import Audio, LABEL_CACHE_DIR
from umdone.commands import audio_io


@lazyobject
def PARSER():
    parser = ArgumentParser('remove-umms')
    parser.add_argument('path',
                        help='path to local file or URL.',
                        nargs="?",
                        default=None,)
    parser.add_argument('--dbfiles',
                        dest='dbfiles',
                        default=None,
                        nargs='+',
                        help='training database files to load'
                        )
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    return parser


@audio_io
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """removes silence from an audio file"""
    print_color('{YELLOW}Removing umms{NO_COLOR}', file=stderr, flush=True)
    ns = PARSER.parse_args(args)
    # ensure audio
    if audio_in is None and ns.path is not None:
        audio_in = Audio(ns.path)
    print('  - audio in:', audio_in, file=stderr, flush=True)
    # get and verify dbfiles
    dbfiles = ns.dbfiles
    if dbfiles is None:
        dbfiles = glob.glob(os.path.join(LABEL_CACHE_DIR, '*.h5'))
    if not dbfiles:
        print_color('{RED}No training database files found!{NO_COLOR}',
                    file=stderr, flush=True)
        return 1
    for dbfile in dbfiles:
        if not os.path.isfile(dbfile):
            print_color('{RED}Training database file ' + dbfile + ' does not exist!{NO_COLOR}',
                        file=stderr, flush=True)
            return 1
    print('  - training database files:\n   * ' + '\n   * '.join(dbfiles), file=stderr, flush=True)
    import umdone.remove_ums
    audio_out = umdone.remove_ums.remove_umms(audio_in, dbfiles=dbfiles,
                                              window_length=ns.window_length,
                                              noise_threshold=ns.noise_threshold,)
    print('  - audio out:', audio_out, file=stderr, flush=True)
    return audio_out
