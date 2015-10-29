
#!/bin/bash

#PBS -l nodes=1:gpus=1
#PBS -l walltime=0:10:00
#PBS -A jvb-000-ag
#PBS -m bea
#PBS -t [0-2]%3

# Note that the range above includes both the first and last number.
# The %3 sign after is to instruct the scheduler that we want to run
# as much as %3 simultaneous jobs. For our uses, there isn't much
# of a reason to launch anything less since we're not dealing
# with sequential and independent jobs.

"""#PBS -M guillaume.alain.umontreal@gmail.com"""

# Before running this, check out a copy of ImportanceSamplingSGD locally.
# Not sure why again, but it works for the HTTP address and not the SSH address.
# git clone https://github.com/alexmlamb/ImportanceSamplingSGD.git ImportanceSamplingSGD

export IMPORTANCE_SAMPLING_SGD_ROOT:${HOME}/Documents/ImportanceSamplingSGD
export PYTHONPATH=${PYTHONPATH}:${IMPORTANCE_SAMPLING_SGD_ROOT}

# Usually this belongs to the .bash_profile but let's list
# this here as a reminder.
export PYTHONPATH=${PYTHONPATH}:${HOME}/deep-learning-suite/fuel
export PYTHONPATH=${PYTHONPATH}:${HOME}/deep-learning-suite/theano
export PYTHONPATH=${PYTHONPATH}:${HOME}/deep-learning-suite/picklable_itertools
export PYTHONPATH=${PYTHONPATH}:${HOME}/deep-learning-suite/blocks

export IMPORTANCE_SAMPLING_SGD_BIN:${IMPORTANCE_SAMPLING_SGD_ROOT}/integration_distributed_training/bin

export CONFIG_FILE=${IMPORTANCE_SAMPLING_SGD_ROOT}/config_files/config_09232.py

# The config file will contain other information such as the directory in
# which we want to output logs.

# Put garbage in there. It's important that this be a unique file that can
# be reached by all the tasks launched since it's going to be how they
# communicate between themselves initially to share where the database is running,
# what port it's on and what's the password.
export BOOSTRAP_FILE=${IMPORTANCE_SAMPLING_SGD_ROOT}/bootstrap_988412873771


# Note that, from the perspective of a script, the assigned GPU is always gpu0,
# regardless of which one it actually is on the machine (when we have only one assigned).

if [ ${MOAB_JOBARRAYINDEX} = "0" ]
then
    # The job 0 is special because it corresponds to running the database and the master.
    # It puts the database in the background and blocks on the master.
    python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_database.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOSTRAP_FILE} &
    # The whole stdbuf is not necessary, but I left it there because it fixes
    # some of the strange behavior when we try to redirect the output to a file.
    THEANO_FLAGS=device=gpu0,floatX=float32 stdbuf -i0 -o0 -e0 python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_master.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOSTRAP_FILE}
else
    THEANO_FLAGS=device=gpu0,floatX=float32 stdbuf -i0 -o0 -e0 python ${IMPORTANCE_SAMPLING_SGD_BIN}/run_worker.py --config_file=${CONFIG_FILE} --bootstrap_file=${BOOSTRAP_FILE}
fi
