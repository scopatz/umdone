"""Main training app."""
from __future__ import unicode_literals, print_function
import os
import sys
import json
from argparse import ArgumentParser

import urwid
import librosa
import numpy as np
import tables as tb

import sounddevice as sd

import umdone.io
from umdone import cli
from umdone import dtw
from umdone import sound
from umdone import segment
from umdone.tools import UMDONE_CONFIG_DIR
from umdone.baseapp import BaseAppModel, BaseAppDisplay


class TrainerModel(BaseAppModel):

    max_val = 1
    min_val = -1
    valid_categories = (
        (0, 'word              (keep)'),
        (1, 'ambiguous         (keep)'),
        (2, 'ummm, like, etc.  (discard)'),
        (3, 'non-word          (discard)'),
        )

    default_settings = {'device': None, 'current_segments': {}}
    settings_file = os.path.join(UMDONE_CONFIG_DIR, 'trainer.json')

    def __init__(self, audio, window_length=0.05, threshold=0.01, n_mfcc=13, device=-1):
        super().__init__(audio, window_length=window_length, threshold=threshold, device=device)
        self.n_mfcc = n_mfcc

    def compute_mfccs(self, callback=None):
        sr = self.sr
        n_mfcc = self.n_mfcc
        n = len(self.categories)
        self.mfccs = mfccs = []
        order = self.segement_order()
        for status, seg in enumerate(order, start=1):
            if callback is not None:
                callback(float(status)/n)
            l, u = self.bounds[seg]
            clip = self.raw[l:u]
            mfcc = librosa.feature.mfcc(clip, sr, n_mfcc=n_mfcc).T
            mfccs.append(mfcc)
        return mfccs

    def compute_distances(self, outfile, callback=None):
        mfccs = self.mfccs
        if os.path.isfile(outfile):
            mfccs = umdone.io._load_mfccs(outfile) + mfccs
        self.distances = dtw.distance_matrix(mfccs, callback=callback)
        return self.distances

    def save(self):
        order = self.segement_order()
        cats = [self.categories[seg] for seg in order]
        umdone.io.save_mfccs(self.dbfile, self.mfccs, cats, distances=self.distances)
        self.reset_data()

    def reset_data(self):
        self.categories.clear()
        del self.mfccs, self.distances


class TrainerDisplay(BaseAppDisplay):

    modelcls = TrainerModel

    def _save(self):
        model = self.model
        view = self.view
        loop = self.loop
        # MFCCs
        view.status.set_text('\nComputing MFCCs\n')
        def mfcc_callback(frac):
            view.status.set_text('\nComputing MFCCs: {:.1%}\n'.format(frac))
            loop.draw_screen()
        mfcc_callback(0.0)
        model.compute_mfccs(callback=mfcc_callback)
        # Distance Matrix
        view.status.set_text('\nComputing distance matrix\n')
        def dist_callback(frac):
            view.status.set_text('\nComputing distance matrix: {:.1%}\n'.format(frac))
            loop.draw_screen()
        dist_callback(0.0)
        model.compute_distances(self.dbfile, callback=dist_callback)
        # save
        view.status.set_text('\nSaving data\n')
        loop.draw_screen()
        model.save()
        view.status.set_text('\nSaving settings\n')
        loop.draw_screen()
        model.save_settings()
        view.status.set_text('\nSaved\n')
        loop.draw_screen()
        view.update_progress()


def add_arguments(parser):
    cli.add_output(parser)
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    cli.add_n_mfcc(parser)
    cli.add_input(parser)


def main(ns=None, args=None):
    """Entry point for umdone trainer."""
    if ns is None:
        parser = ArgumentParser('umdone-trainer')
        add_arguments(parser)
        ns = parser.parse_args(args)
    if ns.output is None:
        ns.output = '{0}-umdone-training.h5'.format(os.path.splitext(ns.input)[0])
    TrainerDisplay(ns.input, ns.output, window_length=ns.window_length,
                   noise_threshold=ns.noise_threshold, n_mfcc=ns.n_mfcc).main()


if __name__ == '__main__':
    main()
