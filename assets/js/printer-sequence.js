/* ============================================================
   Druckts? — sequential 3D-printer animation (V1 · Eco Clean)
   "Create your own product" motif: a clean line-art gantry
   printer that prints object after object on a loop — seedling,
   gear, tree and the poo emoji — layer by layer (bottom-up
   reveal), then ejects each finished part. The sun sits in the
   background sky and feeds the printer via a dotted energy
   line: we print with solar power.

   Drop-in & self-contained: it injects its own scoped <style>
   and an inline SVG into every [data-printer-sequence] element,
   and plays only when scrolled into view. Honours
   prefers-reduced-motion. Colours follow the brand theme vars:
     --pr-stroke   outline colour
     --pr-object   default object fill (mint)
     --pr-accent   nozzle / hot-layer / sun (solar yellow)
   plus optional overrides: --seq-leaf --seq-bark --seq-poo
   --seq-surface
   ============================================================ */
(function () {
  "use strict";

  var STYLE_ID = "seq-printer-styles";
  var uidCounter = 0;
  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canAnimate = typeof Element !== "undefined" &&
    typeof Element.prototype.animate === "function";

  /* ---- the objects that get printed, in cycle order ----
     top = y-coordinate of the object's highest point, so the
     nozzle finishes exactly at the top of the part. */
  var OBJECTS = [
    { name: "sprout", top: 114 },
    { name: "gear",   top: 114 },
    { name: "tree",   top: 116 },
    { name: "poo",    top: 116 }   // the obligatory crowd-pleaser
  ];
  var STATIC_INDEX = 0;            // shown when motion is reduced
  var BED_Y = 182;                 // top surface of the print bed

  /* ---- scoped styles (injected once) ---- */
  var CSS = [
    ".seq-printer{width:100%;height:auto;overflow:visible;display:block}",
    ".seq-printer [stroke]{vector-effect:non-scaling-stroke}",
    /* static frame: white-filled line art */
    ".seq-frame{fill:var(--seq-surface,#fff);stroke:var(--pr-stroke,#16201d);",
      "stroke-width:3;stroke-linejoin:round;stroke-linecap:round}",
    ".seq-detail{fill:none;stroke:var(--pr-stroke,#16201d);stroke-width:2.4;",
      "stroke-linecap:round;stroke-linejoin:round}",
    /* draw-on intro */
    ".seq-draw{stroke-dasharray:var(--len,600);stroke-dashoffset:var(--len,600);fill-opacity:0}",
    ".seq-printer.is-live .seq-draw{animation:seq-drawline 1.1s cubic-bezier(.4,0,.2,1) forwards,",
      "seq-fillin .45s ease .6s forwards}",
    "@keyframes seq-drawline{to{stroke-dashoffset:0}}",
    "@keyframes seq-fillin{to{fill-opacity:1}}",
    /* moving gantry + tool head */
    ".seq-head-y{opacity:0}",
    ".seq-printer.is-live .seq-head-y{animation:seq-fadein .5s ease .85s forwards}",
    "@keyframes seq-fadein{to{opacity:1}}",
    ".seq-beam,.seq-slider,.seq-carriage{fill:var(--seq-surface,#fff);",
      "stroke:var(--pr-stroke,#16201d);stroke-width:3}",
    ".seq-head-x{animation:seq-osc .55s ease-in-out infinite alternate}",
    "@keyframes seq-osc{from{transform:translateX(-34px)}to{transform:translateX(34px)}}",
    ".seq-printer.seq-idle .seq-head-x{animation-play-state:paused}",
    ".seq-nozzle{fill:var(--pr-accent,#FFC94D);stroke:var(--pr-stroke,#16201d);",
      "stroke-width:2.4;stroke-linejoin:round}",
    ".seq-glow{fill:var(--pr-accent,#FFC94D);animation:seq-pulse .5s ease-in-out infinite alternate}",
    ".seq-printer.seq-idle .seq-glow{animation-play-state:paused;opacity:.3}",
    "@keyframes seq-pulse{from{opacity:.35}to{opacity:1}}",
    /* hot layer line */
    ".seq-line{stroke:var(--pr-accent,#FFC94D);stroke-width:2.6;stroke-linecap:round}",
    /* printed objects */
    ".seq-obj{will-change:clip-path,transform,opacity}",
    ".seq-obj path,.seq-obj rect,.seq-obj circle,.seq-obj ellipse{",
      "stroke:var(--pr-stroke,#16201d);stroke-width:3;stroke-linejoin:round;stroke-linecap:round}",
    ".seq-obj .nofill{fill:none}",
    /* background sun = solar power */
    ".seq-sun{transform-box:fill-box;transform-origin:center}",
    ".seq-printer.is-live .seq-sun{animation:seq-spin 24s linear infinite}",
    "@keyframes seq-spin{to{transform:rotate(360deg)}}",
    ".seq-energy{fill:none;stroke:var(--pr-accent,#FFC94D);stroke-width:2.4;",
      "stroke-linecap:round;stroke-dasharray:.1 7}",
    ".seq-printer.is-live .seq-energy{animation:seq-flow .9s linear infinite}",
    "@keyframes seq-flow{to{stroke-dashoffset:-7.1}}",
    /* reduced motion: show everything, move nothing */
    "@media (prefers-reduced-motion: reduce){",
      ".seq-printer .seq-draw{stroke-dashoffset:0;fill-opacity:1;animation:none}",
      ".seq-printer .seq-head-y{opacity:1;animation:none}",
      ".seq-printer.is-live .seq-head-x,.seq-printer.is-live .seq-sun,",
      ".seq-printer.is-live .seq-energy,.seq-printer.is-live .seq-glow{animation:none}}"
  ].join("");

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  }

  /* ---- gear silhouette (computed, so the teeth are exact) ---- */
  function gearPath(cx, cy, rTip, rRoot, teeth, phase) {
    var pitch = Math.PI * 2 / teeth;
    var tipHalf = 0.115, rootHalf = 0.24;
    function pt(r, a) {
      return (cx + r * Math.cos(a)).toFixed(1) + "," +
             (cy + r * Math.sin(a)).toFixed(1);
    }
    var d = "";
    for (var k = 0; k < teeth; k++) {
      var a = phase + k * pitch;
      d += (k ? "L" : "M") + pt(rRoot, a - rootHalf) +
           " L" + pt(rTip, a - tipHalf) +
           " L" + pt(rTip, a + tipHalf) +
           " L" + pt(rRoot, a + rootHalf) + " ";
    }
    return d + "Z";
  }

  /* ---- object artwork (line art, all parts stand on y=182) ----
     Each object carries a translucent stripe overlay (tex) that
     mimics 3D-print layer lines. */
  function sproutSVG(tex) {
    var leaf1 = "M120,140 C111,139 104,133 103,124 C112,124 119,130 120,138 Z";
    var leaf2 = "M120,131 C129,130 136,124 137,115 C128,115 121,121 120,129 Z";
    var pot   = "M104,159 L136,159 L131,182 L109,182 Z";
    return '<g class="seq-obj" data-name="sprout" style="display:none">' +
      '<path class="nofill" d="M120,152 C120,144 119,136 120,127"/>' +
      '<path d="' + leaf1 + '" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<path d="' + leaf2 + '" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<path d="' + leaf1 + '" fill="' + tex + '" style="stroke:none"/>' +
      '<path d="' + leaf2 + '" fill="' + tex + '" style="stroke:none"/>' +
      '<path d="' + pot + '" fill="var(--pr-object,#A6D8D2)"/>' +
      '<path d="' + pot + '" fill="' + tex + '" style="stroke:none"/>' +
      '<rect x="100" y="152" width="40" height="7" rx="2.5" fill="var(--pr-object,#A6D8D2)"/>' +
    '</g>';
  }
  function gearSVG(tex) {
    var d = gearPath(120, 148, 34, 27, 9, Math.PI / 2);
    return '<g class="seq-obj" data-name="gear" style="display:none">' +
      '<path d="' + d + '" fill="var(--pr-object,#A6D8D2)"/>' +
      '<path d="' + d + '" fill="' + tex + '" style="stroke:none"/>' +
      '<circle cx="120" cy="148" r="8.5" fill="var(--seq-surface,#fff)"/>' +
    '</g>';
  }
  function treeSVG(tex) {
    return '<g class="seq-obj" data-name="tree" style="display:none">' +
      '<rect x="114" y="152" width="12" height="30" rx="2" fill="var(--seq-bark,#9A6B3F)"/>' +
      '<circle cx="104" cy="152" r="13" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<circle cx="136" cy="152" r="13" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<circle cx="120" cy="137" r="20" fill="var(--seq-leaf,#3FA66B)"/>' +
      '<circle cx="104" cy="152" r="13" fill="' + tex + '" style="stroke:none"/>' +
      '<circle cx="136" cy="152" r="13" fill="' + tex + '" style="stroke:none"/>' +
      '<circle cx="120" cy="137" r="20" fill="' + tex + '" style="stroke:none"/>' +
    '</g>';
  }
  function pooSVG(tex) {
    var body = "M90,182 C86,164 96,160 104,160 C98,154 100,144 110,144 " +
      "C104,140 106,132 114,132 C110,128 112,120 120,117 " +
      "C128,120 130,128 126,132 C134,132 136,140 130,144 " +
      "C140,144 142,154 136,160 C144,160 154,164 150,182 Z";
    return '<g class="seq-obj" data-name="poo" style="display:none">' +
      '<path d="' + body + '" fill="var(--seq-poo,#8A5A2B)"/>' +
      '<path d="' + body + '" fill="' + tex + '" style="stroke:none"/>' +
      '<path class="nofill" d="M104,160 Q120,154 136,160"/>' +
      '<path class="nofill" d="M110,144 Q120,139 130,144"/>' +
      '<ellipse cx="114" cy="130" rx="4.3" ry="5.3" fill="#fff" style="stroke:none"/>' +
      '<ellipse cx="126" cy="130" rx="4.3" ry="5.3" fill="#fff" style="stroke:none"/>' +
      '<circle cx="114.5" cy="131" r="2.1" fill="#1a1a1a" style="stroke:none"/>' +
      '<circle cx="126.5" cy="131" r="2.1" fill="#1a1a1a" style="stroke:none"/>' +
      '<path d="M113,136 Q120,142 127,136" style="fill:none;stroke:#1a1a1a;stroke-width:2.4"/>' +
    '</g>';
  }

  function svgMarkup(uid) {
    var texId = "seq-tex-" + uid;
    var tex = "url(#" + texId + ")";
    return [
      '<svg class="seq-printer" viewBox="0 0 240 240" role="img" ',
        'aria-label="Animierter 3D-Drucker, der mit Solarenergie nacheinander ',
        'verschiedene Objekte druckt" xmlns="http://www.w3.org/2000/svg">',
        /* layer-line texture for printed parts */
        '<defs><pattern id="', texId, '" patternUnits="userSpaceOnUse" width="8" height="5">',
          '<rect x="0" y="3.1" width="8" height="1.7" fill="var(--pr-stroke,#16201d)" opacity=".12"/>',
        '</pattern></defs>',
        /* background sun, set off from the printer */
        '<g transform="translate(23,21)"><g class="seq-sun">',
          '<circle r="7.5" fill="var(--pr-accent,#FFC94D)"/>',
          '<g stroke="var(--pr-accent,#FFC94D)" stroke-width="2.4" stroke-linecap="round">',
            '<path d="M0,-15 L0,-11"/><path d="M0,11 L0,15"/>',
            '<path d="M-15,0 L-11,0"/><path d="M11,0 L15,0"/>',
            '<path d="M-10.6,-10.6 L-7.8,-7.8"/><path d="M7.8,7.8 L10.6,10.6"/>',
            '<path d="M10.6,-10.6 L7.8,-7.8"/><path d="M-7.8,7.8 L-10.6,10.6"/>',
          '</g>',
        '</g></g>',
        /* gantry frame: columns, top bar, base, print bed */
        '<rect class="seq-frame seq-draw" x="52"  y="40" width="10" height="152" rx="4"/>',
        '<rect class="seq-frame seq-draw" x="178" y="40" width="10" height="152" rx="4"/>',
        '<rect class="seq-frame seq-draw" x="46"  y="32" width="148" height="14" rx="7"/>',
        '<rect class="seq-frame seq-draw" x="44"  y="192" width="152" height="26" rx="8"/>',
        '<rect class="seq-frame seq-draw" x="58"  y="183" width="124" height="9" rx="2.5"/>',
        '<rect class="seq-detail seq-draw" x="152" y="200" width="24" height="10" rx="3"/>',
        '<circle class="seq-detail seq-draw" cx="142" cy="205" r="4"/>',
        /* dotted solar-energy feed: sun powers the printer */
        '<path class="seq-energy" d="M34,35 Q45,39 56,39"/>',
        /* printed objects (revealed bottom-up, one at a time) */
        '<g class="seq-stage">',
          sproutSVG(tex), gearSVG(tex), treeSVG(tex), pooSVG(tex),
        '</g>',
        /* rising hot-layer line */
        '<g class="seq-line-y"><line class="seq-line" x1="-30" y1="0" x2="30" y2="0"/></g>',
        /* tool head: outer group rises in Z, inner oscillates in X;
           nozzle tip sits at local y=0 */
        '<g class="seq-head-y">',
          '<rect class="seq-beam" x="-58" y="-31" width="116" height="9" rx="4.5"/>',
          '<rect class="seq-slider" x="-69" y="-34" width="14" height="15" rx="3"/>',
          '<rect class="seq-slider" x="55"  y="-34" width="14" height="15" rx="3"/>',
          '<g class="seq-head-x">',
            '<rect class="seq-carriage" x="-14" y="-38" width="28" height="18" rx="4"/>',
            '<path class="seq-nozzle" d="M-8,-20 L8,-20 L4,-9 L-4,-9 Z"/>',
            '<path class="seq-nozzle" d="M-4,-9 L4,-9 L0,-1 Z"/>',
            '<circle class="seq-glow" cx="0" cy="1.5" r="2.8"/>',
          '</g>',
        '</g>',
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

  function setHead(ctx, y) {
    ctx.headY.style.transform = "translate(120px," + y + "px)";
    ctx.lineY.style.transform = "translate(120px," + y + "px)";
  }

  var CLIP_HIDDEN = "inset(100% 0% 0% 0%)";
  var CLIP_SHOWN  = "inset(0% 0% 0% 0%)";

  function showStatic(ctx, idx) {
    ctx.objEls.forEach(function (g, i) {
      g.style.display = (i === idx) ? "inline" : "none";
      g.style.clipPath = "none";
      g.style.opacity = 1;
      g.style.transform = "none";
    });
    setHead(ctx, OBJECTS[idx].top);
    ctx.lineY.style.opacity = 0;
  }

  function cancelLive(ctx) {
    // forwards-filling animations override inline styles until
    // cancelled, so clear out the previous cycle's animations
    ctx.live.forEach(function (a) { try { a.cancel(); } catch (e) { /* */ } });
    ctx.live = [];
  }

  function runCycle(ctx, token) {
    if (!ctx.running || token !== ctx.token) return;
    var idx = ctx.idx;
    var meta = OBJECTS[idx];
    var g = ctx.objEls[idx];

    // present current object, reset stage; head starts on the bed
    cancelLive(ctx);
    ctx.svg.classList.remove("seq-idle");
    ctx.objEls.forEach(function (el, i) {
      el.style.display = (i === idx) ? "inline" : "none";
      el.style.opacity = 1;
      el.style.transform = "none";
      el.style.clipPath = CLIP_HIDDEN;
    });
    ctx.lineY.style.opacity = 1;
    setHead(ctx, BED_Y);
    void ctx.svg.getBoundingClientRect(); // reflow

    var D = 1500; // print duration per object — steady, like a real print
    var lin = "linear";
    var growA = g.animate(
      [{ clipPath: CLIP_HIDDEN }, { clipPath: CLIP_SHOWN }],
      { duration: D, easing: lin, fill: "forwards" });
    ctx.live.push(growA);
    ctx.live.push(ctx.headY.animate(
      [{ transform: "translate(120px," + BED_Y + "px)" },
       { transform: "translate(120px," + meta.top + "px)" }],
      { duration: D, easing: lin, fill: "forwards" }));
    ctx.live.push(ctx.lineY.animate(
      [{ transform: "translate(120px," + BED_Y + "px)" },
       { transform: "translate(120px," + meta.top + "px)" }],
      { duration: D, easing: lin, fill: "forwards" }));

    growA.finished.then(function () {
      if (!ctx.running || token !== ctx.token) return Promise.reject();
      ctx.svg.classList.add("seq-idle"); // motors stop while we admire the part
      ctx.live.push(ctx.lineY.animate([{ opacity: 1 }, { opacity: 0 }],
        { duration: 180, fill: "forwards" }));
      return wait(420); // hold the finished part
    }).then(function () {
      if (!ctx.running || token !== ctx.token) return Promise.reject();
      var ej = g.animate(
        [{ opacity: 1, transform: "translateY(0px)" },
         { opacity: 0, transform: "translateY(-12px)" }],
        { duration: 380, easing: "cubic-bezier(.4,0,.7,1)", fill: "forwards" });
      ctx.live.push(ej);
      return ej.finished;
    }).then(function () {
      ctx.idx = (idx + 1) % OBJECTS.length;
      runCycle(ctx, token);
    }).catch(function () { /* animation cancelled / loop stopped */ });
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
      token: 0,
      live: [],
      running: false,
      startedOnce: false
    };

    measureDraw(svg);
    setHead(ctx, BED_Y);
    ctx.lineY.style.opacity = 0;

    if (reduce || !canAnimate) {
      svg.classList.add("is-live");
      showStatic(ctx, STATIC_INDEX); // a friendly static frame
      return;
    }

    function start() {
      svg.classList.add("is-live");
      if (ctx.running) return;
      ctx.running = true;
      var token = ++ctx.token;
      var delay = ctx.startedOnce ? 0 : 900; // let the frame draw on first
      ctx.startedOnce = true;
      wait(delay).then(function () { runCycle(ctx, token); });
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
