import bpy

from . import operators, ui_panel

bl_info = {
    "name": "Animate4U: Assistive 3D Animation Tool",
    "author": "Gregory Turner",
    "version": (0, 2, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Animate4U",
    "description": "Assistive 3D character animation cleanup tool in Blender.",
    "category": "Animation",
}

CLASSES = (
    ui_panel.ANIMATE4U_PG_settings,
    operators.ANIMATE4U_OT_toggle_before_after,
    ui_panel.ANIMATE4U_PT_main_panel,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.animate4u_settings = bpy.props.PointerProperty(
        type=ui_panel.ANIMATE4U_PG_settings
    )


def unregister() -> None:
    if hasattr(bpy.types.Scene, "animate4u_settings"):
        del bpy.types.Scene.animate4u_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()