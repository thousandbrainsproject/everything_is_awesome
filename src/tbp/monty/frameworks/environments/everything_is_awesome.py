# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, TypedDict, Union, cast

import cv2
import numpy as np
import Pyro5.api
import quaternion
from numpy.random import Generator
from scipy.spatial.transform import Rotation as R  # noqa: N817

from tbp.monty.frameworks.actions.action_samplers import ActionSampler
from tbp.monty.frameworks.actions.actions import Action
from tbp.monty.frameworks.environments.embodied_data import EnvironmentDataLoader
from tbp.monty.frameworks.environments.embodied_environment import (
    ActionSpace,
    EmbodiedEnvironment,
)
from tbp.monty.frameworks.measure import measure_time
from tbp.monty.frameworks.models.motor_policies import BasePolicy
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
    id: Motor
    absolute_position: int = 0
    origin: int = 0
    position: int = 0
    speed: int = 0


class EverythingIsAwesomeEnvironment(EmbodiedEnvironment):
    """Everything Is Awesome hackathon environment."""

    def __init__(
        self,
        actuator_server_uri: str,
        depth_server_uri: str,
        pitch_diameter_rr: float,
        rgb_server_uri: str,
    ) -> None:
        """Initialize the Everything Is Awesome environment.

        Args:
            actuator_server_uri: The URI of the actuator server.
            depth_server_uri: The URI of the depth server.
            pitch_diameter_rr: The pitch diameter in units of robot_radius. One
                robot_radius is the distance between the sensor and the center of the
                platform that the robot can rotate around.
            rgb_server_uri: The URI of the rgb server.
        """
        self._actuator_server = cast(
            Union[ActuatorProtocol, ProprioceptionProtocol],
            Pyro5.api.Proxy(actuator_server_uri),
        )
        self._pitch_diameter_rr = pitch_diameter_rr
        self._actuator = EverythingIsAwesomeActuator(
            actuator_server=self._actuator_server,
            pitch_diameter_rr=self._pitch_diameter_rr,
        )
        self._proprioception_server = cast(
            ProprioceptionProtocol, self._actuator_server
        )
        self._depth_server = cast(DepthProtocol, Pyro5.api.Proxy(depth_server_uri))
        self._rgb_server = cast(RgbProtocol, Pyro5.api.Proxy(rgb_server_uri))

        self._orbit_motor = MotorState(id=Motor.ORBIT)
        self._translate_motor = MotorState(id=Motor.TRANSLATE)

        self._update_orbit_motor_state()
        self._update_translate_motor_state()

    @property
    def action_space(self) -> ActionSpace:
        raise NotImplementedError

    def add_object(self):
        raise NotImplementedError

    def close(self):
        pass

    def _extract_patch(self, img, side=70, resize_to=None, start_pos=(0, 0)):
        """Extracts a patch from the given image.

        Args:
          img (numpy.array): The input image.
          side (int): The size of the square patch to extract. Defaults to 70.
          resize_to (tuple or int): Optional tuple specifying the new dimensions
            for resizing, or an integer for a single dimension. If None, no resizing
            is performed.
          start_pos (tuple): A tuple specifying the starting position of the patch,
            as (x, y) coordinates. Uses top left for the origin. Defaults to (0, 0).

        Returns:
          numpy.array: A 2D array representing the extracted patch.
        """
        if resize_to is not None:
            img = cv2.resize(img, resize_to, interpolation=cv2.INTER_NEAREST)

        start_x, start_y = start_pos
        end_x, end_y = start_x + side, start_y + side
        patch = img[start_y:end_y, start_x:end_x]
        return patch

    @measure_time(__name__)
    def _observations(self) -> EverythingIsAwesomeObservations:
        """Requests and prepares RGB and depth observations.

        This function will call the server proxy to request RGB and depth images,
        then the images are stitched and patches are extracted to be used for
        observations. Note that the stitching parameters (e.g., resize_to, start_pos)
        are based on the hardware design of the robot and the placement of the sensors.

        Returns:
          EverythingIsAwesomeObservations: An object containing RGB and depth
            observations, as well as other relevant information.
        """
        # Get RGB image and extract the patch
        rgb = self._rgb()
        rgb_patch = self._extract_patch(rgb, start_pos=(0, 0))

        # stack alpha channel with 255 to the rgb
        alpha_patch = np.full(rgb_patch.shape[:2], 255, dtype=rgb_patch.dtype)
        rgba_patch = np.dstack((rgb_patch, alpha_patch))

        # Get Depth image and extract the patch
        # Linear transformation coefficients are specific to depth sensor.
        depth = self._depth()
        depth_patch = self._extract_patch(
            depth, resize_to=(1000, 1000), start_pos=(550, 350)
        )
        depth_patch = 0.003846 * depth_patch - 0.1569

        return EverythingIsAwesomeObservations(
            agent_id_0=EverythingIsAwesomeAgentObservation(
                patch=EverythingIsAwesomeSensorObservation(
                    rgba=rgba_patch,
                    depth=depth_patch,
                )
            )
        )

    def _rgb(self) -> np.ndarray:
        rgb = np.array(self._rgb_server.rgb(size=100), dtype=np.uint8)
        return rgb

    def _depth(self) -> np.ndarray:
        depth = np.array(self._depth_server.depth(size=180), dtype=np.float64)
        return depth

    def _update_orbit_motor_state(self) -> None:
        """Updates the orbit motor state from the proprioception server.

        Only updates the absolute position, position, and speed.
        """
        self._orbit_motor.absolute_position = (
            self._proprioception_server.absolute_position(Motor.ORBIT)
        )
        self._orbit_motor.position = self._proprioception_server.position(Motor.ORBIT)
        self._orbit_motor.speed = self._proprioception_server.speed(Motor.ORBIT)

    def _update_translate_motor_state(self) -> None:
        """Updates the translate motor state from the proprioception server.

        Only updates the absolute position, position, and speed.
        """
        self._translate_motor.absolute_position = (
            self._proprioception_server.absolute_position(Motor.TRANSLATE)
        )
        self._translate_motor.position = self._proprioception_server.position(
            Motor.TRANSLATE
        )
        self._translate_motor.speed = self._proprioception_server.speed(Motor.TRANSLATE)

    @measure_time(__name__)
    def step(self, action: Action) -> EverythingIsAwesomeObservations:
        action.act(self._actuator)
        return self._observations()

    def get_state(self) -> ProprioceptiveState:
        """Get the Monty proprioceptive state from the environment.

        The coordinate origin is located above the orbit motor, inline with the
        bottom-most position of the camera sensors.

        In the reset position, the translate motor is at a minimum position possible.
        The orbit motor is at an arbitrary position it considers to be 0 degrees.
        The default orientation of the robot from which all rotations are calculated
        is [1, 0, 0, 0] in WXYZ format. This is to be interpreted as a robot at location
        [0,0,1] and facing the origin, looking down the negative Z axis.

        The units of the coordinate system are robot_radius. So, that location [0,0,1]
        places the robot on the ZX unit circle, on the positive Z axis, 1 robot_radius
        away from the origin.

        Returns:
            ProprioceptiveState: The Monty proprioceptive state.
        """
        self._update_orbit_motor_state()
        self._update_translate_motor_state()

        orbit_degrees = self._orbit_motor.position - self._orbit_motor.origin
        orbit_radians = np.radians(orbit_degrees)
        z_pos = np.cos(orbit_radians)
        x_pos = np.sin(orbit_radians)
        translate_degrees = (
            self._translate_motor.position - self._translate_motor.origin
        )
        translate_radians = np.radians(translate_degrees)
        y_pos = translate_radians * self._pitch_diameter_rr
        position = [x_pos, y_pos, z_pos]

        # Simple rotation around the y-axis. This assumes agent starts at
        # an orientation facing the object.
        # Note: simpler due to x_pos and y_pos being on the unit circle
        orientation = R.from_euler("y", orbit_radians, degrees=False)
        orientation_quat = orientation.as_quat().tolist()
        rotation_candidate_one = quaternion.from_float_array(
            np.array([orientation_quat[3], *orientation_quat[:3]])
        )
        rotation_candidate_two = quaternion.from_float_array(
            np.array(
                [
                    np.cos(orbit_radians / 2),
                    0,
                    np.sin(orbit_radians / 2),
                    0,
                ]
            )
        )
        assert np.allclose(
            quaternion.as_float_array(rotation_candidate_one),
            quaternion.as_float_array(rotation_candidate_two),
        )
        rotation = rotation_candidate_one

        return ProprioceptiveState(
            agent_id_0=AgentState(
                sensors={
                    "patch.depth": SensorState(
                        # The sensor is fully coupled to the agent's position
                        position=[0.0, 0.0, 0.0],
                        rotation=quaternion.from_float_array([1.0, 0.0, 0.0, 0.0]),
                    ),
                    "patch.rgba": SensorState(
                        # The sensor is fully coupled to the agent's position
                        position=[0.0, 0.0, 0.0],
                        rotation=quaternion.from_float_array([1.0, 0.0, 0.0, 0.0]),
                    ),
                },
                position=position,
                rotation=rotation,
            )
        )

    def remove_all_objects(self):
        raise NotImplementedError

    def reset(self) -> EverythingIsAwesomeObservations:
        # slowly move the translate motor to the bottom
        curr_pos = self._proprioception_server.position(Motor.TRANSLATE)
        prev_pos = curr_pos + 1  # just make them different
        while prev_pos != curr_pos:
            self._actuator_server.run_for_rotations(
                motor=Motor.TRANSLATE,
                rotations=-EverythingIsAwesomeActuator.MIN_GRAVITY_ASSISTED_ROTATION,
            )
            prev_pos = curr_pos
            curr_pos = self._proprioception_server.position(Motor.TRANSLATE)

        # reset to the arbitrary starting position
        self._actuator_server.run_to_position(motor=Motor.ORBIT, degrees=45.0)
        time.sleep(0.5)
        self._actuator_server.run_to_position(motor=Motor.ORBIT, degrees=0.0)
        time.sleep(0.5)
        self._update_orbit_motor_state()
        self._orbit_motor.origin = self._orbit_motor.position
        self._update_translate_motor_state()
        self._translate_motor.origin = self._translate_motor.position

        # Note: Set at top of module once importlib.reload(logging) is removed
        logger = logging.getLogger(__name__)

        logger.info(self._orbit_motor)
        logger.info(self._translate_motor)

        return self._observations()


class EverythingIsAwesomeDataLoader(EnvironmentDataLoader):
    """DataLoader for the Everything Is Awesome hackathon environment."""

    def __init__(self, object_name: str, *args, **kwargs) -> None:
        """Initialize the data loader.

        Args:
            object_name: The ground truth name of the object presented to the robot.
            *args: Additional arguments to pass to the parent class.
            **kwargs: Additional keyword arguments to pass to the parent class.
        """
        super().__init__(*args, **kwargs)
        self._object_name = object_name
        self.primary_target = {
            "object": self._object_name,
            "rotation": np.quaternion(0, 0, 0, 1),
            "euler_rotation": np.array([0, 0, 0]),
            "quat_rotation": [0, 0, 0, 1],
            "position": np.array([0, 0, 0]),
            "scale": [1.0, 1.0, 1.0],
        }

    def __iter__(self):
        """Do not reset the dataset when starting the iterator.

        Returns:
            The iterator.
        """
        return self


class EverythingIsAwesomePolicy(BasePolicy):
    """Policy for the Everything Is Awesome hackathon environment."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.use_goal_state_driven_actions = False


class EverythingIsAwesomeTrainingPolicy(BasePolicy):
    """Training policy for the Everything Is Awesome hackathon environment."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.use_goal_state_driven_actions = False
        self._level = 0
        self._max_levels = 10
        self._rotation_degrees = 0
        self._orbit_step = 7
        self._translate_step = 0.00774016

    def dynamic_call(
        self, _state: MotorSystemState | None = None
    ) -> OrbitLeft | OrbitRight | TranslateUp:
        """Sample an action from the policy.

        From the starting position, alternates orbiting all the way around the object
        and then translating up the object. Effectively, doing a 360 degree scan of the
        object from the bottom to the top.

        Args:
            _state (MotorSystemState | None): The current state of the motor system.
                Defaults to None. Unused.

        Returns:
            OrbitLeft | OrbitRight | TranslateUp: An action to take.

        Raises:
            StopIteration: If the policy is done scanning.
        """
        if self._level < self._max_levels:
            if self._rotation_degrees < 360:
                self._rotation_degrees += self._orbit_step
                return OrbitRight(agent_id=self.agent_id, degrees=self._orbit_step)
            else:
                self._level += 1
                self._rotation_degrees = 0
                return TranslateUp(
                    agent_id=self.agent_id, distance=self._translate_step
                )

        # I am not proud of this, but... hackathon.
        raise StopIteration()


class EverythingIsAwesomeActionSampler(ActionSampler):
    """ActionSampler for the Everything Is Awesome hackathon environment."""

    MIN_ORBIT_DEGREES = 5.0  # Empirically determined
    MAX_ORBIT_DEGREES = 45.0  # Arbitrary choice

    MIN_TRANSLATE_DISTANCE = 0.00774016  # Empirically determined
    MAX_TRANSLATE_DISTANCE = 0.1  # Arbitrary choice

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
        return self.rng.uniform(low=self.MIN_ORBIT_DEGREES, high=self.MAX_ORBIT_DEGREES)

    def _sample_distance(self) -> float:
        return self.rng.uniform(
            low=self.MIN_TRANSLATE_DISTANCE, high=self.MAX_TRANSLATE_DISTANCE
        )

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

    MIN_AGAINST_GRAVITY_ROTATION = 0.1  # Empirically determined
    MIN_GRAVITY_ASSISTED_ROTATION = 0.02  # Empirically determined
    MAX_GRAVITY_ASSISTED_ROTATION = 0.1  # Empirically determined

    def __init__(
        self, actuator_server: ActuatorProtocol, pitch_diameter_rr: float
    ) -> None:
        self._actuator_server = actuator_server
        self._pitch_diameter_rr = pitch_diameter_rr
        """The pitch diamater in units of robot_radius.

        One robot_radius is the distance between the sensor and the center of the
        platform that the robot can rotate around.

        Note:
            The robot_radius is 276mm.
            The pitch diameter is 17mm, pitch diameter is 34mm.
            The pitch diameter in robot_radius is 34mm / 276mm = 0.12318841.
        """
        self._min_distance_rr = (
            np.pi
            * self._pitch_diameter_rr
            * min(self.MIN_AGAINST_GRAVITY_ROTATION, self.MIN_GRAVITY_ASSISTED_ROTATION)
        )

    def _distance_to_rotations(self, distance_rr: float) -> float:
        """Convert a distance in robot_radius to rotations.

        Args:
            distance_rr: The distance in robot_radius.

        Returns:
            The distance in rotations.
        """
        return distance_rr / (np.pi * self._pitch_diameter_rr)

    def actuate_orbit_left(self, action: OrbitLeft) -> None:
        self._actuator_server.run_for_degrees(
            motor=Motor.ORBIT, degrees=-action.degrees
        )

    def actuate_orbit_right(self, action: OrbitRight) -> None:
        self._actuator_server.run_for_degrees(motor=Motor.ORBIT, degrees=action.degrees)

    def actuate_translate_up(self, action: TranslateUp) -> None:
        rotations = self._distance_to_rotations(action.distance)
        # account for minimum viable rotation against gravity
        rotations = max(rotations, self.MIN_AGAINST_GRAVITY_ROTATION)
        self._actuator_server.run_for_rotations(
            motor=Motor.TRANSLATE, rotations=rotations
        )

    def actuate_translate_down(self, action: TranslateDown) -> None:
        rotations = self._distance_to_rotations(action.distance)
        # account for minimum viable gravity-assisted rotation
        rotations = max(rotations, self.MIN_GRAVITY_ASSISTED_ROTATION)
        # account for maximum gravity-assisted rotation
        rotations = min(rotations, self.MAX_GRAVITY_ASSISTED_ROTATION)
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
    def rgb(self, size: int = 64) -> list[list[list[int]]]: ...


class DepthProtocol(Protocol):
    def depth(self, size: int = 64) -> list[list[list[int]]]: ...


class ProprioceptionProtocol(Protocol):
    def absolute_position(self, motor: Motor) -> int: ...
    def position(self, motor: Motor) -> int: ...
    def speed(self, motor: Motor) -> int: ...
