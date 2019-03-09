import json
import os
import time
from typing import Dict

import numpy as np
import tensorflow as tf
from tensorflow.python import keras
from tensorflow.python.keras import layers
from tensorflow.python.keras.callbacks import ModelCheckpoint

from data.preprocess import PreProcessor
from models.cnn_attention import ConvAttention
from utils.f1_evaluator import evaluate_f1
from utils.run_utils import save_train_validate_history


# TODO refactor the save into util functions
# TODO add pickling to preprocessors for easier reproducibility
class CnnAttentionModel(object):
    def __init__(self, hyperparameters: Dict[str, any],
                 preprocessors: Dict[str, PreProcessor],
                 trained_model_path: str = None):
        self.hyperparameters = hyperparameters
        self.preprocessors = preprocessors
        self.vocab = preprocessors['training_dataset_preprocessor'].metadata['token_vocab']

        # create model
        self.model = self._compile_cnn_attention_model()

        if trained_model_path:
            self.directory = "trained_models/{}/{}/{}".format(hyperparameters['model_type'],
                                                              hyperparameters['run_name'],
                                                              time.strftime("%Y-%m-%d-%H-%M"))
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)

            with open('{}/config.json'.format(self.directory), 'w') as fp:
                json.dump(hyperparameters, fp)

            self._train_cnn_attention_model()

        else:
            self.directory = trained_model_path
            self.model.load_weights("{}/weights-final.hdf5".format(self.directory))

    def evaluate_f1(self):
        # testing loop
        testing_data_tensors = self.preprocessors['testing_dataset_preprocessor'].get_tensorise_data()
        testing_body_subtokens = np.expand_dims(testing_data_tensors['body_tokens'], axis=-1)
        testing_method_name_subtokens = np.expand_dims(testing_data_tensors['name_tokens'], axis=-1)

        f1_evaluation, visualised_input = evaluate_f1(self.model,
                                                      self.vocab,
                                                      testing_body_subtokens,
                                                      testing_method_name_subtokens,
                                                      self.hyperparameters['beam_search_config'])
        with open('{}/results.txt'.format(self.directory), 'w') as fp:
            fp.write(str(f1_evaluation))

        with open('{}/visualised_results.txt'.format(self.directory), 'w') as fp:
            fp.write(visualised_input)

        # Store evaluation size
        with open('{}/inputs.txt'.format(self.directory), 'a') as fp:
            inputs_str = "Testing samples: {}".format(testing_body_subtokens.shape[0])
            fp.write(inputs_str)

        return f1_evaluation

    def _compile_cnn_attention_model(self):
        model_hyperparameters = self.hyperparameters['model_hyperparameters']
        model_hyperparameters["vocabulary_size"] = len(self.vocab) + 1
        batch_size = model_hyperparameters['batch_size']
        main_input = layers.Input(shape=(None, 1), batch_size=batch_size, dtype=tf.int32, name='main_input')
        cnn_layer = ConvAttention(model_hyperparameters)
        optimizer = keras.optimizers.Nadam()  # RMSprop with Nesterov momentum
        loss_func = keras.losses.sparse_categorical_crossentropy
        # define execution
        cnn_output = cnn_layer(main_input)
        model = keras.Model(inputs=[main_input], outputs=cnn_output)
        model.compile(optimizer=optimizer,
                      loss=loss_func,
                      metrics=['accuracy'])
        return model

    def _train_cnn_attention_model(self):
        # get the data and curate it for the model
        training_data_tensors = self.preprocessors['training_dataset_preprocessor'].get_tensorise_data()
        validating_data_tensors = self.preprocessors['validating_dataset_preprocessor'].get_tensorise_data()

        # get tensorised training/validating dataset
        training_body_subtokens = np.expand_dims(training_data_tensors['body_tokens'], axis=-1)
        training_method_name_subtokens = np.expand_dims(training_data_tensors['name_tokens'], axis=-1)

        validating_dataset = (np.expand_dims(validating_data_tensors['body_tokens'], axis=-1),
                              np.expand_dims(validating_data_tensors['name_tokens'], axis=-1))

        # Store input size
        with open('{}/inputs.txt'.format(self.directory), 'w') as fp:
            inputs_str = "Training samples: {}, validating samples: {}".format(training_body_subtokens.shape[0],
                                                                               validating_dataset[0].shape[0])
            fp.write(inputs_str)
        # training loop
        model_hyperparameters = self.hyperparameters['model_hyperparameters']
        checkpoint_fp = "{}/weights-{{epoch:02d}}-{{val_acc:.2f}}.hdf5".format(self.directory)
        checkpoint = ModelCheckpoint(checkpoint_fp, monitor='val_acc',
                                     verbose=1,
                                     save_best_only=True,
                                     save_weights_only=True,
                                     mode='max')
        callbacks_list = [checkpoint]
        history = self.model.fit(training_body_subtokens,
                                 training_method_name_subtokens,
                                 epochs=model_hyperparameters['epochs'],
                                 verbose=2,
                                 batch_size=model_hyperparameters['batch_size'],
                                 callbacks=callbacks_list,
                                 validation_data=validating_dataset,
                                 )
        self.model.save_weights("{}/weights-final.hdf5".format(self.directory))
        save_train_validate_history(self.directory, history)