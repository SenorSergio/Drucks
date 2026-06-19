"""
Druckts? Idea-to-Print — Phase 1 API.

Pipeline per request:  build → validate (+auto-correct) → estimate → export.
Generated files are cached in memory and served for preview/download.

For local development the same server also serves the static site, so the
configurator page and the API share one origin (no CORS headaches).
"""
from __future__ import annotations

import uuid
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import estimate as estimate_mod
from . import export, pricing, validation
from .config import CONFIG, MATERIALS, PRINTERS, material as get_material, printer as get_printer
from .geometry import engine
from .models import GenerateRequest
from .spec import build_spec

app = FastAPI(title="Druckts? Idea-to-Print", version="0.1.0")

# Dev convenience: allow the static site to call the API from any origin.
# TODO (deploy): restrict allow_origins to druckts.ch.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple bounded in-memory cache of generated files: id -> {stl, threemf, base}.
_CACHE: "OrderedDict[str, dict]" = OrderedDict()
_CACHE_MAX = 50


def _remember(entry: dict) -> str:
    rid = uuid.uuid4().hex[:12]
    _CACHE[rid] = entry
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return rid


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "slicer": estimate_mod.find_slicer()}


@app.get("/api/config")
def config() -> dict:
    return {
        "printers": [
            {
                "id": p.id,
                "name": p.name,
                "build_volume_mm": {"x": p.build_x, "y": p.build_y, "z": p.build_z},
                "nozzle_mm": p.nozzle_diameter,
            }
            for p in PRINTERS.values()
        ],
        "materials": [
            {
                "id": m.id,
                "name": m.name,
                "brand": m.brand,
                "type": m.mtype,
                "min_wall": m.min_wall,
                "blurb": m.blurb,
                "colors": [{"name": c.name, "hex": c.hex} for c in m.colors],
            }
            for m in MATERIALS.values()
        ],
    }


@app.get("/api/templates")
def templates() -> dict:
    return {"templates": engine.list_templates()}


@app.post("/api/generate")
def generate(req: GenerateRequest) -> dict:
    prn = get_printer(req.printer)
    try:
        out = engine.build_object(req.template, req.params, req.material)
    except engine.UnknownTemplate as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=422,
            detail=f"Modell konnte nicht erzeugt werden: {exc}",
        )

    mesh, report = validation.validate(out.mesh, out.params_used, out.material, prn)
    out.mesh = mesh
    stl = export.to_stl(mesh)
    est = estimate_mod.estimate(mesh, out.material, stl_bytes=stl,
                                prn=prn, precise=req.precise)
    price = pricing.production_cost(est, out.material, prn)
    spec = build_spec(out, report, est, color=req.color, printer_name=prn.name)

    rid = _remember({
        "stl": stl,
        "threemf": export.to_3mf(mesh),
        "base": f"druckts_{req.template}",
    })

    return {
        "id": rid,
        "spec": spec,
        "validation": report.as_dict(),
        "estimate": est.as_dict(),
        "params_used": out.params_used,
        "material": out.material.name,
        "material_id": out.material.id,
        "printer": {"id": prn.id, "name": prn.name},
        "color": req.color,
        # Team-internal: never rendered in the customer view.
        "team": {"price": price.as_dict()},
        "preview_url": f"/api/preview/{rid}.stl",
        "downloads": {
            "stl": f"/api/download/{rid}/stl",
            "3mf": f"/api/download/{rid}/3mf",
        },
    }


@app.get("/api/preview/{rid}.stl")
def preview(rid: str) -> Response:
    entry = _CACHE.get(rid)
    if not entry:
        raise HTTPException(status_code=404, detail="Vorschau abgelaufen.")
    return Response(content=entry["stl"], media_type="model/stl")


@app.get("/api/download/{rid}/{fmt}")
def download(rid: str, fmt: str) -> Response:
    entry = _CACHE.get(rid)
    if not entry:
        raise HTTPException(status_code=404, detail="Datei abgelaufen.")
    fmt = fmt.lower()
    if fmt == "stl":
        data, mime, ext = entry["stl"], "model/stl", "stl"
    elif fmt in ("3mf", "threemf"):
        data, mime, ext = entry["threemf"], "model/3mf", "3mf"
    else:
        raise HTTPException(status_code=400, detail="Unbekanntes Format.")
    filename = f"{entry['base']}.{ext}"
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
#  Serve the static site last, so /api/* always wins.
# --------------------------------------------------------------------------- #
_SITE_ROOT = Path(__file__).resolve().parents[2]
app.mount("/", StaticFiles(directory=str(_SITE_ROOT), html=True), name="site")
