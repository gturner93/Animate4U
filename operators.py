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