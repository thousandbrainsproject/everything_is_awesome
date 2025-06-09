![](media/everything_is_awesome.png)

# Everything Is Awesome May 2025 Robot Hackathon repository

> [!NOTE]
>
> This is a fork of the main Monty project used in the May 2025 Hackathon. For the up-to-date Monty project, please see the main repository: https://github.com/thousandbrainsproject/tbp.monty

This is our code for the May 2025 Robot Hackathon repository. We took the fork approach, so all of the Monty code at the time is included in this repository, with some infrastructure and documentation deleted.

## Project Overview

We built a LEGO robot that could orbit around an object, learn the object, and later, recognize the object.

https://github.com/user-attachments/assets/14b6bd9c-69ce-41f6-8099-0c0474a63a80

# Getting Started

> [!WARNING]
> This project is not reproducible.

While this project is not reproducible, it can be used as an example of how to connect Monty to a real-world robot.

## Parts List

TODO

## Robot

TODO

## Networking

TODO

## Code changes

The following files were changed after forking from Monty:

```
README.md
benchmarks/configs/my_experiments.py
benchmarks/configs/names.py
pyproject.toml
src/tbp/monty/frameworks/actions/action_samplers.py
src/tbp/monty/frameworks/environment_utils/transforms.py
src/tbp/monty/frameworks/environments/embodied_data.py
src/tbp/monty/frameworks/environments/everything_is_awesome.py
src/tbp/monty/frameworks/experiments/everything_is_awesome.py
src/tbp/monty/frameworks/experiments/monty_experiment.py
src/tbp/monty/frameworks/experiments/object_recognition_experiments.py
src/tbp/monty/frameworks/measure.py
src/tbp/monty/frameworks/models/monty_base.py
src/tbp/monty/frameworks/models/object_model.py
src/tbp/monty/frameworks/utils/everything_is_awesome_visualizations.py
```

To see specific changes, run:
```
$ git diff 1c7b7b166d1ec80e66b641d9e5f8c94d18ffe9f7 8e4328766532ed91dfdc62139a06720a26eaf953
```

First, note the configurations for the training and evaluation experiments in `benchmarks/config/my_experiments.py`: `everything_is_awesome_train` and `everything_is_awesome_eval`.

Next, `pyproject.toml` declares optional dependencies for the project, to be installed after Monty with `pip install -e '.[everything_is_awesome]'`.

We needed to provide our own Actions for Monty to tell the robot how to behave. This required some refactoring of at-the-time implementation of Actions that was not flexibile enough to accomodate plugging in a new action.

We parametrized and slightly refactored the `DepthTo3DLocations` transform in `src/tbp/monty/frameworks/environment_utils/transforms.py`.

The bulk of the new implementation is in `src/tbp/monty/frameworks/environments/everything_is_awesome.py` and `src/tbp/monty/frameworks/experiments/everything_is_awesome.py`.

## Monty Installation

The environment for this project is managed with [conda](https://www.anaconda.com/download/success).

To create the environment, run:

### ARM64 (Apple Silicon) (zsh shell)
```
conda env create -f environment.yml --subdir=osx-64
conda init zsh
conda activate paper # TODO: Update to your paper's name
conda config --env --set subdir osx-64
```

### ARM64 (Apple Silicon) (bash shell)
```
conda env create -f environment.yml --subdir=osx-64
conda init
conda activate paper # TODO: Update to your paper's name
conda config --env --set subdir osx-64
```

### Intel (zsh shell)
```
conda env create -f environment.yml
conda init zsh
conda activate paper # TODO: Update to your paper's name
```

### Intel (bash shell)
```
conda env create -f environment.yml
conda init
conda activate paper # TODO: Update to your paper's name
```

# License

The MIT License. See the [LICENSE](LICENSE) for details.
