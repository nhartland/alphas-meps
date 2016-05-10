#!/usr/bin/env python
# coding=utf-8
"""
Walks through subdirectories of the current working directory
and start Sherpa processes for all run cards found.
All files with a '.dat' ending are assumed to be run cards.
Hidden directories (starting with '.') will be ignored.
"""

import os
import sys
import math
import argparse

try:
    import lhapdf
    HAS_LHAPDF = True
except ImportError:
    HAS_LHAPDF = False

# prevent cluttering our setup directory with pyc files
sys.dont_write_bytecode = True

import submitprocess

SCALE_VARIATIONS_TAG = 'SCALE_VARIATIONS'
PDF_VARIATIONS_TAG = 'PDF_VARIATIONS'


def main():
    """Entry point if this file is executed as a script."""

    # define and parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("target_path", default=".")
    parser.add_argument("-s", "--sherpa", default='Sherpa',
                        help='Sherpa binary')
    parser.add_argument("-c", "--run-command", default='run_local',
                        help="""Function for submitting jobs, must be defined
                        in submitprocess.py.""")
    parser.add_argument("-m", "--mode", default='all',
                        choices=["integration", "production", "all"])
    parser.add_argument("-a", "--analysis-prefix", default='',
                        help='Prefix for the analysis directory name')
    parser.add_argument("-n", "--random-seed-count", default=1, type=int,
                        help="""The number of random seeds to sample over. Only
                        used in production runs.""")
    parser.add_argument("-o", "--random-seed-offset", default=0, type=int,
                        help="""The first random seed is offset from 1 by this number.
                        Only used in production runs.""")
    sampling_group = parser.add_mutually_exclusive_group()
    sampling_group.add_argument("-p", "--sampling-parameter", default=None,
                                help="""Tag values to sample over in
                                reweighting runs.  E.g. "TAG[0,1,2,3]" will
                                start reweighting runs with TAG:=0, TAG:=1, ...
                                passed to Sherpa with TAG-0, TAG-1, ... used as
                                a suffix for the analysis directory name. Only
                                used in production runs.""")
    sampling_group.add_argument("-P", "--sampling-parameter-all", default=None,
                                help="""Tag values to sample over in
                                reweighting AND dedicated runs.  E.g.
                                "TAG[0,1,2,3]" will start runs with TAG:=0,
                                TAG:=1, ... passed to Sherpa with TAG-0, TAG-1,
                                ... used as a suffix for the analysis directory
                                name. Only used in production runs.""")
    parser.add_argument("-d", "--dedicated-runs-disabled", action="store_true")
    parser.add_argument("-v", "--variation-run-disabled", action="store_true")
    parser.add_argument("-y", "--dry-run", action="store_true")
    args = parser.parse_args()

    # map run_command arg to run_command function
    if args.dry_run:
        run_command = getattr(submitprocess, 'run_dry')
    else:
        run_command = getattr(submitprocess, args.run_command)

    for run_card in get_run_cards(args.target_path):
        process_run_card(run_card, run_command, args)


def process_run_card(run_card, run_command, args):
    """Submits all processes required by mode for run_card based on run_command."""
    print "Processing run card: ", run_card

    # remember where we came from, then walk into MCEG working dir, picking up resources
    previous_dir = os.path.abspath(os.curdir)
    if not os.path.dirname(run_card) == "":
        os.chdir(os.path.dirname(run_card))
    resources = import_resources()
    os.chdir(makedir_for_run_card(run_card))

    # create common command parts
    sherpa_command = [args.sherpa, '-f', '../' + os.path.basename(run_card)]

    if args.mode in ('all', 'integration'):
        # integrate
        name = basename_for_run_card(run_card) + '-prep'
        run_command(sherpa_command + ['-e0'] + ['; ./makelibs &&'] + sherpa_command + ['-e0'],
                    resources['integration'], name=name)

    if args.mode in ('all', 'production'):

        sampling_tag = None
        reweighting_sampling_values = [None]
        dedicated_runs_sampling_values = [None]
        if args.sampling_parameter is not None:
            sampling_tag, reweighting_sampling_values = parse_sampling_argument(args.sampling_parameter)
        elif args.sampling_parameter_all is not None:
            sampling_tag, reweighting_sampling_values = parse_sampling_argument(args.sampling_parameter_all)
            dedicated_runs_sampling_values = reweighting_sampling_values

        for random_seed in range(1 + args.random_seed_offset, args.random_seed_count + 1 + args.random_seed_offset):
            random_seed_args = ['-R', str(random_seed)]

            if args.variation_run_disabled:
                print "No variation runs wanted ..."
            else:
                for sampling_value in reweighting_sampling_values:

                    if sampling_value is not None:
                        sampling_args = [sampling_tag + ':=' + sampling_value]
                        # note that sampling_tag in the analysis path
                        # would be replaced by Sherpa's tag replacement
                        analysis_suffix = '-' + sampling_value
                    else:
                        sampling_args = []
                        analysis_suffix = ''

                    # run central (with on-the-fly variations)
                    name = basename_for_run_card(run_card) + '-prod_rew-seed_' + str(random_seed)
                    analysis_output_args = get_analysis_output_sherpa_arg(args.analysis_prefix,
                                                                          random_seed,
                                                                          'Reweighting',
                                                                          analysis_suffix)
                    run_command(sherpa_command + random_seed_args
                                + analysis_output_args + sampling_args,
                                resources['reweighting'], name=name)

            if args.dedicated_runs_disabled:
                print "No dedicated runs wanted ..."
            else:
                dedicated_sherpa_command = sherpa_command + random_seed_args
                dedicated_sherpa_command += [SCALE_VARIATIONS_TAG + "=None", PDF_VARIATIONS_TAG + "=None"]

                for sampling_value in dedicated_runs_sampling_values:

                    if sampling_value is not None:
                        sampling_args = [sampling_tag + ':=' + sampling_value]
                        # note that sampling_tag in the analysis path
                        # would be replaced by Sherpa's tag replacement
                        analysis_suffix = '-' + sampling_value
                    else:
                        sampling_args = []
                        analysis_suffix = ''

                    scale_vars = parse_scale_variations('../' + os.path.basename(run_card))
                    pdf_vars = parse_pdf_variations('../' + os.path.basename(run_card))
                    print "Will iterate over variations:", scale_vars, pdf_vars

                    # run dedicated scale variations
                    for scale_var in scale_vars:
                        name = (basename_for_run_card(run_card)
                                + '-prod_scale_' + '_'.join([str(sf) for sf in scale_var])
                                + '-seed_' + str(random_seed))
                        run_command(dedicated_sherpa_command + sampling_args +
                                    get_sherpa_args_for_scale_var(scale_var,
                                                                  args.analysis_prefix,
                                                                  analysis_suffix,
                                                                  random_seed),
                                    resources['single'], name=name)

                    # run dedicated PDF variations
                    for pdf_var in pdf_vars:
                        name = (basename_for_run_card(run_card)
                                + '-prod_pdf_' + '.'.join([str(pdf) for pdf in pdf_var])
                                + '-seed_' + str(random_seed))
                        run_command(dedicated_sherpa_command + sampling_args +
                                    get_sherpa_args_for_pdf_var(pdf_var,
                                                                args.analysis_prefix,
                                                                analysis_suffix,
                                                                random_seed),
                                    resources['single'], name=name)

    os.chdir(previous_dir)

def parse_sampling_argument(arg):
    """Return tag name and associated values parsing e.g. TAG[1,2,3]."""
    sampling_tag, rest = arg.split('[')
    sampling_values = [value.strip() for value in rest[:-1].split(',')]
    return sampling_tag, sampling_values

def get_sherpa_args_for_scale_var(scale_var, analysis_prefix, analysis_suffix, random_seed):
    """Returns arguments for the sherpa command for a given scale variation tuple."""
    rsf, fsf = [scale_factor for scale_factor in scale_var]
    scale_factors_args = ['RSF:=' + str(rsf), 'FSF:=' + str(fsf)]
    analysis_output_args = get_analysis_output_sherpa_arg(analysis_prefix, random_seed,
                                                          'Dedicated.MUR' + str(math.sqrt(rsf))
                                                          + '.MUF' + str(math.sqrt(fsf)), analysis_suffix)
    return scale_factors_args + analysis_output_args

def get_sherpa_args_for_pdf_var(pdf_var, analysis_prefix, analysis_suffix, random_seed):
    """Returns arguments for the sherpa command for a given scale variation tuple."""
    pdf = pdf_var[0]
    version = str(pdf_var[1])
    pdf_args = ['PDF_SET=' + pdf, 'PDF_SET_VERSION=' + version,
                'ALPHAS_PDF_SET=' + pdf, 'ALPHAS_PDF_SET_VERSION=' + version]
    analysis_output_args = get_analysis_output_sherpa_arg(analysis_prefix, random_seed,
                                                          'Dedicated.' + pdf + '.' + version, analysis_suffix)
    return pdf_args + analysis_output_args

def get_analysis_output_sherpa_arg(prefix, random_seed, base_name, suffix=''):
    """Combine the arguments to a canonical analysis output path and return the Sherpa args."""
    return ['-A', prefix + 'Analysis/Seed.' + str(random_seed) + suffix + '/' + base_name]

def get_run_cards(dir_or_file):
    """Returns all run cards at dir_or_file."""
    if os.path.isfile(dir_or_file):
        return [dir_or_file]
    found_run_cards = []
    for current_dir, sub_dirs, files in os.walk(dir_or_file):
        for file_name in files:
            basename, extension = os.path.splitext(file_name)
            if not extension == '.dat':
                continue
            # prune subdirectories with the same base name as a run card
            if basename in sub_dirs:
                sub_dirs.remove(basename)
            found_run_cards.append(os.path.join(current_dir, file_name))
        # prune all hidden subdirectories
        for sub_dir in list(sub_dirs):
            if sub_dir[0] == '.':
                sub_dirs.remove(sub_dir)

    return found_run_cards

def import_resources():
    """Returns the resources member from ./resources.py or None if this file does not exist."""
    sys.path.insert(0, os.path.abspath(os.curdir))
    try:
        from resources import resources
        return resources
    except ImportError:
        return {'integration': None, 'single': None, 'reweighting': None}

def makedir_for_run_card(run_card):
    """Makes sure a working dir for run_card exists and returns its name."""
    working_dir_name = basename_for_run_card(run_card)
    try:
        os.makedirs(working_dir_name)
    except OSError:
        pass
    return working_dir_name

def basename_for_run_card(run_card):
    """Return the base name of the path run_card assuming '.dat' as the extension."""
    return os.path.basename(run_card)[:-4]

def parse_scale_variations(file_name):
    """Returns a (FSF, RSF) tuple for each scale variation found in file_name."""
    tuples = []
    variations = parse_parameters(file_name, SCALE_VARIATIONS_TAG)
    for variation in variations:
        ren_sf, fac_sf = [float(sf) for sf in variation.strip(';').split(',')]
        tuples.append([ren_sf, fac_sf])
    return tuples

def parse_pdf_variations(file_name):
    """Returns a (PDF_SET, PDF_SET_VERSION) tuple for each PDF variation found in file_name."""
    tuples = []
    variations = parse_parameters(file_name, PDF_VARIATIONS_TAG)
    for variation in variations:
        all_pos = variation.find('[all]')
        if not all_pos == -1:
            pdf_set = variation[:all_pos]
            for repl in range(1, get_number_of_versions(pdf_set)):
                tuples.append([pdf_set, repl])
            continue
        slash_pos = variation.find('/')
        if not slash_pos == -1:
            pdf_set = variation[:slash_pos]
            pdf_set_version = int(variation[slash_pos + 1:].strip(';'))
            tuples.append([pdf_set, pdf_set_version])
            continue
        print "Could not parse PDF variation:", variation
    return tuples

def get_number_of_versions(pdf_set):
    """Returns the number of versions for pdf_set.
    If lhapdf is not available, the fallback value is 101."""
    if HAS_LHAPDF:
        pdf = lhapdf.mkPDF(pdf_set + '/0')
        return int(pdf.info().get_entry('NumMembers'))
    else:
        return 101

def parse_parameters(file_name, tag):
    """Returns parameters for a given run card tag."""
    with open(file_name) as run_card_contents:
        for line in run_card_contents:
            if line.split('#', 1)[0].strip().find(tag) == 0:
                return line.split()[1:]
    return []

if __name__ == "__main__":
    main()
