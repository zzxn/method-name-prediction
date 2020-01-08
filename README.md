# 如何运行 (by ZXN)

1. 按照下方`Method Name Prediction > Setup > Prerequisites`中的指示配置好环境，另需安装`matplotlib`
2. cd到`method-name-prediction`目录
3. 把所有`.java`文件放置到`data/raw`目录下，**这些代码文件可以在任意层嵌套的目录中**
4. 运行`python src/preprocess.py data/raw data/processed`，把`.java`文件处理成`.proto`文件，在处理完成后可以在`data/processed`
目录下看到处理好的同等数量的`.proto`文件（如无法编译，则不会输出）
5. 配置`configs/example-config.json`，指定超参数
6. 运行`python src/run_model.py data/processed --hyperparameters-config=configs/example-config.json`，训练模型

# Method Name Prediction
This repository contains the Keras Implementation of [A convolutional attention network for extreme summarization of source code](https://arxiv.org/abs/1602.03001) [1]

The model takes in a sequence of subtokens composed of Java's method body and output an extreme summarisation in form of predicted method name.

Example input: 
```java 
hi--; while (lo < hi) { Object t = a[lo]; a[lo++] = a[hi]; a[hi--] = t; }
```
Example model output: `[reverse, range]`

Status:
* Successfully reproduce (and improve) results of the Convolution Attention Model.
* The Copy Attention Model is struggling to learn useful features - the code exist and compliment notebooks to allow further investigation.

## Setup
### Prerequisites 
The easiest way to install the prerequisites is to use [Anaconda](https://conda.io/en/latest/). 

```bash
# Install the environment
conda env create --file=environment.yml

# Activate the environment
source activate method-name-prediction

```

The dependencies contains jupyter dependency and can be started using `jupyter notebook`
and there are examples in the [notebooks directory](https://github.com/samialabed/method-name-prediction/tree/master/notebooks).


### Dataset

The model can be generalised to any dataset.

However, the preprocessors and utility functions are written to work with specific type of data available to students enrolled in [R252 - Machine learning in Programming](https://www.cl.cam.ac.uk/teaching/1819/R252/) at Cambridge University.

The expected input data format is .proto files that contains a feature graph of Java programs.
The feature graph can be generated by compiling Java programs with the features extractor extension enabled from [features-javac](https://github.com/acr31/features-javac)

## Usage Instructions

To execute training -> evaluation -> inference and output the results to a file: 

``` run_model.py DATA_DIR (--hyperparameters-config=FILE | --trained-model-dir=DIR [--use-same-input-dir]) [options]```

Where: 
* `DATA_DIR`: The path to the input data (training/testing/validating) - the preprocessor will split the input to 65% training, 5% validating, and 30% to test and inference.
* `--hyperparameters-config=FILE`: The model hyperparameters as json config file. Expected of config files are in the [configs directory](https://github.com/samialabed/method-name-prediction/tree/master/configs)
* `--trained-model-dir=DIR`: Path to a trained model directory to skip training and restore vocabulary.
* `--use-same-input-dir` Use the same dataset used in the trained-model, intended to allow reproducible results.
* `[options]` can be any of the following:
  * `--help` to show help screen.
  * `--debug` to intercept any failure and enable debugging, also output DEBUG logs to console.


The model will create a directory in the trained_models

```Output directory: trained_models/<NAME OF THE MODEL>/<RUN_NAME>/<DATE AND TIME>/*```

Unless the `trained-model-dir` is specified, then the model will restore trained model information and
 create a new subdirectory under the trained model dir called `experiement/date-time-hour` where the results of running 
 an experiment against the trained model will be saved.


Output files:
* `hyperparameters.json` Copy of the hyperparameters used in training the model.
* `inputs.txt` Stats about the input including how many methods used in training/testing/validating.
* `results.txt` The model f1 score, unknown accuracy, and exact copy accuracy.
* `model_accuracy.png` and `model_loss.png` The training/validating model loss and accuracy.
* `visualised_results.txt` randomly selected 10 predictions and visualised.
* Various hdf5 and pkl files meant to aid the reproducibility of your evaluation.

Full list of output filenames in [src/utils/save_util.py](https://github.com/samialabed/method-name-prediction/blob/master/src/utils/save_util.py)

The model uses a full beamsearch, therefore it takes a logn time to perform inference and require a reasonable memory size. 
Using smaller size beam width can help the performance and/or if constrained by memory.

### Reproducing Evaluation Results
#### Model trained on Elasticsearch corpus excluding the unit tests
To reproduce the results of the model trained on Elasticsearch corpus excluding unittests:
```bash
python src/run_model.py \
    'data/raw/r252-corpus-features/org/elasticsearch/' \
    --trained-model-dir=trained_models/cnn_attention/elasticsearch_with_no_tests/2019-03-09-16-12/ \
    --use-same-input-dir
```
The model will generate F1-results and predictions and output them to files in the same training directory.

#### Model trained on Elasticsearch corpus excluding the unit tests
To reproduce the results of the model trained on Elasticsearch corpus excluding unittests:
```bash
python src/run_model.py \
    'data/raw/r252-corpus-features/org/elasticsearch/' \
    --trained-model-dir=trained_models/cnn_attention/elasticsearch_with_tests/2019-03-09-23-45/ \
    --use-same-input-dir
```
The model will generate F1-results and predictions and output them to files in the same training directory.


To run your own experiments on those models, simply omit `--use-same-input-dir`

### Directory structure

* [configs](https://github.com/samialabed/method-name-prediction/tree/master/configs): Contains hyperparameters used in training the model and running the preprocessor. src/run_model.py validates the needed parameters.
* [data](https://github.com/samialabed/method-name-prediction/tree/master/data): (Git Ignored directory) Contains the raw .proto files used to train/test the model.
* [notebooks](https://github.com/samialabed/method-name-prediction/tree/master/notebooks): Contains example notebooks used to execute the model and archived notebooks used in training/testing.
* [src](https://github.com/samialabed/method-name-prediction/tree/master/src): The directory contains the code for the model. 
* [trained_models](https://github.com/samialabed/method-name-prediction/tree/master/trained_models/): the output directory for any experiment.

## References 
````
[1] Allamanis, M., Peng, H. and Sutton, C., 2016, June. 
A convolutional attention network for extreme summarization of source code.  
In International Conference on Machine Learning (pp. 2091-2100).

@inproceedings{allamanis2016convolutional,
  title={A Convolutional Attention Network for Extreme Summarization of Source Code},
  author={Allamanis, Miltiadis and Peng, Hao and Sutton, Charles},
  booktitle={International Conference on Machine Learning (ICML)},
  year={2016}
}
````
