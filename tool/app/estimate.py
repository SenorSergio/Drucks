"""
Print-time & material estimate.

Phase 1 uses a transparent, conservative heuristic derived from the geometry
(shell + infill model). If a PrusaSlicer/OrcaSlicer binary *and* a slicing
profile are available, `slice_estimate` will produce exact numbers instead —
wiring is in place so no code changes are needed once a slicer is installed.
"""
from __future__ import annotations

import math
import os
import shutil
from dataclasses import asdict, dataclass

import trimesh

from .config import CONFIG, Material


# Filament cross-section for 1.75 mm stock (mm²).
_FILAMENT_AREA = math.pi * (1.75 / 2) ** 2


@dataclass
class Estimate:
    time_min: int
    mass_g: float
    length_m: float
    method: str          # German label of how it was produced

    def as_dict(self) -> dict:
        d = asdict(self)
        d["mass_g"] = round(self.mass_g, 1)
        d["length_m"] = round(self.length_m, 2)
        return d


def _plastic_volume_mm3(mesh: trimesh.Trimesh, mat: Material) -> float:
    """Estimate the actual extruded plastic: solid shell + infill of the core.

    Shell thickness comes from the material's real perimeter count × line width
    (their @MK3 profile); the core is filled at the material's infill ratio.
    """
    solid = max(mesh.volume, 0.0)
    shell_mm = mat.perimeters * CONFIG.rules.line_width
    shell = min(mesh.area * shell_mm, solid)
    core = max(solid - shell, 0.0)
    return shell + mat.infill * core


def heuristic_estimate(mesh: trimesh.Trimesh, mat: Material) -> Estimate:
    vol = _plastic_volume_mm3(mesh, mat)
    mass = vol / 1000.0 * mat.density          # cm³ × g/cm³
    length = vol / _FILAMENT_AREA / 1000.0     # mm → m
    seconds = CONFIG.speed.overhead_s + vol / CONFIG.speed.flow_mm3_s
    return Estimate(
        time_min=max(1, round(seconds / 60.0)),
        mass_g=mass,
        length_m=length,
        method="Schätzung (ohne Slicer)",
    )


def find_slicer() -> str | None:
    """Locate a slicer CLI on PATH or in the usual install locations."""
    for name in ("prusa-slicer-console", "prusa-slicer", "orca-slicer",
                 "PrusaSlicer", "OrcaSlicer"):
        found = shutil.which(name)
        if found:
            return found
    candidates = [
        r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
        r"C:\Program Files\OrcaSlicer\orca-slicer.exe",
        "/usr/bin/prusa-slicer",
        "/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def estimate(mesh: trimesh.Trimesh, mat: Material, stl_bytes: bytes | None = None,
             prn=None, precise: bool = False) -> Estimate:
    """Best available estimate.

    Fast heuristic by default. When ``precise`` is requested and a slicer +
    profile are available, slice the real STL for exact time/material; on any
    failure fall back to the heuristic so a result is always returned.
    """
    if precise and stl_bytes is not None:
        try:
            from . import slicer
            sliced = slicer.slice_estimate(stl_bytes, mat, prn)
            if sliced is not None:
                return sliced
        except Exception:
            pass
    return heuristic_estimate(mesh, mat)
