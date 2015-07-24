"""Main functionality for umdone."""
from argparse import ArgumentParser

import librosa

from umdone import segment
from umdone import discovery


def remove_umms():
    x, sr = librosa.load(f, sr=None)
    bounds = segment.boundaries(x, sr)
    td = discovery.load_training_data(files)
    matches = discovery.match(x, bounds, td)
    y = segment.remove_slices(x, matches)
    librosa.output.write_wav('out.wav', y, sr)
    

def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone')
    ns = parser.parse_args(args)


if __name__ == '__main__':
    main()