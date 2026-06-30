# Anleitung: Neuen Inspiration-Post hinzufügen

Diese Anleitung richtet sich an alle im Verein — **es sind keine Programmierkenntnisse nötig.**
Die Galerie auf `inspiration.html` und der Teaser auf der Startseite lesen ihre Inhalte aus
einer einzigen Datei: `assets/data/posts.json`. Ein neuer Post = ein neuer Eintrag in dieser Datei.

## Schritt 1: Fotos vorbereiten

1. Wähle 1–5 Fotos des Auftrags aus (quadratisch wirkt am besten).
2. Verkleinere jedes Foto auf ca. **1200 × 1200 Pixel** und unter **~400 KB**.
   Am einfachsten geht das gratis im Browser mit [squoosh.app](https://squoosh.app):
   Bild hineinziehen → rechts «Resize» auf 1200 setzen → als **JPG (MozJPEG)** speichern.
3. Lege im Projekt einen neuen Ordner an: `assets/img/posts/<post-id>/`
   — die `<post-id>` ist ein kurzer Name ohne Leerzeichen und Umlaute,
   z. B. `assets/img/posts/engitec-aschenbecher/`.
4. Speichere die Fotos dort, z. B. `bild-1.jpg`, `bild-2.jpg`.

## Schritt 2: Eintrag in posts.json einfügen

Öffne `assets/data/posts.json` in einem Texteditor (z. B. Editor/Notepad).
Kopiere den folgenden Block und füge ihn **zuoberst** in die Liste `"posts": [ … ]` ein
(der oberste Eintrag erscheint auf der Website zuerst). Achte darauf, dass nach dem
Block ein **Komma** steht, wenn darunter weitere Posts folgen.

```json
{
  "id": "kunde-projekt",
  "kunde": "Name des Kunden",
  "websiteUrl": null,
  "avatar": null,
  "projekt": "Kurze Projektbeschreibung (eine Zeile)",
  "caption": "Erster Absatz der Bildunterschrift.\nZweiter Absatz (\\n macht einen Zeilenumbruch).",
  "produktTags": [
    { "label": "Aschenbecher", "url": "aschenbecher.html" }
  ],
  "bilder": [
    { "src": "assets/img/posts/kunde-projekt/bild-1.jpg", "alt": "Beschreibung des Bilds für Sehbehinderte" },
    { "src": "assets/img/posts/kunde-projekt/bild-2.jpg", "alt": "Beschreibung des zweiten Bilds" }
  ]
}
```

Was die Felder bedeuten:

| Feld | Bedeutung |
|---|---|
| `id` | Kurzname des Posts, gleich wie der Bilderordner |
| `kunde` | Angezeigter Name (fett, wie ein Account-Name) |
| `websiteUrl` | Website des Kunden — nur eintragen, wenn der Kunde **schriftlich zugestimmt** hat, sonst `null` |
| `avatar` | Pfad zu einem kleinen Logo-Bild des Kunden, sonst `null` (dann werden Initialen gezeigt) |
| `projekt` | Kleine Zeile unter dem Namen |
| `caption` | Text unter den Bildern; `\n` erzeugt einen Zeilenumbruch |
| `produktTags` | Verlinkte Produkt-Chips; möglich: `aschenbecher.html`, `spiele.html` — oder leer lassen: `[]` |
| `bilder` | Liste der Fotos; `alt` ist Pflicht (kurze Bildbeschreibung) |

## Schritt 3: Lokal prüfen

1. Öffne im Projektordner ein Terminal (Windows: Rechtsklick → «Im Terminal öffnen»).
2. Starte: `python -m http.server 8000` (auf Mac/Linux: `python3 -m http.server 8000`)
3. Öffne im Browser: `http://localhost:8000/inspiration.html`
   — der neue Post muss zuoberst erscheinen, ohne Fehlermeldung.
   (Direktes Öffnen der HTML-Datei per Doppelklick funktioniert **nicht**, die Posts
   laden nur über einen lokalen Server.)

## Schritt 4: Veröffentlichen

Änderungen committen und pushen (z. B. via GitHub im Browser: Repository öffnen →
Datei → Stift-Symbol bzw. «Add file → Upload files» für die Fotos → «Commit changes»).
Netlify veröffentlicht danach automatisch; nach wenigen Minuten ist der Post online.

## Häufige Fehler

- **Komma vergessen/zu viel:** Nach jedem Post-Block in der Liste steht ein Komma — ausser nach dem letzten.
- **Anführungszeichen:** Immer gerade `"` verwenden, keine schönen „Anführungszeichen".
- **Bildpfad falsch:** Pfad in `src` muss exakt dem Dateinamen entsprechen (Gross-/Kleinschreibung zählt).
- Wenn gar nichts mehr lädt: Die JSON-Datei auf [jsonlint.com](https://jsonlint.com) einfügen — das Tool zeigt die fehlerhafte Stelle.
