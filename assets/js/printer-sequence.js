/* ============================================================
   Druckts? — sequential 3D-printer animation
   "Create your own product" motif: a clean line-art printer that
   rapidly prints object after object on a loop — house, tree,
   star and the poo emoji — then ejects each finished part.

   Drop-in & self-contained: it injects its own scoped <style> and
   an inline SVG into every [data-printer-sequence] element, and
   plays only when scrolled into view. Honours prefers-reduced-motion.
   Colours follow the existing brand theme vars when present:
     --pr-stroke   outline colour
     --pr-object   default object fill
     --pr-accent   nozzle / hot-layer / star
   plus optional overrides: --seq-leaf --seq-bark --seq-roof --seq-poo
   ============================================================ */
(function () {
  "use strict";

  var STYLE_ID = "seq-printer-styles";
  var uidCounter = 0;
  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canAnimate = typeof Element !== "undefined" &&
    typeof Element.prototype.animate === "function";

  /* ---- the objects that get printed, in cycle order ---- */
  var OBJECTS = [
    { name: "house", top: 106 },
    { name: "tree",  top: 114 },
    { name: "star",  top: 108 },
    { name: "poo",   top: 113 }   // the obligatory crowd-pleaser
  ];
  var POO_INDEX = 3;

  /* ---- scoped styles (injected once) ---- */
  var CSS = [
    ".seq-printer{width:100%;height:auto;overflow:visible;display:block}",
    ".seq-printer [stroke]{vector-effect:non-scaling-stroke}",
    ".seq-frame,.seq-rail,.seq-beam,.seq-bed{fill:none;stroke:var(--pr-stroke,#0E0E0E);",
      "stroke-width:3;stroke-linecap:round;stroke-linejoin:round}",
    ".seq-frame{stroke-width:3.4}.seq-bed{stroke-width:4.6}",
    ".seq-draw{stroke-dasharray:var(--len,1600);stroke-dashoffset:var(--len,1600)}",
    ".seq-printer.is-live .seq-draw{animation:seq-draw 1.5s cubic-bezier(.22,1,.36,1) forwards}",
    "@keyframes seq-draw{to{stroke-dashoffset:0}}",
    ".seq-head-x{animation:seq-osc .5s ease-in-out infinite alternate}",
    "@keyframes seq-osc{from{transform:translateX(-19px)}to{transform:translateX(19px)}}",
    ".seq-carriage{fill:var(--seq-surface,#fff);stroke:var(--pr-stroke,#0E0E0E);stroke-width:3}",
    ".seq-nozzle,.seq-glow{fill:var(--pr-accent,#FFC94D)}",
    ".seq-line{stroke:var(--pr-accent,#FFC94D);stroke-width:2.6;stroke-linecap:round}",
    ".seq-obj{transform-box:fill-box;transform-origin:center bottom;will-change:transform,opacity}",
    ".seq-obj path,.seq-obj rect,.seq-obj circle,.seq-obj ellipse{",
      "stroke:var(--pr-stroke,#0E0E0E);stroke-width:3;stroke-linejoin:round;stroke-linecap:round}",
    ".seq-obj .nofill{fill:none}",
    ".seq-sun{transform-box:fill-box;transform-origin:center}",
    ".seq-printer.is-live .seq-sun{animation:seq-spin 16s linear infinite}",
    "@keyframes seq-spin{to{transform:rotate(360deg)}}",
    "@media (prefers-reduced-motion: reduce){",
      ".seq-printer .seq-draw{stroke-dashoffset:0}",
      ".seq-printer.is-live .seq-head-x,.seq-printer.is-live .seq-sun{animation:none}}"
  ].join("");

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  }

  /* ---- object artwork (clean line-art) ---- */
  function houseSVG() {
    return '<g class="seq-obj" data-name="house" style="display:none">' +
      '<rect x="98" y="132" width="44" height="46" rx="2" fill="var(--pr-object,#A6D8D2)"/>' +
      '<path d="M92,134 L148,134 L120,106 Z" fill="var(--seq-roof,var(--pr-accent,#FFC94D))"/>' +
      '<rect x="111" y="152" width="16" height="26" rx="1.5" fill="var(--seq-surface,#fff)"/>' +
      '<rect x="103" y="141" width="11" height="11" rx="1.5" fill="var(--seq-surface,#fff)"/>' +
    '</g>';
  }
  function treeSVG() {
    return '<g class="seq-obj" data-name="tree" style="display:none">' +
      '<rect x="114" y="150" width="12" height="28" rx="2" fill="var(--seq-bark,#9A6B3F)"/>' +
      '<circle cx="104" cy="150" r="14" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<circle cx="136" cy="150" r="14" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<circle cx="120" cy="136" r="22" fill="var(--seq-leaf,#3FA66B)"/>' +
    '</g>';
  }
  function starSVG() {
    return '<g class="seq-obj" data-name="star" style="display:none">' +
      '<path d="M120,108 L128.8,131.9 L154.2,132.9 L134.3,148.6 L141.2,173.1 ' +
        'L120,159 L98.8,173.1 L105.7,148.6 L85.8,132.9 L111.2,131.9 Z" ' +
        'fill="var(--pr-accent,#FFC94D)"/>' +
    '</g>';
  }
  function pooSVG() {
    return '<g class="seq-obj" data-name="poo" style="display:none">' +
      // lumpy 3-tier silhouette
      '<path d="M90,178 C86,160 96,156 104,156 C98,150 100,140 110,140 ' +
        'C104,136 106,128 114,128 C110,124 112,116 120,113 ' +
        'C128,116 130,124 126,128 C134,128 136,136 130,140 ' +
        'C140,140 142,150 136,156 C144,156 154,160 150,178 Z" ' +
        'fill="var(--seq-poo,#8A5A2B)"/>' +
      // tier swirls
      '<path class="nofill" d="M104,156 Q120,150 136,156"/>' +
      '<path class="nofill" d="M110,140 Q120,135 130,140"/>' +
      // face
      '<ellipse cx="114" cy="126" rx="4.3" ry="5.3" fill="#fff" stroke="none"/>' +
      '<ellipse cx="126" cy="126" rx="4.3" ry="5.3" fill="#fff" stroke="none"/>' +
      '<circle cx="114.5" cy="127" r="2.1" fill="#1a1a1a" stroke="none"/>' +
      '<circle cx="126.5" cy="127" r="2.1" fill="#1a1a1a" stroke="none"/>' +
      '<path d="M113,132 Q120,138 127,132" fill="none" stroke="#1a1a1a" stroke-width="2.4"/>' +
    '</g>';
  }

  function svgMarkup(uid) {
    // wireframe cabinet (one path → clean draw-on)
    var FRAME =
      "M36,44 L204,44 L204,192 L36,192 Z " +     // front face
      "M36,44 L58,28 L226,28 L204,44 " +          // top face
      "M204,192 L226,176 L226,28";                // right depth
    return [
      '<svg class="seq-printer" viewBox="0 0 240 240" role="img" ',
        'aria-label="Animierter 3D-Drucker, der nacheinander verschiedene Objekte druckt" ',
        'xmlns="http://www.w3.org/2000/svg">',
        // cabinet + rails
        '<path class="seq-frame seq-draw" d="', FRAME, '"/>',
        '<path class="seq-rail seq-draw" d="M58,60 L58,176 M182,60 L182,176"/>',
        // printed objects (grow up from the bed, one at a time)
        '<g class="seq-stage">',
          houseSVG(), treeSVG(), starSVG(), pooSVG(),
        '</g>',
        // rising hot-layer line
        '<g class="seq-line-y"><line class="seq-line" x1="-26" y1="0" x2="26" y2="0"/></g>',
        // print head: outer group rises in Z, inner oscillates in X
        '<g class="seq-head-y">',
          '<line class="seq-beam" x1="-54" y1="-22" x2="54" y2="-22"/>',
          '<g class="seq-head-x">',
            '<rect class="seq-carriage" x="-15" y="-32" width="30" height="16" rx="3"/>',
            '<path class="seq-nozzle" d="M-8,-16 L8,-16 L0,0 Z"/>',
            '<circle class="seq-glow" cx="0" cy="3" r="2.6"/>',
          '</g>',
        '</g>',
        // print bed
        '<path class="seq-bed seq-draw" d="M44,180 L196,180"/>',
        // little sun — "Sonnenschein in sich"
        '<g transform="translate(206,52)"><g class="seq-sun">',
          '<circle r="7" fill="var(--pr-accent,#FFC94D)"/>',
          '<g stroke="var(--pr-accent,#FFC94D)" stroke-width="2.4" stroke-linecap="round">',
            '<path d="M0,-13 L0,-10"/><path d="M0,10 L0,13"/><path d="M-13,0 L-10,0"/>',
            '<path d="M10,0 L13,0"/><path d="M-9,-9 L-7,-7"/><path d="M7,7 L9,9"/>',
            '<path d="M9,-9 L7,-7"/><path d="M-7,7 L-9,9"/>',
          '</g>',
        '</g></g>',
      '</svg>'
    ].join("");
  }

  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function measureDraw(svg) {
    svg.querySelectorAll(".seq-draw").forEach(function (p) {
      try {
        var len = p.getTotalLength();
        p.style.strokeDasharray = len;
        p.style.strokeDashoffset = len;
        p.style.setProperty("--len", len);
      } catch (e) { /* ignore */ }
    });
  }

  var BED_Y = 180;

  function setHead(ctx, y) {
    ctx.headY.style.transform = "translate(120px," + y + "px)";
    ctx.lineY.style.transform = "translate(120px," + y + "px)";
  }

  function showStatic(ctx, idx) {
    ctx.objEls.forEach(function (g, i) {
      g.style.display = (i === idx) ? "inline" : "none";
      g.style.transform = (i === idx) ? "scaleY(1)" : "scaleY(0)";
      g.style.opacity = 1;
    });
    setHead(ctx, OBJECTS[idx].top);
    ctx.lineY.style.opacity = 0;
  }

  function runCycle(ctx) {
    if (!ctx.running) return;
    var idx = ctx.idx;
    var meta = OBJECTS[idx];
    var g = ctx.objEls[idx];

    // present current object, reset stage
    ctx.objEls.forEach(function (el, i) {
      el.style.display = (i === idx) ? "inline" : "none";
      el.style.opacity = 1;
      el.style.transform = "scaleY(0)";
    });
    ctx.lineY.style.opacity = 1;
    setHead(ctx, BED_Y);
    void ctx.svg.getBoundingClientRect(); // reflow

    var D = 1250; // print duration per object
    var lin = "linear";
    var growA = g.animate(
      [{ transform: "scaleY(0)" }, { transform: "scaleY(1)" }],
      { duration: D, easing: lin, fill: "forwards" });
    ctx.headY.animate(
      [{ transform: "translate(120px," + BED_Y + "px)" },
       { transform: "translate(120px," + meta.top + "px)" }],
      { duration: D, easing: lin, fill: "forwards" });
    ctx.lineY.animate(
      [{ transform: "translate(120px," + BED_Y + "px)" },
       { transform: "translate(120px," + meta.top + "px)" }],
      { duration: D, easing: lin, fill: "forwards" });

    growA.finished.then(function () {
      ctx.lineY.animate([{ opacity: 1 }, { opacity: 0 }],
        { duration: 180, fill: "forwards" });
      return wait(320); // hold the finished part
    }).then(function () {
      var ej = g.animate(
        [{ opacity: 1, transform: "scaleY(1)" },
         { opacity: 0, transform: "translateY(-7px) scale(1.07)" }],
        { duration: 360, easing: "cubic-bezier(.4,0,.6,1)", fill: "forwards" });
      return ej.finished;
    }).then(function () {
      ctx.idx = (idx + 1) % OBJECTS.length;
      runCycle(ctx);
    }).catch(function () { /* animation cancelled */ });
  }

  function build(el) {
    var uid = ++uidCounter;
    el.innerHTML = svgMarkup(uid);
    var svg = el.querySelector(".seq-printer");
    var ctx = {
      svg: svg,
      headY: svg.querySelector(".seq-head-y"),
      lineY: svg.querySelector(".seq-line-y"),
      objEls: Array.prototype.slice.call(svg.querySelectorAll(".seq-obj")),
      idx: 0,
      running: false
    };

    measureDraw(svg);

    if (reduce || !canAnimate) {
      svg.classList.add("is-live");
      showStatic(ctx, POO_INDEX); // a friendly static frame
      return;
    }

    function start() {
      svg.classList.add("is-live");
      if (!ctx.running) { ctx.running = true; runCycle(ctx); }
    }
    function stop() { ctx.running = false; }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) start(); else stop();
        });
      }, { threshold: 0.25 });
      io.observe(svg);
    } else {
      start();
    }
  }

  function init() {
    injectStyles();
    document.querySelectorAll("[data-printer-sequence]").forEach(build);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }

  // expose for manual init if injected after load
  window.DrucktsPrinterSequence = { init: init };
})();
