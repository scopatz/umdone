"""Filters out undesirable words in audio from the AWS Transcribe data."""
import os
import sys
import glob
from argparse import ArgumentParser

from lazyasd import lazyobject

from xonsh.tools import print_color

from umdone.sound import Audio, CLIPS_CACHE_DIR
from umdone.commands import audio_io, data_in



@lazyobject
def PARSER():
    parser = ArgumentParser("aws-filter-words")
    parser.add_argument(
        "audio_path", help="path to local file or URL.", nargs="?", default=None
    )
    parser.add_argument(
        "transcript_file", help="path to local file or URL.", nargs="?", default=None
    )
    return parser


@audio_io
@data_in
def main(transcript_file, audio_in, args, stdin=None, stdout=None, stderr=None, spec=None):
    """Filters out undesirable words in audio from the AWS Transcribe data."""
    print_color("{YELLOW}Filtering out words via the AWS Transcribe data{NO_COLOR}", file=stderr, flush=True)
    ns = PARSER.parse_args(args)
    # ensure audio
    if audio_in is None and ns.audio_path is not None:
        audio_in = Audio(ns.audio_path)
    # ensure transciption
    if transcript_file is None and ns.transcript_file is not None:
        transcript_file = ns.transcript_file
    print("  - audio in:", audio_in, file=stderr, flush=True)
    print("  - transcript file:", transcript_file, file=stderr, flush=True)
    from umdone.aws_transcribe import filter_words
    audio_out = filter_words(audio_in, transcript_file)
    print("  - audio out:", audio_out, file=stderr, flush=True)
    return audio_out
