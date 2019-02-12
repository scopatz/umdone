"""Transcribes audio using AWS Transcribe"""
import os
import sys
import glob
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio, CLIPS_CACHE_DIR
from umdone.commands import audio_io, data_out



@lazyobject
def PARSER():
    parser = ArgumentParser("aws-transcribe")
    parser.add_argument('bucket', help="AWS bucket to use")
    parser.add_argument(
        "audio_path", help="path to local file or URL.", nargs="?", default=None
    )
    parser.add_argument(
        "--audio-file",
        dest="audio_file",
        default=None,
        help="local file where the audio should be stored",
    )
    parser.add_argument(
        "--transcript-file",
        dest="transcript_file",
        default=None,
        help="local file where the transcript should be stored",
    )
    return parser


@audio_io
@data_out
def main(audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Transcribes the audio using AWS Transcribe"""
    print_color("{YELLOW}Transcribing audio via AWS{NO_COLOR}", file=stderr, flush=True)
    ns = PARSER.parse_args(args)
    # ensure audio
    if audio_in is None and ns.audio_path is not None:
        audio_in = Audio(ns.audio_path)
    print("  - audio in:", audio_in, file=stderr, flush=True)
    print("  - bucket:", ns.bucket, file=stderr, flush=True)
    from umdone.aws_transcribe import transcribe
    transcript_filename = transcribe(audio_in, ns.bucket, filename=ns.audio_file,
                                     transcript_filename=ns.transcript_file)
    print("  - transcript:", transcript_filename, file=stderr, flush=True)
    return audio_in, transcript_filename
