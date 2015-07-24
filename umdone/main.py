"""Main functionality for umdone."""
import os
from argparse import ArgumentParser

import librosa

from umdone import segment
from umdone import discover


def remove_umms(ns):
    x, sr = librosa.load(ns.input, sr=None)
    bounds = segment.boundaries(x, sr, window_length=ns.window_length, 
                                threshold=ns.noise_threshold)
    td = discover.load_training_data(ns.train, n=ns.n_mfcc)
    matches = discover.match(x, bounds, td, n=ns.n_mfcc, threshold=ns.match_threashold)
    y = segment.remove_slices(x, matches)
    librosa.output.write_wav('out.wav', y, sr)
    

def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone')
    parser.add_argument('input', help='input file')
    parser.add_argument('-o', '--output', dest='output', default=None, 
                        help='Output file.')
    parser.add_argument('-t', '--train', nargs='*', dest='train', 
                        help='list of training files')
    parser.add_argument('--window-length', dest='window_length', default=0.05,
                        help='Word boundary window length.')
    parser.add_argument('--noise-threshold', dest='noise_threshold', default=0.01,
                        help='Noise threshold on words vs quiet.')
    parser.add_argument('--n-mfcc', dest='n_mfcc', default=13,
                        help='Number of MFCC components.')
    parser.add_argument('--match-threshold', dest='match_threshold', default=0.45,
                        help='Threshold distance to match words.')
    ns = parser.parse_args(args)
    if ns.output is None:
        ns.output = '{0}-umdone{1}'.format(*os.path.splitext(ns.input))
    remove_umms(ns)

if __name__ == '__main__':
    main()