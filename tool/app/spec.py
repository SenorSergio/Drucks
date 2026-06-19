"""
Plain-language spec (German, de-CH) for non-experts, plus a compact technical
summary for the team review. Built from the engine output + validation + estimate.
"""
from __future__ import annotations

from .estimate import Estimate
from .geometry.engine import BuildOutput
from .validation import ValidationReport


def _dims(bbox: tuple[float, float, float]) -> str:
    x, y, z = bbox
    return f"{x:.0f} × {y:.0f} × {z:.0f} mm (L × B × H)"


def build_spec(out: BuildOutput, report: ValidationReport,
               est: Estimate, color: str | None = None,
               printer_name: str | None = None) -> dict:
    t = out.template
    hinweise: list[str] = []
    hinweise.extend(out.corrections)
    hinweise.extend(out.built.notes)
    hinweise.extend(report.corrections)

    material = out.material.name
    if color:
        material = f"{material}, {color}"

    spec = {
        "titel": t.name,
        "beschreibung": t.tagline,
        "familie": t.family,
        "teile": out.built.parts,
        "masse": _dims(report.bbox_mm),
        "material": material,
        "farbe": color or "—",
        "drucker": printer_name or "",
        "ausrichtung": out.built.orientation,
        "druckzeit": f"ca. {est.time_min} Min",
        "materialverbrauch": f"ca. {est.mass_g:.0f} g · {est.length_m:.1f} m Filament",
        "schaetzmethode": est.method,
        "hinweise": hinweise,
    }
    spec["klartext"] = _plain_text(spec)
    return spec


def _plain_text(spec: dict) -> str:
    teile = ", ".join(spec["teile"])
    lines = [
        f"{spec['titel']} — {spec['beschreibung']}",
        "",
        f"Was entsteht: {teile}.",
        f"Grösse: {spec['masse']}.",
        f"Material: {spec['material']} (biologisch abbaubar, mit Solarstrom gedruckt).",
        f"Ausrichtung beim Druck: {spec['ausrichtung']}",
        f"Geschätzte Druckzeit: {spec['druckzeit']}.",
        f"Materialeinsatz: {spec['materialverbrauch']} ({spec['schaetzmethode']}).",
    ]
    if spec["hinweise"]:
        lines.append("")
        lines.append("Hinweise:")
        lines.extend(f"• {h}" for h in spec["hinweise"])
    return "\n".join(lines)
