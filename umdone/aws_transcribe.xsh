"""Tools for transcribing audio with AWS."""
import os
import sys

from xonsh.tools import print_color

from umdone.tools import cache
from umdone.sound import Audio


def aws_cache_dir():
    return os.path.join($UMDONE_CACHE_DIR, 'aws')


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


@cache
def _transcribe(a, bucket, filename=None):
    a = Audio.from_hash_or_init(a, sr=sr)
    sr = a.sr
    # first upload to S3
    filename, s3file = upload_to_s3(a, bucket, filename=filename)



def transcibe(a, bucket, filename=None):
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
    """
    if isinstance(a, Audio):
        a = a.hash_str()
    out = _transcribe(a, bucket, filename=filename)
