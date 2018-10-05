import argparser

import librosa.core

from umdone import cli


def reduce_noise():
    pass



_PARSER = None


def _make_parser():
    global _PARSER
    if _PARSER is not None:
        return _PARSER
    parser = argparse.ArgumentParser('nr')
    cli.add_input(parser)
    cli.add_output(parser)
    _PARSER = parser
    return _PARSER


def main(args=None):
    """Main noise reduction"""



if __name__ == '__main__':
    main()