"""Discovery functions."""
import numpy as np
import librosa 

from umdone import dtw

def load_training_data(files, n=13):
    """Returns the MFCCs for list of training data files."""
    mfccs = []
    for f in files:
        x, sr = librosa.load(f, sr=None)
        mfcc = librosa.feature.mfcc(x, sr, n_mfcc=n).T
        mfccs.append(mfcc)
    return mfccs


def is_match(clip_mfcc, training_mfccs, threshold=0.45):
    """Compare an MFCC for a clip to a training dataset via dynamic time 
    warping. Return True if matches any training data, and False otherwise.
    """
    for training_mfcc in training_mfccs:
        cost = dtw.cost_matrix(clip_mfcc, training_mfcc)
        d = dtw.distance(cost=cost)
        norm_d = d / (cost.shape[0] + cost.shape[1])
        if norm_d <= threshold:
            return True
    return False


def match(x, sr, bounds, training_mfccs, threshold=0.45, n=13):
    """Finds the matches to the training data in x that is in valid the bounds.
    Returns the matched bounds.
    """
    matches = []
    for i, (l, u) in enumerate(bounds):
        clip = x[l:u]
        clip_mfcc = librosa.feature.mfcc(clip, sr, n_mfcc=n).T
        if is_match(clip_mfcc, training_mfccs, threshold=threshold):
            matches.append([l, u])
            training_mfccs.append(clip_mfcc)
    return np.array(matches)
