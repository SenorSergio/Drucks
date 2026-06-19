"""
Druckts? Idea-to-Print — central configuration.

All values are grounded in Druckts' *real* production setup, taken from their
PrusaSlicer config bundle, Materialtabelle and 2026 pricing sheet:

- Printers they actually run (Prusa MK3S+MMU, Voron V2).
- The three customer materials with real densities, spool prices and the
  "0.15 mm QUALITY @MK3" print profile (gyroid, 15–20 % infill, 2–3 perimeters).
- The pricing inputs (printer power, electricity price) behind the cost formula.

Editing values here changes the whole pipeline — there is no hidden limit elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# --------------------------------------------------------------------------- #
#  Printers (user-selectable)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Printer:
    id: str
    name: str
    build_x: float
    build_y: float
    build_z: float
    nozzle_diameter: float = 0.4
    margin_mm: float = 5.0          # kept free on every axis so parts never touch the edge
    power_w: float = 100.0          # average power draw, for the energy cost estimate

    @property
    def usable(self) -> tuple[float, float, float]:
        m = 2 * self.margin_mm
        return (self.build_x - m, self.build_y - m, self.build_z - m)


PRINTERS: dict[str, Printer] = {
    # Their main multi-material FDM workhorse; all print profiles are tuned "@MK3".
    "mk3s": Printer("mk3s", "Prusa MK3S+", 250.0, 210.0, 210.0, power_w=100.0),
    # Larger custom FDM.
    "voron": Printer("voron", "Voron V2", 350.0, 350.0, 200.0, power_w=150.0),
}
DEFAULT_PRINTER = "mk3s"


def printer(printer_id: str | None) -> Printer:
    if not printer_id:
        return PRINTERS[DEFAULT_PRINTER]
    return PRINTERS.get(printer_id, PRINTERS[DEFAULT_PRINTER])


# --------------------------------------------------------------------------- #
#  Colours (customer-facing palette per material)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Color:
    name: str       # German display name
    hex: str        # approximate swatch colour for the UI + 3D preview


def _c(name: str, hex_: str) -> Color:
    return Color(name, hex_)


# Curated from Druckts' real Extrudr / Formfutura colour ranges.
_PLA_COLORS = (
    _c("Schwarz", "#1b1b1b"), _c("Weiss", "#f2f1ec"), _c("Anthrazit", "#383b3e"),
    _c("Grau", "#8b9094"), _c("Silber", "#c7cacc"), _c("Blau", "#1f4fa8"),
    _c("Hellblau", "#6fa8dc"), _c("Türkis", "#1bb5b0"), _c("Smaragdgrün", "#1f8a4c"),
    _c("Signalgrün", "#3fb24a"), _c("Gelb", "#f4c518"), _c("Orange", "#ef7d1a"),
    _c("Neonorange", "#ff5a1f"), _c("Rot", "#c5302a"), _c("Braun", "#6b4a2f"),
    _c("Purpur", "#6a3da8"), _c("Gold", "#c7a24a"), _c("Beige", "#cbb48a"),
)
_GREENTEC_COLORS = (
    _c("Anthrazit", "#383b3e"), _c("Schwarz", "#1b1b1b"), _c("Natur", "#d9d2c4"),
    _c("Navyblau", "#243b6b"), _c("Rot", "#b5302a"), _c("Silber", "#c7cacc"),
    _c("Weiss", "#f2f1ec"),
)
_RPETG_COLORS = (
    _c("Schwarz", "#1b1b1b"), _c("Cremeweiss", "#ece7d8"), _c("Dunkelblau", "#243b6b"),
    _c("Grau", "#8b9094"), _c("Hellblau", "#6fa8dc"), _c("Rot", "#c5302a"),
)


# --------------------------------------------------------------------------- #
#  Materials (the real Druckts catalogue)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Material:
    id: str
    name: str
    brand: str
    mtype: str                  # "PLA" | "PETG"
    density: float              # g/cm³
    cost_per_kg: float          # CHF/kg (spool price used for pricing)
    min_wall: float             # mm
    max_overhang_deg: float     # unsupported overhang from vertical
    fit_clearance: float        # mm clearance for fitting parts (lids etc.)
    perimeters: int             # wall loops in their @MK3 profile
    infill: float               # fraction 0–1
    top_layers: int
    bottom_layers: int
    colors: tuple[Color, ...]
    blurb: str = ""             # short German description for the UI


MATERIALS: dict[str, Material] = {
    "pla_nx2": Material(
        "pla_nx2", "PLA NX2", "Extrudr", "PLA",
        density=1.24, cost_per_kg=26.0, min_wall=0.8, max_overhang_deg=50.0,
        fit_clearance=0.20, perimeters=2, infill=0.15, top_layers=6, bottom_layers=5,
        colors=_PLA_COLORS,
        blurb="Unser Standard: biologisch abbaubar, grosse Farbauswahl.",
    ),
    "greentec_pro": Material(
        "greentec_pro", "GreenTec Pro", "Extrudr", "PLA",
        density=1.35, cost_per_kg=56.0, min_wall=0.8, max_overhang_deg=50.0,
        fit_clearance=0.25, perimeters=3, infill=0.15, top_layers=4, bottom_layers=4,
        colors=_GREENTEC_COLORS,
        blurb="Robuster Biokunststoff – wärme- und schlagfest, für Beanspruchtes.",
    ),
    "reform_rpetg": Material(
        "reform_rpetg", "ReForm rPETG", "Formfutura", "PETG",
        density=1.27, cost_per_kg=20.0, min_wall=1.0, max_overhang_deg=45.0,
        fit_clearance=0.30, perimeters=3, infill=0.18, top_layers=8, bottom_layers=5,
        colors=_RPETG_COLORS,
        blurb="Recyceltes PETG – zäh und wasserfest, ideal für draussen.",
    ),
}
DEFAULT_MATERIAL = "pla_nx2"


def material(material_id: str | None) -> Material:
    """Return a material, falling back to the default (PLA NX2).

    Accepts either an id ("pla_nx2") or a display name ("PLA NX2") for tolerance.
    """
    if not material_id:
        return MATERIALS[DEFAULT_MATERIAL]
    if material_id in MATERIALS:
        return MATERIALS[material_id]
    for m in MATERIALS.values():
        if m.name.lower() == material_id.lower():
            return m
    return MATERIALS[DEFAULT_MATERIAL]


# --------------------------------------------------------------------------- #
#  Print profile + design rules (Druckts "0.15 mm QUALITY @MK3")
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DesignRules:
    nozzle_diameter: float = 0.4
    line_width: float = 0.45         # extrusion width per perimeter
    preferred_wall: float = 1.2      # nudge target for durability
    min_feature: float = 0.4         # warn below ≈ nozzle diameter
    max_bridge: float = 10.0
    layer_height: float = 0.15       # their quality standard
    first_layer_height: float = 0.2

    @property
    def absolute_min_wall(self) -> float:
        return round(2 * self.nozzle_diameter, 3)


# --------------------------------------------------------------------------- #
#  Speed model — calibrated to Druckts' real per-piece print times
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SpeedModel:
    # Effective volumetric throughput in mm³/s for their 0.15 mm fine-quality
    # workflow. Derived from real production data (e.g. Explorer body 27.5 g in
    # 220 min → ≈1.7 mm³/s). Deliberately conservative; real slicing refines it.
    flow_mm3_s: float = 1.8
    overhead_s: float = 180.0        # heat-up + first layers


# --------------------------------------------------------------------------- #
#  Pricing inputs (from the 2026 Preisberechnung sheet)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Energy:
    price_per_kwh: float = 0.32       # CHF/kWh used in their cost sheet


@dataclass(frozen=True)
class Config:
    rules: DesignRules = field(default_factory=DesignRules)
    speed: SpeedModel = field(default_factory=SpeedModel)
    energy: Energy = field(default_factory=Energy)
    ui_language: str = "de-CH"


CONFIG = Config()
