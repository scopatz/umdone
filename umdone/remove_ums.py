"""Main functionality for umdone."""
import os
from argparse import ArgumentParser

import librosa

import umdone.io
from umdone import cli
from umdone import trainer
from umdone import segment
from umdone import discover


def remove_umms(ns):
    if ns.output is None:
        ns.output = '{0}-umdone{1}'.format(*os.path.splitext(ns.input))
    x, sr = librosa.load(ns.input, mono=True, sr=None)
    bounds = segment.boundaries(x, sr, window_length=ns.window_length, 
                                threshold=ns.noise_threshold)
    mfccs, distances, categories = umdone.io.load(ns.train)
    matches = discover.match(x, sr, bounds, mfccs, distances, categories) 
    del x, sr, bounds, mfccs, distances, categories
    # read back in to preserve mono/stereo and levels on output
    x, sr = librosa.load(ns.input, mono=False, sr=None)
    y = segment.remove_slices(x.T, matches)
    librosa.output.write_wav(ns.output, y.T, sr, norm=False)


def remove_add_arguments(parser):
    cli.add_output(parser)
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    cli.add_train_argument(parser)
    cli.add_input(parser)


MAINS = {
    'train': trainer.main,
    'rm': remove_umms,
    }

def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone')
    subparsers = parser.add_subparsers(dest='cmd', help='sub-command help')

    # train
    parser_train = subparsers.add_parser('train', help='create a training dataset')
    trainer.add_arguments(parser_train)

    # remove umms
    parser_rm = subparsers.add_parser('rm', help='remove umms')
    remove_add_arguments(parser_rm)

    ns = parser.parse_args(args)
    MAINS[ns.cmd](ns)


if __name__ == '__main__':
    main()