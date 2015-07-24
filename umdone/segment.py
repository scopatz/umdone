"""Segements long audio into clips when someone is speaking."""
import numpy as np


def boundaries(x, sr, window_length=0.05, threshold=0.01):
    """Computes the indexes of a wav between which some one is speaking, ie
    there is meaningful sound other than noise.

    Parameters
    ----------
    x : ndarray
        wav data
    sr : int
        Sample rate
    window_length : num, optional
        The length of the boundary windowing in seconds [s].
    threshold : float
        The noise threshold, below which a window is considered noise and above
        which the window is considered valuable sound.

    Returns
    -------
    bounds : ndarray
        N x 2 array of indexes of wav where there is sound above the threshold level.
    """
    window_size = int(sr * window_length)
    # y = window x
    y = x[:-(len(x)%window_size)]
    y.shape = (len(y)//window_size), window_size
    rms = np.sqrt((y**2).sum(axis=1)/window_size)  # RMS of each window
    idx = np.argwhere(rms > 0.01).flat  # fancy index of window boundaries
    window_bounds = np.argwhere((idx[1:] - idx[:-1]) > 1).flatten()
    window_lower = idx[window_bounds + 1]
    window_upper = idx[window_bounds]
    bounds = np.array([window_lower[:-1], window_upper[1:]]).T * window_size
    return bounds


def remove_slices(arr, slices):
    """Removes slices from an array. Assumes that slices are sorted."""
    if len(slices) == 0:
        return arr
    elif len(slices) == 1:
        return np.concatenate([arr[:slices[0][0]], arr[slices[0][1]:]])
    else:
        views = [arr[:slices[0][0]]]
        for (_, l), (u, _) in zip(slices[:-1], slices[1:]):
            views.append(arr[l:u])
        #views.append(arr[slices[-1][1]:])
        return np.concatenate(views)

