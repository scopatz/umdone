"""Persistance routines for umdone."""
from __future__ import print_function, unicode_literals
import os

import librosa
import numpy as np
import tables as tb

from umdone import dtw


def save(fname, mfccs, categories, distances=None):
    """Saves data to a file.

    Parameters
    ----------
    fname : str
        Filename 
    mfccs : list of arrays
        MFCCs
    categories : 
    """
    # data prep
    n = len(mfccs)
    categories = np.asarray(categories)
    mfcc_lengths = np.empty(n, int)
    for i, mfcc in enumerate(mfccs):
        mfcc_lens[i] = mfcc.shape[0]
    flat_mfccs = np.concatenate(mfccs, axis=0)
    # save data
    if os.path.isfile(fname):
        _save_append(fname, mfccs, flat_mfccs, categories, distances, mfcc_lens)
    else:
        _save_new(fname, mfccs, flat_mfccs, categories, distances, mfcc_lens)
        

def _save_new(fname, mfccs, flat_mfccs, categories, distances, lengths):
    if distances is None:
        distances = dtw.distance_matrix(mfccs)
    with tb.open_file(fname, 'a') as f:
        f.create_earray('/', 'categories', shape=(0,), obj=categories)
        f.create_earray('/', 'mfcc_lengths', shape=(0,), obj=lengths)
        f.create_earray('/', 'mfccs', shape=(0, flat_mfccs.shape[1]), obj=flat_mfccs)
        f.create_array('/', 'distances', obj=distances)  # not extendable!


def _save_append(fname, mfccs, flat_mfccs, categories, distances, lengths):
    if distances is None:
        mfccs = _load_mfccs(fname) + mfccs
        distances = dtw.distance_matrix(mfccs)
    with tb.open_file(fname, 'a') as f:
        f.root.categories.append(categories)
        f.root.mfcc_lengths.append(lengths)
        f.root.mfccs.append(flat_mfccs)
        f.remove_node('/', 'distances')
        f.create_array('/', 'distances', obj=distances)  # not extendable!


def _load_mfccs(fname):
    with tb.open_file(fname, 'r') as f:
        lens = f.root.mfcc_lengths[:]
        flat_mfccs = f.root.mfccs[:]
    return _unflatten_mfccs(flat_mfccs, lens)


def _unflatten_mfccs(flat_mfccs, lens):
    i = 0
    mfccs = []
    for n in lens:
        j = i + n
        mfccs.append(flat_mfccs[i:j])
        i = j
    return mfccs


def load(fname):
    with tb.open_file(fname, 'r') as f:
        dists = f.root.distances[:]
        cats = f.root.categories
        lens = f.root.mfcc_lengths[:]
        flat_mfccs = f.root.mfccs[:]
    mfccs = _unflatten_mfccs(flat_mfccs, lens)
    return mfccs, dists, cats


