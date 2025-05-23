# Copyright 2025 Thousand Brains Project
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import os

import numpy as np
import trimesh
import vedo


class EverythingIsAwesomeTrainVisualizer(vedo.Plotter):
    def __init__(self, axes=False):
        super().__init__()
        self.show_axes = axes
        self.graph_obj = None
        self.agent_obj = None

    def update_data(self, graph, agent_position, interactive=False):
        self.clear_scene()

        # add graph points
        self.graph_obj = vedo.Points(graph, r=5).c("black")
        self.add(self.graph_obj)

        # add agent
        self.agent_obj = self.add_agent(agent_position)
        self.add(self.agent_obj)

        self.render()
        self.show(resetcam=True, interactive=interactive, axes=self.show_axes)

    def add_agent(self, position):
        return vedo.Cube(side=0.1).scale(0.1).pos(position).color("red")

    def clear_scene(self):
        if self.graph_obj is not None:
            self.remove(self.graph_obj)
            self.graph_obj = None

        if self.agent_obj is not None:
            self.remove(self.agent_obj)
            self.agent_obj = None


class EverythingIsAwesomeEvalVisualizer(vedo.Plotter):
    def __init__(self, axes=False):
        super().__init__()
        self.show_axes = axes
        self.initialize_parameters()

        self.forward_axis = np.array([-1, 0, 0])
        self.up_axis = np.array([0, 0, 1])
        self.data_dir = os.path.join(os.environ["MONTY_DATA"], "tbp_robot_lab/meshes")

    def update_data(
        self, mlh_object, object_orientation, agent_position, agent_orientation
    ):
        glb_path = self.find_glb_orig(self.data_dir, mlh_object)
        if self.glb_path != glb_path:
            self.clear_scene()
            self.add_glb(glb_path, load_texture=False)
            self.glb_path = glb_path

        self.set_camera_absolute_orientation(
            position=agent_position, orientation=agent_orientation
        )

        self.set_object_orientation(orientation=object_orientation)

        self.show(resetcam=False, interactive=False, axes=self.show_axes)

    def find_glb_orig(self, data_dir, object_name):
        """Searches for the .glb.orig file of a given YCB object in a directory.

        Args:
            data_dir: The root directory where YCB objects are stored.
            object_name: The object name to search for (e.g., "master_chef_can").

        Returns:
            The full path to the .glb.orig file if found; otherwise, None.
        """
        for dirpath, dirnames, _ in os.walk(data_dir):
            for dirname in dirnames:
                if dirname.endswith(object_name):
                    glb_orig_path = os.path.join(
                        dirpath, dirname, "google_16k", "textured.glb"
                    )
                    if os.path.exists(glb_orig_path):
                        return glb_orig_path
                    else:
                        glb_orig_path = os.path.join(dirpath, dirname, "textured.glb")
                        if os.path.exists(glb_orig_path):
                            return glb_orig_path

        return None  # Return None if no match is found

    def set_object_orientation(self, orientation):
        orientation_xyz = orientation.as_euler("xyz", orientation)
        self.obj.rotate_x(orientation_xyz[0], rad=False)
        self.obj.rotate_y(orientation_xyz[1], rad=False)
        self.obj.rotate_z(orientation_xyz[2], rad=False)

    def set_camera_absolute_orientation(
        self,
        position: np.ndarray,
        orientation: np.ndarray,
    ):
        forward_world = orientation.apply(self.forward_axis)
        up_world = orientation.apply(self.up_axis)
        focal_point = position + forward_world

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

    def add_glb(self, file, load_texture=False):
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
        if load_texture:
            img.save("tmp_texture.png", format="PNG")
            obj.texture("tmp_texture.png", tcoords=uv)
            os.remove("tmp_texture.png")

        # add mesh to plotter
        self.obj = obj
        self.add(obj)
