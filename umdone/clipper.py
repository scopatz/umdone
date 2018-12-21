"""Main clipping app."""
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


class ClipperModel(BaseAppModel):

    default_settings = {"device": None, "current_segments": {}}
    settings_file = os.path.join(UMDONE_CONFIG_DIR, "clipper.json")

    def __init__(self, audio, dbfile=None, **kwargs):
        if dbfile is not None and os.path.isfile(dbfile):
            _, self.bounds, _ = umdone.io.load_clips(
                dbfile, raw=False, mask=False
            )
        super().__init__(audio, dbfile=dbfile, **kwargs)

    def save(self):
        order = self.segement_order()
        cats = [self.categories[seg] for seg in order]
        mask = np.array(cats, dtype=bool)
        umdone.io.save_clips(self.dbfile, self.raw, self.bounds, mask)
        self.reset_data()

    def reset_data(self):
        self.categories.clear()


class ClipperDisplay(BaseAppDisplay):

    modelcls = ClipperModel
    auto_save = True

    def _save(self):
        model = self.model
        view = self.view
        loop = self.loop
        # save
        view.status.set_text("\nSaving data\n")
        loop.draw_screen()
        model.save()
        view.status.set_text("\nSaving settings\n")
        loop.draw_screen()
        model.save_settings()
        view.status.set_text("\nSaved\n")
        loop.draw_screen()
        view.update_progress()


def add_arguments(parser):
    cli.add_output(parser)
    cli.add_window_length(parser)
    cli.add_noise_threshold(parser)
    cli.add_input(parser)


def main(ns=None, args=None):
    """Entry point for umdone trainer."""
    if ns is None:
        parser = ArgumentParser("umdone-clipper")
        add_arguments(parser)
        ns = parser.parse_args(args)
    if ns.output is None:
        ns.output = "{0}-umdone-clipping.h5".format(os.path.splitext(ns.input)[0])
    ClipperDisplay(
        ns.input,
        ns.output,
        window_length=ns.window_length,
        noise_threshold=ns.noise_threshold,
    ).main()


if __name__ == "__main__":
    main()
