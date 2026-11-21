import bpy

from .core.fcurve_io import collect_selected_bone_fcurves
from .core.state_cache import CACHE


class ANIMATE4U_OT_toggle_before_after(bpy.types.Operator):
    """Toggle between original backup curves and cleaned/modified curves."""

    bl_idname = "animate4u.toggle_before_after"
    bl_label = "Before / After"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        props = context.scene.animate4u_settings
        fcurves = collect_selected_bone_fcurves(context)

        if not fcurves:
            self.report({"WARNING"}, "Select animated pose bones with unlocked F-Curves.")
            return {"CANCELLED"}

        CACHE.save_original(fcurves)

        if not props.before_after_toggle:
            if not CACHE.modified_coords:
                CACHE.save_modified(fcurves)
            CACHE.apply_modified(fcurves)
            props.before_after_toggle = True
        else:
            CACHE.save_modified(fcurves)
            CACHE.restore_original(fcurves)
            props.before_after_toggle = False

        return {"FINISHED"}
    import bpy
import numpy as np

from .core.fcurve_io import (
    apply_smoothed_curve_with_handles,
    collect_selected_bone_fcurves,
    read_fcurve_coords,
)
from .core.smoothing import compute_pin_locked_smoothed_values
from .core.state_cache import CACHE


def _curve_key(fcurve) -> str:
    return f"{fcurve.data_path}[{fcurve.array_index}]"


def _get_pinned_mask(fcurve) -> np.ndarray:
    """Return boolean mask of keyframes tagged as EXTREME."""
    count = len(fcurve.keyframe_points)
    return np.array([kp.type == "EXTREME" for kp in fcurve.keyframe_points], dtype=bool)


def apply_assistance_slider(context: bpy.types.Context, alpha: float) -> None:
    """Blend original and pin-locked smoothed curves for selected bones."""
    fcurves = collect_selected_bone_fcurves(context)
    if not fcurves:
        return

    CACHE.save_original(fcurves)

    for fc in fcurves:
        key = _curve_key(fc)
        orig_coords = CACHE.original_coords.get(key)
        if orig_coords is None or len(orig_coords) == 0:
            orig_coords = read_fcurve_coords(fc)

        frames = orig_coords[:, 0]
        raw_vals = orig_coords[:, 1]
        pinned_mask = _get_pinned_mask(fc)

        updated_vals = compute_pin_locked_smoothed_values(
            frames=frames,
            raw_values=raw_vals,
            pinned_mask=pinned_mask,
            slider_alpha=alpha,
        )
        apply_smoothed_curve_with_handles(fc, updated_vals)

    CACHE.save_modified(fcurves)


class ANIMATE4U_OT_toggle_extreme_pin(bpy.types.Operator):
    """Toggle EXTREME keyframe tag on selected keyframes to protect main poses."""

    bl_idname = "animate4u.toggle_extreme_pin"
    bl_label = "Pin / Unpin EXTREME"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        fcurves = collect_selected_bone_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "Select animated pose bones with unlocked F-Curves.")
            return {"CANCELLED"}

        selected_kps = [
            kp for fc in fcurves for kp in fc.keyframe_points if kp.select_control_point
        ]
        if not selected_kps:
            self.report({"WARNING"}, "Select one or more keyframes to pin or unpin.")
            return {"CANCELLED"}

        any_unpinned = any(kp.type != "EXTREME" for kp in selected_kps)
        target_type = "EXTREME" if any_unpinned else "KEYFRAME"

        for kp in selected_kps:
            kp.type = target_type

        for fc in fcurves:
            fc.update()

        action_label = "Pinned as EXTREME" if any_unpinned else "Unpinned EXTREME"
        self.report({"INFO"}, f"{action_label} ({len(selected_kps)} keyframes).")
        return {"FINISHED"}


class ANIMATE4U_OT_toggle_before_after(bpy.types.Operator):
    """Toggle between original backup curves and cleaned/modified curves."""

    bl_idname = "animate4u.toggle_before_after"
    bl_label = "Before / After"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        props = context.scene.animate4u_settings
        fcurves = collect_selected_bone_fcurves(context)

        if not fcurves:
            self.report({"WARNING"}, "Select animated pose bones with unlocked F-Curves.")
            return {"CANCELLED"}

        CACHE.save_original(fcurves)

        if not props.before_after_toggle:
            if not CACHE.modified_coords:
                CACHE.save_modified(fcurves)
            CACHE.apply_modified(fcurves)
            props.before_after_toggle = True
        else:
            CACHE.save_modified(fcurves)
            CACHE.restore_original(fcurves)
            props.before_after_toggle = False

        return {"FINISHED"}