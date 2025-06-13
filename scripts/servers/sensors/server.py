import time
import cv2
import Pyro5.api
import numpy as np
from picamera2 import Picamera2

from pyro_utils import Pyro5Mixin


class PatchCamera:
    def __init__(self, *args, **kwargs):
        # Initialize and configure Picamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(main={"size": (800, 600)})
        self.picam2.configure(config)
        self.picam2.start()
        self.width = 800
        self.height = 600
        print("[PatchCamera] Picamera2 started.")

    @Pyro5.api.expose
    def rgb(self, size: int = 64):
        # Capture a new frame for every request
        image = self.picam2.capture_array()
        if image is None:
            return None

        image = cv2.rotate(image, cv2.ROTATE_180)
        h, w, _ = image.shape
        x_center, y_center= self.width//2, self.height//2
        side = size//2
        x1, x2 = x_center-side, x_center+side
        y1, y2 = y_center-side, y_center+side
        patch = image[y1:y2, x1:x2]

        return patch.tolist()

    def stop(self):
        self.picam2.stop()
        print("[PatchCamera] Camera stopped.")


@Pyro5.api.expose
class PatchCameraServer(Pyro5Mixin, PatchCamera):
    pass


if __name__ == "__main__":
    daemon = Pyro5.api.Daemon(host="192.168.0.143", port=3512)
    PatchCameraServer(daemon=daemon, object_id="rgb").run()

