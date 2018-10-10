"""Plays and manipulates sound files."""
from __future__ import unicode_literals
import io
import os
import sys
import tempfile
import subprocess
from threading import Thread
from collections.abc import Iterable, MutableMapping

import numpy as np

import joblib

import librosa
import librosa.core
import librosa.output
from scipy.io import wavfile

from xonsh.tools import print_color

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
    outfile = os.path.join($UMDONE_CAHE_DIR, os.path.basename(url))
    print_color('Downloading {YELLOW}' + url + '{NO_COLOR} to {GREEN}' + outfile
                + '{NO_COLOR}...', file=sys.stderr)
    r = requests.get(url)
    with open(outfile, 'wb') as f:
        f.write(r.content)
    return outfile


@cache
def load(path):
    """Loads a file from a local file or url. This function is cached in order
    to prevent re-decoding files in certain formats, such as MP3.

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
    if path.startswith('http'):
        path = download(path)
    data, sr = librosa.core.load(path)
    return data, sr


class Audio:
    """A container for audio"""

    def __init__(self, data=None, sr=None):
        self._sr = sr
        self._data = None
        self._hash = None
        if data is None:
            pass
        elif isinstance(data, str):
            if data.startswith('hash:'):
                cached = AUDIO_CACHE[data[5:]]
                self._data, self._sr = cached.data, cached.sr
            else:
                self.load(data)
        elif isinstance(data, Iterable):
            self._data = data
        else:
            raise ValueError('audio data must be None, str, or iterable; got '
                             + str(type(data)))

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if self._data is None or self._sr is None:
            self._data = value
        else:
            raise RuntimeError('cannot set audio data once it has been set.')

    @property
    def sr(self):
        return self._sr

    @sr.setter
    def sr(self, value):
        if self._data is None or self._sr is None:
            self._sr = value
        else:
            raise RuntimeError('cannot set audio sample rate once it has been set.')

    @classmethod
    def from_hash(cls, h):
        if h.startswith('hash:'):
            h = h[5:]
        return AUDIO_CACHE[h]

    @classmethod
    def from_hash_or_init(cls, data=None, sr=None):
        if isinstance(data, str):
            if data.startswith('hash:') or data in AUDIO_CACHE:
                return cls.from_hash(data)
            else:
                return cls(data=data, sr=sr)
        else:
            return cls(data=data, sr=sr)

    def __repr__(self):
        if isinstance(self.data, np.ndarray) and isinstance(self.sr, int):
            self.ensure_in_cache()
            return "Audio.from_hash(" + repr(self.hash()) + ")"
        else:
            return f"Audio(data={self.data!r}, sr={self.sr!r})"

    def load(self, filename):
        """Loads audio from a file or URL."""
        self.data, self.sr = load(filename)

    def save(self, filename):
        librosa.output.write_wav(filename, self.data, self.sr, norm=True)

    def hash(self):
        if self._hash is None:
            self._hash = joblib.hash((self.data, self.sr),
                                     hash_name='md5')
        return self._hash

    def hash_str(self):
        """Returns the hash string"""
        self.ensure_in_cache()
        return 'hash:' + self.hash()

    def ensure_in_cache(self):
        """Makes sure this audio is in the cache"""
        if self.hash() not in AUDIO_CACHE:
            AUDIO_CACHE[self.hash()] = self


class AudioCache(MutableMapping):

    def __init__(self, location):
        self.cachedir = os.path.join(location, 'audio-cache')
        os.makedirs(self.cachedir, exist_ok=True)
        self.d = {}

    def _filename(self, key):
        return os.path.join(self.cachedir, key + '.bz2')

    def __getitem__(self, key):
        if key in self.d:
            return self.d[key]
        filename = self._filename(key)
        if os.path.isfile(filename):
            value = joblib.load(filename)
            value._hash = key
            self.d[key] = value
            return value
        raise KeyError(f"Could not find {key} in-memory or on disk")

    def __setitem__(self, key, value):
        self.d[key] = value
        filename = self._filename(key)
        if os.path.isfile(filename):
            return
        joblib.dump(value, filename, compress=1)

    def __delitem__(self, key):
        del self.d[key]

    def __len__(self):
        return len(self.d)

    def __iter__(self):
        yield from self.d

    def __contains__(self, key):
        return key in self.d or os.path.isfile(self._filename(key))


AUDIO_CACHE = AudioCache(location=$UMDONE_CACHE_DIR)


if __name__ == '__main__':
    import sys
    x, sr = load(sys.argv[1])
    play(x, sr)
