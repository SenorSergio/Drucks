"""
The Phase 1 template catalogue.

Each template is a small, dependable parametric program that returns a watertight
mesh. Geometry is designed to print *without supports* (closed bottoms, vertical
walls, rounded vertical edges) in line with our low-waste mission.

A `ParamSpec` describes one friendly input in German; the frontend renders the
sliders/fields straight from these specs, and `engine.py` clamps user values to
them, so there is a single source of truth for every limit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

import trimesh

from ..config import Material
from . import solids as S
from . import text3d


# --------------------------------------------------------------------------- #
#  Spec dataclasses
# --------------------------------------------------------------------------- #
@dataclass
class ParamSpec:
    key: str
    label: str                       # German label
    kind: str                        # 'number' | 'bool' | 'choice' | 'text'
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    unit: str | None = None
    help: str | None = None          # German help text
    options: list[dict] | None = None  # for 'choice': [{"value","label"}]
    maxlength: int | None = None       # for 'text'

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Built:
    mesh: trimesh.Trimesh
    orientation: str                 # German print-orientation guidance
    parts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class Template:
    id: str
    name: str                        # German display name
    tagline: str                     # short German description
    family: str                      # German object family
    params: list[ParamSpec]
    build: Callable[[dict, Material], Built]

    def schema(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "family": self.family,
            "params": [p.as_dict() for p in self.params],
        }


# --------------------------------------------------------------------------- #
#  1 · Dose mit Deckel  (box with lid)
# --------------------------------------------------------------------------- #
def build_box(p: dict, mat: Material) -> Built:
    length, width, height = p["laenge"], p["breite"], p["hoehe"]
    wall, radius = p["wandstaerke"], p["eckenradius"]
    clr = mat.fit_clearance

    outer = S.rounded_box(length, width, height, radius)
    inner = S.rounded_box(length - 2 * wall, width - 2 * wall, height,
                          max(0.0, radius - wall), z0=wall)
    container = S.difference(outer, inner)
    meshes, parts = [container], ["Behälter"]
    notes: list[str] = []

    if p["mit_deckel"]:
        lid_h = wall + 6.0
        skirt = 6.0  # how far the lid reaches down over the box
        lo_l = length + 2 * (wall + clr)
        lo_w = width + 2 * (wall + clr)
        lid_outer = S.rounded_box(lo_l, lo_w, lid_h, radius + wall + clr)
        cavity = S.rounded_box(length + 2 * clr, width + 2 * clr, skirt,
                               radius + clr, z0=lid_h - skirt)
        lid = S.difference(lid_outer, cavity)
        lid.apply_translation((0.0, width / 2 + 8.0 + lo_w / 2, 0.0))
        meshes.append(lid)
        parts.append("Deckel")
        notes.append(f"Deckel mit {clr:.2f} mm Spiel – sitzt saugend, ohne zu klemmen.")

    mesh = trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]
    return Built(
        mesh=mesh,
        orientation="Behälter offen nach oben, Deckel mit der geschlossenen Seite "
                    "nach unten – beide Teile drucken ohne Stützen.",
        parts=parts,
        notes=notes,
    )


# --------------------------------------------------------------------------- #
#  2 · Tablett / Schale  (tray)
# --------------------------------------------------------------------------- #
def build_tray(p: dict, mat: Material) -> Built:
    length, width, height = p["laenge"], p["breite"], p["hoehe"]
    wall, radius = p["wandstaerke"], p["eckenradius"]

    outer = S.rounded_box(length, width, height, radius)
    inner = S.rounded_box(length - 2 * wall, width - 2 * wall, height,
                          max(0.0, radius - wall), z0=wall)
    tray = S.difference(outer, inner)
    return Built(
        mesh=tray,
        orientation="Mit dem Boden auf das Druckbett – die offene Seite zeigt nach "
                    "oben, keine Stützen nötig.",
        parts=["Tablett"],
    )


# --------------------------------------------------------------------------- #
#  3 · Untersetzer  (coaster)
# --------------------------------------------------------------------------- #
def build_coaster(p: dict, mat: Material) -> Built:
    size, thick = p["groesse"], p["staerke"]
    rim = p["mit_rand"]
    text = p.get("text", "")
    notes: list[str] = []

    if p["form"] == "rund":
        base = S.disc(size / 2, thick)
        if rim:
            rim_h, rim_w = 2.0, 2.5
            ring = S.difference(S.disc(size / 2, rim_h, z0=thick),
                                S.disc(size / 2 - rim_w, rim_h, z0=thick))
            base = S.union(base, ring)
    else:
        r = size * 0.12
        base = S.rounded_box(size, size, thick, r)
        if rim:
            rim_h, rim_w = 2.0, 2.5
            ring = S.difference(
                S.rounded_box(size, size, rim_h, r, z0=thick),
                S.rounded_box(size - 2 * rim_w, size - 2 * rim_w, max(0.1, r - rim_w),
                              z0=thick),
            )
            base = S.union(base, ring)

    if text.strip():
        cap = min(size * 0.28, 22.0)
        tm = text3d.extrude_text(text, cap_height_mm=cap, depth_mm=1.0, z0=thick)
        if tm is not None:
            base = S.union(base, tm)
            notes.append(f"Schriftzug «{text.strip()}» erhaben aufgedruckt.")
        else:
            notes.append("Schriftzug konnte nicht erzeugt werden – ohne Text gedruckt.")

    return Built(
        mesh=base,
        orientation="Flach auf das Druckbett – die beschriftete Seite nach oben.",
        parts=["Untersetzer"],
        notes=notes,
    )


# --------------------------------------------------------------------------- #
#  4 · Stiftehalter / Utensilien-Becher  (pen & utensil holder)
# --------------------------------------------------------------------------- #
def build_holder(p: dict, mat: Material) -> Built:
    length, width, height = p["laenge"], p["breite"], p["hoehe"]
    wall = p["wandstaerke"]
    compartments = int(p["faecher"])
    radius = min(8.0, length / 4, width / 4)

    outer = S.rounded_box(length, width, height, radius)
    inner = S.rounded_box(length - 2 * wall, width - 2 * wall, height,
                          max(0.0, radius - wall), z0=wall)
    holder = S.difference(outer, inner)
    notes: list[str] = []

    if compartments > 1:
        interior = length - 2 * wall
        div_w = width - 2 * wall
        div_h = height - wall
        for i in range(1, compartments):
            x = -length / 2 + wall + interior * i / compartments
            div = S.rounded_box(wall, div_w, div_h, 0.0, z0=wall)
            div.apply_translation((x, 0.0, 0.0))
            holder = S.union(holder, div)
        notes.append(f"{compartments} Fächer durch Trennwände.")

    return Built(
        mesh=holder,
        orientation="Mit dem geschlossenen Boden auf das Druckbett – offen nach "
                    "oben, druckt ohne Stützen.",
        parts=["Halter"],
        notes=notes,
    )


# --------------------------------------------------------------------------- #
#  5 · Schlüsselanhänger / Namensschild  (keychain / name tag)
# --------------------------------------------------------------------------- #
def build_keychain(p: dict, mat: Material) -> Built:
    tag_h, thick = p["hoehe"], p["staerke"]
    hole_d = p["lochdurchmesser"]
    raised = p["text_erhaben"]
    text = (p.get("text") or "").strip()
    notes: list[str] = []

    cap = tag_h * 0.55
    poly = text3d.text_polygon(text, cap) if text else None
    if poly is not None:
        minx, _, maxx, _ = poly.bounds
        text_w = maxx - minx
    else:
        text_w = tag_h * 2.0
        if text:
            notes.append("Schriftzug konnte nicht erzeugt werden – Rohling ohne Text.")

    pad = tag_h * 0.45
    hole_zone = tag_h            # left area reserved for the hole
    tag_len = hole_zone + text_w + 2 * pad

    tag = S.rounded_box(tag_len, tag_h, thick, tag_h * 0.3)

    hole_x = -tag_len / 2 + tag_h * 0.5
    hole = S.cylinder(hole_d / 2, thick * 3, z0=-thick)
    hole.apply_translation((hole_x, 0.0, 0.0))
    tag = S.difference(tag, hole)

    if text and poly is not None:
        # Centre of the writable area (everything to the right of the hole zone).
        left = -tag_len / 2 + hole_zone
        right = tag_len / 2 - pad
        center_x = (left + right) / 2
        if raised:
            tm = text3d.extrude_text(text, cap, depth_mm=1.0, z0=thick)
            if tm is not None:
                tm.apply_translation((center_x, 0.0, 0.0))
                tag = S.union(tag, tm)
                notes.append(f"«{text}» erhaben.")
        else:
            depth = min(1.0, thick - 0.8)
            tm = text3d.extrude_text(text, cap, depth_mm=depth + 0.2, z0=thick - depth)
            if tm is not None:
                tm.apply_translation((center_x, 0.0, 0.0))
                tag = S.difference(tag, tm)
                notes.append(f"«{text}» eingraviert.")

    return Built(
        mesh=tag,
        orientation="Flach auf das Druckbett – Schrift nach oben, druckt ohne Stützen.",
        parts=["Anhänger"],
        notes=notes,
    )


# --------------------------------------------------------------------------- #
#  Registry
# --------------------------------------------------------------------------- #
def _num(key, label, default, lo, hi, step=0.5, unit="mm", help=None):
    return ParamSpec(key, label, "number", default, min=lo, max=hi, step=step,
                     unit=unit, help=help)


TEMPLATES: dict[str, Template] = {
    "box": Template(
        id="box", name="Dose mit Deckel", family="Haushalt & Deko",
        tagline="Eine Aufbewahrungsdose mit passendem Deckel – für Schrauben, Schmuck oder Würfel.",
        params=[
            _num("laenge", "Länge", 80, 20, 200),
            _num("breite", "Breite", 60, 20, 90),
            _num("hoehe", "Höhe", 45, 15, 150),
            _num("wandstaerke", "Wandstärke", 1.6, 0.8, 4.0, step=0.2),
            _num("eckenradius", "Eckenradius", 4, 0, 20),
            ParamSpec("mit_deckel", "Mit Deckel", "bool", True,
                      help="Erzeugt zusätzlich einen passenden Deckel."),
        ],
        build=build_box,
    ),
    "tray": Template(
        id="tray", name="Tablett / Schale", family="Haushalt & Deko",
        tagline="Eine flache Schale für Schlüssel, Münzen oder als Ordnungshelfer.",
        params=[
            _num("laenge", "Länge", 160, 40, 230),
            _num("breite", "Breite", 120, 40, 190),
            _num("hoehe", "Höhe", 25, 8, 60),
            _num("wandstaerke", "Wandstärke", 1.6, 0.8, 4.0, step=0.2),
            _num("eckenradius", "Eckenradius", 8, 0, 30),
        ],
        build=build_tray,
    ),
    "coaster": Template(
        id="coaster", name="Untersetzer", family="Haushalt & Deko",
        tagline="Ein Untersetzer für Gläser oder Tassen – rund oder eckig, mit Namen.",
        params=[
            ParamSpec("form", "Form", "choice", "rund",
                      options=[{"value": "rund", "label": "Rund"},
                               {"value": "eckig", "label": "Eckig"}]),
            _num("groesse", "Grösse (Ø / Kantenlänge)", 95, 60, 140),
            _num("staerke", "Stärke", 4, 2, 8, step=0.5),
            ParamSpec("mit_rand", "Mit erhöhtem Rand", "bool", True,
                      help="Hält Tropfen zurück."),
            ParamSpec("text", "Text (optional)", "text", "", maxlength=14,
                      help="Z. B. ein Name – erhaben aufgedruckt."),
        ],
        build=build_coaster,
    ),
    "holder": Template(
        id="holder", name="Stiftehalter", family="Ordnung & Halter",
        tagline="Ein Becher für Stifte und Werkzeug – wahlweise mit mehreren Fächern.",
        params=[
            _num("laenge", "Länge", 90, 30, 200),
            _num("breite", "Breite", 70, 30, 150),
            _num("hoehe", "Höhe", 95, 30, 180),
            _num("wandstaerke", "Wandstärke", 2.0, 0.8, 4.0, step=0.2),
            ParamSpec("faecher", "Fächer", "number", 1, min=1, max=4, step=1, unit=""),
        ],
        build=build_holder,
    ),
    "keychain": Template(
        id="keychain", name="Schlüsselanhänger", family="Geschenke & Personalisiert",
        tagline="Ein personalisiertes Namensschild mit Loch – ideal als kleines Geschenk.",
        params=[
            ParamSpec("text", "Text", "text", "Druckts", maxlength=16,
                      help="Dein Name oder Wort."),
            _num("hoehe", "Höhe", 22, 12, 40),
            _num("staerke", "Stärke", 3, 2, 6, step=0.5),
            _num("lochdurchmesser", "Loch-Ø", 5, 3, 10),
            ParamSpec("text_erhaben", "Schrift erhaben", "bool", True,
                      help="Erhaben (aus) = eingraviert."),
        ],
        build=build_keychain,
    ),
}
