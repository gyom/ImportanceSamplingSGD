import numpy as np
import os

def get_model_config():

    model_config = {}

    #Importance sampling or vanilla sgd.
    model_config["importance_algorithm"] = "isgd"
    #model_config["importance_algorithm"] = "sgd"

    #Momentum rate, where 0.0 corresponds to not using momentum
    model_config["momentum_rate"] = 0.0

    #RMS rate of 0 corresponds to not using RMS prop
    model_config['rms_rate'] = 0.0

     #Enable adagrad
    model_config['adagrad'] = 1

    #The learning rate to use on the gradient averaged over a minibatch
    model_config["learning_rate"] = 0.0001

    #model_config["dataset"] = "mnist"
    model_config["dataset"] = "svhn"

    if model_config["dataset"] == "mnist":
        model_config["num_input"] = 784
    elif model_config["dataset"] == "svhn":
        model_config["num_input"] = 3072

    # Pick one, depending where you run this.
    # This could be done differently too by looking at fuelrc
    # or at the hostname.
    #import socket
    #data_root = {   "serendib":"/home/dpln/data/data_lisa_data",
    #                "lambda":"/home/gyomalin/ML/data_lisa_data",
    #                "szkmbp":"/Users/gyomalin/Documents/fuel_data"}[socket.gethostname().lower()]
    data_root = "/rap/jvb-000-aa/data/alaingui"

    model_config["mnist_file"] = os.path.join(data_root, "mnist/mnist.pkl.gz")
    model_config["svhn_file_train"] = os.path.join(data_root, "svhn/train_32x32.mat")
    model_config["svhn_file_extra"] = os.path.join(data_root, "svhn/extra_32x32.mat")
    model_config["svhn_file_test"] = os.path.join(data_root, "svhn/test_32x32.mat")

    model_config["load_svhn_normalization_from_file"] = True
    model_config["save_svhn_normalization_to_file"] = False
    model_config["svhn_normalization_value_file"] = os.path.join(data_root, "svhn/svhn_normalization_values.pkl")

    model_config["hidden_sizes"] = [2048, 2048, 2048, 2048]

    # Note from Guillaume : I'm not fond at all of using seeds,
    # but here it is used ONLY for the initial partitioning into train/valid.
    model_config["seed"] = 42

    #Weights are initialized to N(0,1) * initial_weight_size
    model_config["initial_weight_size"] = 0.01

    #Hold this fraction of the instances in the validation dataset
    model_config["fraction_validation"] = 0.05

    model_config["master_routine"] = ["sync_params"] + ["refresh_importance_weights"] + (["process_minibatch"] * 16)
    model_config["worker_routine"] = ["sync_params"] + (["process_minibatch"] * 2)

    model_config["turn_off_importance_sampling"] = True

    model_config['image']                         = '/rap/jvb-000-aa/data/chinna/iclr2015/logging/noisy_images/'
    model_config['noise']                         = 'no_noise'#'uniform'#'normal'#'black_out'#'guassian'#'no_noise'
    model_config['fraction_noise']                = 0.0

    return model_config


def get_database_config():

    # Try to connect to the database for at least 10 minutes before giving up.
    # When setting this to below 1 minute on Helios, the workers would give up
    # way to easily. This value also controls how much time the workers will
    # be willing to wait for the parameters to be present on the server.
    connection_setup_timeout = 10*60

    experiment_root_dir = "/rap/jvb-000-aa/data/chinna/iclr2015/logging/rms_prop_exp/usgd_r"
    redis_rdb_path_plus_filename = os.path.join(experiment_root_dir, "uniform.rdb")
    logging_folder = experiment_root_dir




    # Some of those values are placeholder.
    # Need to update the (Ntrain, Nvalid, Ntest) to the actual values for SVHN.

    (Ntrain, Nvalid, Ntest) = (574168, 30220, 26032)
    # Training Set (574168, 32, 3, 32) (574168, 1)
    # Validation Set (30220, 32, 3, 32) (30220, 1)
    # Test Set (26032, 32, 3, 32) (26032, 1)
    # svhn data loaded...

    # When skipping the "extra" part of the dataset.
    #(Ntrain, Nvalid, Ntest) = (69594, 3663, 26032)




    # This is part of a discussion about when we should the master
    # start its training with uniform sampling SGD and when it should
    # perform importance sampling SGD.
    # The default value is set to np.Nan, and right now the criterion
    # to decide if a weight is usable is to check if it's not np.Nan.
    #
    # We can decide to add other options later to include the staleness
    # of the importance weights, or other simular criterion, to define
    # what constitutes a "usable" value.

    default_importance_weight = np.NaN
    #default_importance_weight = 1.0

    want_master_to_do_USGD_when_ISGD_is_not_possible = True
    master_usable_importance_weights_threshold_to_ISGD = 0.01 # cannot be None

    # The master will only consider importance weights which were updated this number of seconds ago.
    staleness_threshold_seconds = None
    staleness_threshold_num_minibatches_master_processed = None

    # Guillaume is not so fond of this approach.
    importance_weight_additive_constant = 1e-32

    serialized_parameters_format ="opaque_string"

    # These two values don't have to be the same.
    # It might be possible that the master runs on a GPU
    # and the workers run on CPUs just to try stuff out.
    workers_minibatch_size = 1024*4*4
    master_minibatch_size = 1024*4

    # This is not really being used anywhere.
    # We should consider deleting it after making sure that it
    # indeed is not being used, but then we could argue that it
    # would be a good idea to use that name to automatically determine
    # the values of (Ntrain, Nvalid, Ntest).
    dataset_name='svhn'

    L_measurements=["individual_importance_weight", "individual_gradient_square_norm", "individual_loss", "individual_accuracy", "minibatch_gradient_mean_square_norm"]

    #
    # The rest of this code is just checks and quantities generated automatically.
    #

    L_segments = []
    assert 0 < Ntrain
    if Ntrain != 0:
        L_segments.append("train")
    if Nvalid != 0:
        L_segments.append("valid")
    if Ntest != 0:
        L_segments.append("test")


    assert workers_minibatch_size is not None and 0 < workers_minibatch_size
    assert master_minibatch_size is not None and 0 < master_minibatch_size
    assert dataset_name is not None
    assert Ntrain is not None and 0 < Ntrain
    assert Nvalid is not None
    assert Ntest is not None

    assert serialized_parameters_format in ["opaque_string", "ndarray_float32_tostring"]

    assert 0.0 <= master_usable_importance_weights_threshold_to_ISGD
    assert master_usable_importance_weights_threshold_to_ISGD <= 1.0

    return dict(connection_setup_timeout=connection_setup_timeout,
                workers_minibatch_size=workers_minibatch_size,
                master_minibatch_size=master_minibatch_size,
                dataset_name=dataset_name,
                Ntrain=Ntrain,
                Nvalid=Nvalid,
                Ntest=Ntest,
                L_measurements=L_measurements,
                L_segments=L_segments,
                want_only_indices_for_master=True,
                want_exclude_partial_minibatch=True,
                serialized_parameters_format=serialized_parameters_format,
                default_importance_weight=default_importance_weight,
                want_master_to_do_USGD_when_ISGD_is_not_possible=want_master_to_do_USGD_when_ISGD_is_not_possible,
                master_usable_importance_weights_threshold_to_ISGD=master_usable_importance_weights_threshold_to_ISGD,
                staleness_threshold_seconds=staleness_threshold_seconds,
                staleness_threshold_num_minibatches_master_processed=staleness_threshold_num_minibatches_master_processed,
                importance_weight_additive_constant=importance_weight_additive_constant,
                logging_folder=logging_folder,
                redis_rdb_path_plus_filename=redis_rdb_path_plus_filename)

def get_helios_config():
    # Optional.

    return {}
