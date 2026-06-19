"""Full-pipeline smoke test: build -> validate -> estimate -> price -> spec."""
from app import estimate as estimate_mod
from app import export, pricing, validation
from app.config import printer as get_printer
from app.geometry import engine
from app.spec import build_spec

cases = [
    ("box", {"laenge": 90, "breite": 60, "hoehe": 50}, "pla_nx2", "mk3s", "Blau"),
    ("tray", {}, "reform_rpetg", "mk3s", "Grau"),
    ("coaster", {"form": "eckig", "text": "Anna"}, "greentec_pro", "mk3s", "Rot"),
    ("holder", {"faecher": 3}, "pla_nx2", "voron", None),
    ("keychain", {"text": "Druckts"}, "pla_nx2", "mk3s", "Gold"),
    # out-of-range -> clamp + (on MK3S) fit check
    ("box", {"laenge": 9999, "wandstaerke": 0.1}, "pla_nx2", "mk3s", None),
]

for tid, params, matid, prnid, color in cases:
    prn = get_printer(prnid)
    out = engine.build_object(tid, params, matid)
    mesh, report = validation.validate(out.mesh, out.params_used, out.material, prn)
    out.mesh = mesh
    stl = export.to_stl(mesh)
    est = estimate_mod.estimate(mesh, out.material, stl_bytes=stl, prn=prn)
    price = pricing.production_cost(est, out.material, prn)
    spec = build_spec(out, report, est, color=color, printer_name=prn.name)

    print(f"{tid:9s} {out.material.name:13s} {prn.name:10s} status={report.status:4s} "
          f"{est.time_min:4d}min {est.mass_g:5.0f}g  "
          f"cost=CHF {price.total_chf:5.2f} (mat {price.material_chf:.2f} + en {price.energy_chf:.2f})  "
          f"farbe={spec['farbe']}")
    if out.corrections:
        print("   corr:", out.corrections)

print("\nALL CASES OK")
