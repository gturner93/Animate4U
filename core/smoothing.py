from __future__ import annotations

import numpy as np


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


def _savgol_smooth(values: np.ndarray, window: int, poly_order: int) -> np.ndarray:
    half_window = window // 2
    offsets = np.arange(-half_window, half_window + 1, dtype=np.float64)
    design = np.vander(offsets, N=poly_order + 1, increasing=True)
    weights = np.linalg.pinv(design)[0]
    smoothed = np.empty_like(values)

    for index in range(half_window, len(values) - half_window):
        smoothed[index] = weights @ values[
            index - half_window : index + half_window + 1
        ]

    fit_x = np.arange(window, dtype=np.float64)
    left_coefficients = np.polynomial.polynomial.polyfit(
        fit_x, values[:window], poly_order
    )
    right_coefficients = np.polynomial.polynomial.polyfit(
        fit_x, values[-window:], poly_order
    )
    smoothed[:half_window] = np.polynomial.polynomial.polyval(
        fit_x[:half_window], left_coefficients
    )
    smoothed[-half_window:] = np.polynomial.polynomial.polyval(
        fit_x[-half_window:], right_coefficients
    )
    return smoothed


def _natural_cubic_interpolate(
    x: np.ndarray, y: np.ndarray, query: np.ndarray
) -> np.ndarray:
    interval_widths = np.diff(x)
    second_derivatives = np.zeros_like(y)
    if len(x) > 2:
        matrix = np.diag(2.0 * (interval_widths[:-1] + interval_widths[1:]))
        if len(x) > 3:
            off_diagonal = interval_widths[1:-1]
            matrix += np.diag(off_diagonal, k=1)
            matrix += np.diag(off_diagonal, k=-1)
        slopes = np.diff(y) / interval_widths
        right_hand_side = 6.0 * (slopes[1:] - slopes[:-1])
        second_derivatives[1:-1] = np.linalg.solve(matrix, right_hand_side)

    segment = np.clip(np.searchsorted(x, query, side="right") - 1, 0, len(x) - 2)
    width = interval_widths[segment]
    left_distance = x[segment + 1] - query
    right_distance = query - x[segment]
    return (
        second_derivatives[segment] * left_distance**3 / (6.0 * width)
        + second_derivatives[segment + 1] * right_distance**3 / (6.0 * width)
        + (y[segment] - second_derivatives[segment] * width**2 / 6.0)
        * left_distance
        / width
        + (y[segment + 1] - second_derivatives[segment + 1] * width**2 / 6.0)
        * right_distance
        / width
    )


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
    smoothed = _savgol_smooth(raw_arr, window=win_len, poly_order=poly_order)

    pin_indices = np.flatnonzero(pins_arr)
    if pin_indices.size >= 2:
        pin_frames = frames_arr[pin_indices]
        pin_errors = raw_arr[pin_indices] - smoothed[pin_indices]
        order = np.argsort(pin_frames)
        unique_frames, unique_idx = np.unique(pin_frames[order], return_index=True)
        if unique_frames.size >= 2:
            correction = _natural_cubic_interpolate(
                unique_frames, pin_errors[order][unique_idx], frames_arr
            )
            smoothed = smoothed + correction
    elif pin_indices.size == 1:
        idx = pin_indices[0]
        smoothed = smoothed + (raw_arr[idx] - smoothed[idx])

    for idx in pin_indices:
        if abs(smoothed[idx] - raw_arr[idx]) > 0.001:
            smoothed[idx] = raw_arr[idx]

    blended = (1.0 - alpha) * raw_arr + alpha * smoothed
    return blended