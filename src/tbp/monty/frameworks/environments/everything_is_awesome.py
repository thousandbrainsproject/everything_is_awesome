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

from tbp.monty.frameworks.actions.action_samplers import ActionSampler
from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.actions.actuator import Actuator
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

class EverythingIsAwesomeActionSampler(ActionSampler):
    """ActionSampler for the Everything Is Awesome hackathon environment."""

    def sample_orbit_left(self, agent_id: str) -> OrbitLeft:
        return OrbitLeft(agent_id=agent_id, distance=1.0)

    def sample_orbit_right(self, agent_id: str) -> OrbitRight:
        return OrbitRight(agent_id=agent_id, distance=1.0)

    def sample_translate_up(self, agent_id: str) -> TranslateUp:
        return TranslateUp(agent_id=agent_id, distance=1.0)

    def sample_translate_down(self, agent_id: str) -> TranslateDown:
        return TranslateDown(agent_id=agent_id, distance=1.0)


class EverythingIsAwesomeActuator(Actuator):
    """Actuator for the Everything Is Awesome hackathon environment."""

    def actuate_orbit_left(self, action: OrbitLeft) -> None:
        pass

    def actuate_orbit_right(self, action: OrbitRight) -> None:
        pass

    def actuate_translate_up(self, action: TranslateUp) -> None:
        pass

    def actuate_translate_down(self, action: TranslateDown) -> None:
        pass


class OrbitLeft(Action):
    """Orbit at current distance from target to the left."""

    @classmethod
    def sample(
        cls, agent_id: str, sampler: EverythingIsAwesomeActionSampler
    ) -> OrbitLeft:
        return sampler.sample_orbit_left(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_orbit_left(self)


class OrbitRight(Action):
    """Orbit at current distance from target to the right."""

    @classmethod
    def sample(
        cls, agent_id: str, sampler: EverythingIsAwesomeActionSampler
    ) -> OrbitRight:
        return sampler.sample_orbit_right(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_orbit_right(self)


class TranslateUp(Action):
    """Translate up."""

    @classmethod
    def sample(
        cls, agent_id: str, sampler: EverythingIsAwesomeActionSampler
    ) -> TranslateUp:
        return sampler.sample_translate_up(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_translate_up(self)


class TranslateDown(Action):
    """Translate down."""

    @classmethod
    def sample(
        cls, agent_id: str, sampler: EverythingIsAwesomeActionSampler
    ) -> TranslateDown:
        return sampler.sample_translate_down(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: Actuator) -> None:
        actuator.actuate_translate_down(self)
