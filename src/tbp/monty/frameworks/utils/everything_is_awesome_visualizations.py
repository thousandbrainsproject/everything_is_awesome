import os
import time

import numpy as np
import trimesh
import vedo


class EverythingIsAwesomeVisualizer(vedo.Plotter):
    def __init__(self, axes=False):
        super().__init__()
        self.show_axes = axes
        self.initialize_parameters()

    def update_data(
        self, glb_path, object_orientation, agent_position, agent_orientation
    ):
        if self.glb_path != glb_path:
            self.add_glb(glb_path)
            self.glb_path = glb_path

        self.set_camera_absolute_orientation(
            position=agent_position, orientation=agent_orientation
        )

        self.set_object_orientation(orientation=object_orientation)

        self.show(resetcam=False, interactive=False, axes=self.show_axes)
        time.sleep(0.01)

    def set_object_orientation(self, orientation):
        orientation_xyz = orientation.as_euler("xyz", orientation)
        self.obj.rotate_x(orientation_xyz[0], rad=False)
        self.obj.rotate_y(orientation_xyz[1], rad=False)
        self.obj.rotate_z(orientation_xyz[2], rad=False)

    def set_camera_absolute_orientation(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
        forward_axis: np.ndarray = np.array([-1, 0, 0]),
        up_axis: np.ndarray = np.array([0, 0, 1]),
    ):
        forward_world = orientation.apply(forward_axis)
        up_world = orientation.apply(up_axis)
        focal_point = position + forward_world  # Look "one unit" ahead in world space

        self.camera.SetPosition(*position)
        self.camera.SetFocalPoint(*focal_point)
        self.camera.SetViewUp(*up_world)

    def clear_scene(self):
        if self.obj is not None:
            self.remove(self.obj)
            self.obj = None

        self.render()

    def initialize_parameters(self):
        self.glb_path = ""
        self.obj = None
        self.cam = None

    def add_glb(self, file):
        def load_glb_orig_binary(file_path):
            with open(file_path, "rb") as f:
                mesh = trimesh.load(f, file_type="glb")
            return mesh

        # read the glb file
        geometry = list(load_glb_orig_binary(file).geometry.values())[0]
        vertices = geometry.vertices
        faces = geometry.faces
        uv = geometry.visual.uv
        img = geometry.visual.material.baseColorTexture

        # create mesh from vertices and faces
        obj = vedo.Mesh([geometry.vertices, geometry.faces])

        # add texture
        img.save("tmp_texture.png", format="PNG")
        obj.texture("tmp_texture.png", tcoords=uv)
        os.remove("tmp_texture.png")

        # add mesh to plotter
        self.obj = obj
        self.add(obj)

    def add_sensor(self):
        self.camera_position = (0.1, 0.1, 0.1)  # Position of the camera in 3D space
        self.focal_point = (0, 0, 0)  # The point the camera is looking at

        self.cam = (
            vedo.Cube(side=0.1).scale(0.05).pos(self.camera_position).color("red")
        )
        self.line = (
            vedo.Line(self.camera_position, self.focal_point).color("black").lw(2)
        )

        self.add(self.cam)
        self.add(self.line)


if __name__ == "__main__":
    mug_glb_path = "/home/ramy/tbp/data/habitat/objects/ycb/meshes/025_mug/google_16k/textured.glb.orig"
    vis = EverythingIsAwesomeVisualizer(axes=False)

    for i in range(10):
        vis.update_data(
            mug_glb_path,
            object_orientation=(0, 0, 0),
            agent_position=(0, 1.5, i / 100),
            agent_orientation=(0, 0, 0),
        )
