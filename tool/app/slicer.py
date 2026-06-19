"""
Real slicing via PrusaSlicer (optional, exact numbers).

When a PrusaSlicer console binary is available, this slices the generated STL
using Druckts' own profiles (committed in ``tool/profiles``) and reads the exact
print time + filament weight from the g-code. If no slicer is found, callers
fall back to the calibrated heuristic in :mod:`app.estimate`.

Enabling it: install PrusaSlicer and either put it on PATH, set the
``DRUCKTS_SLICER`` env var to ``prusa-slicer-console.exe``, or drop a portable
copy in ``tool/slicer/``. (The production archive's bundled folder ships only the
g-code viewer, not the slicer, so it cannot be used directly.)
"""
from __future__ import annotations

import configparser
import os
import re
import subprocess
import tempfile
from pathlib import Path

from .config import Material, Printer, printer as get_printer
from .estimate import Estimate, find_slicer

_BASE = Path(__file__).resolve().parent.parent
_BUNDLE = _BASE / "profiles" / "druckts_prusaslicer.ini"

# material id -> (print preset, filament preset) names in the config bundle
_PRESETS = {
    "pla_nx2": ("0.15mm QUALITY @MK3 - PLA NX2", "Extrudr PLA NX2 @MMU2"),
    "greentec_pro": ("0.15mm QUALITY @MK3 - GreenTec Pro", "Extrudr GreenTec Pro @MMU2"),
    "reform_rpetg": ("0.15mm QUALITY @MK3 - PETG", "Formfutura ReForm rPETG @MMU2"),
}

# Preset-management keys that must not appear in a flat slicing config.
_SKIP_KEYS = ("inherits", "print_settings_id", "filament_settings_id",
              "printer_settings_id", "compatible_printers_condition",
              "compatible_prints_condition", "printer_model", "printer_variant")


# --------------------------------------------------------------------------- #
#  Slicer discovery
# --------------------------------------------------------------------------- #
def find_prusa() -> str | None:
    env = os.environ.get("DRUCKTS_SLICER")
    if env and os.path.exists(env):
        return env
    for name in ("prusa-slicer-console.exe", "PrusaSlicer.exe", "prusa-slicer"):
        cand = _BASE / "slicer" / name
        if cand.exists():
            return str(cand)
    return find_slicer()


# --------------------------------------------------------------------------- #
#  Config flattening (bundle presets -> one flat config PrusaSlicer can --load)
# --------------------------------------------------------------------------- #
def _read_bundle() -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str  # keep key case
    cp.read(_BUNDLE, encoding="utf-8")
    return cp


def _flatten_config(mat: Material, prn: Printer) -> str:
    cp = _read_bundle()
    print_preset, filament_preset = _PRESETS.get(mat.id, _PRESETS["pla_nx2"])

    merged: dict[str, str] = {}
    # any printer section (the bundle only ships Voron V2); bed is overridden below
    printer_sec = next((s for s in cp.sections() if s.startswith("printer:")), None)
    for section in (printer_sec, f"print:{print_preset}", f"filament:{filament_preset}"):
        if section and cp.has_section(section):
            for key, val in cp.items(section):
                if key not in _SKIP_KEYS:
                    merged[key] = val

    # Override the build volume for the selected printer.
    bx, by, bz = prn.build_x, prn.build_y, prn.build_z
    merged["bed_shape"] = f"0x0,{bx:g}x0,{bx:g}x{by:g},0x{by:g}"
    merged["max_print_height"] = f"{bz:g}"
    merged["nozzle_diameter"] = f"{prn.nozzle_diameter:g}"

    lines = [f"{k} = {v}" for k, v in merged.items()]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
#  G-code footer parsing (pure + unit-tested)
# --------------------------------------------------------------------------- #
_TIME_RE = re.compile(
    r"estimated printing time \(normal mode\)\s*=\s*"
    r"(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?")
_GRAMS_RE = re.compile(r"filament used \[g\]\s*=\s*([\d.]+)")
_MM_RE = re.compile(r"filament used \[mm\]\s*=\s*([\d.]+)")


def parse_gcode(text: str) -> tuple[int, float, float] | None:
    """Return (time_min, mass_g, length_m) from a PrusaSlicer g-code, or None."""
    tm = _TIME_RE.search(text)
    gm = _GRAMS_RE.search(text)
    if not tm or not gm:
        return None
    d, h, m, s = (int(x) if x else 0 for x in tm.groups())
    seconds = ((d * 24 + h) * 60 + m) * 60 + s
    grams = float(gm.group(1))
    mmm = _MM_RE.search(text)
    length_m = float(mmm.group(1)) / 1000.0 if mmm else 0.0
    return max(1, round(seconds / 60.0)), grams, length_m


# --------------------------------------------------------------------------- #
#  Public entry point
# --------------------------------------------------------------------------- #
def slice_estimate(stl_bytes: bytes, mat: Material, prn: Printer | None = None,
                   timeout_s: int = 120) -> Estimate | None:
    exe = find_prusa()
    if not exe or not _BUNDLE.exists():
        return None
    prn = prn or get_printer(None)

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        stl = tdp / "model.stl"
        cfg = tdp / "config.ini"
        out = tdp / "out.gcode"
        stl.write_bytes(stl_bytes)
        cfg.write_text(_flatten_config(mat, prn), encoding="utf-8")
        try:
            subprocess.run(
                [exe, "--export-gcode", "--load", str(cfg),
                 "--output", str(out), str(stl)],
                cwd=td, capture_output=True, timeout=timeout_s, check=True,
            )
        except (subprocess.SubprocessError, OSError):
            return None
        if not out.exists():
            return None
        parsed = parse_gcode(out.read_text(encoding="utf-8", errors="ignore"))
        if not parsed:
            return None
        time_min, grams, length_m = parsed
        return Estimate(time_min=time_min, mass_g=grams, length_m=length_m,
                        method="PrusaSlicer (exakt)")
