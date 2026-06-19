"""
Engine orchestration: validate the template id, clamp every user value to the
template spec *and* the printer/material limits, then build the mesh.

Clamping here means the LLM (Phase 2) and the sliders (Phase 1) physically
cannot ask for something out of bounds — corrections are recorded and reported
back in plain German.
"""
from __future__ import annotations

from dataclasses import dataclass

import trimesh

from ..config import CONFIG, Material, material
from . import solids as S
from .templates import TEMPLATES, Built, Template


class UnknownTemplate(ValueError):
    pass


@dataclass
class BuildOutput:
    template: Template
    mesh: trimesh.Trimesh
    params_used: dict
    corrections: list[str]
    material: Material
    built: Built


def list_templates() -> list[dict]:
    return [t.schema() for t in TEMPLATES.values()]


def get_template(template_id: str) -> Template:
    try:
        return TEMPLATES[template_id]
    except KeyError:
        raise UnknownTemplate(f"Unbekannte Vorlage: {template_id!r}")


def _coerce_params(template: Template, raw: dict, mat: Material) -> tuple[dict, list[str]]:
    clean: dict = {}
    notes: list[str] = []

    for spec in template.params:
        value = raw.get(spec.key, spec.default)

        if spec.kind == "number":
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = float(spec.default)
            if spec.step == 1:
                value = round(value)
            lo, hi = spec.min, spec.max
            if lo is not None and value < lo:
                notes.append(f"{spec.label} auf {_fmt(lo, spec)} angehoben (Minimum).")
                value = lo
            if hi is not None and value > hi:
                notes.append(f"{spec.label} auf {_fmt(hi, spec)} begrenzt (Druckbett).")
                value = hi

        elif spec.kind == "bool":
            value = bool(value)

        elif spec.kind == "choice":
            allowed = {o["value"] for o in (spec.options or [])}
            if value not in allowed:
                value = spec.default

        elif spec.kind == "text":
            value = str(value or "")
            if spec.maxlength and len(value) > spec.maxlength:
                value = value[: spec.maxlength]
                notes.append(f"{spec.label} auf {spec.maxlength} Zeichen gekürzt.")

        clean[spec.key] = value

    # Material-aware minimum wall thickness overrides any thinner request.
    if "wandstaerke" in clean and clean["wandstaerke"] < mat.min_wall:
        notes.append(
            f"Wandstärke auf {mat.min_wall:.1f} mm angehoben "
            f"(Minimum für {mat.name})."
        )
        clean["wandstaerke"] = mat.min_wall

    return clean, notes


def _fmt(value: float, spec) -> str:
    unit = f" {spec.unit}" if spec.unit else ""
    text = f"{value:g}"
    return f"{text}{unit}"


def build_object(template_id: str, raw_params: dict,
                 material_name: str | None) -> BuildOutput:
    template = get_template(template_id)
    mat = material(material_name)
    params, corrections = _coerce_params(template, raw_params, mat)

    built = template.build(params, mat)
    mesh = S.cleanup(built.mesh)
    S.place_on_bed(mesh)

    return BuildOutput(
        template=template,
        mesh=mesh,
        params_used=params,
        corrections=corrections,
        material=mat,
        built=built,
    )
