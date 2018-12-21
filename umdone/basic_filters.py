"""Basic audio filters"""
import sys

import numpy as np

import librosa.core
import librosa.util
import librosa.effects

from umdone.io import load_clips_file
from umdone.tools import cache
from umdone.sound import Audio


def complement_intervals(intervals, size=None):
    """Returns and interval array (2d ndarray) of all intervals
    complementing the input interval array
    """
    inner = np.concatenate(
        [intervals[:-1, 1, np.newaxis], intervals[1:, 0, np.newaxis]], axis=1
    )
    total = []
    if intervals[0, 0] != 0:
        total.append([[0, intervals[0, 0]]])
    total.append(inner)
    if size is not None and intervals[-1, 1] != size:
        total.append([[intervals[-1, 1], size]])
    if len(total) > 1:
        comp = np.concatenate(total)
    else:
        comp = inner
    return comp


def intervals_to_mask(intervals, size):
    """Returns numpy boolean mask from intervals array."""
    mask = np.zeros(size, bool)
    for start, end in intervals:
        mask[start : end + 1] = True
    return mask


@cache
def _reduce_noise(noisy, sr=None, norm=True):
    noisy = Audio.from_hash_or_init(noisy, sr=sr)
    sr = noisy.sr
    non_silent_intervals = librosa.effects.split(noisy.data)
    silent_intervals = complement_intervals(non_silent_intervals, size=len(noisy.data))
    mask = intervals_to_mask(silent_intervals, len(noisy.data))
    D_silent = librosa.stft(noisy.data[mask])
    D_noisy = librosa.stft(noisy.data)
    D_nr = -np.max(D_silent, axis=1)[:, np.newaxis] + D_noisy
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
    silent_intervals = complement_intervals(non_silent_intervals, size=len(inp.data))
    reduce_to_samp = int(reduce_to * sr)
    long_silences_mask = (
        silent_intervals[:, 1] - silent_intervals[:, 0]
    ) > reduce_to_samp
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


def _remove_marked_clips(inp, bounds, mask):
    # does the real work
    keepers = np.ones(inp.data.shape[0], dtype=bool)
    bad_bounds = bounds[~mask]
    for start, end in bad_bounds:
        keepers[start:end+1] = False
    out = Audio(inp.data[keepers], sr=inp.sr)
    return out


@cache
def _remove_marked_clips_cached(inp, sr, dbfile):
    # cache-safe version
    inp = Audio.from_hash_or_init(inp, sr=sr)
    _, bounds, mask = load_clips_file(dbfile)
    out = _remove_marked_clips(inp, bounds, mask)
    return out.hash_str()


def remove_marked_clips(inp, bounds=None, mask=None, dbfile=None):
    """Removes marked clips from audio.

    Parameters
    ----------
    inp : str or Audio
        Input audio. If this is a string, it will be read in from
        a file. If this is an Audio instance, it will be used directly.
    bounds : 2D array of intervals or None, optional
        Represents the interval bounds where masks are given. If not None,
        mask must also be given.
    mask : boolean array of length of the bounds or None, optional
        Masks the bounds, False means to discard and True means to keep.
    dbfile : str or None, optional
        If given, the bounds and mask are read from a database file.

    Returns
    -------
    out : Audio
    """
    if dbfile is not None and bounds is None and mask is None:
        # have dbfile, use cached version
        sr = None
        if isinstance(inp, Audio):
            sr = inp.sr
            inp = inp.hash_str()
        out = _remove_marked_clips_cached(inp, sr, dbfile)
        out = Audio.from_hash(out)
    elif dbfile is None and bounds is not None and mask is not None:
        # no db, can't use cached version
        if isinstance(inp, str):
            inp = Audio.from_hash_or_init(inp)
        out = _remove_marked_clips(inp, bounds, mask)
    else:
        raise RuntimeError("both bounds and mask must not be None OR dbfile must not be None")
    return out


def afade(n, base=10, dtype="f4"):
    """Creates a fade-in array of length-n for a given base."""
    t = np.linspace(0.0, np.log(base + 1) / np.log(base), n, dtype=dtype)
    f = np.power(base, t) / base - (1 / base)
    return f


def cross_fade_arrays(x, y, n, base=10):
    """Fades and x-array out while fading a y-array in over n points."""
    f = afade(n, base=base, dtype=x.dtype)
    out = np.concatenate([x[:-n], x[-n:] * f[::-1] + y[:n] * f, y[n:]])
    return out


@cache
def _cross_fade(a, b, sr=None, t=3.0, base=10):
    a = Audio.from_hash_or_init(a, sr=sr)
    b = Audio.from_hash_or_init(b, sr=sr)
    assert a.sr == b.sr, "sample rates must be equal to cross-fade"
    sr = a.sr
    n = int(t * sr)
    z = cross_fade_arrays(a.data, b.data, n, base=base)
    c = Audio(z, sr)
    return c.hash_str()


def cross_fade(a, b, t=3.0, base=10):
    """Fades an audio in and another one out simeltaneously over t seconds."""
    if isinstance(a, Audio):
        a = a.hash_str()
    if isinstance(b, Audio):
        b = b.hash_str()
    c = _cross_fade(a, b, t=t, base=base)
    c = Audio.from_hash(c)
    return c
