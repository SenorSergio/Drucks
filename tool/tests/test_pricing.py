"""Pricing must reproduce Druckts' 2026 cost sheet exactly."""
import pytest

from app.config import material, printer as get_printer
from app.estimate import Estimate
from app.pricing import production_cost


def test_matches_sheet_explorer_body():
    # Sheet row: 27.5 g, 220 min, PLA NX2 @ 26 CHF/kg, 100 W, 0.32 CHF/kWh
    est = Estimate(time_min=220, mass_g=27.5, length_m=0.0, method="x")
    price = production_cost(est, material("pla_nx2"), get_printer("mk3s"))
    assert price.material_chf == pytest.approx(0.715, abs=1e-3)
    assert price.energy_chf == pytest.approx(0.11733, abs=1e-3)
    assert price.total_chf == pytest.approx(0.83233, abs=1e-3)


def test_voron_costs_more_energy_than_mk3s():
    est = Estimate(time_min=100, mass_g=20.0, length_m=0.0, method="x")
    mk3 = production_cost(est, material("pla_nx2"), get_printer("mk3s"))
    voron = production_cost(est, material("pla_nx2"), get_printer("voron"))
    assert voron.energy_chf > mk3.energy_chf  # Voron draws more power
    assert mk3.material_chf == voron.material_chf
