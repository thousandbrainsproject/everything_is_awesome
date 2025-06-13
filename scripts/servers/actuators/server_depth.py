import ArducamDepthCamera as ac
import cv2
import numpy as np
import Pyro5.api
from pyro_utils import Pyro5Mixin

MAX_DISTANCE = 2000

class DepthPatchCamera:
    def __init__(self, *args, **kwargs):
        self.cam = ac.ArducamCamera()
        ret = self.cam.open(ac.Connection.CSI, 0)
        if ret != 0:
            raise RuntimeError(f"[DepthPatchCamera] Failed to open camera (code {ret})")

        ret = self.cam.start(ac.FrameType.DEPTH)
        if ret != 0:
            raise RuntimeError(
                f"[DepthPatchCamera] Failed to start camera (code {ret})"
            )

        self.cam.setControl(ac.Control.RANGE, MAX_DISTANCE)
        self.max_range = self.cam.getControl(ac.Control.RANGE)

        # Initialize once to get dimensions
        frame = self.cam.requestFrame(MAX_DISTANCE)
        if frame is None or not isinstance(frame, ac.DepthData):
            raise RuntimeError("[DepthPatchCamera] Failed to get initial frame.")

        self.height, self.width = frame.depth_data.shape
        self.cam.releaseFrame(frame)

        print(f"[DepthPatchCamera] Started with resolution: {self.width}x{self.height}")

    def _get_colorized_depth_frame(self):
        frame = self.cam.requestFrame(MAX_DISTANCE)
        if frame is None or not isinstance(frame, ac.DepthData):
            return None

        depth = frame.depth_data
        conf = frame.confidence_data
        self.cam.releaseFrame(frame)

        # Normalize and apply colormap
        depth_image = (depth * (255.0 / self.max_range)).astype(np.uint8)
        colorized = cv2.applyColorMap(depth_image, cv2.COLORMAP_RAINBOW)
        colorized[conf < 30] = (0, 0, 0)
        return colorized

    @Pyro5.api.expose
    def depth_color(self, size: int = 64):
        image = self._get_colorized_depth_frame()
        if image is None:
            return None
        image = cv2.rotate(image, cv2.ROTATE_180)
        x_center, y_center = self.width // 2, self.height // 2
        side = size // 2
        x1, x2 = x_center - side, x_center + side
        y1, y2 = y_center - side, y_center + side
        patch = image[y1:y2, x1:x2]

        return patch.tolist()

    @Pyro5.api.expose
    def depth(self, size: int = 64):
        frame = self.cam.requestFrame(MAX_DISTANCE)

        depth_image = frame.depth_data
        #conf = frame.confidence_data
        self.cam.releaseFrame(frame)

        # Normalize depth to 0-255
        #depth_image = (depth_image * (255.0 / self.max_range)).astype(np.uint8)

        # Mask out low-confidence areas
        # depth_image[conf < 30] = 0

        # Rotate 180 degrees
        depth_image = cv2.rotate(depth_image, cv2.ROTATE_180)

        # Extract patch from center
        x_center, y_center = self.width // 2, self.height // 2
        side = size // 2
        x1, x2 = x_center - side, x_center + side
        y1, y2 = y_center - side, y_center + side
        patch = depth_image[y1:y2, x1:x2]

        return patch.tolist()

    def stop(self):
        self.cam.stop()
        self.cam.close()
        print("[DepthPatchCamera] Camera stopped.")


@Pyro5.api.expose
class DepthPatchCameraServer(Pyro5Mixin, DepthPatchCamera):
    pass


if __name__ == "__main__":
    daemon = Pyro5.api.Daemon(host="192.168.0.235", port=3513)
    DepthPatchCameraServer(daemon=daemon, object_id="depth").run()

