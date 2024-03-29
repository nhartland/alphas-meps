#!/usr/bin/env python
# coding=utf-8
"""
Merges YODA files found in sub directories of the passed Analysis directory
generated by run.py.

This script is aware of the -p option of run.py and merges only YODA files
with the same tag value.

Merged YODA files will be written to the passed directory.
"""

import os
import sys
import re
import argparse
import numpy as np

# prevent cluttering our setup directory with pyc files
sys.dont_write_bytecode = True

import submitprocess


def main():
    """Entry point if this file is executed as a script."""
    # define CLI
    parser = argparse.ArgumentParser()
    parser.add_argument("target_path", default=".")
    parser.add_argument("-p", "--sampling-parameter", default=None)
    parser.add_argument("-c", "--run-command", default='run_local')
    parser.add_argument("-n", "--max-seed-number", default=0, type=int)
    parser.add_argument("-b", "--directory-basename", default='Seed')
    args = parser.parse_args()

    # post-process command line arguments
    if args.sampling_parameter is not None:
        prompted_tag_values = set(args.sampling_parameter.split(','))
    else:
        prompted_tag_values = None
    run_command = getattr(submitprocess, args.run_command)

    # get some random subdir, this might be of the form "Seed.n" or "Seed.n-m"
    # (where m might even be -1)
    regex_prefix = '^{}.'.format(args.directory_basename)
    first_seed_subdir = get_immediate_subdirectories(args.target_path, regex=regex_prefix)[0]
    first_seed = first_seed_subdir.split('-')[0].split('.')[-1]

    # get values for m that have been used and filter those if we an explicit request
    first_seed_subdirs = get_immediate_subdirectories(args.target_path, regex=regex_prefix + first_seed + '(-[-0-9]+)?$')
    tag_values = set([''.join(subdir.split('-', 1)[1:]) for subdir in first_seed_subdirs])
    if prompted_tag_values is not None:
        tag_values = tag_values & prompted_tag_values  # use union of sets

    # merge entries within directories that share the same tag
    for tag_value in tag_values:
        # collect directories
        dir_suffix = '' if tag_value == '' else '-' + tag_value
        tag_value_subdirs = get_immediate_subdirectories(args.target_path, regex=regex_prefix + '\d+' + dir_suffix + '$')
        # process all directories at once if not otherwise specified, otherwise do subsamples
        max_seed_number = len(tag_value_subdirs) if args.max_seed_number <= 1 else args.max_seed_number 
        if len(tag_value_subdirs) % max_seed_number != 0:
            raise Exception("Number of seeds not a multiple of {}".format(max_seed_number))
        # merge each subsample
        number_of_subsamples = len(tag_value_subdirs) / max_seed_number
        for subsample in xrange(number_of_subsamples):
            tag_value_subdirs_sample = tag_value_subdirs[subsample * max_seed_number:(subsample + 1) * max_seed_number]
            targetdir = "Combined.{}{}".format(subsample + 1, dir_suffix) if number_of_subsamples > 1 else None
            file_suffix = '' if number_of_subsamples > 1 else dir_suffix
            combine_files(args.target_path, tag_value_subdirs_sample, file_suffix, 'yoda', combine_yodas, run_command, targetdir)
            combine_files(args.target_path, tag_value_subdirs_sample, file_suffix, 'dat', combine_dats, run_command, targetdir)


def combine_files(rootdir, subdirs, suffix, extension, combiner, run_command, targetdir=None):
    if targetdir is not None:
        targetdir = os.path.join(rootdir, targetdir)
        try:
            os.mkdir(targetdir)
        except OSError:
            pass
    else:
        targetdir = rootdir
    for file_name in get_files(subdirs[0], extension):
        input_paths = [os.path.join(subdir, file_name) for subdir in subdirs]
        output_path = os.path.join(targetdir, os.path.splitext(file_name)[0]
                                   + suffix + os.path.splitext(file_name)[1])
        combiner(input_paths, output_path, run_command)


def combine_yodas(input_paths, output_path, run_command):
    command_parts = ['yodamerge', '-o', output_path] + input_paths
    run_command(command_parts, resources={'walltime': 10, 'mem': 1}, name="yodamerge")


def combine_dats(input_paths, output_path, run_command):
    combined = None
    ycols = None
    header = None
    try:
        for input_path in input_paths:
            histo = np.loadtxt(input_path)
            if combined is None:
                combined = histo
                ycols = dat_ycolumns(input_path)
                header = dat_header(input_path)
            else:
                # add all columns in the right oder (except for the first one)
                for histo_idx, col in enumerate(dat_ycolumns(input_path)):
                    combined_idx = ycols.index(col)
                    combined[:, combined_idx + 1] += histo[:, histo_idx + 1]
    except IOError:
        print "Can not combine", output_path
        return
    np.savetxt(output_path, combined, header=header)


def dat_ycolumns(path):
    return dat_header(path).split()[1:]


def dat_header(path):
    header = ''
    with open(path) as f:
        header = f.readline()[1:].strip()
    return header


def get_immediate_subdirectories(a_dir, begin='', end='', regex=None):
    """Return list of a_dir's immediate subdirectories."""
    if regex is not None:
        p = re.compile(regex)
    else:
        p = re.compile('')
    return [os.path.join(a_dir, name) for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))
            and name[:len(begin)] == begin
            and name[len(name) - len(end):] == end
            and p.match(name) is not None]


def get_files(a_dir, extension):
    """Return list of YODA files located in a_dir."""
    return [name for name in os.listdir(a_dir)
            if os.path.isfile(os.path.join(a_dir, name)) and name[-len(extension)-1:].lower() == '.' + extension]

if __name__ == "__main__":
    main()
