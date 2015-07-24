"""Main functionality for umdone."""
from argparse import ArgumentParser


def main(args=None):
    """Main umdone entry point."""
    parser = ArgumentParser('umdone')
    ns = parser.parse_args(args)


if __name__ == '__main__':
    main()