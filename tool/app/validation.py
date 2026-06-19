"""
Validation & auto-correction.

Runs the printability checks from the brief against a built mesh and, where it
safely can, corrects the geometry (currently: auto-scale to fit the build
volume). Every check carries a plain-German message for both the customer view
and the team review.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import numpy as np
import trimesh

from .config import CONFIG, Material, Printer


OK, WARN, FAIL = "ok", "warn", "fail"
_RANK = {OK: 0, WARN: 1, FAIL: 2}


@dataclass
class Check:
    id: str
    label: str
    status: str
    detail: str


@dataclass
class ValidationReport:
    status: str
    checks: list[Check] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    bbox_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": [asdict(c) for c in self.checks],
            "corrections": self.corrections,
            "bbox_mm": [round(v, 1) for v in self.bbox_mm],
        }


def _worst(checks: list[Check]) -> str:
    return max((c.status for c in checks), key=lambda s: _RANK[s], default=OK)


def _bbox(mesh: trimesh.Trimesh) -> tuple[float, float, float]:
    size = mesh.bounds[1] - mesh.bounds[0]
    return (float(size[0]), float(size[1]), float(size[2]))


# --------------------------------------------------------------------------- #
#  Individual checks
# --------------------------------------------------------------------------- #
def _check_integrity(mesh: trimesh.Trimesh) -> Check:
    problems = []
    if not mesh.is_watertight:
        problems.append("nicht wasserdicht")
    if not mesh.is_winding_consistent:
        problems.append("uneinheitliche Flächen")
    if mesh.volume <= 0:
        problems.append("kein Volumen")
    if problems:
        return Check("integrity", "Geometrie-Integrität", FAIL,
                     "Modell ist " + ", ".join(problems) + ".")
    return Check("integrity", "Geometrie-Integrität", OK,
                 "Wasserdicht und vollständig geschlossen – druckbar.")


def _check_fit(mesh: trimesh.Trimesh, prn: Printer) -> Check:
    ux, uy, uz = prn.usable
    x, y, z = _bbox(mesh)
    if x <= ux and y <= uy and z <= uz:
        return Check("fit", "Bauraum", OK,
                     f"Passt aufs Druckbett ({x:.0f}×{y:.0f}×{z:.0f} mm "
                     f"in {ux:.0f}×{uy:.0f}×{uz:.0f} mm).")
    return Check("fit", "Bauraum", FAIL,
                 f"Zu gross ({x:.0f}×{y:.0f}×{z:.0f} mm) für den Bauraum "
                 f"{ux:.0f}×{uy:.0f}×{uz:.0f} mm.")


def _check_walls(params: dict, mat: Material) -> Check:
    rules = CONFIG.rules
    wall = params.get("wandstaerke")
    if wall is None:
        wall = params.get("staerke")
    if wall is None:
        return Check("walls", "Wandstärke", OK,
                     "Keine dünnen Wände – massives Teil.")
    wall = float(wall)
    if wall < rules.absolute_min_wall:
        return Check("walls", "Wandstärke", FAIL,
                     f"{wall:.1f} mm ist zu dünn (Minimum "
                     f"{rules.absolute_min_wall:.1f} mm = 2 Düsenbreiten).")
    if wall < rules.preferred_wall:
        return Check("walls", "Wandstärke", WARN,
                     f"{wall:.1f} mm ist druckbar, aber {rules.preferred_wall:.1f} mm "
                     f"wäre stabiler.")
    return Check("walls", "Wandstärke", OK,
                 f"{wall:.1f} mm – stabil und materialsparend.")


def _check_features(params: dict) -> Check:
    """Warn if any small dimensional feature is below the nozzle diameter."""
    rules = CONFIG.rules
    suspects = {
        "lochdurchmesser": "Loch-Durchmesser",
        "eckenradius": "Eckenradius",
    }
    for key, label in suspects.items():
        if key in params:
            val = float(params[key])
            if 0 < val < rules.min_feature:
                return Check("features", "Feine Details", WARN,
                             f"{label} {val:.1f} mm liegt unter der Düsenbreite "
                             f"({rules.min_feature:.1f} mm) und kann ungenau werden.")
    return Check("features", "Feine Details", OK,
                 "Alle Details sind grösser als die Düsenbreite.")


def _check_overhangs(mesh: trimesh.Trimesh, mat: Material) -> Check:
    """
    Flag downward-facing surfaces above the bed that exceed the material's
    unsupported-overhang limit. Our templates are designed support-free, so this
    is normally clean — but the same check guards future (Phase 2) geometry.
    """
    fn = mesh.face_normals
    fc = mesh.triangles_center
    z_floor = mesh.bounds[0][2]

    # A downward surface tilted more than `max_overhang_deg` from vertical has a
    # normal whose downward (−z) component exceeds sin(limit).
    limit_z = math.sin(math.radians(mat.max_overhang_deg))
    downward = fn[:, 2] < -limit_z
    above_bed = fc[:, 2] > z_floor + 0.6
    risky = downward & above_bed

    area = float(mesh.area_faces[risky].sum()) if risky.any() else 0.0
    if area > 5.0:
        return Check("overhangs", "Überhänge", WARN,
                     f"≈{area:.0f} mm² überhängende Fläche – evtl. Stützen oder "
                     f"andere Ausrichtung nötig.")
    return Check("overhangs", "Überhänge", OK,
                 "Keine kritischen Überhänge – druckt ohne Stützen.")


# --------------------------------------------------------------------------- #
#  Auto-correction: scale down to fit the build volume
# --------------------------------------------------------------------------- #
def _autoscale_to_fit(mesh: trimesh.Trimesh, prn: Printer) -> tuple[trimesh.Trimesh, str | None]:
    ux, uy, uz = prn.usable
    x, y, z = _bbox(mesh)
    factors = [ux / x if x > ux else 1.0,
               uy / y if y > uy else 1.0,
               uz / z if z > uz else 1.0]
    factor = min(factors)
    if factor >= 1.0:
        return mesh, None
    factor *= 0.999  # tiny safety margin
    mesh.apply_scale(factor)
    return mesh, (f"Modell auf {factor * 100:.0f} % skaliert, "
                  f"damit es aufs Druckbett passt.")


# --------------------------------------------------------------------------- #
#  Public entry point
# --------------------------------------------------------------------------- #
def validate(mesh: trimesh.Trimesh, params: dict, mat: Material, prn: Printer,
             autoscale: bool = True) -> tuple[trimesh.Trimesh, ValidationReport]:
    corrections: list[str] = []

    if autoscale:
        mesh, note = _autoscale_to_fit(mesh, prn)
        if note:
            corrections.append(note)
            # Re-centre on the bed after scaling.
            from .geometry.solids import place_on_bed
            place_on_bed(mesh)

    checks = [
        _check_integrity(mesh),
        _check_fit(mesh, prn),
        _check_walls(params, mat),
        _check_features(params),
        _check_overhangs(mesh, mat),
    ]
    report = ValidationReport(
        status=_worst(checks),
        checks=checks,
        corrections=corrections,
        bbox_mm=_bbox(mesh),
    )
    return mesh, report
