"""Plays and manipulates sound files."""
from __future__ import unicode_literals
import io
import tempfile
import subprocess

import librosa
from scipy.io import wavfile

def array_to_bytes(x, sr):
    """Converts a numpy array to bytes in memory"""
    with io.BytesIO() as f:
        wavfile.write(f, sr, x)
        f.seek(0)
        b = f.read()
    return b


def play_posix(x, sr):
    """Play's a numpy array on Linux that represents a wav file with a given 
    sample rate.
    """
    with tempfile.NamedTemporaryFile() as f:
        librosa.output.write_wav(f.name, x, sr)
        subprocess.check_output(['mplayer', f.name, '&'], stderr=subprocess.STDOUT)


def play(x, sr):
    """Play's a numpy array that represents a wav file with a given sample rate."""
    play_posix(x, sr)


if __name__ == '__main__':
    import sys
    x, sr = librosa.core.load(sys.argv[1])
    play(x, sr)
