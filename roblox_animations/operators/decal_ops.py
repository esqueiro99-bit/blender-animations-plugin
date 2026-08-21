"""
Decal animation and management operators for Roblox models in Blender.
"""

import os
import bpy
from bpy.types import Operator
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    EnumProperty,
    CollectionProperty,
)
from bpy_extras.io_utils import ImportHelper

from ..animation.decals import (
    get_active_decal_target,
    get_material_decals,
    build_decal_shader_stack,
    set_decal_transparency,
    keyframe_decal_transparency,
    keyframe_all_decals,
    solo_decal,
    clear_decal_animation,
    generate_roblox_luau_script,
)


def sync_ui_decal_list(context):
    """Update context.scene.rbx_decals with current material decal state."""
    scene = getattr(context, "scene", None)
    if not scene or not hasattr(scene, "rbx_decals"):
        return

    obj, mat = get_active_decal_target(context)
    decal_settings = scene.rbx_decals
    decal_settings.target_object = obj
    decal_settings.target_material = mat

    decal_settings.items.clear()
    if not mat:
        return

    decals = get_material_decals(mat)
    mode = decal_settings.transparency_mode

    for d in decals:
        item = decal_settings.items.add()
        item.name = d['name']
        item.image_name = d.get('image_name', '')
        if mode == 'ROBLOX':
            item.transparency = d['roblox_transparency']
        else:
            item.transparency = d['blender_alpha']


class OBJECT_OT_RbxDecalScan(Operator):
    """Scan the selected mesh/material for Roblox decals"""
    bl_idname = "object.rbx_decal_scan"
    bl_label = "Scan Decals"
    bl_description = "Scan the active object's material for Roblox decals"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, mat = get_active_decal_target(context)
        if not obj:
            self.report({'WARNING'}, "No active mesh or armature selected.")
            return {'CANCELLED'}

        if not mat:
            self.report({'WARNING'}, f"Object '{obj.name}' has no active material.")
            return {'CANCELLED'}

        sync_ui_decal_list(context)
        count = len(context.scene.rbx_decals.items)
        self.report({'INFO'}, f"Found {count} decal layer(s) on '{mat.name}'.")
        return {'FINISHED'}


class OBJECT_OT_RbxDecalImportImages(Operator, ImportHelper):
    """Import multiple decal images (e.g. Face.1 to Face.6) and build shader stack"""
    bl_idname = "object.rbx_decal_import_images"
    bl_label = "Import Decal Images (Stack)"
    bl_description = "Select multiple decal PNG images to build a layered face decal shader"
    bl_options = {'REGISTER', 'UNDO'}

    # Allow selecting multiple files
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN', 'SKIP_SAVE'})
    directory: StringProperty(subtype='DIR_PATH')
    filter_image: BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        obj, mat = get_active_decal_target(context)
        if not obj:
            self.report({'WARNING'}, "Please select a character or head mesh first.")
            return {'CANCELLED'}

        # If object has no material, create one
        if not mat:
            mat = bpy.data.materials.new(name=f"{obj.name}_FaceMaterial")
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat

        image_paths = []
        if self.files:
            for file_elem in self.files:
                path = os.path.join(self.directory, file_elem.name)
                if os.path.isfile(path):
                    image_paths.append(path)
        elif self.filepath and os.path.isfile(self.filepath):
            image_paths.append(self.filepath)

        if not image_paths:
            self.report({'WARNING'}, "No image files selected.")
            return {'CANCELLED'}

        success = build_decal_shader_stack(
            material=mat,
            image_paths=image_paths,
            replace_existing=True,
        )

        if success:
            sync_ui_decal_list(context)
            self.report({'INFO'}, f"Successfully built decal stack with {len(image_paths)} layer(s).")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to build decal shader stack.")
            return {'CANCELLED'}


class OBJECT_OT_RbxDecalSolo(Operator):
    """Solo this decal (set visible and all others hidden) and optionally keyframe"""
    bl_idname = "object.rbx_decal_solo"
    bl_label = "Solo Decal"
    bl_description = "Make this decal 100% visible and all other decals transparent"
    bl_options = {'REGISTER', 'UNDO'}

    decal_name: StringProperty(name="Decal Name", default="")

    def execute(self, context):
        scene = context.scene
        obj, mat = get_active_decal_target(context)
        if not mat:
            self.report({'WARNING'}, "No active material found.")
            return {'CANCELLED'}

        settings = scene.rbx_decals
        mode = settings.transparency_mode
        interp = settings.interpolation
        auto_kf = settings.auto_keyframe

        target_name = self.decal_name
        if not target_name and len(settings.items) > 0 and settings.active_index < len(settings.items):
            target_name = settings.items[settings.active_index].name

        if not target_name:
            self.report({'WARNING'}, "No decal specified to solo.")
            return {'CANCELLED'}

        solo_decal(
            material=mat,
            target_decal_name=target_name,
            frame=scene.frame_current,
            insert_keyframe=auto_kf,
            interpolation=interp,
        )

        sync_ui_decal_list(context)
        self.report({'INFO'}, f"Soloed decal '{target_name}' at frame {scene.frame_current}.")
        return {'FINISHED'}


class OBJECT_OT_RbxDecalQuickSwitch(Operator):
    """Quick switch expression by index (e.g. 1 to 6) at current frame"""
    bl_idname = "object.rbx_decal_quick_switch"
    bl_label = "Quick Switch"
    bl_description = "Switch active decal frame index at current frame"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Decal Index", default=0)

    def execute(self, context):
        scene = context.scene
        obj, mat = get_active_decal_target(context)
        if not mat:
            return {'CANCELLED'}

        settings = scene.rbx_decals
        if self.index < 0 or self.index >= len(settings.items):
            return {'CANCELLED'}

        target_name = settings.items[self.index].name
        settings.active_index = self.index

        solo_decal(
            material=mat,
            target_decal_name=target_name,
            frame=scene.frame_current,
            insert_keyframe=settings.auto_keyframe,
            interpolation=settings.interpolation,
        )

        sync_ui_decal_list(context)
        return {'FINISHED'}


class OBJECT_OT_RbxDecalKeyframe(Operator):
    """Insert keyframe for decal transparency at the current frame"""
    bl_idname = "object.rbx_decal_keyframe"
    bl_label = "Keyframe Decals"
    bl_description = "Insert keyframes for decal transparency on the active material"
    bl_options = {'REGISTER', 'UNDO'}

    decal_name: StringProperty(name="Decal Name", default="")  # Empty = keyframe all

    def execute(self, context):
        scene = context.scene
        obj, mat = get_active_decal_target(context)
        if not mat:
            self.report({'WARNING'}, "No active material found.")
            return {'CANCELLED'}

        settings = scene.rbx_decals
        interp = settings.interpolation

        if self.decal_name:
            success = keyframe_decal_transparency(
                material=mat,
                decal_name=self.decal_name,
                frame=scene.frame_current,
                interpolation=interp,
            )
            if success:
                self.report({'INFO'}, f"Keyframed decal '{self.decal_name}' at frame {scene.frame_current}.")
            else:
                self.report({'WARNING'}, f"Could not keyframe decal '{self.decal_name}'.")
        else:
            count = keyframe_all_decals(
                material=mat,
                frame=scene.frame_current,
                interpolation=interp,
            )
            self.report({'INFO'}, f"Keyframed {count} decal(s) at frame {scene.frame_current}.")

        return {'FINISHED'}


class OBJECT_OT_RbxDecalClearKeyframes(Operator):
    """Clear all animation keyframes for decals on this material"""
    bl_idname = "object.rbx_decal_clear_keyframes"
    bl_label = "Clear Decal Keyframes"
    bl_description = "Remove all keyframe curves for decals on the active material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj, mat = get_active_decal_target(context)
        if not mat:
            self.report({'WARNING'}, "No active material found.")
            return {'CANCELLED'}

        success = clear_decal_animation(mat)
        if success:
            self.report({'INFO'}, "Cleared all decal keyframes.")
        else:
            self.report({'INFO'}, "No decal keyframes found to clear.")
        return {'FINISHED'}


class OBJECT_OT_RbxDecalExportScript(Operator):
    """Generate and copy Roblox Luau script for decal animation"""
    bl_idname = "object.rbx_decal_export_script"
    bl_label = "Generate Roblox Script"
    bl_description = "Generate Roblox Luau code to drive Decal.Transparency in Studio"
    bl_options = {'REGISTER'}

    part_name: StringProperty(name="Roblox Face Part Name", default="Face")

    def execute(self, context):
        obj, mat = get_active_decal_target(context)
        if not mat:
            self.report({'WARNING'}, "No active material found.")
            return {'CANCELLED'}

        target_part = self.part_name or (obj.name if obj else "Face")
        script_code = generate_roblox_luau_script(
            material=mat,
            part_name=target_part,
            track_name="FaceAnimation",
        )

        # 1. Create or update Blender Text DataBlock
        text_name = "Roblox_Face_Decal_Script.lua"
        text_block = bpy.data.texts.get(text_name) or bpy.data.texts.new(name=text_name)
        text_block.clear()
        text_block.write(script_code)

        # 2. Copy to system clipboard via Blender window manager
        try:
            context.window_manager.clipboard = script_code
            copied = True
        except Exception:
            copied = False

        msg = f"Script written to text block '{text_name}'" + (" and copied to clipboard!" if copied else "!")
        self.report({'INFO'}, msg)
        return {'FINISHED'}


__all__ = [
    "OBJECT_OT_RbxDecalScan",
    "OBJECT_OT_RbxDecalImportImages",
    "OBJECT_OT_RbxDecalSolo",
    "OBJECT_OT_RbxDecalQuickSwitch",
    "OBJECT_OT_RbxDecalKeyframe",
    "OBJECT_OT_RbxDecalClearKeyframes",
    "OBJECT_OT_RbxDecalExportScript",
    "sync_ui_decal_list",
]
