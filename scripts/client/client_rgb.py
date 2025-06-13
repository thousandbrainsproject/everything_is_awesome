from time import perf_counter

import cv2
import numpy as np
import Pyro5.api

PATCH_SIZE = 180


class PatchViewerClient:
    def __init__(self, server_uri: str):
        self.server = Pyro5.api.Proxy(server_uri)
        self.canvas = np.zeros((PATCH_SIZE, PATCH_SIZE, 3), dtype=np.uint8)

    def fetch_center_patch(self):
        t1 = perf_counter()
        patch = self.server.rgb(PATCH_SIZE)
        print(perf_counter() - t1)
        if patch is not None:
            self.canvas[:, :] = patch

    def draw(self):
        display = self.canvas.copy()
        display = cv2.cvtColor(display, cv2.COLOR_RGB2BGR)
        cv2.imshow("Image Patch Viewer", display)

    def run(self):
        while True:
            self.draw()
            key = cv2.waitKey(0) & 0xFF  # Wait indefinitely for a key
            if key == ord("q"):
                break
            elif key == 13:  # Enter key
                self.fetch_center_patch()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    pv = PatchViewerClient(server_uri="PYRO:rgb@192.168.0.143:3512")
    pv.run()
