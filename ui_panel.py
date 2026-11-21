import bpy

from . import operators


def _on_assistance_strength_update(self, context: bpy.types.Context) -> None:
    operators.apply_assistance_slider(context, self.assistance_strength)


class ANIMATE4U_PG_settings(bpy.types.PropertyGroup):
    """Stores UI properties for the Animate4U sidebar."""

    assistance_strength: bpy.props.FloatProperty(
        name="Assistance Strength",
        description="Blend between raw animation and pin-locked smoothed animation",
        default=0.0,
        min=0.0,
        max=1.0,
        update=_on_assistance_strength_update,
    )
    before_after_toggle: bpy.props.BoolProperty(
        name="Before / After",
        description="Toggle between original backup and modified curves",
        default=False,
    )


class ANIMATE4U_PT_main_panel(bpy.types.Panel):
    """Main Animate4U sidebar panel inside the 3D Viewport."""

    bl_label = "Animate4U"
    bl_idname = "ANIMATE4U_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animate4U"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        props = scene.animate4u_settings

        header_row = layout.row(align=True)
        header_row.prop(props, "assistance_strength", slider=True)
        header_row.operator(
            "animate4u.toggle_before_after",
            text="After" if props.before_after_toggle else "Before",
            depress=props.before_after_toggle,
        )

        smooth_box = layout.box()
        smooth_box.label(text="Smoothing", icon="SMOOTHCURVE")
        smooth_box.operator("animate4u.toggle_extreme_pin", icon="PINNED")

        breakdown_box = layout.box()
        breakdown_box.label(text="Smart Breakdowns", icon="KEYFRAME")

        secondary_box = layout.box()
        secondary_box.label(text="Secondary Motion", icon="BONE_DATA")