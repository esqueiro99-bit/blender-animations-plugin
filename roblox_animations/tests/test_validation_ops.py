import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

from ..operators import validation_ops

importlib.reload(validation_ops)


class TestValidationScaleCalibration(unittest.TestCase):
    def test_internal_r15_scale_uses_rest_distance_ratio(self):
        canonical = validation_ops._INTERNAL_EMOTE_R15_REST
        source = {
            bone_name: {
                "parent": entry["parent"],
                "distance": entry["distance"] * 0.25,
            }
            for bone_name, entry in canonical.items()
        }

        resolved = validation_ops._resolve_validation_scale_from_rest_samples(
            source,
            canonical,
        )

        self.assertIsNotNone(resolved)
        scale, sample_count = resolved
        self.assertAlmostEqual(scale, 0.25, places=6)
        self.assertEqual(sample_count, len(canonical))

    def test_internal_r15_scale_skips_parent_mismatches(self):
        canonical = validation_ops._INTERNAL_EMOTE_R15_REST
        source = {
            "lowertorso": {"parent": "humanoidrootpart", "distance": 0.5},
            "uppertorso": {"parent": "humanoidrootpart", "distance": 9.0},
            "head": {
                "parent": canonical["head"]["parent"],
                "distance": canonical["head"]["distance"] * 0.5,
            },
        }

        resolved = validation_ops._resolve_validation_scale_from_rest_samples(
            source,
            canonical,
        )

        self.assertIsNotNone(resolved)
        scale, sample_count = resolved
        self.assertAlmostEqual(scale, 0.5, places=6)
        self.assertEqual(sample_count, 2)

    def test_floor_scale_prefers_lower_body_subset(self):
        canonical = validation_ops._INTERNAL_EMOTE_R15_REST
        source = {
            bone_name: {
                "parent": entry["parent"],
                "distance": entry["distance"] * 0.75,
            }
            for bone_name, entry in canonical.items()
        }

        for bone_name in validation_ops._INTERNAL_EMOTE_R15_FLOOR_BONES:
            source[bone_name]["distance"] = canonical[bone_name]["distance"] * 1.125

        resolved = validation_ops._resolve_validation_scale_from_rest_samples(
            source,
            canonical,
            preferred_bone_names=validation_ops._INTERNAL_EMOTE_R15_FLOOR_BONES,
        )

        self.assertIsNotNone(resolved)
        scale, sample_count = resolved
        self.assertAlmostEqual(scale, 1.125, places=6)
        self.assertEqual(sample_count, len(validation_ops._INTERNAL_EMOTE_R15_FLOOR_BONES))

    def test_floor_limit_tracks_lowest_candidate(self):
        floor_limit = None
        floor_limit = validation_ops._accumulate_floor_limit_z(floor_limit, 2.0)
        floor_limit = validation_ops._accumulate_floor_limit_z(floor_limit, -1.5)
        floor_limit = validation_ops._accumulate_floor_limit_z(floor_limit, 0.25)

        self.assertEqual(floor_limit, -1.5)

    def test_motion_threshold_scales_with_fps(self):
        self.assertAlmostEqual(
            validation_ops._resolve_motion_threshold_for_fps(1.0, 30.0),
            1.0,
            places=6,
        )
        self.assertAlmostEqual(
            validation_ops._resolve_motion_threshold_for_fps(1.0, 60.0),
            0.5,
            places=6,
        )
        self.assertAlmostEqual(
            validation_ops._resolve_motion_threshold_for_fps(1.0, 15.0),
            2.0,
            places=6,
        )

    def test_manual_validation_fallback_uses_manual_scale(self):
        scene = SimpleNamespace(unit_settings=SimpleNamespace(scale_length=0.01))
        settings = SimpleNamespace(
            rbx_auto_deform_scale=False,
            rbx_deform_rig_scale=0.25,
            id_data=scene,
        )

        with mock.patch.object(validation_ops, "is_deform_bone_rig", return_value=True):
            scale, source, sample_count = validation_ops._fallback_validation_units_per_stud(
                SimpleNamespace(),
                settings,
            )

        self.assertAlmostEqual(scale, 0.25, places=6)
        self.assertEqual(source, "manual")
        self.assertEqual(sample_count, 0)

    def test_validation_root_prefers_humanoid_root_part(self):
        pose_bones = _FakePoseBones(
            [
                _FakePoseBone("Root"),
                _FakePoseBone("HumanoidRootPart"),
                _FakePoseBone("LowerTorso"),
            ]
        )

        self.assertEqual(
            validation_ops._resolve_validation_root_bone_name(pose_bones),
            "HumanoidRootPart",
        )

    def test_validation_root_falls_back_to_parentless_bone(self):
        child = _FakePoseBone("Child", parent=object())
        root = _FakePoseBone("WeirdRigRoot")
        pose_bones = _FakePoseBones([child, root])

        self.assertEqual(
            validation_ops._resolve_validation_root_bone_name(pose_bones),
            "WeirdRigRoot",
        )

    def test_validation_body_bones_filter_to_canonical_r15_set(self):
        resolved = validation_ops._resolve_validation_body_bone_name_set(
            [
                "HumanoidRootPart",
                "LowerTorso",
                "UpperTorso",
                "Head",
                "LeftUpperArm",
                "LeftLowerArm",
                "LeftHand",
                "RightUpperArm",
                "RightLowerArm",
                "RightHand",
                "LeftUpperLeg",
                "LeftLowerLeg",
                "LeftFoot",
                "RightUpperLeg",
                "RightLowerLeg",
                "RightFoot",
                "RightFoot.005",
                "LeftFoot.005",
                "RightLowerLeg-IKTarget",
                "LeftLowerLeg-IKTarget",
                "RightLowerLeg.001",
                "LeftLowerLeg.001",
            ]
        )

        self.assertIsNotNone(resolved)
        self.assertIn("LeftFoot", resolved)
        self.assertIn("RightFoot", resolved)
        self.assertNotIn("RightFoot.005", resolved)
        self.assertNotIn("LeftFoot.005", resolved)
        self.assertNotIn("RightLowerLeg-IKTarget", resolved)

    def test_validation_body_bones_fallback_when_not_enough_matches(self):
        resolved = validation_ops._resolve_validation_body_bone_name_set(
            ["ControlRoot", "Widget", "FootCtrl", "PoleTarget"]
        )

        self.assertIsNone(resolved)


class _FakePoseBone(SimpleNamespace):
    def __init__(self, name, parent=None):
        super().__init__(name=name, parent=parent)


class _FakePoseBones(list):
    def get(self, name):
        for bone in self:
            if bone.name == name:
                return bone
        return None


if __name__ == "__main__":
    unittest.main()