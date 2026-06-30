/* ============================================================
   Druckts? — Produkt ↔ Inspiration-Verknüpfung
   Auf den Produktseiten (aschenbecher.html, spiele.html): liest
   assets/data/posts.json und fügt in jeden Produkt-Detaildialog einen
   Link "Dieses Modell im Einsatz sehen" ein, sofern es in der
   Inspirations-Galerie einen Post gibt, dessen "produkte"-Liste die
   Modell-ID enthält (Modell-ID = Dialog-ID ohne das "m-").
   Ohne passende Posts (oder ohne posts.json) passiert nichts.
   ============================================================ */
(function () {
  "use strict";

  var DATA_URL = "assets/data/posts.json";

  function modelIdOf(dialogId) { return dialogId.replace(/^m-/, ""); }

  function init() {
    var dialogs = Array.prototype.slice.call(
      document.querySelectorAll("dialog.model-modal[id]"));
    if (!dialogs.length) return;

    fetch(DATA_URL)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        var posts = data && data.posts;
        if (!posts || !posts.length) return;

        dialogs.forEach(function (d) {
          var model = modelIdOf(d.id);
          var matches = posts.filter(function (p) {
            return Array.isArray(p.produkte) && p.produkte.indexOf(model) !== -1;
          });
          if (!matches.length) return;

          var info = d.querySelector(".model-modal__info");
          if (!info) return;

          var link = document.createElement("a");
          link.className = "model-modal__inspo";
          link.href = "inspiration.html#post-" + matches[0].id;
          link.textContent = (matches.length > 1)
            ? "📸 Dieses Modell im Einsatz sehen (" + matches.length + ")"
            : "📸 Dieses Modell im Einsatz sehen";

          var btn = info.querySelector(".btn");
          if (btn) { info.insertBefore(link, btn); }
          else { info.appendChild(link); }
        });
      })
      .catch(function () { /* offline / keine Daten: nichts tun */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
