"""Basic audio filters"""
import sys

import numpy as np

import librosa.core
import librosa.util
import librosa.effects

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
    if isinstance(noisy, Audio):
        noisy = noisy.hash_str()
    reduced = _reduce_noise(noisy, norm=norm)
    reduced = Audio.from_hash(reduced)
    if outfile is not None:
        reduced.save(outfile)
    return reduced


@cache
def _remove_silence(inp, sr=None, reduce_to=0.0):
    inp = Audio.from_hash_or_init(inp, sr=sr)
    sr = inp.sr
    non_silent_intervals = librosa.effects.split(inp.data)
    silent_intervals = complement_intervals(non_silent_intervals,
                                            size=len(inp.data))
    reduce_to_samp = int(reduce_to * sr)
    long_silences_mask = (silent_intervals[:,1] - silent_intervals[:,0]) > reduce_to_samp
    long_silences = silent_intervals[long_silences_mask]
    keep_intervals = complement_intervals(long_silences, size=len(inp.data))
    mask = intervals_to_mask(keep_intervals, len(inp.data))
    out = Audio(inp.data[mask], sr)
    return out.hash_str()


def remove_silence(inp, reduce_to=0.0):
    """Reduces noise in audio

    Parameters
    ----------
    inp : str or Audio
        Input audio. If this is a string, it will be read in from
        a file. If this is an Audio instance, it will be used directly.
    reduce_to : int or float, optional
        The amount of time (in sec) to which silences should be reduced.
        Silences shorter than this time are not replaced. For example,
        if this parameter is 1 sec, a 10 sec silence will become a 1 sec
        silence, while a 0.5 sec silence will remain 0.5 sec long.

    Returns
    -------
    out : Audio
    """
    if isinstance(inp, Audio):
        inp = inp.hash_str()
    out = _remove_silence(inp, reduce_to=reduce_to)
    out = Audio.from_hash(out)
    return out


def afade(n, base=10, dtype='f4'):
    """Creates a fade-in array of length-n for a given base."""
    t = np.linspace(0.0, np.log(base+1)/np.log(base), n, dtype=dtype)
    f = np.power(base, t)/base - (1/base)
    return f


def cross_fade(x, y, n, base=10):
    """Fades and x-array out while fading a y-array in over n points."""
    f = afade(n, base=base, dtype=x.dtype)
    out = np.concatenate([x[:-n], x[-n:]*f[::-1] + y[:n]*f ,y[n:]])
    return out
