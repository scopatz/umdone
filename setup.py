#!/usr/bin/env python
# coding=utf-8
"""The umdone installer."""
import os
import sys
try:
    from setuptools import setup
    from setuptools.command.develop import develop
    HAVE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup
    HAVE_SETUPTOOLS = False

VERSION = "0.1.dev0"


def main():
    with open(os.path.join(os.path.dirname(__file__), 'README.rst'), 'r') as f:
        readme = f.read()
    skw = dict(
        name='umdone',
        description='removes umms from audio files',
        long_description=readme,
        license='BSD',
        version=VERSION,
        author='Anthony Scopatz',
        maintainer='Anthony Scopatz',
        author_email='scopatz@gmail.com',
        url='https://github.com/scopatz/umdone',
        platforms='Cross Platform',
        classifiers=['Programming Language :: Python :: 3'],
        packages=['umdone'],
        package_dir={'umdone': 'umdone'},
        package_data={'umdone': ['*.xsh']},
        scripts=['scripts/umdone'],
        zip_safe=False,
        )
    if HAVE_SETUPTOOLS:
        skw['setup_requires'] = []
        skw['install_requires'] = ['numpy', 'librosa', 'xonsh']
    setup(**skw)


if __name__ == '__main__':
    main()

