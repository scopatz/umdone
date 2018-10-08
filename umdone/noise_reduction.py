import argparse

import numpy as np

import librosa.core
import librosa.effects

from umdone import cli
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


def reduce_noise(noisy, outfile=None):
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
    reduced : audio
    """
    if isinstance(noisy, str):
        noisy = Audio(noisy)
    non_silent_intervals = librosa.effects.split(noisy.data)
    silent_intervals = complement_intervals(non_silent_intervals,
                                            size=len(noisy.data))
    mask = intervals_to_mask(silent_intervals, len(noisy.data))
    D_silent = librosa.stft(noisy.data[mask])
    D_noisy = librosa.stft(noisy.data)
    D_nr = -np.max(D_silent, axis=1)[:,np.newaxis] + D_noisy
    nr = librosa.core.istft(D_nr)
    nr = Audio(nr, noisy.sr)
    if outfile is not None:
        nr.save(outfile)
    return nr


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