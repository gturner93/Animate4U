from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .fcurve_io import read_fcurve_coords, write_fcurve_values


@dataclass
class CurveBackupCache:
    """Stores original and modified keyframe coordinates in memory."""

    original_coords: dict[str, np.ndarray] = field(default_factory=dict)
    modified_coords: dict[str, np.ndarray] = field(default_factory=dict)
    showing_modified: bool = False

    @staticmethod
    def _curve_key(fcurve) -> str:
        return f"{fcurve.data_path}[{fcurve.array_index}]"

    def save_original(self, fcurves: list, overwrite: bool = False) -> None:
        """Save original keyframe coordinates before cleanup changes the animation."""
        for fc in fcurves:
            key = self._curve_key(fc)
            if overwrite or key not in self.original_coords:
                self.original_coords[key] = read_fcurve_coords(fc).copy()

    def save_modified(self, fcurves: list) -> None:
        """Store modified keyframe coordinates so Before/After can swap between states."""
        for fc in fcurves:
            key = self._curve_key(fc)
            self.modified_coords[key] = read_fcurve_coords(fc).copy()

    def restore_original(self, fcurves: list) -> None:
        """Restore original keyframe values from the in-memory cache."""
        for fc in fcurves:
            key = self._curve_key(fc)
            cached = self.original_coords.get(key)
            if cached is not None and len(cached) > 0:
                write_fcurve_values(fc, cached[:, 1])
        self.showing_modified = False

    def apply_modified(self, fcurves: list) -> None:
        """Restore modified keyframe values from the in-memory cache."""
        for fc in fcurves:
            key = self._curve_key(fc)
            cached = self.modified_coords.get(key)
            if cached is not None and len(cached) > 0:
                write_fcurve_values(fc, cached[:, 1])
        self.showing_modified = True


CACHE = CurveBackupCache()