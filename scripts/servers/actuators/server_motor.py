import Pyro5.api
from buildhat import Motor

from pyro_utils import Pyro5Mixin

SPEED = 10


class MotorController:
    def __init__(self, *args, **kwargs):
        self.motors = {"translate": Motor("A"), "orbit": Motor("D")}

    @Pyro5.api.expose
    def run_for_degrees(self, motor, degrees):
        self.motors[motor].run_for_degrees(degrees, speed=SPEED)

    @Pyro5.api.expose
    def run_for_rotations(self, motor, rotations):
        self.motors[motor].run_for_rotations(rotations, speed=SPEED)

    @Pyro5.api.expose
    def run_to_position(self, motor, degrees):
        self.motors[motor].run_to_position(degrees, speed=SPEED)

    @Pyro5.api.expose
    def absolute_position(self, motor: Motor):
        return self.motors[motor].get_aposition()

    @Pyro5.api.expose
    def position(self, motor):
        return self.motors[motor].get_position()

    @Pyro5.api.expose
    def speed(self, motor):
        return self.motors[motor].get_speed()


@Pyro5.api.expose
class MotorControllerServer(Pyro5Mixin, MotorController):
    pass


if __name__ == "__main__":
    daemon = Pyro5.api.Daemon(host="192.168.0.235", port=3514)
    MotorControllerServer(daemon=daemon, object_id="motor").run()
