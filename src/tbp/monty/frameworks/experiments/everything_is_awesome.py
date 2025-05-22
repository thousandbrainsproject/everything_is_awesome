# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

from scipy.spatial.transform import Rotation

from tbp.monty.frameworks.experiments.monty_experiment import MontyExperiment
from tbp.monty.frameworks.utils.everything_is_awesome_visualizations import (
    EverythingIsAwesomeVisualizer,
)


class EverythingIsAwesomeTrainExperiment(MontyExperiment):
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
        self.model.switch_to_exploratory_step()
        self.model.detected_object = self.model.primary_target["object"]
        for lm in self.model.learning_modules:
            lm.detected_object = self.model.primary_target["object"]

        self.dataloader.pre_episode()

        self.max_steps = self.max_train_steps

        self.logger_handler.pre_episode(self.logger_args)

        if self.show_sensor_output:
            self.online_visualizer = EverythingIsAwesomeVisualizer(axes=True)


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
            self.online_visualizer = EverythingIsAwesomeVisualizer(axes=True)

    def post_step(self, step, observation):
        """Hook for anything you want to do after a step."""
        super().post_step(step, observation)

        if self.show_sensor_output:
            agent_state = self.dataset.env.get_state()
            agent_position = agent_state["agent_id_0"]["position"]
            agent_rotation_quat = agent_state["agent_id_0"]["rotation"]
            agent_rotation = Rotation.from_quat(
                [
                    agent_rotation_quat.x,
                    agent_rotation_quat.y,
                    agent_rotation_quat.z,
                    agent_rotation_quat.w,
                ]
            )

            current_mlh = self.model.learning_modules[0].current_mlh
            mlh_object = current_mlh["graph_id"]
            mlh_location = current_mlh["location"]
            mlh_rotation = current_mlh["rotation"]

            glb_path = "/home/ramy/tbp/data/habitat/objects/ycb/meshes/025_mug/google_16k/textured.glb.orig"

            self.online_visualizer.update_data(
                glb_path,
                object_orientation=mlh_rotation,
                agent_position=agent_position,
                agent_orientation=agent_rotation,
            )
