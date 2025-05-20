# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypedDict, cast

import numpy as np
import Pyro5.api
from numpy.random import Generator

from tbp.monty.frameworks.actions.action_samplers import ActionSampler
from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.embodied_data import EnvironmentDataLoader
from tbp.monty.frameworks.environments.embodied_environment import (
    ActionSpace,
    EmbodiedEnvironment,
)
from tbp.monty.frameworks.models.motor_system_state import (
    AgentState,
    MotorSystemState,
    ProprioceptiveState,
    SensorState,
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


@dataclass
class MotorState:
    speed: int
    position: int
    absolute_position: int


class EverythingIsAwesomeEnvironment(EmbodiedEnvironment):
    """Everything Is Awesome hackathon environment."""

    def __init__(
        self,
        actuator_server_uri: str,
        depth_server_uri: str,
        pitch_diameter_r: float,
        rgb_server_uri: str,
    ) -> None:
        """Initialize the Everything Is Awesome environment.

        Args:
            actuator_server_uri: The URI of the actuator server.
            depth_server_uri: The URI of the depth server.
            pitch_diameter_r: The pitch diameter in units of radii. One radius is the
                distance between the sensor and the center of the platform that the
                robot can rotate around.
            rgb_server_uri: The URI of the rgb server.
        """
        self._actuator_server = cast(
            ActuatorProtocol | ProprioceptionProtocol,
            Pyro5.api.Proxy(actuator_server_uri),
        )
        self._actuator = EverythingIsAwesomeActuator(
            actuator_server=self._actuator_server,
            pitch_diameter_r=pitch_diameter_r,
        )
        self._proprioception_server = cast(
            ProprioceptionProtocol, self._actuator_server
        )
        self._depth_server = cast(DepthProtocol, Pyro5.api.Proxy(depth_server_uri))
        self._rgb_server = cast(RgbProtocol, Pyro5.api.Proxy(rgb_server_uri))

        orbit_speed = self._proprioception_server.speed(Motor.ORBIT)
        orbit_position = self._proprioception_server.position(Motor.ORBIT)
        orbit_absolute_position = self._proprioception_server.absolute_position(
            Motor.ORBIT
        )
        self._orbit_motor = MotorState(
            speed=orbit_speed,
            position=orbit_position,
            absolute_position=orbit_absolute_position,
        )
        translate_speed = self._proprioception_server.speed(Motor.TRANSLATE)
        translate_position = self._proprioception_server.position(Motor.TRANSLATE)
        translate_absolute_position = self._proprioception_server.absolute_position(
            Motor.TRANSLATE
        )
        self._translate_motor = MotorState(
            speed=translate_speed,
            position=translate_position,
            absolute_position=translate_absolute_position,
        )

    @property
    def action_space(self) -> ActionSpace:
        raise NotImplementedError

    def add_object(self):
        raise NotImplementedError

    def close(self):
        pass

    def _observations(self) -> EverythingIsAwesomeObservations:
        rgb = self._rgb_server.rgb()
        depth = self._depth_server.depth()
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
        return self._observations()

    def get_state(self) -> ProprioceptiveState:
        position = None
        rotation = None
        # TODO: request state from self._proprioception_server
        #       and calculate position vector and rotation quaternion
        return ProprioceptiveState(
            agent_id_0=AgentState(
                sensors=dict(
                    patch=SensorState(
                        # The sensor is fully coupled to the agent's position
                        position=[0.0, 0.0, 0.0],
                        rotation=[1.0, 0.0, 0.0, 0.0],  # WXYZ
                    )
                ),
                position=position,
                rotation=rotation,
            )
        )

    def remove_all_objects(self):
        raise NotImplementedError

    def reset(self) -> EverythingIsAwesomeObservations:
        self._actuator_server.run_to_position(motor=Motor.ORBIT, position=0.0)
        self._actuator_server.run_to_position(motor=Motor.TRANSLATE, position=0.0)
        # TODO: Validate that the above code works as there are reports that it wouldn't
        #       See https://github.com/RaspberryPiFoundation/python-build-hat/issues/179
        return self._observations()


class EverythingIsAwesomeDataLoader(EnvironmentDataLoader):
    """DataLoader for the Everything Is Awesome hackathon environment."""

    def pre_episode(self):
        super().pre_episode()
        self._reset_agent()

    def _reset_agent(self):
        self._observation, proprioceptive_state = self.dataset.reset()
        self._motor_system_state = MotorSystemState(proprioceptive_state)
        self._counter = 0
        self._action = None
        return self._observation


class EverythingIsAwesomeActionSampler(ActionSampler):
    """ActionSampler for the Everything Is Awesome hackathon environment."""

    def __init__(self, rng: Generator = None) -> None:
        super().__init__(
            rng=rng,
            actions=[
                OrbitLeft,
                OrbitRight,
                TranslateUp,
                TranslateDown,
            ],
        )

    def _sample_degrees(self) -> float:
        return self.rng.uniform(low=1.0, high=10.0)

    def _sample_distance(self) -> float:
        return self.rng.uniform(low=0.01, high=0.1)

    def sample_orbit_left(self, agent_id: str) -> OrbitLeft:
        degrees = self._sample_degrees()
        return OrbitLeft(agent_id=agent_id, degrees=degrees)

    def sample_orbit_right(self, agent_id: str) -> OrbitRight:
        degrees = self._sample_degrees()
        return OrbitRight(agent_id=agent_id, degrees=degrees)

    def sample_translate_up(self, agent_id: str) -> TranslateUp:
        distance = self._sample_distance()
        return TranslateUp(agent_id=agent_id, distance=distance)

    def sample_translate_down(self, agent_id: str) -> TranslateDown:
        distance = self._sample_distance()
        return TranslateDown(agent_id=agent_id, distance=distance)


class EverythingIsAwesomeActuator:
    """Actuator for the Everything Is Awesome hackathon environment.

    Note:
        Actuators are use case specific, and don't need to implement all Actuator(ABC)
        methods. In fact, the Actuator(ABC) should not be abstract, but concrete.
        In its place, we will likely want to use a Protocol instead.
    """

    def __init__(
        self, actuator_server: ActuatorProtocol, pitch_diameter_r: float
    ) -> None:
        self._actuator_server = actuator_server
        self._pitch_diameter_r = pitch_diameter_r
        """The pitch diamater in units of radii.

        One radius is the distance between the sensor and the center of the platform
        that the robot can rotate around.
        """

    def _distance_to_rotations(self, distance_r: float) -> float:
        """Convert a distance in radii to rotations.

        Args:
            distance_r: The distance in radii.

        Returns:
            The distance in rotations.
        """
        return distance_r / (np.pi * self._pitch_diameter_r)

    def actuate_orbit_left(self, action: OrbitLeft) -> None:
        # TODO: validate the sign of the degrees
        self._actuator_server.run_for_degrees(motor=Motor.ORBIT, degrees=action.degrees)

    def actuate_orbit_right(self, action: OrbitRight) -> None:
        # TODO: validate the sign of the degrees
        self._actuator_server.run_for_degrees(
            motor=Motor.ORBIT, degrees=-action.degrees
        )

    def actuate_translate_up(self, action: TranslateUp) -> None:
        rotations = self._distance_to_rotations(action.distance)
        # TODO: validate the sign of the rotations
        self._actuator_server.run_for_rotations(
            motor=Motor.TRANSLATE, rotations=rotations
        )

    def actuate_translate_down(self, action: TranslateDown) -> None:
        rotations = self._distance_to_rotations(action.distance)
        # TODO: validate the sign of the rotations
        self._actuator_server.run_for_rotations(
            motor=Motor.TRANSLATE, rotations=-rotations
        )


class OrbitLeftActionSampler(Protocol):
    def sample_orbit_left(self, agent_id: str) -> OrbitLeft: ...


class OrbitLeftActuator(Protocol):
    def actuate_orbit_left(self, action: OrbitLeft) -> None: ...


class OrbitLeft(Action):
    """Orbit at current distance from target to the left."""

    @classmethod
    def sample(cls, agent_id: str, sampler: OrbitLeftActionSampler) -> OrbitLeft:
        return sampler.sample_orbit_left(agent_id)

    def __init__(self, agent_id: str, degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.degrees = degrees

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

    def __init__(self, agent_id: str, degrees: float) -> None:
        super().__init__(agent_id=agent_id)
        self.degrees = degrees

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
    def run_for_degrees(self, motor: Motor, degrees: float) -> None: ...
    def run_for_rotations(self, motor: Motor, rotations: float) -> None: ...
    def run_to_position(self, motor: Motor, degrees: float) -> None: ...


class RgbProtocol(Protocol):
    def rgb(self) -> list[list[list[int]]]: ...


class DepthProtocol(Protocol):
    def depth(self) -> list[list[list[int]]]: ...

class ProprioceptionProtocol(Protocol):
    def absolute_position(self, motor: Motor) -> int: ...
    def position(self, motor: Motor) -> int: ...
    def speed(self, motor: Motor) -> int: ...
