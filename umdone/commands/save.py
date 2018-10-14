"""Save pipeline command"""
import sys
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color, unthreadable, uncapturable

from umdone.sound import Audio
from umdone.commands import audio_in


@lazyobject
def PARSER():
    parser = ArgumentParser('save')
    parser.add_argument('files',
                        help='paths to local files or URL. The first file is '
                             'the input, if needed. Remaining files are output.',
                        nargs='+',
                        default=())
    return parser


@uncapturable
@unthreadable
@audio_in
def main(ain, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Saves an audio file"""
    ns = PARSER.parse_args(args)
    print_color('{YELLOW}Saving audio{NO_COLOR}', file=stderr, flush=True)
    if ain is None:
        infile, outfiles = ns.files[0], ns.files[1:]
        ain = Audio(infile)
    else:
        outfiles = ns.files
    print('  - saving audio', ain, file=stderr)
    for outfile in outfiles:
        print_color('  - output: {GREEN}' + outfile + '{NO_COLOR}',
                    file=stderr, flush=True)
        ain.save(outfile)
    return 0
