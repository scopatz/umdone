import sys
import argparse

import numpy as np

import librosa.core
import librosa.util
import librosa.effects

from umdone import cli
from umdone.tools import cache
from umdone.sound import Audio


def complement_intervals(intervals, size=None):
    """Returns and interval array (2d ndarray) of all intervals
    complementing the input interval array
    """
    inner = np.concatenate([intervals[:-1,1, np.newaxis],
                            intervals[1:,0,np.newaxis]], axis=1)
    total = []
    if intervals[0,0] != 0:
        total.append([[0, intervals[0,0]]])
    total.append(inner)
    if size is not None and intervals[-1,1] != size:
        total.append([[intervals[-1,1], size]])
    if len(total) > 1:
        comp = np.concatenate(total)
    else:
        comp = inner
    return comp


def intervals_to_mask(intervals, size):
    """Returns numpy boolean mask from intervals array."""
    mask = np.zeros(size, bool)
    for start, end in intervals:
        mask[start:end+1] = True
    return mask


@cache
def _reduce_noise(noisy, sr=None, norm=True):
    print('    - in _reduce_noide:', noisy, file=sys.stderr, flush=True)
    noisy = Audio.from_hash_or_init(noisy, sr=sr)
    sr = noisy.sr
    non_silent_intervals = librosa.effects.split(noisy.data)
    silent_intervals = complement_intervals(non_silent_intervals,
                                            size=len(noisy.data))
    mask = intervals_to_mask(silent_intervals, len(noisy.data))
    D_silent = librosa.stft(noisy.data[mask])
    D_noisy = librosa.stft(noisy.data)
    D_nr = -np.max(D_silent, axis=1)[:,np.newaxis] + D_noisy
    nr = librosa.core.istft(D_nr)
    if norm and np.issubdtype(nr.dtype, np.floating):
        nr = librosa.util.normalize(nr, norm=np.inf, axis=None)
    reduced = Audio(nr, sr)
    print('    - leaving _reduce_noide:', reduced, file=sys.stderr, flush=True)
    return reduced.hash_str()


def reduce_noise(noisy, outfile=None, norm=True):
    """Reduces noise in audio

    Parameters
    ----------
    noisy : str or Audio
        Input audio. If this is a string, it will be read in from
        a file. If this is an Audio instance, it will be used directly.
    outfile : str or None, optional
        Outfile to write the reduced audio to.

    Returns
    -------
    reduced : Audio
    """
    print('  - in reduce noise', file=sys.stderr, flush=True)
    if isinstance(noisy, Audio):
        print('  - noisy is audio:', noisy, file=sys.stderr, flush=True)
        noisy = noisy.hash_str()
        print('  - noisy hash:', noisy, file=sys.stderr, flush=True)
    print('  - have noisy:', noisy, file=sys.stderr, flush=True)
    reduced = _reduce_noise(noisy, norm=norm)
    print('  - reduced hash:', reduced, file=sys.stderr, flush=True)
    reduced = Audio.from_hash(reduced)
    print('  - reduced audio:', reduced, file=sys.stderr, flush=True)
    if outfile is not None:
        reduced.save(outfile)
    print('  - returnng reduced', file=sys.stderr, flush=True)
    return reduced


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
    parser = _make_parser()
    ns = parser.parse_args(args=args)
    reduce_noise(ns.input, ns.output)


if __name__ == '__main__':
    main()