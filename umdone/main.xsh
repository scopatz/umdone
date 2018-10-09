"""Main functionality for umdone."""
import os
import builtins
from argparse import ArgumentParser

from xonsh.codecache import run_script_with_cache, run_code_with_cache

import umdone
from umdone.commands import swap_aliases


def run(file=None, command=None):
    shell = builtins.__xonsh__.shell
    if file is not None:
        # run a script contained in a file
        path = os.path.abspath(os.path.expanduser(file))
        if os.path.isfile(path):
            $XONSH_SOURCE = path
            shell.ctx.update({"__file__": file, "__name__": "__main__"})
            run_script_with_cache(
                file, shell.execer, glb=shell.ctx, loc=None, mode="exec"
            )
        else:
            print("umdone: {0}: No such file or directory.".format(file))
    elif command is not None:
        run_code_with_cache(command.lstrip(), shell.execer, mode="single")
    else:
        raise RuntimeError('Either a script file or a command (-c) must be given')


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