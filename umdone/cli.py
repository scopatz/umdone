"""Command-line utilites for umdone"""
from __future__ import print_function, unicode_literals
import os
from argparse import ArgumentParser


def add_input(parser):
    parser.add_argument('input', help='input file')

def add_output(parser):
    parser.add_argument('-o', '--output', dest='output', default=None, 
                        help='Output file.')

def add_train_argument(parser):
    parser.add_argument('train', help='training set databases')

def add_train_option(parser):
    parser.add_argument('-t', '--train', nargs='*', dest='train', 
                        help='list of training files')

def add_window_length(parser):
    parser.add_argument('--window-length', dest='window_length', default=0.05,
                        type=float, help='Word boundary window length.')

def add_noise_threshold(parser):
    parser.add_argument('--noise-threshold', dest='noise_threshold', default=0.01,
                        type=float, help='Noise threshold on words vs quiet.')

def add_n_mfcc(parser):
    parser.add_argument('--n-mfcc', dest='n_mfcc', default=13, type=int, 
                        help='Number of MFCC components.')

def add_match_threshold(parser):
    parser.add_argument('--match-threshold', dest='match_threshold', default=0.45,
                        help='Threshold distance to match words.', type=float)
