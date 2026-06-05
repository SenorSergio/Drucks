/* ============================================================
   Druckts? — animated 3D-printer brand motif
   Injects an inline SVG into every [data-printer] element and
   plays the draw-on / print-head / layer-build animation when
   it scrolls into view. Honours prefers-reduced-motion.
   ============================================================ */
(function () {
  "use strict";

  // Wireframe enclosure (single path → clean draw-on)
  var FRAME =
    "M48,60 L158,60 L158,170 L48,170 Z " +   // front face
    "M48,60 L74,38 L184,38 L158,60 " +        // top face
    "M158,170 L184,148 L184,38";              // right depth

  var SVG = [
    '<svg class="printer" viewBox="0 0 220 220" role="img" aria-label="Animierter 3D-Drucker, der ein Objekt Schicht für Schicht aufbaut" xmlns="http://www.w3.org/2000/svg">',
      // enclosure
      '<path class="pr-frame pr-draw" d="' + FRAME + '"/>',
      // vertical rails
      '<path class="pr-rail pr-draw" d="M64,60 L64,170 M142,60 L142,170"/>',
      // X gantry
      '<path class="pr-gantry pr-draw" d="M58,92 L150,92"/>',
      // printed object — bottom layer first
      '<g class="pr-object">',
        '<rect class="pr-layer" x="83" y="148" width="42" height="9" rx="1.5"/>',
        '<rect class="pr-layer" x="83" y="139" width="42" height="9" rx="1.5"/>',
        '<rect class="pr-layer" x="86" y="130" width="36" height="9" rx="1.5"/>',
        '<rect class="pr-layer" x="86" y="121" width="36" height="9" rx="1.5"/>',
        '<rect class="pr-layer" x="90" y="112" width="28" height="9" rx="1.5"/>',
        '<rect class="pr-layer" x="94" y="103" width="20" height="9" rx="1.5"/>',
      '</g>',
      // print head + nozzle
      '<g class="pr-head">',
        '<rect x="92" y="84" width="24" height="15" rx="3" fill="none" stroke="var(--pr-stroke, #0E0E0E)" stroke-width="3"/>',
        '<path class="pr-nozzle" d="M99,99 L117,99 L108,114 Z"/>',
      '</g>',
      // base / print bed
      '<path class="pr-bed pr-draw" d="M56,170 L150,170"/>',
      // little sun — "Sonnenschein in sich"
      // outer <g> positions, inner <g.pr-sun> rotates (CSS transform must not
      // clobber the position, so the two transforms live on separate elements)
      '<g transform="translate(176,54)">',
        '<g class="pr-sun">',
          '<circle r="7" fill="var(--pr-accent, #FFC94D)"/>',
          '<g stroke="var(--pr-accent, #FFC94D)" stroke-width="2.4" stroke-linecap="round">',
            '<path d="M0,-13 L0,-10"/><path d="M0,10 L0,13"/>',
            '<path d="M-13,0 L-10,0"/><path d="M10,0 L13,0"/>',
            '<path d="M-9,-9 L-7,-7"/><path d="M7,7 L9,9"/>',
            '<path d="M9,-9 L7,-7"/><path d="M-7,7 L-9,9"/>',
          '</g>',
        '</g>',
      '</g>',
    '</svg>'
  ].join("");

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function build(el) {
    el.innerHTML = SVG;
    var svg = el.querySelector(".printer");

    // measure each drawable path so the draw-on is pixel-perfect
    svg.querySelectorAll(".pr-draw").forEach(function (p) {
      try {
        var len = p.getTotalLength();
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.setProperty("--len", len);
      } catch (e) { /* getTotalLength unsupported — ignore */ }
    });

    if (reduce) { svg.classList.add("is-live"); return; }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-live");
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.35 });
      io.observe(svg);
    } else {
      svg.classList.add("is-live");
    }
  }

  function init() {
    document.querySelectorAll("[data-printer]").forEach(build);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
