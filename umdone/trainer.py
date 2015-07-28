"""Main training app."""
from __future__ import unicode_literals, print_function
import os
import sys
from argparse import ArgumentParser

import urwid
import librosa
import tables as tb

from umdone import sound
from umdone import segment


class TrainerModel(object):

    max_val = 1
    min_val = -1
    valid_categories = (
        (0, 'word'),
        (1, 'ummm'),
        (2, 'like'),
        (3, 'non-word'),
        )

    def __init__(self, fname, window_length=0.05, threshold=0.01, n_mfcc=13):
        # settings
        self.filename = fname
        self.window_length = window_length
        self.threshold = threshold
        self.n_mfcc = n_mfcc

        # data
        self.current_segment = 0
        self.raw, self.sr = librosa.load(fname, mono=True, sr=None)
        self.bounds = segment.boundaries(self.raw, self.sr, window_length=window_length, 
                                         threshold=threshold)

        # results, keyed by current segement
        self.mfccs = {}
        self.categories = {}

    @property
    def clip(self):
        l, u = self.bounds[self.current_segment]
        return self.raw[l:u]

    def distances(self):
        pass

    def save(self):
        pass

    def get_data(self, offset, r):
        """
        Return the data in [offset:offset+r], the maximum value
        for items returned, and the offset at which the data
        repeats.
        """
        l = []
        d = self.data[self.current_mode]
        while r:
            offset = offset % len(d)
            segment = d[offset:offset+r]
            r -= len(segment)
            offset += len(segment)
            l += segment
        return l, self.data_max_value, len(d)


class TrainerView(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface and
    graph display.
    """
    palette = [
        ('body',         'black',      'light gray', 'standout'),
        ('header',       'white',      'dark red',   'bold'),
        ('screen edge',  'light blue', 'dark cyan'),
        ('main shadow',  'dark gray',  'black'),
        ('line',         'black',      'light gray', 'standout'),
        ('bg background','light gray', 'black'),
        ('bg 1',         'black',      'dark blue', 'standout'),
        ('bg 1 smooth',  'dark magenta',  'black'),
        ('bg 2',         'black',      'dark cyan', 'standout'),
        ('bg 2 smooth',  'dark cyan',  'black'),
        ('button normal','light gray', 'dark blue', 'standout'),
        ('button select','white',      'dark green'),
        ('line',         'black',      'light gray', 'standout'),
        ('pg normal',    'white',      'black', 'standout'),
        ('pg complete',  'white',      'dark magenta'),
        ('pg smooth',    'dark magenta','black')
        ]

    graph_samples_per_bar = 10
    graph_num_bars = 5
    graph_offset_per_second = 5

    def __init__(self, controller):
        self.controller = controller
        super(TrainerView, self).__init__(self.main_window())

    def get_offset_now(self):
        if self.start_time is None:
            return 0
        if not self.started:
            return self.offset
        tdelta = time.time() - self.start_time
        return int(self.offset + (tdelta*self.graph_offset_per_second))

    def update_graph(self, force_update=False):
        o = self.get_offset_now()
        if o == self.last_offset and not force_update:
            return False
        self.last_offset = o
        gspb = self.graph_samples_per_bar
        r = gspb * self.graph_num_bars
        d, max_value, repeat = self.controller.get_data( o, r )
        l = []
        for n in range(self.graph_num_bars):
            value = sum(d[n*gspb:(n+1)*gspb])/gspb
            # toggle between two bar types
            if n & 1:
                l.append([0,value])
            else:
                l.append([value,0])
        self.graph.set_data(l,max_value)

        # also update progress
        if (o//repeat)&1:
            # show 100% for first half, 0 for second half
            if o%repeat > repeat//2:
                prog = 0
            else:
                prog = 1
        else:
            prog = float(o%repeat) / repeat
        self.animate_progress.set_completion( prog )
        return True

    def on_nav_button(self, button, offset):
        self.controller.offset_current_segment(offset)

    def on_cat_button(self, button, i):
        self.controller.select_category(i)

    def on_unicode_checkbox(self, w, state):
        self.graph = self.bar_graph(state)
        self.graph_wrap._w = self.graph
        self.update_graph(True)

    def main_shadow(self, w):
        """Wrap a shadow and background around widget w."""
        bg = urwid.AttrWrap(urwid.SolidFill(u"\u2592"), 'screen edge')
        shadow = urwid.AttrWrap(urwid.SolidFill(u" "), 'main shadow')

        bg = urwid.Overlay( shadow, bg,
            ('fixed left', 3), ('fixed right', 1),
            ('fixed top', 2), ('fixed bottom', 1))
        w = urwid.Overlay( w, bg,
            ('fixed left', 2), ('fixed right', 3),
            ('fixed top', 1), ('fixed bottom', 2))
        return w

    def bar_graph(self, smooth=False):
        satt = None
        if smooth:
            satt = {(1,0): 'bg 1 smooth', (2,0): 'bg 2 smooth'}
        w = urwid.BarGraph(['bg background','bg 1','bg 2'], satt=satt)
        return w

    def button(self, t, fn, *args, **kwargs):
        w = urwid.Button(t, fn, *args, **kwargs)
        w = urwid.AttrWrap(w, 'button normal', 'button select')
        return w

    def exit_program(self, w):
        raise urwid.ExitMainLoop()

    def graph_controls(self):
        # setup category buttons
        vc = self.controller.model.valid_categories
        self.category_buttons = [self.button(cat, self.on_cat_button, i) 
                                 for i, cat in vc]
        # setup animate button
        nav_controls = urwid.GridFlow([
            self.button(" prev ", self.on_nav_button, -1),
            self.button("replay", self.on_nav_button, 0),
            self.button(" next ", self.on_nav_button, 1),
            ], 10, 3, 0, 'center')

        if urwid.get_encoding_mode() == "utf8":
            unicode_checkbox = urwid.CheckBox("Enable Unicode Graphics",
                                              on_state_change=self.on_unicode_checkbox)
        else:
            unicode_checkbox = urwid.Text("UTF-8 encoding not detected")

        l = [urwid.Text("Categories", align="center")]
        l += self.category_buttons
        l += [urwid.Divider(),
              urwid.Text("Navigation", align="center"),
              nav_controls,
              urwid.Divider(),
              urwid.LineBox( unicode_checkbox),
              urwid.Divider(),
              self.button("Quit", self.exit_program),
              ]
        w = urwid.ListBox(urwid.SimpleListWalker(l))
        return w

    def main_window(self):
        self.graph = self.bar_graph()
        self.graph_wrap = urwid.WidgetWrap( self.graph )
        vline = urwid.AttrWrap(urwid.SolidFill('\u2502'), 'line')
        c = self.graph_controls()
        w = urwid.Columns([('weight', 2, self.graph_wrap),
                           ('fixed', 1, vline), c],
            dividechars=1, focus_column=2)
        w = urwid.Padding(w, ('fixed left', 1),('fixed right', 0))
        w = urwid.AttrWrap(w,'body')
        w = urwid.LineBox(w)
        w = urwid.AttrWrap(w,'line')
        w = self.main_shadow(w)
        return w


class TrainerDisplay(object):

    def __init__(self, ns):
        self.model = TrainerModel(ns.input, window_length=ns.window_length, 
                                  threshold=ns.noise_threshold, n_mfcc=ns.n_mfcc)
        self.view = TrainerView(self)

    def select_category(self, cat):
        s = self.model.current_segment 
        self.model.categories[s] = cat
        self.select_segment(s+1)

    def select_segment(self, s):
        self.model.current_segment = s
        clip = self.model.clip
        sound.play(clip, self.model.sr)

    def offset_current_segment(self, offset):
        s = self.model.current_segment
        s += offset
        self.select_segment(s)

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.view.palette)
        self.loop.run()


def main(args=None):
    """Entry point for umdone trainer."""
    parser = ArgumentParser('umdone-trainer')
    parser.add_argument('input', help='input file')
    parser.add_argument('-o', '--output', dest='output', default=None, 
                        help='Output file.')
    parser.add_argument('--window-length', dest='window_length', default=0.05,
                        type=float, help='Word boundary window length.')
    parser.add_argument('--noise-threshold', dest='noise_threshold', default=0.01,
                        type=float, help='Noise threshold on words vs quiet.')
    parser.add_argument('--n-mfcc', dest='n_mfcc', default=13, type=int, 
                        help='Number of MFCC components.')
    ns = parser.parse_args(args)
    if ns.output is None:
        ns.output = '{0}-umdone-training.h5'.format(os.path.splitext(ns.input)[0])
    TrainerDisplay(ns).main()


if __name__ == '__main__':
    main()
