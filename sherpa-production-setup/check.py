#!/usr/bin/env python
# coding=utf-8
"""
Check if all YODA files found in sub directories of the passed Analysis
directory are actually there and whether they have the expected event count.

Examples:
    ./check.py 1-100 0,1,-1 500k
    ./check.py 1-100 500k
"""

import os
import sys

import yoda

from merge import get_files


def main():
    # define what is expected
    uses_tag_values = len(sys.argv) == 4
    seeds = parse_seed_argument(sys.argv[1])
    if uses_tag_values:
        tag_values = parse_tag_values_argument(sys.argv[2])
        event_count = parse_event_count_argument(sys.argv[3])
    else:
        event_count = parse_event_count_argument(sys.argv[2])
    event_count_tolerance = event_count / 1000  # per-mille deviations are okay
    print "Will test whether we deviate more than", event_count_tolerance, "from", event_count, "..."

    # expected yodafiles will be determined from the first directory being
    # inspected
    expected_yodafiles = None

    if uses_tag_values:
        directories = ['Seed.' + str(seed) + '-' + tag
                       for seed, tag in zip(seeds, tag_values)]
    else:
        directories = ['Seed.' + str(seed) for seed in seeds]

    for directory in directories:

        if not os.path.exists(directory):
            print "Missing directory:", directory
            continue

        yodafiles = set(get_files(directory, 'yoda'))

        if expected_yodafiles is None:
            expected_yodafiles = yodafiles
        else:
            if not yodafiles == expected_yodafiles:
                print "Missing files in " + directory + ":", expected_yodafiles - yodafiles

        for yodafile in yodafiles:
            filepath = os.path.join(directory, yodafile)
            histos = yoda.readYODA(filepath)
            count = int(histos['/MC_XS/N'].numEntries())
            if abs(count - event_count) > event_count_tolerance:
                print filepath, "has wrong statistics: ", count


def parse_seed_argument(arg):
    first, last = [int(i) for i in arg.split('-')]
    print "Will look for seeds from", str(first), "to", str(last), "..."
    return xrange(first, last + 1)


def parse_tag_values_argument(arg):
    tag_values = arg.split(',')
    print "Will look for the following tag values:", tag_values, "..."
    return tag_values


def parse_event_count_argument(arg):
    return int(arg[:-1]) * 1000


if __name__ == "__main__":
    main()
