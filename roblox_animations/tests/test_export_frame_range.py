import importlib
import json
import unittest
import zlib

import bpy

from ..animation import serialization
from ..core.utils import (
    get_action_channelbag,
    get_animation_data_action_slot,
    invalidate_armature_cache,
)
from ..server import requests as server_requests

importlib.reload(serialization)


class TestExportFrameRange(unittest.TestCase):
    def setUp(self):
        for action in list(bpy.data.actions):
            bpy.data.actions.remove(action)
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for armature in list(bpy.data.armatures):
            bpy.data.armatures.remove(armature, do_unlink=True)
        bpy.context.view_layer.update()
        invalidate_armature_cache()

    def _make_armature_with_action(self, action_name, keyframes):
        bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
        armature_obj = bpy.context.object
        armature_obj.name = f"{action_name}Rig"

        bone = armature_obj.data.edit_bones.new("Root")
        bone.head = (0, 0, 0)
        bone.tail = (0, 0, 1)

        bpy.ops.object.mode_set(mode="POSE")
        pose_bone = armature_obj.pose.bones["Root"]
        pose_bone.bone["transform"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        pose_bone.bone["transform1"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        pose_bone.bone["nicetransform"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]

        action = bpy.data.actions.new(action_name)
        armature_obj.animation_data_create()
        armature_obj.animation_data.action = action

        fcurve = self._new_action_fcurve(
            armature_obj,
            action,
            'pose.bones["Root"].location',
            0,
        )
        fcurve.keyframe_points.add(len(keyframes))
        for point, frame in zip(fcurve.keyframe_points, keyframes):
            point.co = (float(frame), float(frame))

        return armature_obj

    def _new_action_fcurve(self, armature_obj, action, data_path, index):
        slot = get_animation_data_action_slot(
            getattr(armature_obj, "animation_data", None),
            action=action,
        )
        channelbag = get_action_channelbag(action, slot=slot)
        if channelbag and hasattr(channelbag, "fcurves"):
            return channelbag.fcurves.new(data_path, index=index)
        return action.fcurves.new(data_path=data_path, index=index)

    def _make_export_armature_without_action(self, name):
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
        armature_obj = bpy.context.object
        armature_obj.name = name

        if "Root" not in armature_obj.data.edit_bones:
            bone = armature_obj.data.edit_bones.new("Root")
            bone.head = (0, 0, 0)
            bone.tail = (0, 0, 1)

        bpy.ops.object.mode_set(mode="POSE")
        pose_bone = armature_obj.pose.bones["Root"]
        pose_bone.bone["transform"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        pose_bone.bone["transform1"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]
        pose_bone.bone["nicetransform"] = [1, 0, 0, 0, 1, 0, 0, 0, 1]

        return armature_obj

    def _add_copy_location_constraint(self, driven_armature, target_armature):
        bpy.context.view_layer.objects.active = driven_armature
        if driven_armature.mode != "POSE":
            bpy.ops.object.mode_set(mode="POSE")

        pose_bone = driven_armature.pose.bones["Root"]
        constraint = pose_bone.constraints.new(type="COPY_LOCATION")
        constraint.target = target_armature
        constraint.subtarget = "Root"
        constraint.owner_space = "WORLD"
        constraint.target_space = "WORLD"
        return constraint

    def test_export_range_sync_uses_new_action_after_file_switch(self):
        armature_obj = self._make_armature_with_action("First", (1, 44))
        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = 44

        new_action = bpy.data.actions.new("Second")
        armature_obj.animation_data.action = new_action
        fcurve = self._new_action_fcurve(
            armature_obj,
            new_action,
            'pose.bones["Root"].location',
            0,
        )
        fcurve.keyframe_points.add(2)
        fcurve.keyframe_points[0].co = (8.0, 0.0)
        fcurve.keyframe_points[1].co = (12.0, 1.0)

        resolved = serialization.sync_scene_frame_range_to_export_source(
            scene,
            armature_obj,
        )

        self.assertEqual(resolved, (8, 12))
        self.assertEqual(scene.frame_start, 8)
        self.assertEqual(scene.frame_end, 12)

    def test_export_range_uses_constraint_target_action_for_proxy_rig(self):
        control_armature = self._make_armature_with_action("Control", (6, 38))
        export_armature = self._make_export_armature_without_action("__Rig")
        self._add_copy_location_constraint(export_armature, control_armature)

        scene = bpy.context.scene
        scene.frame_start = 1
        scene.frame_end = 120

        resolved = serialization.sync_scene_frame_range_to_export_source(
            scene,
            export_armature,
        )

        self.assertEqual(resolved, (6, 38))
        self.assertEqual(scene.frame_start, 6)
        self.assertEqual(scene.frame_end, 38)

    def test_server_export_respects_scene_frame_range_each_time(self):
        armature_obj = self._make_armature_with_action("ActionA", (1, 90))
        scene = bpy.data.scenes.get("Scene") or bpy.context.scene

        action_b = bpy.data.actions.new("ActionB")
        fcurve_b = self._new_action_fcurve(
            armature_obj,
            action_b,
            'pose.bones["Root"].location',
            0,
        )
        fcurve_b.keyframe_points.add(2)
        fcurve_b.keyframe_points[0].co = (1.0, 0.0)
        fcurve_b.keyframe_points[1].co = (45.0, 1.0)

        action_c = bpy.data.actions.new("ActionC")
        fcurve_c = self._new_action_fcurve(
            armature_obj,
            action_c,
            'pose.bones["Root"].location',
            0,
        )
        fcurve_c.keyframe_points.add(2)
        fcurve_c.keyframe_points[0].co = (1.0, 0.0)
        fcurve_c.keyframe_points[1].co = (100.0, 1.0)

        def export_with_scene_range(action, frame_end, task_id):
            scene.frame_start = 1
            scene.frame_end = frame_end
            armature_obj.animation_data.action = action
            server_requests.pending_responses.pop(task_id, None)
            server_requests.execute_in_main_thread(task_id, armature_obj.name)
            success, payload = server_requests.pending_responses.pop(task_id)
            self.assertTrue(success)
            exported = json.loads(zlib.decompress(payload).decode("utf-8"))
            return exported["export_info"]["frame_start"], exported["export_info"]["frame_end"]

        a_start, a_end = export_with_scene_range(armature_obj.animation_data.action, 90, "task_a")
        self.assertEqual((a_start, a_end), (1, 90))

        b_start, b_end = export_with_scene_range(action_b, 90, "task_b")
        self.assertEqual((b_start, b_end), (1, 90))

        c_start, c_end = export_with_scene_range(action_c, 45, "task_c")
        self.assertEqual((c_start, c_end), (1, 45))

        b2_start, b2_end = export_with_scene_range(action_b, 100, "task_b2")
        self.assertEqual((b2_start, b2_end), (1, 100))


if __name__ == "__main__":
    unittest.main()
