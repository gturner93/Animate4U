import numpy as np


def align_quaternion_signs(quaternions: np.ndarray) -> np.ndarray:
    """Align neighboring quaternion signs (q vs -q) to prevent 360-degree spins."""
    aligned = np.array(quaternions, dtype=np.float64, copy=True)
    if aligned.ndim != 2 or aligned.shape[1] != 4 or aligned.shape[0] < 2:
        return aligned

    for i in range(1, aligned.shape[0]):
        if np.dot(aligned[i - 1], aligned[i]) < 0.0:
            aligned[i] = -aligned[i]
    return aligned


def read_fcurve_coords(fcurve) -> np.ndarray:
    """Read keyframe (frame, value) coordinates from an F-Curve using bulk foreach_get."""
    key_count = len(fcurve.keyframe_points)
    if key_count == 0:
        return np.empty((0, 2), dtype=np.float64)

    coords = np.empty(key_count * 2, dtype=np.float64)
    fcurve.keyframe_points.foreach_get("co", coords)
    return coords.reshape((key_count, 2))


def write_fcurve_values(fcurve, values: np.ndarray) -> None:
    """Write updated keyframe values back to an F-Curve using bulk foreach_set."""
    key_count = len(fcurve.keyframe_points)
    if key_count == 0:
        return

    coords = read_fcurve_coords(fcurve)
    coords[:, 1] = np.asarray(values, dtype=np.float64)
    fcurve.keyframe_points.foreach_set("co", coords.ravel())
    fcurve.update()


def collect_selected_bone_fcurves(context) -> list:
    """Return unlocked F-Curves matching currently selected pose bones."""
    obj = context.active_object
    if obj is None or obj.type != "ARMATURE" or obj.animation_data is None:
        return []
    action = obj.animation_data.action
    if action is None:
        return []

    selected_bone_names = {bone.name for bone in (context.selected_pose_bones or [])}
    if not selected_bone_names:
        return []

    matching_curves = []
    fcurves = []
    if hasattr(action, "fcurves"):
        fcurves = action.fcurves
    else:
        action_slot = obj.animation_data.action_slot
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in getattr(strip, "channelbags", ()):
                    if action_slot is None or channelbag.slot == action_slot:
                        fcurves.extend(channelbag.fcurves)

    for fc in fcurves:
        if fc.lock or getattr(fc, "driver", None) is not None:
            continue
        if any(f'pose.bones["{name}"]' in fc.data_path for name in selected_bone_names):
            matching_curves.append(fc)
    return matching_curves
def apply_smoothed_curve_with_handles(fcurve, new_values: np.ndarray) -> None:
    """Write smoothed values via bulk foreach_set and recalculate smooth handles."""
    key_count = len(fcurve.keyframe_points)
    if key_count == 0:
        return

    coords = read_fcurve_coords(fcurve)
    coords[:, 1] = np.asarray(new_values, dtype=np.float64)
    fcurve.keyframe_points.foreach_set("co", coords.ravel())

    for kp in fcurve.keyframe_points:
        kp.handle_left_type = "AUTO"
        kp.handle_right_type = "AUTO"

    fcurve.update()