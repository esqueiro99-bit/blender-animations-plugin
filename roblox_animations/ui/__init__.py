"""
UI module for the Roblox Animations Blender Addon.

This module contains all UI panels, properties, and interface components.
"""

from .panels import (
    OBJECT_PT_RbxAnimations,
    OBJECT_PT_RbxAnimations_Tool,
    OBJECT_PT_RbxDecals,
)
from .properties import (
    RobloxAnimationSettings,
    RbxDecalItem,
    RbxDecalSettings,
    register_properties,
    unregister_properties,
)

__all__ = [
    # Panels
    "OBJECT_PT_RbxAnimations",
    "OBJECT_PT_RbxAnimations_Tool",
    "OBJECT_PT_RbxDecals",
    # Properties
    "RobloxAnimationSettings",
    "RbxDecalItem",
    "RbxDecalSettings",
    "register_properties",
    "unregister_properties",
]
