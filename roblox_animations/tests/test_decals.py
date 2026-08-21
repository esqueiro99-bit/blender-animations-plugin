import unittest
from unittest import mock
import sys
import os

if "bpy" not in sys.modules:
    mock_bpy = mock.MagicMock()
    mock_bpy.app.version = (4, 2, 0)
    sys.modules["bpy"] = mock_bpy
    sys.modules["bpy.types"] = mock.MagicMock()
    sys.modules["bpy.props"] = mock.MagicMock()
    sys.modules["bpy_extras"] = mock.MagicMock()
    sys.modules["bpy_extras.io_utils"] = mock.MagicMock()

from ..animation.decals import (
    natural_sort_key,
    set_decal_transparency,
    generate_roblox_luau_script,
    DECAL_VAL_PREFIX,
    DECAL_NODE_PREFIX,
)



class TestDecals(unittest.TestCase):
    def test_natural_sort_order(self):
        decal_names = ["Face.10", "Face.2", "Face.1", "Face.20", "Face.3", "Face.6"]
        sorted_names = sorted(decal_names, key=natural_sort_key)
        self.assertEqual(sorted_names, ["Face.1", "Face.2", "Face.3", "Face.6", "Face.10", "Face.20"])

    def test_transparency_mode_roblox(self):
        mock_mat = mock.MagicMock()
        mock_val_node = mock.MagicMock()
        mock_mat.node_tree.nodes.get.return_value = mock_val_node
        mock_mat.use_nodes = True

        # In Roblox mode: 0.0 is fully visible -> Alpha = 1.0
        set_decal_transparency(mock_mat, "Face.1", 0.0, mode='ROBLOX')
        mock_val_node.outputs[0].default_value = 1.0

        # In Roblox mode: 1.0 is invisible -> Alpha = 0.0
        set_decal_transparency(mock_mat, "Face.1", 1.0, mode='ROBLOX')
        mock_val_node.outputs[0].default_value = 0.0

    def test_luau_script_generation(self):
        mock_mat = mock.MagicMock()
        mock_mat.use_nodes = True
        mock_mat.node_tree.animation_data = None

        node1 = mock.MagicMock()
        node1.type = 'VALUE'
        node1.name = f"{DECAL_VAL_PREFIX}Face.1"
        node1.outputs = [mock.MagicMock(default_value=1.0)]

        node2 = mock.MagicMock()
        node2.type = 'VALUE'
        node2.name = f"{DECAL_VAL_PREFIX}Face.2"
        node2.outputs = [mock.MagicMock(default_value=0.0)]

        mock_mat.node_tree.nodes = [node1, node2]
        mock_mat.node_tree.nodes.get.side_effect = lambda n: node1 if "Face.1" in n else node2

        with mock.patch("bpy.context") as mock_context:
            mock_context.scene.render.fps = 30
            mock_context.scene.frame_start = 0
            mock_context.scene.frame_end = 60

            script = generate_roblox_luau_script(mock_mat, part_name="Face")
            self.assertIn("setupFaceDecalAnimation", script)
            self.assertIn("Face.1", script)
            self.assertIn("Face.2", script)
            self.assertIn("Decal.Transparency", script)


if __name__ == "__main__":
    unittest.main()
