"""Persistance routines for umdone."""
from __future__ import print_function, unicode_literals
import os

import librosa
import numpy as np
import tables as tb

from umdone import dtw


def save_mfccs(fname, mfccs, categories, distances=None):
    """Saves MFCC data to a file.

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
    mfcc_lens = np.empty(n, int)
    for i, mfcc in enumerate(mfccs):
        mfcc_lens[i] = mfcc.shape[0]
    flat_mfccs = np.concatenate(mfccs, axis=0)
    # save data
    if os.path.isfile(fname):
        _save_mfccs_append(fname, mfccs, flat_mfccs, categories, distances, mfcc_lens)
    else:
        _save_mfccs_new(fname, mfccs, flat_mfccs, categories, distances, mfcc_lens)


def _save_mfccs_new(fname, mfccs, flat_mfccs, categories, distances, lengths):
    if distances is None:
        distances = dtw.distance_matrix(mfccs)
    with tb.open_file(fname, "a") as f:
        f.create_earray("/", "categories", shape=(0,), obj=categories)
        f.create_earray("/", "mfcc_lengths", shape=(0,), obj=lengths)
        f.create_earray("/", "mfccs", shape=(0, flat_mfccs.shape[1]), obj=flat_mfccs)
        f.create_array("/", "distances", obj=distances)  # not extendable!


def _save_mfccs_append(fname, mfccs, flat_mfccs, categories, distances, lengths):
    if distances is None:
        mfccs = _load_mfccs(fname) + mfccs
        distances = dtw.distance_matrix(mfccs)
    with tb.open_file(fname, "a") as f:
        f.root.categories.append(categories)
        f.root.mfcc_lengths.append(lengths)
        f.root.mfccs.append(flat_mfccs)
        f.remove_node("/", "distances")
        f.create_array("/", "distances", obj=distances)  # not extendable!


def _load_mfccs(fname):
    with tb.open_file(fname, "r") as f:
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


def load_mfccs_file(fname):
    with tb.open_file(fname, "r") as f:
        dists = f.root.distances[:]
        cats = f.root.categories[:]
        lens = f.root.mfcc_lengths[:]
        flat_mfccs = f.root.mfccs[:]
    mfccs = _unflatten_mfccs(flat_mfccs, lens)
    return mfccs, dists, cats


def load_mfccs(fnames):
    """Loads one or many MFCC database files"""
    if isinstance(fnames, str):
        return load_mfccs_file(fnames)
    mfccs = []
    dists = []
    cats = []
    for fname in fnames:
        m, d, c = load_mfccs_file(fname)
        mfccs.extend(m)
        dists.append(d)
        cats.append(c)
    dists = np.concatenate(dists)
    cats = np.concatenate(cats)
    return mfccs, dists, cats


def save_clips(fname, raw, bounds, categories):
    """Saves clips data to a file.

    Parameters
    ----------
    fname : str
        Filename
    raw :
    clips :
    categories :
    """
    # data prep
    categories = np.asarray(categories)
    # save data
    if os.path.isfile(fname):
        _save_clips_append(fname, raw, bounds, categories)
    else:
        _save_clips_new(fname, raw, bounds, categories)


def _save_clips_new(fname, raw, bounds, categories):
    with tb.open_file(fname, "a") as f:
        f.create_array("/", "raw", obj=raw)
        f.create_array("/", "bounds", obj=bounds)
        f.create_earray("/", "categories", shape=(0,), obj=categories)


def _save_clips_append(fname, raw, bounds, categories):
    with tb.open_file(fname, "a") as f:
        f.root.categories.append(categories)


def load_clips_file(fname, raw=True, bounds=True, categories=True):
    with tb.open_file(fname, "r") as f:
        r = f.root.raw[:] if raw else None
        b = f.root.bounds[:] if bounds else None
        c = f.root.categories[:] if categories else None
    return r, b, c


def load_clips(fnames, raw=True, bounds=True, categories=True):
    """Loads one or many clips database files"""
    if isinstance(fnames, str):
        return load_clips_file(fnames, raw=raw, bounds=bounds, categories=categories)
    raws = []
    bnds = []
    cats = []
    for fname in fnames:
        r, b, c = load_clips_file(fname, raw=raw, bounds=bounds, categories=categories)
        raws.extend(r)
        bnds.append(b)
        cats.append(c)
    raws = np.concatenate(raws)
    bnds = np.concatenate(bnds)
    cats = np.concatenate(cats)
    return raws, bnds, cats
