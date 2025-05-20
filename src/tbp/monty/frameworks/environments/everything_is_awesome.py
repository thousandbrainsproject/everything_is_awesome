# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

from enum import Enum
from typing import Protocol, TypedDict, cast

import numpy as np
import Pyro5.api

from tbp.monty.frameworks.actions.action_samplers import ActionSampler
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

    def __init__(self, actuator_server_uri: str, sensor_server_uri: str) -> None:
        self._actuator_server = cast(
            ActuatorProtocol | ProprioceptionProtocol,
            Pyro5.api.Proxy(actuator_server_uri),
        )
        self._actuator = EverythingIsAwesomeActuator(
            actuator_server=self._actuator_server
        )
        self._proprioception_server = cast(
            ProprioceptionProtocol, self._actuator_server
        )
        self._sensor_server = cast(SensorProtocol, Pyro5.api.Proxy(sensor_server_uri))

    @property
    def action_space(self) -> ActionSpace:
        raise NotImplementedError

    def add_object(self):
        raise NotImplementedError

    def close(self):
        pass

    def observations(self) -> EverythingIsAwesomeObservations:
        rgb = self._sensor_server.rgb()
        depth = self._sensor_server.depth()
        # TODO: process observations and create rgba and correct depth
        rgba = None
        return EverythingIsAwesomeObservations(
            agent_id_0=EverythingIsAwesomeAgentObservation(
                patch=EverythingIsAwesomeSensorObservation(
                    rgba=rgba,
                    depth=depth,
                )
            )
        )

    def step(self, action: Action) -> EverythingIsAwesomeObservations:
        action.act(self._actuator)
        return self.observations()

    def get_state(self) -> ProprioceptiveState:
        # TODO: request state from self._proprioception_server
        pass

    def remove_all_objects(self):
        raise NotImplementedError

    def reset(self) -> EverythingIsAwesomeObservations:
        self._actuator_server.run_to_position(motor=Motor.ORBIT, position=0.0)
        self._actuator_server.run_to_position(motor=Motor.TRANSLATE, position=0.0)
        # TODO: Validate that the above code works as there are reports that it wouldn't
        #       See https://github.com/RaspberryPiFoundation/python-build-hat/issues/179
        return self.observations()


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


class EverythingIsAwesomeActuator:
    """Actuator for the Everything Is Awesome hackathon environment.

    Note:
        Actuators are use case specific, and don't need to implement all Actuator(ABC)
        methods. In fact, the Actuator(ABC) should not be abstract, but concrete.
        In its place, we will likely want to use a Protocol instead.
    """

    def __init__(self, actuator_server: ActuatorProtocol) -> None:
        self._actuator_server = actuator_server

    def actuate_orbit_left(self, action: OrbitLeft) -> None:
        # TODO: send command to self._actuator_server
        pass

    def actuate_orbit_right(self, action: OrbitRight) -> None:
        # TODO: send command to self._actuator_server
        pass

    def actuate_translate_up(self, action: TranslateUp) -> None:
        # TODO: send command to self._actuator_server
        pass

    def actuate_translate_down(self, action: TranslateDown) -> None:
        # TODO: send command to self._actuator_server
        pass


class OrbitLeftActionSampler(Protocol):
    def sample_orbit_left(self, agent_id: str) -> OrbitLeft: ...


class OrbitLeftActuator(Protocol):
    def actuate_orbit_left(self, action: OrbitLeft) -> None: ...


class OrbitLeft(Action):
    """Orbit at current distance from target to the left."""

    @classmethod
    def sample(cls, agent_id: str, sampler: OrbitLeftActionSampler) -> OrbitLeft:
        return sampler.sample_orbit_left(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: OrbitLeftActuator) -> None:
        actuator.actuate_orbit_left(self)


class OrbitRightActionSampler(Protocol):
    def sample_orbit_right(self, agent_id: str) -> OrbitRight: ...


class OrbitRightActuator(Protocol):
    def actuate_orbit_right(self, action: OrbitRight) -> None: ...


class OrbitRight(Action):
    """Orbit at current distance from target to the right."""

    @classmethod
    def sample(cls, agent_id: str, sampler: OrbitRightActionSampler) -> OrbitRight:
        return sampler.sample_orbit_right(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: OrbitRightActuator) -> None:
        actuator.actuate_orbit_right(self)


class TranslateUpActionSampler(Protocol):
    def sample_translate_up(self, agent_id: str) -> TranslateUp: ...


class TranslateUpActuator(Protocol):
    def actuate_translate_up(self, action: TranslateUp) -> None: ...


class TranslateUp(Action):
    """Translate up."""

    @classmethod
    def sample(cls, agent_id: str, sampler: TranslateUpActionSampler) -> TranslateUp:
        return sampler.sample_translate_up(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: TranslateUpActuator) -> None:
        actuator.actuate_translate_up(self)


class TranslateDownActionSampler(Protocol):
    def sample_translate_down(self, agent_id: str) -> TranslateDown: ...


class TranslateDownActuator(Protocol):
    def actuate_translate_down(self, action: TranslateDown) -> None: ...


class TranslateDown(Action):
    """Translate down."""

    @classmethod
    def sample(
        cls, agent_id: str, sampler: TranslateDownActionSampler
    ) -> TranslateDown:
        return sampler.sample_translate_down(agent_id)

    def __init__(self, agent_id: str, distance: float) -> None:
        super().__init__(agent_id=agent_id)
        self.distance = distance

    def act(self, actuator: TranslateDownActuator) -> None:
        actuator.actuate_translate_down(self)


class Motor(Enum):
    ORBIT = "orbit"
    TRANSLATE = "translate"


class ActuatorProtocol(Protocol):
    def run_to_position(self, motor: Motor, position: float) -> None: ...


class SensorProtocol(Protocol):
    def rgb(self) -> list[list[int]]: ...
    def depth(self) -> list[list[int]]: ...


class ProprioceptionProtocol(Protocol):
    def absolute_position(self) -> list[float]: ...
