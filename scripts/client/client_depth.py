import cv2
import numpy as np
import Pyro5.api

PATCH_SIZE = 180  # maximum is 180


class PatchViewerClient:
    def __init__(self, server_uri: str):
        self.server = Pyro5.api.Proxy(server_uri)
        self.canvas = np.zeros((PATCH_SIZE, PATCH_SIZE), dtype=np.float64)

    def fetch_center_patch(self):
        patch = self.server.depth(PATCH_SIZE)
        if patch is not None:
            self.canvas[:, :] = patch

    def draw(self):
        display = self.canvas.copy()
        cv2.imshow("Image Patch Viewer", display)

    def run(self):
        while True:
            self.draw()
            key = cv2.waitKey(0) & 0xFF  # Wait indefinitely for a key
            if key == ord("q"):
                break
            elif key == 13:  # Enter key
                self.fetch_center_patch()
                # point = self.canvas[90, 90]
                # y_val = 0.003846 * point - 0.1569
                # print(y_val)

        cv2.destroyAllWindows()


if __name__ == "__main__":
    pv = PatchViewerClient(server_uri="PYRO:depth@192.168.0.235:3513")
    pv.run()
