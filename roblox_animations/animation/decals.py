"""
Roblox Decal Animation and Shader Management for Blender.

This module provides tools for:
- Detecting decals on imported Roblox models (.obj meshes).
- Building multi-layer shader node trees (Decal Stacks) with opacity/transparency controls.
- Keyframing decal transparency on the timeline (Constant / Linear / Bezier).
- Soloing and flipbook-style frame switching for facial expressions (e.g. Face.1 to Face.6).
- Exporting Roblox Luau scripts and animation events.
"""

import os
import re
import bpy
from typing import Dict, List, Optional, Tuple, Any

# Node naming prefixes
DECAL_NODE_PREFIX = "RBX_DECAL_TEX_"
DECAL_VAL_PREFIX = "RBX_DECAL_VAL_"
DECAL_MATH_PREFIX = "RBX_DECAL_MATH_"
DECAL_MIX_PREFIX = "RBX_DECAL_MIX_"


def is_blender_4_or_newer() -> bool:
    """Check if Blender version is 4.0 or newer."""
    return bpy.app.version >= (4, 0, 0)


def is_blender_3_4_or_newer() -> bool:
    """Check if Blender version is 3.4 or newer (supports ShaderNodeMix)."""
    return bpy.app.version >= (3, 4, 0)


def natural_sort_key(s: str):
    """Sort strings with embedded numbers naturally (e.g. Face.1, Face.2, Face.10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def get_active_decal_target(context) -> Tuple[Optional[bpy.types.Object], Optional[bpy.types.Material]]:
    """Find active object and its primary material suitable for decals."""
    obj = getattr(context, "active_object", None) or (context.selected_objects[0] if getattr(context, "selected_objects", None) else None)
    if not obj:
        return None, None

    # If an armature is selected, try to find a Head / Face mesh child
    if obj.type == 'ARMATURE':
        for child in obj.children:
            if child.type == 'MESH' and any(keyword in child.name.lower() for keyword in ['head', 'face', 'decal']):
                obj = child
                break
        else:
            # Fallback to first mesh child
            for child in obj.children:
                if child.type == 'MESH':
                    obj = child
                    break

    if obj.type != 'MESH':
        return obj, None

    mat = obj.active_material
    if not mat and len(obj.data.materials) > 0:
        mat = obj.data.materials[0]

    return obj, mat


def ensure_material_nodes(material: bpy.types.Material) -> bpy.types.NodeTree:
    """Ensure material uses nodes and returns node tree."""
    material.use_nodes = True
    # Configure transparency settings for EEVEE and Cycles
    if hasattr(material, "blend_method"):
        material.blend_method = 'BLEND'
    if hasattr(material, "shadow_method"):
        material.shadow_method = 'HASHED'
    
    # Blender 4.2+ (EEVEE Next) compatibility
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = 'BLENDED'

    return material.node_tree


def find_principled_bsdf(node_tree: bpy.types.NodeTree) -> Optional[bpy.types.Node]:
    """Find the Principled BSDF node in the node tree or create one."""
    for node in node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            return node

    # Create one if missing
    bsdf = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (800, 0)

    # Find or create Material Output
    output_node = None
    for node in node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and getattr(node, "is_active_output", True):
            output_node = node
            break
    if not output_node:
        output_node = node_tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (1100, 0)

    node_tree.links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    return bsdf


def get_material_decals(material: Optional[bpy.types.Material]) -> List[Dict[str, Any]]:
    """
    Inspect material nodes and return a list of registered decal layers.
    Returns: [{'name': 'Face.1', 'val_node': Node, 'tex_node': Node, 'mix_node': Node, 'transparency': 0.0}, ...]
    """
    if not material or not getattr(material, "use_nodes", False) or not material.node_tree:
        return []

    node_tree = material.node_tree
    decals = []

    # Method 1: Look for our tagged Value nodes (RBX_DECAL_VAL_<name>)
    for node in node_tree.nodes:
        if node.type == 'VALUE' and node.name.startswith(DECAL_VAL_PREFIX):
            decal_name = node.name[len(DECAL_VAL_PREFIX):]
            tex_node = node_tree.nodes.get(f"{DECAL_NODE_PREFIX}{decal_name}")
            mix_node = node_tree.nodes.get(f"{DECAL_MIX_PREFIX}{decal_name}")
            val = node.outputs[0].default_value  # 1.0 = visible, 0.0 = transparent

            decals.append({
                'name': decal_name,
                'val_node': node,
                'tex_node': tex_node,
                'mix_node': mix_node,
                'blender_alpha': val,
                'roblox_transparency': 1.0 - max(0.0, min(1.0, val)),
                'image_name': tex_node.image.name if (tex_node and tex_node.image) else "",
            })

    # Method 2: If no tagged nodes found, detect raw Image Texture nodes with Face/Decal naming
    if not decals:
        for node in node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                img_name = node.image.name if node.image else node.name
                if any(kw in img_name.lower() or kw in node.name.lower() for kw in ['face', 'decal']):
                    # Clean up name (e.g. "Face.1.png" -> "Face.1")
                    clean_name = os.path.splitext(node.name)[0]
                    clean_name = re.sub(r'^(RBX_DECAL_TEX_|Image Texture\b)', '', clean_name).strip() or node.name
                    decals.append({
                        'name': clean_name,
                        'val_node': None,
                        'tex_node': node,
                        'mix_node': None,
                        'blender_alpha': 1.0,
                        'roblox_transparency': 0.0,
                        'image_name': node.image.name if node.image else "",
                    })

    # Sort naturally by name (Face.1, Face.2, ... Face.6)
    decals.sort(key=lambda item: natural_sort_key(item['name']))
    return decals


def build_decal_shader_stack(
    material: bpy.types.Material,
    image_paths: List[str],
    base_color: Tuple[float, float, float, float] = (0.7, 0.7, 0.7, 1.0),
    base_texture_path: Optional[str] = None,
    replace_existing: bool = True
) -> bool:
    """
    Builds a clean, layered Decal Shader Node Tree on the material.
    Connects Base -> Mix 1 (Face.1) -> Mix 2 (Face.2) -> ... -> Principled BSDF.
    """
    if not material:
        return False

    node_tree = ensure_material_nodes(material)
    nodes = node_tree.nodes
    links = node_tree.links

    if replace_existing:
        nodes.clear()

    # Create Principled BSDF & Output
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (800, 0)
    
    # Handle Roughness defaults
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 0.5

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1100, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Base Color Input
    curr_color_output = None
    if base_texture_path and os.path.exists(base_texture_path):
        base_tex = nodes.new('ShaderNodeTexImage')
        base_tex.name = "RBX_BASE_TEXTURE"
        base_tex.label = "Base Texture"
        base_tex.location = (-600, 200)
        try:
            base_tex.image = bpy.data.images.load(base_texture_path, check_existing=True)
        except Exception:
            pass
        curr_color_output = base_tex.outputs['Color']
    else:
        # Default Base RGB Node
        rgb_node = nodes.new('ShaderNodeRGB')
        rgb_node.name = "RBX_BASE_COLOR"
        rgb_node.label = "Head Base Color"
        rgb_node.location = (-600, 200)
        rgb_node.outputs['Color'].default_value = base_color
        curr_color_output = rgb_node.outputs['Color']

    # Sort images naturally (e.g. Face.1, Face.2, Face.3, ... Face.6)
    sorted_image_paths = sorted(image_paths, key=lambda p: natural_sort_key(os.path.basename(p)))

    x_start = -300

    for i, img_path in enumerate(sorted_image_paths):
        file_name = os.path.basename(img_path)
        decal_name = os.path.splitext(file_name)[0]
        # Clean up name if it has extensions or numbers
        if decal_name.lower().startswith("face_"):
            decal_name = decal_name.replace("face_", "Face.")
        elif decal_name.lower().startswith("face"):
            decal_name = decal_name.replace("face", "Face")

        x_pos = x_start + (i * 240)
        y_pos = 300 - (i % 2) * 50

        # 1. Texture Node
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.name = f"{DECAL_NODE_PREFIX}{decal_name}"
        tex_node.label = f"Decal: {decal_name}"
        tex_node.location = (x_pos - 100, y_pos + 150)
        try:
            tex_node.image = bpy.data.images.load(img_path, check_existing=True)
        except Exception as e:
            print(f"Blender Decals: Could not load image {img_path}: {e}")

        # 2. Value Node (animatable alpha control: 1.0 = visible, 0.0 = transparent)
        # Default: first decal is visible (1.0), others are hidden (0.0)
        val_node = nodes.new('ShaderNodeValue')
        val_node.name = f"{DECAL_VAL_PREFIX}{decal_name}"
        val_node.label = f"Alpha: {decal_name}"
        val_node.location = (x_pos - 100, y_pos - 80)
        val_node.outputs[0].default_value = 1.0 if i == 0 else 0.0

        # 3. Math Node (Multiply Texture Alpha * Value Node)
        math_node = nodes.new('ShaderNodeMath')
        math_node.name = f"{DECAL_MATH_PREFIX}{decal_name}"
        math_node.label = f"Mult: {decal_name}"
        math_node.operation = 'MULTIPLY'
        math_node.location = (x_pos + 80, y_pos - 40)
        links.new(tex_node.outputs['Alpha'], math_node.inputs[0])
        links.new(val_node.outputs[0], math_node.inputs[1])

        # 4. Mix Node (Mix Color)
        if is_blender_3_4_or_newer():
            mix_node = nodes.new('ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.clamp_result = True
            mix_node.name = f"{DECAL_MIX_PREFIX}{decal_name}"
            mix_node.label = f"Mix: {decal_name}"
            mix_node.location = (x_pos + 260, y_pos)

            # In Blender 3.4+, inputs are [0: Factor, 6: A, 7: B] for RGBA
            links.new(math_node.outputs['Value'], mix_node.inputs['Factor'])
            links.new(curr_color_output, mix_node.inputs['A'])
            links.new(tex_node.outputs['Color'], mix_node.inputs['B'])
            curr_color_output = mix_node.outputs['Result']
        else:
            mix_node = nodes.new('ShaderNodeMixRGB')
            mix_node.blend_type = 'MIX'
            mix_node.use_clamp = True
            mix_node.name = f"{DECAL_MIX_PREFIX}{decal_name}"
            mix_node.label = f"Mix: {decal_name}"
            mix_node.location = (x_pos + 260, y_pos)

            links.new(math_node.outputs['Value'], mix_node.inputs['Fac'])
            links.new(curr_color_output, mix_node.inputs['Color1'])
            links.new(tex_node.outputs['Color'], mix_node.inputs['Color2'])
            curr_color_output = mix_node.outputs['Color']

    # Finally, link output of last mix node to Principled BSDF Base Color
    if curr_color_output:
        links.new(curr_color_output, bsdf.inputs['Base Color'])

    return True


def set_decal_alpha(material: bpy.types.Material, decal_name: str, alpha_value: float) -> bool:
    """Set the alpha value (1.0 = visible, 0.0 = transparent) for a specific decal."""
    if not material or not getattr(material, "use_nodes", False) or not material.node_tree:
        return False

    val_node = material.node_tree.nodes.get(f"{DECAL_VAL_PREFIX}{decal_name}")
    if val_node and val_node.outputs:
        val_node.outputs[0].default_value = max(0.0, min(1.0, alpha_value))
        return True
    return False


def set_decal_transparency(material: bpy.types.Material, decal_name: str, transparency: float, mode: str = 'ROBLOX') -> bool:
    """
    Set transparency for decal.
    If mode == 'ROBLOX': 0.0 is visible, 1.0 is transparent.
    If mode == 'BLENDER': 1.0 is visible, 0.0 is transparent.
    """
    if mode == 'ROBLOX':
        alpha = 1.0 - max(0.0, min(1.0, transparency))
    else:
        alpha = max(0.0, min(1.0, transparency))
    return set_decal_alpha(material, decal_name, alpha)


def keyframe_decal_transparency(
    material: bpy.types.Material,
    decal_name: str,
    frame: Optional[int] = None,
    interpolation: str = 'CONSTANT'
) -> bool:
    """Insert a keyframe for the decal transparency at specified frame."""
    if not material or not getattr(material, "use_nodes", False) or not material.node_tree:
        return False

    val_node = material.node_tree.nodes.get(f"{DECAL_VAL_PREFIX}{decal_name}")
    if not val_node:
        return False

    if frame is None:
        frame = bpy.context.scene.frame_current

    val_node.outputs[0].keyframe_insert(data_path="default_value", frame=frame)

    if material.node_tree.animation_data and material.node_tree.animation_data.action:
        action = material.node_tree.animation_data.action
        for fcurve in action.fcurves:
            if fcurve.data_path.endswith('default_value') and val_node.name in fcurve.data_path:
                for kp in fcurve.keyframe_points:
                    if int(kp.co.x) == int(frame):
                        kp.interpolation = interpolation
    return True


def solo_decal(
    material: bpy.types.Material,
    target_decal_name: str,
    frame: Optional[int] = None,
    insert_keyframe: bool = True,
    interpolation: str = 'CONSTANT'
) -> bool:
    """
    Solo a specific decal (make it 100% visible and all other decals 100% transparent).
    Optionally inserts keyframes for all decals at frame.
    """
    decals = get_material_decals(material)
    if not decals:
        return False

    if frame is None:
        frame = bpy.context.scene.frame_current

    for decal in decals:
        name = decal['name']
        is_target = (name == target_decal_name)
        alpha = 1.0 if is_target else 0.0
        set_decal_alpha(material, name, alpha)

        if insert_keyframe:
            keyframe_decal_transparency(material, name, frame=frame, interpolation=interpolation)

    return True


def keyframe_all_decals(
    material: bpy.types.Material,
    frame: Optional[int] = None,
    interpolation: str = 'CONSTANT'
) -> int:
    """Keyframe all decals on the material at current or specified frame."""
    decals = get_material_decals(material)
    count = 0
    if frame is None:
        frame = bpy.context.scene.frame_current

    for decal in decals:
        if keyframe_decal_transparency(material, decal['name'], frame=frame, interpolation=interpolation):
            count += 1
    return count


def clear_decal_animation(material: bpy.types.Material) -> bool:
    """Remove all keyframes and fcurves for decal value nodes in the material."""
    if not material or not material.node_tree or not material.node_tree.animation_data:
        return False

    action = material.node_tree.animation_data.action
    if not action:
        return False

    to_remove = []
    for fcurve in action.fcurves:
        if DECAL_VAL_PREFIX in fcurve.data_path:
            to_remove.append(fcurve)

    for fcurve in to_remove:
        action.fcurves.remove(fcurve)

    return True


def generate_roblox_luau_script(
    material: bpy.types.Material,
    part_name: str = "Face",
    track_name: str = "FaceAnimation"
) -> str:
    """
    Analyze Blender keyframes for decals on the material and generate a complete,
    ready-to-use Roblox Luau script (ModuleScript / LocalScript) to drive Decal.Transparency.
    """
    decals = get_material_decals(material)
    if not decals:
        return "-- No decals found in Blender material."

    fps = bpy.context.scene.render.fps
    frame_start = bpy.context.scene.frame_start
    frame_end = bpy.context.scene.frame_end

    timeline_events = {}

    if material.node_tree and material.node_tree.animation_data and material.node_tree.animation_data.action:
        action = material.node_tree.animation_data.action
        for decal in decals:
            name = decal['name']
            val_node_name = f"{DECAL_VAL_PREFIX}{name}"
            for fcurve in action.fcurves:
                if val_node_name in fcurve.data_path:
                    for kp in fcurve.keyframe_points:
                        f = int(round(kp.co.x))
                        val = kp.co.y
                        transp = round(1.0 - max(0.0, min(1.0, val)), 3)
                        if f not in timeline_events:
                            timeline_events[f] = {}
                        timeline_events[f][name] = transp

    script_lines = [
        "--!strict",
        "-- Generated by Roblox Animations Decal Plugin for Blender",
        f"-- Target Part: {part_name}",
        f"-- Timeline Range: {frame_start} to {frame_end} @ {fps} FPS",
        "",
        "local TweenService = game:GetService('TweenService')",
        "local RunService = game:GetService('RunService')",
        "",
        "local function setupFaceDecalAnimation(facePart: Instance, animationTrack: AnimationTrack?)",
        f"    -- Reference decals under '{part_name}'",
        "    local decals: { [string]: Decal } = {}",
        "    for _, child in ipairs(facePart:GetChildren()) do",
        "        if child:IsA('Decal') then",
        "            decals[child.Name] = child",
        "        end",
        "    end",
        "",
        "    -- Function to set decal transparency directly",
        "    local function setDecalState(states: { [string]: number })",
        "        for decalName, transparency in pairs(states) do",
        "            local decal = decals[decalName]",
        "            if decal then",
        "                decal.Transparency = transparency",
        "            end",
        "        end",
        "    end",
        "",
        "    -- Timeline keyframe data (Timestamp in seconds -> Decal states)",
        "    local timelineKeyframes = {",
    ]

    if timeline_events:
        for f in sorted(timeline_events.keys()):
            time_sec = round((f - frame_start) / max(1, fps), 3)
            states = timeline_events[f]
            states_str = ", ".join([f'["{k}"] = {v}' for k, v in states.items()])
            script_lines.append(f'        [{time_sec}] = {{ {states_str} }}, -- Frame {f}')
    else:
        states_str = ", ".join([f'["{d["name"]}"] = {d["roblox_transparency"]}' for d in decals])
        script_lines.append(f'        [0.0] = {{ {states_str} }}, -- Default State')

    script_lines.extend([
        "    }",
        "",
        "    -- Playback controller",
        "    local function playDecalTimeline()",
        "        task.spawn(function()",
        "            local sortedTimes = {}",
        "            for t in pairs(timelineKeyframes) do table.insert(sortedTimes, t) end",
        "            table.sort(sortedTimes)",
        "",
        "            local lastTime = 0",
        "            for _, t in ipairs(sortedTimes) do",
        "                local delta = t - lastTime",
        "                if delta > 0 then",
        "                    task.wait(delta)",
        "                end",
        "                setDecalState(timelineKeyframes[t])",
        "                lastTime = t",
        "            end",
        "        end)",
        "    end",

        "",
        "    -- Hook to AnimationTrack if provided",
        "    if animationTrack then",
        "        animationTrack.DidLoop:Connect(function()",
        "            playDecalTimeline()",
        "        end)",
        "        animationTrack.Stopped:Connect(function()",
        "            -- Reset or stop",
        "        end)",
        "    end",
        "",
        "    -- Start initial play",
        "    playDecalTimeline()",
        "end",
        "",
        "return setupFaceDecalAnimation",
    ])

    return "\n".join(script_lines)


def get_decal_keyframes_json() -> dict:
    """
    Read all decal Value node F-Curves from the active scene and return
    a JSON-serializable dict with keyframe data for each decal.

    Return format:
    {
        "fps": 24,
        "frame_start": 1,
        "frame_end": 60,
        "decals": {
            "Face.1": [{"frame": 1, "value": 1.0, "interp": "CONSTANT"}, {"frame": 10, "value": 0.0, "interp": "CONSTANT"}],
            "Face.2": [{"frame": 1, "value": 0.0, "interp": "CONSTANT"}, {"frame": 10, "value": 1.0, "interp": "CONSTANT"}],
        }
    }
    """
    scene = bpy.context.scene
    fps = scene.render.fps
    frame_start = scene.frame_start
    frame_end = scene.frame_end

    decal_keyframes: Dict[str, List[Dict]] = {}

    # Search all objects for materials with RBX_DECAL_VAL_ nodes that have animation
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if not node.name.startswith(DECAL_VAL_PREFIX):
                    continue
                decal_name = node.name[len(DECAL_VAL_PREFIX):]
                # Find the fcurve that drives this Value node's output
                if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
                    action = mat.node_tree.animation_data.action
                    for fc in action.fcurves:
                        if node.name in fc.data_path and 'default_value' in fc.data_path:
                            kfs = []
                            for kp in fc.keyframe_points:
                                kfs.append({
                                    "frame": float(kp.co[0]),
                                    "value": round(float(kp.co[1]), 4),
                                    "interp": str(kp.interpolation)
                                })
                            if kfs:
                                decal_keyframes[decal_name] = kfs

    return {
        "fps": fps,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "decals": decal_keyframes,
    }


def get_decal_meta_json() -> dict:
    """
    Return metadata about all detected decals in the active scene.
    Includes image names, the material they belong to, and detection method.

    Return format:
    {
        "decals": {
            "Face.1": {"image": "Face1.png", "object": "Head", "material": "Head_mat"},
            ...
        }
    }
    """
    result: Dict[str, Dict] = {}

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if not mat or not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.name.startswith(DECAL_NODE_PREFIX):
                    decal_name = node.name[len(DECAL_NODE_PREFIX):]
                    image_name = ""
                    if node.type == 'TEX_IMAGE' and getattr(node, "image", None):
                        image_name = node.image.name
                    result[decal_name] = {
                        "image": image_name,
                        "object": obj.name,
                        "material": mat.name,
                    }

    return {"decals": result}

