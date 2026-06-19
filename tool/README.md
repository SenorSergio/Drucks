# Druckts? Idea-to-Print — Phase 1 (Vorlagen-Konfigurator)

This is the little program that turns a few sliders into a **real, printable file**
(3MF + STL), checks it against our printer's limits, and shows a plain-language
spec with a print-time and material estimate. **No AI yet** — that's Phase 2.

It powers the page **`konfigurator.html`** on the website.

---

## How to start it (the easy way)

1. Open the `tool` folder.
2. Double-click **`start.bat`**.
   A black window opens and stays open — that's the program running. Leave it open.
3. Open your browser and go to:
   **http://127.0.0.1:8000/konfigurator.html**

To **stop** it: click the black window and press `Ctrl + C`, or just close the window.

> The address starts with `127.0.0.1`, which simply means "this same computer".
> Nothing is online yet — it only runs on your machine.

---

## What it can make (Phase 1 templates)

| Vorlage | Was |
|---|---|
| 📦 Dose mit Deckel | Aufbewahrungsdose + passender Deckel |
| 🍽️ Tablett / Schale | flache Schale / Ordnungshelfer |
| 🥃 Untersetzer | rund oder eckig, mit Namen |
| ✏️ Stiftehalter | Becher, optional mit Fächern |
| 🔑 Schlüsselanhänger | Namensschild mit Loch |

Every model is automatically:
- built **watertight** (a valid solid that can actually be printed),
- kept **inside the build volume** (auto-shrunk if too big),
- checked for **wall thickness, fine details and overhangs**,
- designed to print **without supports** (less waste — our mission),
- exported as **3MF** (preferred) **and STL**, with a German spec + estimate.

Everything below is grounded in your **real production setup** (read from your
PrusaSlicer config bundle, Materialtabelle and 2026 pricing sheet) — all in
**`app/config.py`**, the single source of truth:

- **Printers (you pick one):** Prusa MK3S+ (250 × 210 × 210 mm) and Voron V2
  (350 × 350 × 200 mm). The 3D plate resizes to match.
- **Materials (your real catalogue):** Extrudr **PLA NX2**, Extrudr **GreenTec Pro**,
  Formfutura **ReForm rPETG** — with real densities, spool prices and your
  "0.15 mm QUALITY @MK3" profile (gyroid, 15–20 % infill, 2–3 perimeters).
- **Colours:** the real colour palette per material; the chosen colour shows on
  the 3D preview and is recorded for the order.

## Price (team-only)

The tool computes the **production cost** with your 2026 formula
(`material g × spool price + print-time × printer-watts × electricity price`).
Customers never see it. To view it, open the page with
**`konfigurator.html?ansicht=team`** — a "🔒 Intern" panel shows
material + energy + total CHF. The team's donation margin / final Offerte stays
manual, exactly as today.

## Print-time / material estimate

The default estimate is a **calculation calibrated to your real print times**
(≈1.8 mm³/s for the 0.15 mm quality workflow). The **"Genauer berechnen"** button
asks for an exact slice — this activates automatically once a real **PrusaSlicer**
is available (set the `DRUCKTS_SLICER` env var to `prusa-slicer-console.exe`, or
drop a portable copy in `tool/slicer/`). Your config bundle is committed in
`tool/profiles/`. (`/api/health` shows whether a slicer was found.) Note: the
PrusaSlicer folder inside your production archive ships only the g-code *viewer*,
not the slicer itself, so a normal PrusaSlicer install is needed for exact numbers.

---

## For developers

```
tool/
  app/
    main.py            FastAPI app + endpoints (also serves the static site)
    config.py          printer + material limits and design rules (single source of truth)
    models.py          request schema
    geometry/
      solids.py        watertight building blocks (trimesh + manifold3d)
      text3d.py        text → 3D outlines (matplotlib font paths)
      templates.py     the 5 parametric templates + their German parameter specs
      engine.py        clamps inputs to limits, then builds
    validation.py      printability checks + auto-scale (per selected printer)
    estimate.py        calibrated print-time / material estimate (+ slicer hook)
    pricing.py         team-only production-cost (2026 sheet formula)
    slicer.py          optional exact slicing via PrusaSlicer + your profiles
    export.py          STL / 3MF export
    spec.py            plain-language German spec
  profiles/            your committed PrusaSlicer config bundle
  tests/               pytest suite (templates, validation, pricing, slicer)
  scripts/smoke.py     quick manual end-to-end check
  requirements.txt
```

First-time setup (already done on this machine):

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

Run the server manually:

```bash
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
```

Run the tests:

```bash
.venv/Scripts/python -m pytest -q
```

API quick reference:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/templates` | template list + parameter specs (drives the UI) |
| GET | `/api/config` | printer / material info |
| POST | `/api/generate` | build → validate → estimate → export; returns spec + links |
| GET | `/api/preview/{id}.stl` | STL for the 3D viewer |
| GET | `/api/download/{id}/{stl\|3mf}` | download the file |

---

## What is *not* in Phase 1 (on purpose)

- **No AI / free-text wishes** — that's Phase 2 (the brief's plan). The pipeline
  here is built so the AI later just feeds the *same* validate → export steps.
- **No editable STEP file** — Phase 1 uses the lightweight `trimesh` engine so it
  runs anywhere with zero extra installs. CadQuery (with STEP export) belongs in
  the Phase 2 server, where it installs cleanly.
- **Not deployed online** — for now it runs on your computer. Putting it on a small
  server is a later step (and the part that costs a little money each month).
- **Rate-limiting / enquiry gating** — Phase 3.
