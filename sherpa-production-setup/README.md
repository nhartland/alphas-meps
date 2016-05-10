Requirements: Sherpa revision 26690

Run all setups in this directory (recursively):

    ./run.py -c <submit_command>

Run all setup in a subdirectory (recursively):

    ./run.py -c <submit_command> <sub_directory>

Run a single run card:

    ./run.py -c <submit_command> <path_to_run_card>

`<submit_command>` can be one of the function names defined in
`submitprocess.py`. It it is omitted, `run_local` will be used, which will run
everything on the local machine *synchronously*, so this will probably take a
while!

If you want to work on your cluster, go add your own submit function in
`submitprocess.py`.

If you submit your jobs asynchronously, you might want to do the following:

    ./run.py -c <submit_command> -m integration

And later when the integration runs have succeeded:

    ./run.py -c <submit_command> -m production

Walltimes and memory requirements are read from a `resources.py` file
located in the same directory as the run card. Otherwise, default values
are used.

The walltimes should be good overestimates, but if your cluster is slow, you
might want to scale the walltime which is passed as an argument to your custom
submit function.

