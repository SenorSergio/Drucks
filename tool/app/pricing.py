"""
Production-cost calculation — team-internal only.

Mirrors Druckts' 2026 pricing sheet (`Preisberechnung_eigene_Produkte_Druckts_2026.xlsx`):

    Materialkosten  = Spulenpreis[CHF/kg] / 1000 × Gewicht[g]
    Energiekosten   = Druckzeit[min] / 60 × (Druckerleistung[W] / 1000) × Strompreis[CHF/kWh]
    Produktionskosten = Material + Energie

This is the *cost* (no margin). The team adds their donation margin when they
send the binding Offerte, so this figure is shown only in the internal team view,
never to the customer.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import CONFIG, Material, Printer
from .estimate import Estimate


@dataclass
class Price:
    material_chf: float
    energy_chf: float
    total_chf: float
    note: str

    def as_dict(self) -> dict:
        return {
            "material_chf": round(self.material_chf, 2),
            "energy_chf": round(self.energy_chf, 2),
            "total_chf": round(self.total_chf, 2),
            "note": self.note,
        }


def production_cost(est: Estimate, mat: Material, prn: Printer) -> Price:
    material = mat.cost_per_kg / 1000.0 * est.mass_g
    energy = est.time_min / 60.0 * (prn.power_w / 1000.0) * CONFIG.energy.price_per_kwh
    return Price(
        material_chf=material,
        energy_chf=energy,
        total_chf=material + energy,
        note=(f"Produktionskosten nach Druckts-Preismodell 2026 "
              f"({mat.cost_per_kg:.0f} CHF/kg, {prn.power_w:.0f} W, "
              f"{CONFIG.energy.price_per_kwh:.2f} CHF/kWh). Ohne Marge."),
    )
