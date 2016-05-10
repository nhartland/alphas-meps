"""
Functions used for running processes.
Add your own function here to submit this setup on your cluster.
You can use the function name as an argument to the run_all.py script.
"""

import subprocess
import math
import os

def run_dry(sherpa_command_parts, resources, name='sherpa'):
    """Do a dry run, i.e. just print Sherpa commands."""
    command = ' '.join(sherpa_command_parts)
    print name, ':', command

def run_local(sherpa_command_parts, resources, name='sherpa'):
    """Synchronously run command in local processes."""
    command = ' '.join(sherpa_command_parts)
    print name, ':', command
    # enable shell parsing such that chaining commands works
    subprocess.call(command, shell=True)

def run_rocks(sherpa_command_parts, resources, name='sherpa'):
    """Asynchronously run command at the PBS of the Goettingen rocks cluster.

    Queues (automatically assigned based on walltime):

    - express     walltime <= 01:00:00
    - shorttime   walltime <= 24:00:00
    - elong       walltime <= 96:00:00
    - longtime    walltime <= 672:00:00
    """

    # Make sure we have directories for standard and error output
    logs_dir = 'PBS_Logs'
    try:
        os.makedirs(logs_dir)
    except OSError:
        pass
    errors_dir = 'PBS_Errors'
    try:
        os.makedirs(errors_dir)
    except OSError:
        pass

    if resources is None:
        hours = 1
        minutes = 0
        mem = 2
        nodes = 1
    else:
        hours = int(math.floor(resources['walltime'] / 60))
        minutes = int(math.ceil(resources['walltime'] % 60))
        mem = int(resources['mem'])
        try:
            nodes = resources['nodes']
        except KeyError:
            nodes = 1

    if not nodes == 1:
        resource_spec = ':MPI-TCP'
    else:
        resource_spec = ':ppn=1'
        # resource_spec = ':X5355'
        # resource_spec = ':E5440'

    mail = 'enrico.bothmann@phys.uni-goettingen.de'

    # final command looks like `echo 'cd $PBS_O_WORKDIR && Sherpa <args>' | qsub <args> -`

    # build everything left from `|`, first replace Sherpa command
    command_parts = ['echo', '\'cd $PBS_O_WORKDIR', '&&']
    if not nodes == 1:
        command_parts.append('MPI_OPT="--hostfile $PBS_NODEFILE --np $(cat $PBS_NODEFILE|wc -l)"')
        command_parts.append('&& export OMP_NUM_THREADS=1')
        command_parts.append('&& mpirun $MPI_OPT -x OMP_NUM_THREADS')
    command_parts.extend(sherpa_command_parts + ['\''])

    # build everything right from `|`
    qsub_command_parts = ["qsub"]
    qsub_command_parts.extend(["-o", logs_dir])
    qsub_command_parts.extend(["-e", errors_dir])
    qsub_command_parts.extend(["-N", name])
    qsub_command_parts.extend(["-M", mail])
    qsub_command_parts.extend(["-l", "nodes=" + str(nodes) + resource_spec])
    qsub_command_parts.extend(["-l", "walltime={:02d}:{:02d}:00".format(hours, minutes)])
    qsub_command_parts.extend(["-l", "mem={0:d}gb,vmem={0:d}gb".format(mem)])
    qsub_command_parts.append("-")

    # build complete command line and submit
    command = '{0} | {1}'.format(' '.join(command_parts), ' '.join(qsub_command_parts))
    print name, ':', command
    # subprocess.call(command, shell=True)  # enable shell parsing such that the pipe works
    # this will return immediately, make sure integration results are available before production


def run_scc(sherpa_command_parts, resources, name='sherpa'):
    """Asynchronously run command at the LSF of the Goettingen Scientific Compute Cluster.

    Queue variants

    - mpi         walltime <= 48:00:00, nodes <= 1024
    - -long       walltime <= 120:00:00 (longer waiting times)
    - -short      walltime <= 2:00:00   (minimal waiting times, but limited job slots)
    """

    # Make sure we have directories for standard and error output
    logs_dir = 'LSF_Logs'
    try:
        os.makedirs(logs_dir)
    except OSError:
        pass
    log_path = os.path.join(logs_dir, '%J.out')

    if resources is None:
        hours = 1
        minutes = 0
        mem = 2
        nodes = 1
    else:
        hours = int(math.floor(resources['walltime'] / 60))
        minutes = int(math.ceil(resources['walltime'] % 60))
        mem = int(resources['mem'])
        try:
            nodes = resources['nodes']
        except KeyError:
            nodes = 1
    use_mpi = (not nodes == 1)

    # final command looks like `bsub <bsub options> [mpirun.lsf] Sherpa <args>'

    # build cluster-specific part of the command
    bsub_command_parts = ["bsub"]
    bsub_command_parts.extend(["-q", "mpi"])
    bsub_command_parts.extend(["-W", "{:02d}:{:02d}".format(hours, minutes)])
    bsub_command_parts.extend(["-o", log_path])
    bsub_command_parts.extend(["-n", str(nodes)])
    if use_mpi:
        bsub_command_parts.extend(["-a", 'openmpi'])
        bsub_command_parts.append("mpirun.lsf")

    # build complete command line and submit
    command = ' '.join(bsub_command_parts + sherpa_command_parts)
    print name, ':', command
    # subprocess.call(command, shell=True)  # enable shell parsing such that the pipe works
    # this will return immediately, make sure integration results are available before production

