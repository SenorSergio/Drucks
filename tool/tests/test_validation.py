"""Validation, clamping and per-printer fit rules."""
import trimesh

from app import validation
from app.config import material, printer as get_printer
from app.geometry import engine

MK3S = get_printer("mk3s")
VORON = get_printer("voron")


def test_oversized_param_is_clamped():
    out = engine.build_object("box", {"laenge": 9999}, "pla_nx2")
    assert out.params_used["laenge"] == 200  # template max
    assert any("begrenzt" in c for c in out.corrections)


def test_thin_wall_raised_to_material_minimum():
    out = engine.build_object("box", {"wandstaerke": 0.1}, "pla_nx2")
    assert out.params_used["wandstaerke"] == material("pla_nx2").min_wall
    assert any("angehoben" in c for c in out.corrections)


def test_petg_requires_thicker_wall_than_pla():
    pla = engine.build_object("box", {"wandstaerke": 0.5}, "pla_nx2")
    petg = engine.build_object("box", {"wandstaerke": 0.5}, "reform_rpetg")
    assert petg.params_used["wandstaerke"] > pla.params_used["wandstaerke"]


def test_validate_passes_for_default_box():
    out = engine.build_object("box", {}, "pla_nx2")
    _, report = validation.validate(out.mesh, out.params_used, out.material, MK3S)
    assert report.status in ("ok", "warn")
    fit = next(c for c in report.checks if c.id == "fit")
    assert fit.status == "ok"


def test_autoscale_shrinks_oversized_mesh_on_mk3s():
    big = trimesh.creation.box(extents=(400, 400, 400))
    scaled, report = validation.validate(big, {}, material("pla_nx2"), MK3S)
    size = scaled.bounds[1] - scaled.bounds[0]
    ux, uy, uz = MK3S.usable
    assert size[0] <= ux + 1e-3 and size[1] <= uy + 1e-3 and size[2] <= uz + 1e-3
    assert any("skaliert" in c for c in report.corrections)


def test_part_fits_voron_but_not_mk3s():
    # 300×300×150 exceeds the MK3S bed but fits the larger Voron.
    box = trimesh.creation.box(extents=(300, 300, 150))
    _, rep_mk3 = validation.validate(box.copy(), {}, material("pla_nx2"), MK3S)
    _, rep_voron = validation.validate(box.copy(), {}, material("pla_nx2"), VORON)
    assert any("skaliert" in c for c in rep_mk3.corrections)      # had to shrink
    assert not any("skaliert" in c for c in rep_voron.corrections)  # fit as-is


def test_wall_below_preferred_warns():
    check = validation._check_walls({"wandstaerke": 0.8}, material("pla_nx2"))
    assert check.status == "warn"


def test_good_wall_is_ok():
    check = validation._check_walls({"wandstaerke": 1.6}, material("pla_nx2"))
    assert check.status == "ok"
