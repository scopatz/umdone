"""Plays and manipulates sound files."""
from __future__ import unicode_literals
import io
import os
import tempfile
import subprocess
from threading import Thread
from collections.abc import Iterable

import librosa
import librosa.core
import librosa.output
from scipy.io import wavfile

from umdone.tools import cache


def array_to_bytes(x, sr):
    """Converts a numpy array to bytes in memory"""
    with io.BytesIO() as f:
        wavfile.write(f, sr, x)
        f.seek(0)
        b = f.read()
    return b


class MPlayerWorker(Thread):
    """Computes x, v, and a of the ith body."""
    def __init__(self, clip, sr, *args, **kwargs):
        super(MPlayerWorker, self).__init__(*args, **kwargs)
        self.clip = clip
        self.sr = sr
        self.daemon = True
        self.start()

    def run(self):
        with tempfile.NamedTemporaryFile() as f:
            librosa.output.write_wav(f.name, self.clip, self.sr)
            p = subprocess.Popen(['nohup', 'mplayer', f.name],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            while p.poll() is None:
                pass


def play_posix(x, sr):
    """Play's a numpy array on Linux that represents a wav file with a given
    sample rate.
    """
    return MPlayerWorker(x, sr)


def play(x, sr):
    """Play's a numpy array that represents a wav file with a given sample rate."""
    play_posix(x, sr)


@cache
def download(url):
    """Downloads a URL to a local path. This function is cached
    in order to prevent redownloading the same file. Returns the
    local path downloaded to.
    """
    import requests



@cache
def load(path):
    """Loads a file from a local file or url.
This function is cached
    in order to prevent redownloading the same file, or
re-decoding
    files in certain formats, such as MP3.

    Parameters
    ----------
    path : str
        Filename or URL

    Returns
    -------
    data : ndarray
        Numpy array of WAV data.
    sr : int
        Sampling rate to go with data
    """




class Audio:
    """A container for audio"""

    def __init__(self, data=None, sr=None):
        self.sr = sr
        if data is None:
            self.data = None
        elif isinstance(data, str):
            self.load(data)
        elif isinstance(data, Iterable):
            self.data = data
        else:
            raise ValueError('audio data must be None, str, or iterable; got '
                             + str(type(data)))

    def load(self, filename):
        """Loads audio from a file."""
        self.data, self.sr = librosa.core.load(filename)

    def save(self, filename):
        librosa.output.write_wav(filename, self.data, self.sr, norm=True)


if __name__ == '__main__':
    import sys
    x, sr = librosa.core.load(sys.argv[1])
    play(x, sr)
