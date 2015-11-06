
import redis
import numpy as np
import json
import time
import numpy as np

import sys, os
import getopt

import signal
import sys

import hashlib

from startup import delete_bootstrap_file
from common import get_mean_variance_measurement_on_database

def configure(  rsconn,
                workers_minibatch_size, master_minibatch_size,
                dataset_name,
                Ntrain, Nvalid, Ntest,
                L_measurements,
                L_segments,
                want_only_indices_for_master=True,
                want_exclude_partial_minibatch=True,
                default_importance_weight=0.0,
                **kwargs):

    # `workers_minibatch_size` is an int describing how large are the minibatches for the workers.
    # `master_minibatch_size` is an int describing how large are the minibatches for the master.
    # `dataset_name` is a string that is somewhat useless, but is still a good idea to include in the config.
    # `Ntrain` is the total number of training examples (to be split into minibatches).
    # `Nvalid` is the total number of validation examples (to be split into minibatches).
    # `Ntest`  is the total number of test examples (to be split into minibatches).
    # `L_measurements` is a list of quantities computed for each example.
    # `L_segments` is a list of ['train', 'valid', 'test'].
    # `want_only_indices_for_master` determines whether the master will be given arrays of indices or minibatch data directly.
    # `want_exclude_partial_minibatch` indicates if we want to forget about the data that doesn't fit in a complete minibatch.

    # We will use **dataset_config to specify all the arguments of this function.
    # For that reason, we need to have the extra **kwargs to eat up whatever is left.

    rsconn.delete("initialization_is_done")

    def get_next_timestamp():
        get_next_timestamp.counter += 1.0
        return np.float64(get_next_timestamp.counter)
    get_next_timestamp.counter = 0.0

    def timestamp_to_str(timestamp):
        return np.float64(timestamp).tostring()
    def timestamp_from_str(timestamp_str):
        return np.fromstring(timestamp_str, dtype=np.float64)

    # "parameters:current" will contain a numpy float32 array
    # represented efficiently as a string (max 128MB, potential scaling problems)
    rsconn.set("parameters:current", "")
    rsconn.set("parameters:current_timestamp", timestamp_to_str(0.0))
    # potentially not used
    rsconn.set("parameters:current_datestamp", time.strftime("%Y-%m-%d %H:%M:%S"))

    for segment in L_segments:

        # That's a bit of a hacky way to specify Ntrain/Nvalid/Ntest.
        N = {'train':Ntrain, 'valid':Nvalid, 'test':Ntest}[segment]

        rsconn.delete("L_workers_%s_minibatch_indices_QUEUE" % segment)
        rsconn.delete("L_workers_%s_minibatch_indices_ALL" % segment)

        for lower_index in range(0, N+1, workers_minibatch_size):

            if N <= lower_index:
                continue

            # The data points corresponding to `upper_index` are NOT to be included.
            upper_index = np.min([lower_index + workers_minibatch_size, N])

            if want_exclude_partial_minibatch and (upper_index - lower_index < workers_minibatch_size):
                continue

            assert upper_index - lower_index <= workers_minibatch_size

            A_indices = np.arange(lower_index, upper_index, dtype=np.int32)
            A_indices_str = A_indices.tostring()

            print "len(A_indices_str) : %d. Start with %d. Hash : %s." % (len(A_indices_str), A_indices[0], hashlib.sha224(A_indices_str).hexdigest())


            rsconn.rpush("L_workers_%s_minibatch_indices_QUEUE" % segment, A_indices_str)
            rsconn.rpush("L_workers_%s_minibatch_indices_ALL" % segment, A_indices_str)

            for measurement in L_measurements:
                rsconn.hset("H_%s_minibatch_%s" % (segment, measurement), A_indices_str, (np.float32(default_importance_weight) * np.ones(A_indices.shape, dtype=np.float32)).tostring(order='C'))
                rsconn.hset("H_%s_minibatch_%s_measurement_last_update_timestamp" % (segment, measurement), A_indices_str, timestamp_to_str(0.0))

                #print "H_%s_minibatch_%s" % (segment, measurement)

    #import pdb; pdb.set_trace()

    # The master does not really differentiate between the various
    # segments of the dataset. It just takes whatever it is fed
    # because nothing other than the training data should go in there.
    # We decided to put "_train_" in there nonetheless. Seems more consistent.

    # used when `want_only_indices_for_master` is True
    rsconn.delete("L_master_train_minibatch_indices_and_info_QUEUE")
    # used when `want_only_indices_for_master` is False
    rsconn.delete("L_master_train_minibatch_data_and_info_QUEUE")

    rsconn.set("initialization_is_done", True)



def run(DD_config, rserv, rsconn, bootstrap_file):

    configure(  rsconn,
                **DD_config['database'])

    # Use `rserv` to be able to shut down the
    # redis-server when the user hits CTRL+C.
    # Otherwise, the server is left in the background
    # and this can cause problems due to scripts
    # getting tangled together.

    def signal_handler(signal, frame):
        print("You pressed CTRL+C.")
        print("Sending shutdown command to the redis-server.")
        rserv.stop()
        delete_bootstrap_file(bootstrap_file)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        print "Running server. Press CTLR+C to stop. Timestamp %f." % time.time()
        #signal.pause()

        time.sleep(5)
        print ""
