"""Slicer g-code parsing + config flattening (no slicer binary required)."""
import pytest

from app import slicer
from app.config import material, printer as get_printer

GCODE = """
; some header
G1 X1 Y1
; filament used [mm] = 1234.5
; filament used [g] = 12.34
; estimated printing time (normal mode) = 1h 2m 3s
"""


def test_parse_gcode_reads_time_mass_length():
    parsed = slicer.parse_gcode(GCODE)
    assert parsed is not None
    time_min, grams, length_m = parsed
    assert time_min == 62          # 1h2m3s ≈ 62 min
    assert grams == pytest.approx(12.34)
    assert length_m == pytest.approx(1.2345)


def test_parse_gcode_handles_days():
    txt = "; estimated printing time (normal mode) = 1d 1h 0m 0s\n; filament used [g] = 5\n"
    parsed = slicer.parse_gcode(txt)
    assert parsed[0] == 25 * 60     # 25 h


def test_parse_gcode_none_when_missing():
    assert slicer.parse_gcode("nothing useful here") is None


def test_flatten_config_overrides_bed_and_includes_profile_keys():
    cfg = slicer._flatten_config(material("reform_rpetg"), get_printer("mk3s"))
    assert "bed_shape = 0x0,250x0,250x210,0x210" in cfg
    assert "max_print_height = 210" in cfg
    assert "layer_height = 0.15" in cfg
    assert "filament_density" in cfg
    # preset-management keys must be stripped
    assert "print_settings_id" not in cfg
