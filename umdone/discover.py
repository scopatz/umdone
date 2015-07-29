"""Discovery functions."""
import numpy as np
import librosa 
from sklearn import svm

from umdone import dtw


def match(x, sr, bounds, mfccs, distances, categories):
    """Finds the matches to the training data in x that is in valid the bounds.
    Returns the matched bounds.
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
    matches = bounds[results > 0]
    return matches

