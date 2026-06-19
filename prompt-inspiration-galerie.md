# Prompt für den Code-Chat — Referenz-Galerie «Inspiration»

> Diesen gesamten Text in den Code-Chat kopieren (Chat muss Zugriff auf den Ordner «Druckts Website» haben).

---

Baue für die Druckts-Website eine Referenz-Galerie «Inspiration» im Stil von Social-Media-Posts: Bilder vergangener Aufträge, gruppiert pro Auftrag als «Post» mit Bild-Karussell, Kundenname und Caption. Zweck: zeigen, wie bestehende und individuelle Produkte im Einsatz aussehen, und Kunden (z. B. Firmen) Sichtbarkeit für ihren nachhaltigen Einkauf geben.

## Kontext zur Codebase (zuerst lesen: `aschenbecher.html` und `assets/css/v1.css`)

- Statische Website des Vereins «Druckts?» (nachhaltiger 3D-Druck, Winterthur), Sprache de-CH, deployt auf Netlify **ohne Build-Schritt**. Vanilla HTML/CSS/JS, keine Frameworks, keine externen Libraries.
- Live-Design ist V1 «Eco Clean»: `index.html`, `aschenbecher.html`, `spiele.html`, `impressum.html`, `datenschutz.html` nutzen `assets/css/base.css` + `assets/css/v1.css` und `<body class="v1">`.
- Konventionen: BEM-artige Klassen (`block__element--modifier`), Design-Tokens als CSS-Variablen (`:root` in base.css, `.v1` in v1.css), Scroll-Reveals via Klasse `.reveal` + `assets/js/reveal.js`, Karten mit `border-radius: 22px`, `border: 1px solid var(--line)` und Hover-Lift, Buttons `.btn .btn--solid` / `.btn--ghost`, Sektionsköpfe mit `.eyebrow` + `.section-title` + `.section-intro`.
- Header/Footer sind auf jeder Seite identisch kopiertes Markup (kein Include-System).
- Der Ordner `versions/` enthält alte Design-Entwürfe — **nicht anfassen**.
- Lokale Vorschau: `python3 -m http.server 8000` im Projektordner. Wichtig, weil die neue Galerie `fetch()` nutzt und das unter `file://` nicht funktioniert.

## 1. Datenhaltung: JSON + Bilderordner

Posts werden NICHT hartcodiert, sondern aus einer JSON-Datei gerendert, damit der Verein neue Posts ohne HTML-Kenntnisse ergänzen kann.

- `assets/data/posts.json` — Reihenfolge im Array = Anzeigereihenfolge (neuester Post zuoberst).
- Bilder echter Posts liegen künftig unter `assets/img/posts/<post-id>/`.
- `assets/js/posts.js` (vanilla JS, `defer`, gleicher Stil wie `reveal.js`): lädt die JSON und rendert Posts in jedes Element mit `[data-posts]`. Optionales Attribut `data-limit="2"` begrenzt die Anzahl (für den Teaser).
- Sicherheit: Alle Texte aus der JSON über `textContent` / `createElement` einfügen, **kein** `innerHTML` mit JSON-Inhalten. Zeilenumbrüche (`\n`) in Captions als `<br>` umsetzen.
- Fehler-/Leerzustand: Wenn die JSON fehlt oder leer ist, auf `index.html` die ganze Teaser-Sektion ausblenden (`console.warn`), auf `inspiration.html` eine freundliche Meldung zeigen (inkl. Hinweis, dass die Seite über einen lokalen Server geöffnet werden muss, falls `fetch` scheitert).

Schema (deutsche Schlüssel, damit Nicht-Techniker sie verstehen):

```json
{
  "posts": [
    {
      "id": "engitec-aschenbecher",
      "kunde": "Engitec",
      "websiteUrl": null,
      "avatar": null,
      "projekt": "Aschenbecher für Baustellen-Teams",
      "caption": "Engitec stattet ihre Teams auf der Baustelle mit unseren Taschenaschenbechern aus – gedruckt aus PLA, mit Solarstrom in Winterthur.\nAsche bleibt drin, Baustelle bleibt sauber.",
      "produktTags": [
        { "label": "Aschenbecher", "url": "aschenbecher.html" }
      ],
      "bilder": [
        { "src": "assets/img/adventurer-1.jpg", "alt": "Frisch gedruckter Taschenaschenbecher «Adventurer»" },
        { "src": "assets/img/set-itinerants.jpg", "alt": "Die Itinerants-Aschenbecher im Grössenvergleich" }
      ]
    }
  ]
}
```

`websiteUrl` und `avatar` sind optional (null erlaubt). `produktTags` kann leer sein.

## 2. Die Post-Komponente (Social-Post-Look, eigenständig im Eco-Clean-Stil)

Karte im bestehenden Kartenstil (Radius 22px, `var(--surface)`, `var(--line)`), aufgebaut wie ein Social-Media-Post:

- **Kopfzeile:** runder Avatar (Bild aus `avatar`, sonst Initialen-Fallback im Stil von `.member__avatar` mit Mint-Gradient) + Kundenname fett. Wenn `websiteUrl` gesetzt: Name als Link mit `target="_blank" rel="noopener noreferrer"` und dezentem Extern-Indikator (z. B. ↗). Darunter klein die Projektzeile (`projekt`), gestylt wie `.eyebrow`, aber unaufdringlicher.
- **Bild-Karussell:** quadratisch (`aspect-ratio: 1`, `object-fit: cover`), umgesetzt mit CSS scroll-snap (kein Library-Code). Pfeil-Buttons vor/zurück, Punkte-Indikator, Zähler «1/4». Bei nur einem Bild: keine Controls. Touch-Swipe ergibt sich durch scroll-snap automatisch. Tastatur: Buttons fokussierbar, deutsche `aria-label`s («Vorheriges Bild», «Nächstes Bild»). `prefers-reduced-motion`: kein smooth scrolling.
- **Bilder:** `loading="lazy"` (nur das erste Bild des ersten Posts eager), `width`/`height`-Attribute gegen Layout-Shift, `alt` aus der JSON (Pflichtfeld).
- **Caption** unter dem Karussell, danach die **Produkt-Tags** als Chips im Stil von `.product__tag`, verlinkt auf die jeweilige Seite.
- Bewusst **keine** Fake-Likes, -Kommentare oder -Share-Icons und kein Instagram-/Meta-Branding (keine kopierten Icons). Der Look «Social Post» entsteht durch Aufbau und Proportionen, nicht durch Imitation.

## 3. Neue Seite `inspiration.html`

- Aufbau (head, Header, Footer, Schriften, Meta) exakt nach dem Muster von `aschenbecher.html`, inkl. eigenem `<title>` und `meta description`.
- Seitenkopf mit `.page-head`: eyebrow «Referenzen · Echte Aufträge», Titel z. B. «Gedruckt & im Einsatz.», kurzes Intro (Inspiration für bestehende und individuelle Produkte).
- Feed: zentrierte Einspalten-Kolonne, `max-width` ca. 560px — wie ein echter Feed.
- Abschluss-Sektion analog `.models-cta`: «Auch eine Idee im Kopf?» mit Button zu `index.html#kontakt`.

## 4. Teaser auf `index.html`

- Neue Sektion `id="inspiration"` **zwischen** `#produkte` und `#team`, mit Sektionskopf (eyebrow «Inspiration»).
- Zeigt die 2 neuesten Posts nebeneinander (mobile 1 Spalte, Breakpoint 900px wie die übrigen Grids) via `<div data-posts data-limit="2">`.
- Darunter zentrierter Button «Alle Referenzen ansehen» → `inspiration.html`.

## 5. Navigation

Auf **allen fünf Seiten** (`index.html`, `aschenbecher.html`, `spiele.html`, `impressum.html`, `datenschutz.html`) in Header-Nav UND Footer-Nav den Link «Inspiration» → `inspiration.html` ergänzen, jeweils zwischen «Produkte» und «Team». Auf `inspiration.html` selbst dieselbe Nav wie auf den anderen Unterseiten.

## 6. Beispiel-Inhalte (3 Posts)

1. **Engitec (real):** Caption wie im Schema oben, Produkt-Tag «Aschenbecher» → `aschenbecher.html`. Als Bilder vorerst bestehende Aschenbecher-Bilder referenzieren (echte Fotos folgen). `websiteUrl: null` lassen — wird ergänzt, sobald Engitec schriftlich zugestimmt hat.
2. + 3. **Zwei Platzhalter-Posts** mit vorhandenen Bildern (z. B. `schach-*.jpg`, `kartenbox-*.jpg`), Captions klar als Beispiel markiert («Beispiel-Post — durch echten Auftrag ersetzen»), damit Layout mit mehreren Posts sichtbar ist.

## 7. CSS

Neue Styles als kommentierter Block («Inspiration / Posts») ans Ende von `assets/css/v1.css`, ausschliesslich mit bestehenden Tokens (`--surface`, `--line`, `--accent`, `--muted`, …). Reveal-Animationen über die bestehende `.reveal`-Klasse (von `posts.js` beim Rendern setzen und sicherstellen, dass die IntersectionObserver-Logik auch dynamisch eingefügte Elemente erfasst — nötigenfalls kleine eigene Observer-Logik in `posts.js`, da `reveal.js` nur beim Laden scannt).

## 8. Netlify-Cache (wichtig, sonst erscheinen neue Posts verspätet)

`netlify.toml` cached `/assets/*` 7 Tage. Eigene Regel für die Posts-Daten ergänzen:

```toml
[[headers]]
  for = "/assets/data/*"
  [headers.values]
    Cache-Control = "public, max-age=300, must-revalidate"
```

Nach dem nächsten Deploy mit `curl -I` prüfen, dass für `posts.json` die kurze Cache-Zeit greift.

## 9. Anleitung für den Verein

Datei `ANLEITUNG-POSTS.md` im Projekt-Root erstellen: Schritt-für-Schritt «Neuen Post hinzufügen» für Nicht-Techniker — Ordner `assets/img/posts/<post-id>/` anlegen, Fotos als JPG ca. 1200×1200 px und unter ~400 KB exportieren (z. B. mit squoosh.app), JSON-Eintrag zuoberst einfügen (kommentiertes Beispiel zeigen), lokal mit `python3 -m http.server 8000` prüfen, committen/deployen. Im README unter «Noch offen / Feinschliff» verlinken.

## Definition of Done — alles selbst prüfen

- Lokal via `python3 -m http.server 8000`: Startseite und `/inspiration.html` rendern alle 3 Posts aus der JSON, keine Konsolenfehler.
- Karussell: Pfeile, Punkte, Zähler und Swipe funktionieren; bei einem einzelnen Bild keine Controls; per Tastatur bedienbar.
- Teaser zeigt genau die 2 neuesten Posts, CTA führt zur Galerie-Seite.
- Header- und Footer-Nav auf allen 6 Seiten (inkl. neuer Seite) konsistent.
- Mobile (375px) und Desktop geprüft; `prefers-reduced-motion` respektiert.
- Alle Bilder mit `alt`, `width`/`height` und korrektem `loading`-Attribut.
- Kein externes Script, keine Library, kein Build-Schritt; `versions/` unverändert.
- `netlify.toml`-Regel ergänzt; `ANLEITUNG-POSTS.md` vorhanden und im README verlinkt.
- Texte aus JSON werden XSS-sicher eingefügt.

## Nicht tun

- Keine Frameworks, Libraries oder CDN-Einbindungen; kein Build-Schritt einführen.
- Kein Instagram-/Meta-Logo oder kopierte Icons, keine erfundenen Engagement-Zahlen.
- Keine bestehenden Sektionen umbauen — nur die beschriebenen Ergänzungen (Nav, Teaser-Sektion, neue Dateien).
