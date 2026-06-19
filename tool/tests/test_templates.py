"""Every template must build a clean, watertight, in-bounds solid."""
import io

import pytest
import trimesh

from app import export
from app.config import printer as get_printer
from app.geometry import engine
from app.geometry.templates import TEMPLATES

ALL_IDS = list(TEMPLATES.keys())
MK3S = get_printer("mk3s")


@pytest.mark.parametrize("template_id", ALL_IDS)
def test_defaults_build_watertight(template_id):
    out = engine.build_object(template_id, {}, "pla_nx2")
    mesh = out.mesh
    assert mesh.is_watertight, f"{template_id} not watertight"
    assert mesh.is_winding_consistent, f"{template_id} inconsistent winding"
    assert mesh.volume > 0


@pytest.mark.parametrize("template_id", ALL_IDS)
def test_defaults_fit_build_volume(template_id):
    out = engine.build_object(template_id, {}, "pla_nx2")
    size = out.mesh.bounds[1] - out.mesh.bounds[0]
    ux, uy, uz = MK3S.usable
    assert size[0] <= ux + 1e-6
    assert size[1] <= uy + 1e-6
    assert size[2] <= uz + 1e-6


@pytest.mark.parametrize("template_id", ALL_IDS)
def test_exports_roundtrip(template_id):
    out = engine.build_object(template_id, {}, "pla_nx2")
    stl = export.to_stl(out.mesh)
    tmf = export.to_3mf(out.mesh)
    assert len(stl) > 0 and len(tmf) > 0
    reloaded = trimesh.load(io.BytesIO(stl), file_type="stl")
    assert reloaded.is_watertight


def test_unknown_template_raises():
    with pytest.raises(engine.UnknownTemplate):
        engine.build_object("does-not-exist", {}, "pla_nx2")


def test_keychain_text_changes_length():
    short = engine.build_object("keychain", {"text": "Jo"}, "pla_nx2")
    long = engine.build_object("keychain", {"text": "Alejandro"}, "pla_nx2")
    sx = short.mesh.bounds[1][0] - short.mesh.bounds[0][0]
    lx = long.mesh.bounds[1][0] - long.mesh.bounds[0][0]
    assert lx > sx
