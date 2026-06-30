/* ============================================================
   Druckts? — Inspiration / Referenz-Posts
   Lädt assets/data/posts.json und rendert Social-Post-Karten in
   jedes Element mit [data-posts]. Optional:
     data-limit="2"            nur die N neuesten Posts zeigen
     data-fallback="hide"      bei Fehler/leer: ganze Sektion ausblenden
     data-fallback="message"   bei Fehler/leer: freundliche Meldung zeigen
   Lightweight, dependency-free, reduced-motion aware. Alle Texte
   aus der JSON werden via textContent eingefügt (kein innerHTML).
   ============================================================ */
(function () {
  "use strict";

  var DATA_URL = "assets/data/posts.json";
  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function el(tag, className, text) {
    var n = document.createElement(tag);
    if (className) n.className = className;
    if (text != null) n.textContent = text;
    return n;
  }

  function initials(name) {
    var parts = String(name).trim().split(/\s+/);
    var out = parts[0] ? parts[0].charAt(0) : "";
    if (parts.length > 1) out += parts[parts.length - 1].charAt(0);
    return out.toUpperCase();
  }

  /* ---- Kopfzeile: Avatar + Kundenname (+ Link) + Projektzeile ---- */
  function buildHead(post) {
    var head = el("header", "post__head");

    if (post.avatar) {
      var img = el("img", "post__avatar");
      img.src = post.avatar;
      img.alt = "";
      img.width = 44; img.height = 44;
      img.loading = "lazy";
      head.appendChild(img);
    } else {
      var av = el("span", "post__avatar", initials(post.kunde));
      av.setAttribute("aria-hidden", "true");
      head.appendChild(av);
    }

    var meta = el("div", "post__meta");
    var name;
    if (post.websiteUrl) {
      name = el("a", "post__name", post.kunde);
      name.href = post.websiteUrl;
      name.target = "_blank";
      name.rel = "noopener noreferrer";
      var ext = el("span", "post__ext", " ↗");
      ext.setAttribute("aria-hidden", "true");
      name.appendChild(ext);
      name.appendChild(el("span", "sr-only", " (externe Website)"));
    } else {
      name = el("span", "post__name", post.kunde);
    }
    meta.appendChild(name);
    if (post.projekt) meta.appendChild(el("p", "post__project", post.projekt));
    head.appendChild(meta);
    return head;
  }

  /* ---- Bild-Karussell mit scroll-snap, Pfeilen, Punkten, Zähler ---- */
  function buildMedia(post, eagerFirst) {
    var media = el("div", "post__media");
    var track = el("div", "post__track");
    track.setAttribute("role", "group");
    track.setAttribute("aria-label", "Bilder zum Auftrag von " + post.kunde);

    post.bilder.forEach(function (bild, i) {
      var img = el("img", "post__img");
      img.src = bild.src;
      img.alt = bild.alt || "";
      img.width = 900; img.height = 900;
      img.loading = (eagerFirst && i === 0) ? "eager" : "lazy";
      track.appendChild(img);
    });
    media.appendChild(track);

    if (post.bilder.length > 1) {
      var n = post.bilder.length;
      var prev = el("button", "post__nav post__nav--prev", "‹");
      prev.type = "button";
      prev.setAttribute("aria-label", "Vorheriges Bild");
      var next = el("button", "post__nav post__nav--next", "›");
      next.type = "button";
      next.setAttribute("aria-label", "Nächstes Bild");

      var dots = el("div", "post__dots");
      dots.setAttribute("aria-hidden", "true");
      for (var d = 0; d < n; d++) dots.appendChild(el("i", d === 0 ? "is-active" : ""));

      var count = el("span", "post__count", "1/" + n);

      function current() {
        var w = track.clientWidth;
        if (!w) return 0; /* noch nicht im Layout (z. B. beim Aufbau) */
        return Math.max(0, Math.min(n - 1, Math.round(track.scrollLeft / w)));
      }
      function update() {
        var idx = current();
        count.textContent = (idx + 1) + "/" + n;
        Array.prototype.forEach.call(dots.children, function (dot, i) {
          dot.classList.toggle("is-active", i === idx);
        });
        prev.disabled = idx === 0;
        next.disabled = idx === n - 1;
      }
      function go(dir) {
        track.scrollBy({
          left: dir * track.clientWidth,
          behavior: reduce ? "auto" : "smooth"
        });
      }
      prev.addEventListener("click", function () { go(-1); });
      next.addEventListener("click", function () { go(1); });

      var ticking = false;
      track.addEventListener("scroll", function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () { update(); ticking = false; });
      }, { passive: true });

      update();
      media.appendChild(prev);
      media.appendChild(next);
      media.appendChild(dots);
      media.appendChild(count);
    }
    return media;
  }

  /* ---- Caption (\n -> <br>) + Produkt-Tag-Chips ---- */
  function buildBody(post) {
    var body = el("div", "post__body");

    var caption = el("p", "post__caption");
    String(post.caption || "").split("\n").forEach(function (line, i) {
      if (i > 0) caption.appendChild(document.createElement("br"));
      caption.appendChild(document.createTextNode(line));
    });
    body.appendChild(caption);

    if (post.produktTags && post.produktTags.length) {
      var tags = el("div", "post__tags");
      post.produktTags.forEach(function (tag) {
        var a = el("a", "product__tag", tag.label);
        a.href = tag.url;
        tags.appendChild(a);
      });
      body.appendChild(tags);
    }
    return body;
  }

  function buildPost(post, eagerFirst) {
    var article = el("article", "post reveal");
    if (post.id) article.id = "post-" + post.id;
    article.appendChild(buildHead(post));
    article.appendChild(buildMedia(post, eagerFirst));
    article.appendChild(buildBody(post));
    return article;
  }

  /* ---- Reveal für dynamisch eingefügte Karten (reveal.js scannt nur
         beim Laden, darum hier ein eigener kleiner Observer) ---- */
  function revealDynamic(els) {
    if (reduce || !("IntersectionObserver" in window)) {
      els.forEach(function (e) { e.classList.add("is-visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.18, rootMargin: "0px 0px -8% 0px" });
    els.forEach(function (e) { io.observe(e); });
  }

  function render(container, posts) {
    var limit = parseInt(container.getAttribute("data-limit"), 10);
    var list = (limit > 0) ? posts.slice(0, limit) : posts;
    var made = [];
    list.forEach(function (post, i) {
      var card = buildPost(post, i === 0);
      container.appendChild(card);
      made.push(card);
    });
    revealDynamic(made);
  }

  /* ---- Fehler-/Leerzustand ---- */
  function fail(containers, reason, fetchFailed) {
    console.warn("Druckts Posts:", reason);
    containers.forEach(function (c) {
      if (c.getAttribute("data-fallback") === "message") {
        var box = el("div", "feed-status");
        box.appendChild(el("p", null,
          "Hier zeigen wir bald Bilder echter Aufträge. Schau später wieder vorbei!"));
        if (fetchFailed) {
          box.appendChild(el("p", "feed-status__hint",
            "Hinweis für die Vorschau: Diese Seite muss über einen lokalen Server " +
            "geöffnet werden (z. B. «python -m http.server 8000» im Projektordner), " +
            "nicht direkt als Datei."));
        }
        c.appendChild(box);
      } else {
        var section = c.closest("section");
        if (section) section.hidden = true;
      }
    });
  }

  function init() {
    var containers = Array.prototype.slice.call(
      document.querySelectorAll("[data-posts]"));
    if (!containers.length) return;

    fetch(DATA_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status + " für " + DATA_URL);
        return r.json();
      })
      .then(function (data) {
        var posts = data && data.posts;
        if (!posts || !posts.length) {
          fail(containers, "posts.json ist leer", false);
          return;
        }
        containers.forEach(function (c) { render(c, posts); });
        scrollToHash();
      })
      .catch(function (err) { fail(containers, err, true); });
  }

  /* ---- Sprung zu einem per #post-<id> verlinkten Post (z. B. aus den
         Produktseiten "Im Einsatz sehen") + kurzes Hervorheben ---- */
  function scrollToHash() {
    if (!/^#post-/.test(location.hash || "")) return;
    var target = document.getElementById(location.hash.slice(1));
    if (!target) return;
    setTimeout(function () {
      target.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
      target.classList.add("is-target");
      setTimeout(function () { target.classList.remove("is-target"); }, 2400);
    }, 120);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
