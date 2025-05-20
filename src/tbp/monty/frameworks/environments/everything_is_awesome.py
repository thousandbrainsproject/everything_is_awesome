# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

from typing import TypedDict

import numpy as np

from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.embodied_data import EnvironmentDataLoader
from tbp.monty.frameworks.environments.embodied_environment import (
    ActionSpace,
    EmbodiedEnvironment,
)
from tbp.monty.frameworks.models.motor_system_state import (
    MotorSystemState,
    ProprioceptiveState,
)


class EverythingIsAwesomeSensorObservation(TypedDict):
    """SensorObservation for the Everything Is Awesome hackathon environment."""

    depth: np.ndarray
    rgba: np.ndarray


class EverythingIsAwesomeAgentObservation(TypedDict):
    """AgentObservation for the Everything Is Awesome hackathon environment."""

    patch: EverythingIsAwesomeSensorObservation


class EverythingIsAwesomeObservations(TypedDict):
    """Observations for the Everything Is Awesome hackathon environment."""

    agent_id_0: EverythingIsAwesomeAgentObservation


class EverythingIsAwesomeEnvironment(EmbodiedEnvironment):
    """Everything Is Awesome hackathon environment."""

    @property
    def action_space(self) -> ActionSpace:
        raise NotImplementedError

    def add_object(self):
        raise NotImplementedError

    def close(self):
        pass

    def step(self, action: Action) -> EverythingIsAwesomeObservations:
        pass

    def get_state(self) -> ProprioceptiveState:
        pass

    def remove_all_objects(self):
        raise NotImplementedError

    def reset(self) -> EverythingIsAwesomeObservations:
        pass


class EverythingIsAwesomeDataLoader(EnvironmentDataLoader):
    """DataLoader for the Everything Is Awesome hackathon environment."""

    def pre_episode(self):
        super().pre_episode()
        self.reset_agent()

    def reset_agent(self):
        self._observation, proprioceptive_state = self.dataset.reset()
        self._motor_system_state = MotorSystemState(proprioceptive_state)
        self._counter = 0
        self._action = None
        return self._observation
