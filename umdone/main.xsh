"""Main functionality for umdone."""
import os
from argparse import ArgumentParser

import umdone


def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone')
    p.add_argument(
        "-h",
        "--help",
        dest="help",
        action="store_true",
        default=False,
        help="show help and exit",
    )
    p.add_argument(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="show version information and exit",
    )
    p.add_argument(
        "-D",
        dest="defines",
        help="define an environment variable, in the form of "
        "-DNAME=VAL. May be used many times.",
        metavar="ITEM",
        action="append",
        default=None,
    )
    p.add_argument(
        "-c",
        help="Run a single command and exit",
        dest="command",
        required=False,
        default=None,
    )
    parser.add_argument(
        "file",
        metavar="script-file",
        help="If present, execute the script in script-file" " and exit",
        nargs="?",
        default=None,
    )

    # parse the commands
    ns = parser.parse_args(args)

    # execute the commands
    if ns.help:
        parser.print_help()
        parser.exit()
    if ns.version:
        version = "/".join(("umdone", umdone.__version__))
        print(version)
        parser.exit()
    if ns.defines is not None:
        ${...}.update([x.split("=", 1) for x in ns.defines])


if __name__ == '__main__':
    main()