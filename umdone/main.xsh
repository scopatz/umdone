"""Main functionality for umdone."""
import os
import builtins
from argparse import ArgumentParser

from xonsh.tools import swap_values
from xonsh.codecache import run_script_with_cache, run_code_with_cache

import umdone
from umdone.commands import swap_aliases


def run(file=None, command=None):
    execer = builtins.__xonsh__.execer
    if file is not None:
        # run a script contained in a file
        path = os.path.abspath(os.path.expanduser(file))
        mode = 'exec'
        if os.path.isfile(path):
            with open(path, 'r') as f:
                src = f.read()
            if not src.endswith('\n'):
                src += '\n'
        else:
            print("umdone: {0}: No such file or directory.".format(file))
            return
    elif command is not None:
        path = '<script>'
        mode = 'single'
        src = command
    else:
        raise RuntimeError('Either a script file or a command (-c) must be given')
    updates = {"__file__": path, "__name__": "__main__"}
    with ${...}.swap(XONSH_SOURCE=path), swap_values(builtins.__xonsh__.ctx, updates):
        execer.exec(src, mode=mode, glbs=builtins.__xonsh__.ctx, filename=path)


def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone', add_help=False)
    parser.add_argument(
        "-h",
        "--help",
        dest="help",
        action="store_true",
        default=False,
        help="show help and exit",
    )
    parser.add_argument(
        "-V",
        "--version",
        dest="version",
        action="store_true",
        default=False,
        help="show version information and exit",
    )
    parser.add_argument(
        "-D",
        dest="defines",
        help="define an environment variable, in the form of "
        "-DNAME=VAL. May be used many times.",
        metavar="ITEM",
        action="append",
        default=None,
    )
    parser.add_argument(
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
    if ns.help:
        parser.print_help()
        parser.exit()
    if ns.version:
        version = "/".join(("umdone", umdone.__version__))
        print(version)
        parser.exit()
    defs = {} if ns.defines is None else [x.split("=", 1) for x in ns.defines]

    # execute the commands
    with ${...}.swap(defs), swap_aliases():
        run(file=ns.file, command=ns.command)


if __name__ == '__main__':
    main()