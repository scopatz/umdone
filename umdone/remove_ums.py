"""Remove Umms (and similar) from audio."""
import os
import sys

import librosa
import numpy as np
from sklearn import svm

from umdone import dtw

import umdone.io
from umdone import segment
from umdone.tools import cache
from umdone.sound import Audio


def match(x, sr, bounds, mfccs, distances, categories):
    """Finds the matches to the training data in x that is in valid the bounds.
    Returns the matched bou nds.
    """
    # data setup
    n_mfcc = mfccs[0].shape[1]
    d = np.empty((len(bounds), len(distances)), 'f8')
    for i, (l, u) in enumerate(bounds):
        clip = x[l:u]
        clip_mfcc = librosa.feature.mfcc(clip, sr, n_mfcc=n_mfcc).T
        for j, mfcc in enumerate(mfccs):
            d[i, j] = dtw.distance(clip_mfcc, mfcc)
    # learn stuff
    classifier = svm.SVC(gamma=0.001)
    classifier.fit(distances, categories)
    results = classifier.predict(d)
    # words = 0 and ambiguous = 1, so we want to discard cases > 1,
    # ie umm/like/etc = 2 and non-words = 3
    matches = bounds[results > 1]
    return matches


def _remove_umms(audio, mfccs, distances, categories, window_length=0.05, noise_threshold=0.01):
    x, sr = audio.data, audio.sr
    bounds = segment.boundaries(x, sr, window_length=window_length,
                                threshold=noise_threshold)
    matches = match(x, sr, bounds, mfccs, distances, categories)
    y = segment.remove_slices(x.T, matches)
    print('matches: ', matches, file=sys.stderr)
    out = Audio(y, sr)
    return out


@cache
def _remove_umms_cacheable(audio_hash, dbfiles, window_length=0.05, noise_threshold=0.01):
    audio = Audio.from_hash(audio_hash)
    mfccs, distances, categories = umdone.io.load(dbfiles)
    out = _remove_umms(audio, mfccs, distances, categories,
                       window_length=window_length, noise_threshold=noise_threshold)
    return out.hash_str()


def remove_umms(audio, dbfiles=None, mfccs=None, distances=None, categories=None,
                window_length=0.05, noise_threshold=0.01):
    """Filters out umms and other unwanted clips from audio using support vector
    classification.

    Parameters
    ----------
    audio : Audio or str
        Audio instance, or a string loadable as such
    dbfiles : str, list of str, or None, optional
        The training database files to load. If this is None, mfccs, distances,
        and categories must be supplied.
    mfccs : list of ndarrays or None, optional
        MFCCs, if None, dbfiles must not be None,
    distances : float ndarray or None, optional
        distances, if None, dbfiles must not be None.
    categories : int ndarray or None, optional
        categories, if None, dbfiles must not be None.
    window_length : float, optional
        Word boundary window length
    noise_threshold : float, optional
        Noise threshold on words vs quiet

    Returns
    -------
    out : Audio
        Version of audio with umms removed or reduced.
    """
    # make sure we have an Audio object
    if isinstance(audio, str):
        audio = Audio(audio)
    # figure out which command to call.
    if dbfiles is not None:
        # yes, we are in a cacheable situation
        out_hash = _remove_umms_cacheable(audio.hash_str(), dbfiles,
                                          window_length=window_length,
                                          noise_threshold=noise_threshold)
        out = Audio.from_hash(out_hash)
    elif mfccs is not None and distances is not None and categories is not None:
        # just do the comuptation
        out = _remove_umms(audio, mfccs, distances, categories,
                           window_length=window_length, noise_threshold=noise_threshold)
    else:
        raise ValueError('either dbfiles must not be None, or mfccs, distances, '
                         'and categories must all not be None')
    return out
