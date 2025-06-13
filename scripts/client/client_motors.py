import time
from enum import Enum

import Pyro5.api


class Motor(Enum):
    ORBIT = "orbit"
    TRANSLATE = "translate"


class MotorClient:
    def __init__(self, server_uri: str):
        self.server = Pyro5.api.Proxy(server_uri)

    def run_for_degrees(self, motor: Motor, degrees: float) -> None:
        self.server.run_for_degrees(motor, degrees)

    def run_for_rotations(self, motor: Motor, rotations: float) -> None:
        self.server.run_for_rotations(motor, rotations)

    def run_to_position(self, motor: Motor, degrees: float) -> None:
        self.server.run_to_position(motor, degrees)

    def absolute_position(self, motor: Motor) -> int:
        return self.server.absolute_position(motor)

    def position(self, motor: Motor) -> int:
        return self.server.position(motor)

    def speed(self, motor: Motor) -> int:
        return self.server.speed(motor)

    def run(self):
        self.run_for_rotations(Motor.TRANSLATE, -1)
        time.sleep(0.2)
        self.run_for_rotations(Motor.ORBIT, -0.5)
        time.sleep(0.2)
        self.run_for_rotations(Motor.TRANSLATE, 0.5)
        time.sleep(0.2)
        self.run_for_rotations(Motor.ORBIT, -0.5)
        time.sleep(0.2)
        self.run_for_rotations(Motor.TRANSLATE, -0.5)
        time.sleep(0.2)
        self.run_for_rotations(Motor.ORBIT, -0.5)
        time.sleep(0.2)


if __name__ == "__main__":
    pv = MotorClient(server_uri="PYRO:motor@192.168.0.235:3514")
    pv.run()
