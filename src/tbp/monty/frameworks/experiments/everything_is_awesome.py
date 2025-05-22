# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from tbp.monty.frameworks.experiments.monty_experiment import MontyExperiment
from tbp.monty.frameworks.utils.everything_is_awesome_visualizations import (
    EverythingIsAwesomeVisualizer,
)


class EverythingIsAwesomeExperiment(MontyExperiment):
    @property
    def logger_args(self):
        args = super().logger_args
        if self.dataloader is not None:
            args["target"] = self.dataloader.primary_target
        return args

    def pre_episode(self):
        """Required to pass the primary target object to the model.

        TODO: This is a hack to get things working. Do no override
              methods with different signatures in the future.
        """
        self.model.pre_episode(self.dataloader.primary_target)
        self.dataloader.pre_episode()

        self.max_steps = self.max_train_steps
        if not self.model.experiment_mode == "train":
            self.max_steps = self.max_eval_steps

        self.logger_handler.pre_episode(self.logger_args)

        if self.show_sensor_output:
            # self.initialize_online_plotting()
            self.online_visualizer = EverythingIsAwesomeVisualizer(axes=True)
