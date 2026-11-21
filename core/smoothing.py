from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import savgol_filter


def _choose_savgol_window(num_points: int, desired_window: int = 7) -> int:
    """Choose a valid odd Savitzky-Golay window length for short or long curves."""
    if num_points < 3:
        return num_points
    window = min(desired_window, num_points if num_points % 2 == 1 else num_points - 1)
    if window < 3:
        window = 3 if num_points >= 3 else num_points
    if window % 2 == 0:
        window = max(3, window - 1)
    return min(window, num_points)


def compute_pin_locked_smoothed_values(
    frames: np.ndarray,
    raw_values: np.ndarray,
    pinned_mask: np.ndarray,
    slider_alpha: float = 1.0,
) -> np.ndarray:
    """
    Smooth values with Savitzky-Golay while locking pinned EXTREME keyframes.

    Keeps pinned EXTREME keyframes within 0.001 units of their starting value and
    blends between raw_values and smoothed values using slider_alpha [0.0..1.0].
    """
    frames_arr = np.asarray(frames, dtype=np.float64)
    raw_arr = np.asarray(raw_values, dtype=np.float64)
    pins_arr = np.asarray(pinned_mask, dtype=bool)
    alpha = float(np.clip(slider_alpha, 0.0, 1.0))

    if raw_arr.size < 3 or alpha == 0.0:
        return raw_arr.copy()

    win_len = _choose_savgol_window(raw_arr.size, desired_window=7)
    poly_order = min(2, win_len - 1)
    smoothed = savgol_filter(raw_arr, window_length=win_len, polyorder=poly_order)

    pin_indices = np.flatnonzero(pins_arr)
    if pin_indices.size >= 2:
        pin_frames = frames_arr[pin_indices]
        pin_errors = raw_arr[pin_indices] - smoothed[pin_indices]
        order = np.argsort(pin_frames)
        unique_frames, unique_idx = np.unique(pin_frames[order], return_index=True)
        if unique_frames.size >= 2:
            spline = CubicSpline(unique_frames, pin_errors[order][unique_idx], bc_type="natural")
            correction = spline(frames_arr)
            smoothed = smoothed + correction
    elif pin_indices.size == 1:
        idx = pin_indices[0]
        smoothed = smoothed + (raw_arr[idx] - smoothed[idx])

    for idx in pin_indices:
        if abs(smoothed[idx] - raw_arr[idx]) > 0.001:
            smoothed[idx] = raw_arr[idx]

    blended = (1.0 - alpha) * raw_arr + alpha * smoothed
    return blended