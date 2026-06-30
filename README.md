# Druckts? — Website-Relaunch (3 Design-Versionen)

Statischer Relaunch-Entwurf für **druckts.ch** – dem gemeinnützigen Verein aus Winterthur
für nachhaltigen, individuellen 3D-Druck. Es gibt **drei komplette Design-Versionen** mit
identischen Inhalten, aber unterschiedlicher Bildsprache. Der Verein wählt anschliessend
eine Richtung aus.

## Versionen
| | Name | Charakter |
|---|------|-----------|
| **V1** | Eco Clean | Swiss Minimal, hell, viel Weissraum, edel |
| **V2** | Bold Maker | Vibrant, fette Typo, Sticker-Look, verspielt |
| **V3** | Dark Tech | Dunkel, Glas-Effekte, Neon-Mint, premium |

## Struktur
```
index.html              Auswahlseite ("Wähle dein Design")
versions/v1|v2|v3/      die drei Landingpages
assets/css/base.css     Reset, Design-Tokens, Animationen (geteilt)
assets/css/v1|v2|v3.css versionsspezifische Stylesheets
assets/js/printer.js    animiertes 3D-Drucker-SVG (Marken-Leitmotiv)
assets/js/reveal.js     Scroll-Reveals, Count-up, Navigation
assets/svg/favicon.svg  Marken-Icon
netlify.toml            Netlify-Konfiguration (kein Build nötig)
```

## Lokal ansehen
Kein Build erforderlich. Im Projektordner:
```bash
python3 -m http.server 8000
```
Dann `http://localhost:8000/` öffnen. Über `/v1`, `/v2`, `/v3` (Netlify) bzw. die Kacheln
auf der Startseite gelangst du zu den Versionen. Der Umschalter unten in jeder Version
wechselt schnell zwischen den Designs.

## Deploy auf Netlify
Die Seite ist statisch und deployt ohne Build-Schritt.

**Variante A — Git verbinden (empfohlen):**
1. In Netlify → *Add new site* → *Import an existing project*
2. Dieses Repository und den Branch wählen
3. Build command: *leer*, Publish directory: `.` → *Deploy*

**Variante B — CLI:**
```bash
npm i -g netlify-cli
netlify deploy --prod
```

### Kontaktformular
Die Formulare nutzen **Netlify Forms** (`data-netlify="true"` + Honeypot) – nach dem Deploy
landen Einsendungen automatisch im Netlify-Dashboard unter *Forms*, ganz ohne Backend.

## Noch offen / Feinschliff
- Echte Referenz-Fotos für die Inspiration-Galerie einsetzen und die zwei
  Beispiel-Posts ersetzen — Schritt-für-Schritt-Anleitung: [ANLEITUNG-POSTS.md](ANLEITUNG-POSTS.md)
- Social-Links ergänzen, sobald vorhanden
- Masse für «Resident» nachtragen (Detail-Dialog auf aschenbecher.html)
