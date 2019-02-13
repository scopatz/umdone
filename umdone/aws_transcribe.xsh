"""Tools for transcribing audio with AWS."""
import os
import sys
import json
import time
import uuid

import numpy as np

from xonsh.tools import print_color

from umdone.tools import cache
from umdone.sound import Audio
from umdone.basic_filters import remove_marked_clips


def aws_cache_dir():
    d = os.path.join($UMDONE_CACHE_DIR, 'aws')
    os.makedirs(d, exist_ok=True)
    return d


def upload_to_s3(a, bucket, filename=None):
    """Uploads an Audio file to an S3 bucket. If filename is None, it is
    chosen automatically to be in the $UMDONE_CACHE_DIR/aws/ dir.
    This function returns a (filename, S3 URL) tuple.
    """
    if filename is None:
        filename = os.path.join(aws_cache_dir(), a.hash() + '.flac')
    basename = os.path.basename(filename)
    print_color('  - saving {GREEN}' + str(a) + '{NO_COLOR} to file {CYAN}' +
                filename + '{NO_COLOR}', file=sys.stderr)
    a.save(filename)
    s3url = 's3://' + bucket + '/' + basename
    print_color('  - uploading {CYAN}' + filename + '{NO_COLOR} to {YELLOW}' +
                s3url + '{NO_COLOR}', file=sys.stderr)
    ![aws s3 cp @(filename) @(s3url)]
    print_color('    ...done! 🎉', file=sys.stderr)
    return filename, s3url


def _get_job_info(name):
    payload = json.loads($(aws transcribe get-transcription-job --transcription-job-name @(name)))
    info = payload["TranscriptionJob"]
    status = info.get("TranscriptionJobStatus", "IN_PROGRESS")
    done = status != "IN_PROGRESS"
    return done, status, info


@cache
def _transcribe(a, bucket, sr=None, filename=None, transcript_filename=None):
    a = Audio.from_hash_or_init(a, sr=sr)
    sr = a.sr
    # first upload to S3
    filename, s3file = upload_to_s3(a, bucket, filename=filename)
    # now, create a transcription job
    job_name = a.hash() + '-' + str(uuid.uuid4())
    job = {
        "TranscriptionJobName": job_name,
        "LanguageCode": "en-US",
        "MediaSampleRateHertz": sr,
        "MediaFormat": os.path.splitext(filename)[1][1:],
        "Media": {"MediaFileUri": s3file},
        "OutputBucketName": bucket,
        "Settings": {
            "ShowSpeakerLabels": False,
            "ChannelIdentification": False
        }
    }
    job_json = json.dumps(job)
    ![aws transcribe start-transcription-job --cli-input-json @(job_json)]
    # now wait for the job to be done.
    t0 = time.monotonic()
    job_is_done = False
    while not job_is_done:
        current = time.monotonic()
        print('\rwaiting for transcription: {:>4.6} s'.format(current - t0),
              flush=True, end='')
        time.sleep(1.0)
        job_is_done, status, info = _get_job_info(job_name)
    print()
    # check the job status
    if status == "COMPLETED":
        pass
    elif status == "FAILED":
        msg = "Transcription failed with the following message:\n\n"
        msg += info.get("FailureReason", "<no message given>")
        raise RuntimeError(msg)
    else:
        msg = "Transcription failed for unknown reason. Here is what I do know:\n\n"
        msg += str(info)
        raise RuntimeError(msg)
    # get the transcript
    transcript_basename = os.path.basename(info["Transcript"]["TranscriptFileUri"])
    transcript_url = 's3://' + bucket + '/' + transcript_basename
    if transcript_filename is None:
        transcript_filename = os.path.join(aws_cache_dir(), transcript_basename)
    else:
        transcript_dir = os.path.dirname(transcript_filename)
        os.makedirs(transcript_dir, exist_ok=True)
    print_color('  - downloading transcript {GREEN}' + transcript_url + '{NO_COLOR} to {CYAN}' +
                transcript_filename + '{NO_COLOR}', file=sys.stderr)
    ![aws s3 cp @(transcript_url) @(transcript_filename)]
    return transcript_filename


def transcribe(a, bucket, filename=None, transcript_filename=None):
    """Uses AWS to transcribe an Audio instance.

    Parameters
    ----------
    a : str or Audio
        Input audio. If this is a string, it will be read in from
        a file. If this is an Audio instance, it will be used directly.
    bucket : str
        The name of the bucket to save Audio and transcriptions to.
    filename : str or None, optional
        The filename locally to save this audio to. The basename of this
        filename will be the name of the file stored in the bucket.
    transcript_filename : str or None, optional
        The filename locally to save this transcript to.

    Returns
    -------
    transcript_filename : str
        The path to the transcript file.
    """
    if isinstance(a, Audio):
        a = a.hash_str()
    transcript_filename = _transcribe(a, bucket, filename=filename,
                                      transcript_filename=transcript_filename)
    return transcript_filename


DEFAULT_FILTER_WORDS = frozenset([
    "Uh",
    "Um",
    "Ah",
    "Er",
    "Hm",
    "Hmm",
    "Mhm",
    "Uhm",
])


def _expand_words(words):
    expanded = set(words)
    expanded.update(map(str.upper, words))
    expanded.update(map(str.lower, words))
    punctuation = ".,;\"'!?"
    for p in punctuation:
        expanded.update(p + w for w in words)
        expanded.update(w + p for w in words)
        expanded.update(p + w + p for w in words)
    return expanded


@cache
def _filter_words(a, transcript_filename, sr=None, words=None):
    # set up data
    a = Audio.from_hash_or_init(a, sr=sr)
    sr = a.sr
    words = DEFAULT_FILTER_WORDS if words is None else words
    words = _expand_words(words)
    with open(transcript_filename) as f:
        transcript = json.load(f)
    items = transcript['results']['items']
    items = [item for item in items if item['type'] == "pronunciation"]
    # make clip bounds and mask
    bounds = np.empty((len(items), 2), dtype='int64')
    mask = np.empty(len(items), dtype=bool)
    for i, item in enumerate(items):
        bounds[i] = (float(item['start_time']) * sr, float(item['end_time']) * sr)
        word = item['alternatives'][0]['content']
        mask[i] = word not in words
    # now remove the marked parts
    b = remove_marked_clips(a, bounds=bounds, mask=mask)
    return b


def filter_words(a, transcript_filename, words=None):
    """Uses AWS Transcripts to filter out a list of words from audio.

    Parameters
    ----------
    a : str or Audio
        Input audio. If this is a string, it will be read in from
        a file. If this is an Audio instance, it will be used directly.
    transcript_filename : str or None, optional
        The filename locally to save this transcript to.
    words : Iterable of str, optional
        A collection of words to remove from the audio. This listing will be
        normalized by case and punctuation. If None, Ums and Ahs will be removed.

    Returns
    -------
    b : Audio
        The path to the transcript file.
    """
    if isinstance(a, Audio):
        a = a.hash_str()
    b = _filter_words(a, transcript_filename, words=words)
    return b
