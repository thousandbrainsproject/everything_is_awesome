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
    EverythingIsAwesomeTrainVisualizer,
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
            self.online_visualizer = EverythingIsAwesomeTrainVisualizer(axes=True)

    def post_step(self, step, observation):
        """Hook for anything you want to do after a step."""
        super().post_step(step, observation)

        if self.show_sensor_output:
            if "patch" not in self.model.learning_modules[0].buffer.locations:
                return

            graph = self.model.learning_modules[0].buffer.locations["patch"]

            agent_state = self.dataset.env.get_state()
            agent_position = agent_state["agent_id_0"]["position"]

            self.online_visualizer.update_data(
                graph=graph, agent_position=agent_position
            )

    def post_episode(self, steps):
        super().post_episode(steps)

        object_name = self.dataloader.primary_target["object"]
        if self.show_sensor_output:
            graph = (
                self.model.learning_modules[0]
                .graph_memory.models_in_memory[object_name]["patch"]
                .pos
            )
            agent_state = self.dataset.env.get_state()
            agent_position = agent_state["agent_id_0"]["position"]
            self.online_visualizer.update_data(
                graph=graph, agent_position=agent_position, interactive=True
            )


class EverythingIsAwesomeExperiment(MontyExperiment):
    def __init__(self, config):
        """Initialize the experiment based on the provided configuration.

        Args:
            config: config specifying variables of the experiment.
        """
        super().__init__(config)
        self.models_scale_factor = 1.0

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

        # if self.show_sensor_output:
        #     self.online_visualizer = EverythingIsAwesomeEvalVisualizer(axes=True)

        if self.show_sensor_output:
            self.online_visualizer = EverythingIsAwesomeTrainVisualizer(axes=False)

    def init_model(self, monty_config, model_path=None):
        model = super().init_model(monty_config, model_path)
        if self.models_scale_factor != 1.0:
            for obj in model.learning_modules[0].graph_memory.models_in_memory.values():
                obj["patch"].scale_model(self.models_scale_factor)

        return model

    def post_step(self, step, observation):
        """Hook for anything you want to do after a step."""
        super().post_step(step, observation)

        #         if self.show_sensor_output:
        #             agent_state = self.dataset.env.get_state()
        #             agent_position = agent_state["agent_id_0"]["position"]
        #             agent_rotation_quat = agent_state["agent_id_0"]["rotation"]
        #             agent_rotation = Rotation.from_quat(
        #                 [
        #                     agent_rotation_quat.x,
        #                     agent_rotation_quat.y,
        #                     agent_rotation_quat.z,
        #                     agent_rotation_quat.w,
        #                 ]
        #             )

        #             current_mlh = self.model.learning_modules[0].current_mlh
        #             mlh_object = current_mlh["graph_id"]
        #             mlh_location = current_mlh["location"]
        #             mlh_rotation = current_mlh["rotation"]

        #             self.online_visualizer.update_data(
        #                 mlh_object=mlh_object,
        #                 object_orientation=mlh_rotation,
        #                 agent_position=agent_position,
        #                 agent_orientation=agent_rotation,
        #             )

        if self.show_sensor_output:
            if "patch" not in self.model.learning_modules[0].buffer.locations:
                return

            current_mlh = self.model.learning_modules[0].current_mlh
            graph = (
                self.model.learning_modules[0]
                .graph_memory.models_in_memory[current_mlh["graph_id"]]["patch"]
                .pos
            )
            mlh_rotation = current_mlh["rotation"]

            agent_state = self.dataset.env.get_state()
            agent_position = agent_state["agent_id_0"]["position"]

            self.online_visualizer.update_data_eval(
                graph=graph, graph_rot=mlh_rotation, agent_position=agent_position
            )

    def post_episode(self, steps):
        super().post_episode(steps)

        if self.show_sensor_output:
            if "patch" not in self.model.learning_modules[0].buffer.locations:
                return

            current_mlh = self.model.learning_modules[0].current_mlh
            graph = (
                self.model.learning_modules[0]
                .graph_memory.models_in_memory[current_mlh["graph_id"]]["patch"]
                .pos
            )
            mlh_rotation = current_mlh["rotation"]

            agent_state = self.dataset.env.get_state()
            agent_position = agent_state["agent_id_0"]["position"]

            self.online_visualizer.update_data_eval(
                graph=graph,
                graph_rot=mlh_rotation,
                agent_position=agent_position,
                interactive=True,
            )
