/* ============================================================
   Druckts? — Konfigurator (Idea-to-Print, Phase 1)
   UI is built from the backend's template/material/printer specs.
   Live three.js preview of the generated STL, in the chosen colour.
   ============================================================ */
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const API = (window.DRUCKTS_API || "").replace(/\/$/, "");
const TEAM = new URLSearchParams(location.search).get("ansicht") === "team";

const el = (id) => document.getElementById(id);
const state = {
  templates: [], current: null, params: {},
  materials: [], printers: [],
  material: null, printer: null, color: null,
  config: null, lastResult: null, debounce: null,
};

const ICONS = { box: "📦", tray: "🍽️", coaster: "🥃", holder: "✏️", keychain: "🔑" };
const DEFAULT_HEX = "#a6d8d2";

/* ---------------------------------------------------------------- */
async function boot() {
  initViewer();
  if (TEAM) el("team-panel").hidden = false;
  try {
    const [cfg, tpls] = await Promise.all([
      fetch(`${API}/api/config`).then((r) => r.json()),
      fetch(`${API}/api/templates`).then((r) => r.json()),
    ]);
    state.config = cfg;
    state.materials = cfg.materials || [];
    state.printers = cfg.printers || [];
    state.templates = tpls.templates;
  } catch (err) {
    el("offline").hidden = false;
    setStatus("Dienst nicht erreichbar.");
    return;
  }
  state.printer = state.printers[0]?.id || "mk3s";
  state.material = state.materials[0]?.id || "pla_nx2";
  state.color = currentMaterial()?.colors?.[0]?.name || null;

  renderPrinters();
  renderMaterials();
  renderColors();
  rebuildPlate();
  renderTemplateChooser();
  selectTemplate(state.templates[0].id);
}

const currentMaterial = () => state.materials.find((m) => m.id === state.material);
const currentPrinter = () => state.printers.find((p) => p.id === state.printer);
const colorHex = (name) => {
  const m = currentMaterial();
  const c = m?.colors?.find((x) => x.name === name);
  return c ? c.hex : DEFAULT_HEX;
};

/* ---------------------------------------------------------------- */
/*  Templates                                                       */
/* ---------------------------------------------------------------- */
function renderTemplateChooser() {
  const grid = el("tpl-grid");
  grid.innerHTML = "";
  state.templates.forEach((t) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "tpl-card";
    b.setAttribute("aria-pressed", "false"); b.dataset.id = t.id;
    b.innerHTML =
      `<div class="tpl-card__icon">${ICONS[t.id] || "▢"}</div>` +
      `<div class="tpl-card__name">${t.name}</div>` +
      `<div class="tpl-card__tag">${t.tagline}</div>`;
    b.addEventListener("click", () => selectTemplate(t.id));
    grid.appendChild(b);
  });
}

function selectTemplate(id) {
  state.current = state.templates.find((t) => t.id === id);
  document.querySelectorAll(".tpl-card").forEach((c) =>
    c.setAttribute("aria-pressed", String(c.dataset.id === id)));
  state.params = {};
  state.current.params.forEach((p) => (state.params[p.key] = p.default));
  renderParams();
  generate();
}

/* ---------------------------------------------------------------- */
/*  Parameter controls                                              */
/* ---------------------------------------------------------------- */
function renderParams() {
  const wrap = el("params");
  wrap.innerHTML = "";
  state.current.params.forEach((p) => wrap.appendChild(buildControl(p)));
}

function buildControl(p) {
  const div = document.createElement("div");
  div.className = "ctrl";
  if (p.kind === "number") {
    const id = `p-${p.key}`;
    const unit = p.unit ? ` ${p.unit}` : "";
    div.innerHTML =
      `<label class="ctrl__label" for="${id}">${p.label}` +
      `<span class="ctrl__val" id="${id}-val">${p.default}${unit}</span></label>`;
    const input = document.createElement("input");
    input.type = "range"; input.id = id;
    input.min = p.min; input.max = p.max; input.step = p.step || 1; input.value = p.default;
    input.addEventListener("input", () => {
      const v = parseFloat(input.value);
      state.params[p.key] = v;
      el(`${id}-val`).textContent = `${v}${unit}`;
      scheduleGenerate();
    });
    div.appendChild(input);
    if (p.help) div.insertAdjacentHTML("beforeend", `<span class="ctrl__help">${p.help}</span>`);
  } else if (p.kind === "bool") {
    const lab = document.createElement("label");
    lab.className = "switch";
    lab.innerHTML =
      `<input type="checkbox" ${p.default ? "checked" : ""}>` +
      `<span class="switch__track"></span><span>${p.label}</span>`;
    lab.querySelector("input").addEventListener("change", (e) => {
      state.params[p.key] = e.target.checked; scheduleGenerate();
    });
    div.appendChild(lab);
    if (p.help) div.insertAdjacentHTML("beforeend", `<span class="ctrl__help">${p.help}</span>`);
  } else if (p.kind === "choice") {
    div.innerHTML = `<span class="ctrl__label">${p.label}</span>`;
    const seg = document.createElement("div");
    seg.className = "seg";
    p.options.forEach((o) => {
      const b = document.createElement("button");
      b.type = "button"; b.textContent = o.label;
      b.setAttribute("aria-pressed", String(o.value === p.default));
      b.addEventListener("click", () => {
        state.params[p.key] = o.value;
        seg.querySelectorAll("button").forEach((x) =>
          x.setAttribute("aria-pressed", String(x === b)));
        scheduleGenerate();
      });
      seg.appendChild(b);
    });
    div.appendChild(seg);
  } else if (p.kind === "text") {
    const id = `p-${p.key}`;
    div.innerHTML = `<label class="ctrl__label" for="${id}">${p.label}</label>`;
    const input = document.createElement("input");
    input.type = "text"; input.id = id; input.value = p.default || "";
    if (p.maxlength) input.maxLength = p.maxlength;
    input.addEventListener("input", () => { state.params[p.key] = input.value; scheduleGenerate(); });
    div.appendChild(input);
    if (p.help) div.insertAdjacentHTML("beforeend", `<span class="ctrl__help">${p.help}</span>`);
  }
  return div;
}

/* ---------------------------------------------------------------- */
/*  Material / colour / printer selectors                           */
/* ---------------------------------------------------------------- */
function renderMaterials() {
  const wrap = el("material");
  wrap.innerHTML = "";
  state.materials.forEach((m) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = m.name;
    b.setAttribute("aria-pressed", String(m.id === state.material));
    b.addEventListener("click", () => {
      state.material = m.id;
      wrap.querySelectorAll("button").forEach((x) =>
        x.setAttribute("aria-pressed", String(x === b)));
      // keep colour if the new material has it, else pick its first colour
      const names = (currentMaterial().colors || []).map((c) => c.name);
      if (!names.includes(state.color)) state.color = names[0] || null;
      renderColors();
      el("material-blurb").textContent = currentMaterial().blurb || "";
      applyColor();
      generate();
    });
    wrap.appendChild(b);
  });
  el("material-blurb").textContent = currentMaterial()?.blurb || "";
}

function renderColors() {
  const wrap = el("colors");
  wrap.innerHTML = "";
  (currentMaterial()?.colors || []).forEach((c) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "swatch";
    b.style.background = c.hex; b.title = c.name;
    b.setAttribute("aria-pressed", String(c.name === state.color));
    b.setAttribute("aria-label", c.name);
    b.addEventListener("click", () => {
      state.color = c.name;
      wrap.querySelectorAll(".swatch").forEach((x) =>
        x.setAttribute("aria-pressed", String(x === b)));
      applyColor();
      // colour is recorded in the spec — refresh result without a heavy rebuild feel
      scheduleGenerate();
    });
    wrap.appendChild(b);
  });
}

function renderPrinters() {
  const wrap = el("printer");
  wrap.innerHTML = "";
  state.printers.forEach((p) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = p.name;
    b.setAttribute("aria-pressed", String(p.id === state.printer));
    b.addEventListener("click", () => {
      state.printer = p.id;
      wrap.querySelectorAll("button").forEach((x) =>
        x.setAttribute("aria-pressed", String(x === b)));
      updatePrinterNote();
      rebuildPlate();
      generate();
    });
    wrap.appendChild(b);
  });
  updatePrinterNote();
}

function updatePrinterNote() {
  const p = currentPrinter();
  if (!p) return;
  const b = p.build_volume_mm;
  el("printer-note").textContent = `Bauraum ${b.x}×${b.y}×${b.z} mm`;
}

/* ---------------------------------------------------------------- */
/*  Generate                                                        */
/* ---------------------------------------------------------------- */
function scheduleGenerate() { clearTimeout(state.debounce); state.debounce = setTimeout(generate, 350); }

async function generate(opts = {}) {
  if (!state.current) return;
  setStatus(opts.precise ? "Slicer berechnet … (kann etwas dauern)" : "Wird erzeugt …");
  try {
    const res = await fetch(`${API}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        template: state.current.id, params: state.params,
        material: state.material, printer: state.printer,
        color: state.color, precise: !!opts.precise,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Fehler");
    }
    const data = await res.json();
    state.lastResult = data;
    showResult(data);
    await loadPreview(`${API}${data.preview_url}`);
    setStatus(null);
  } catch (err) {
    setStatus("Konnte das Modell nicht erzeugen.");
  }
}

/* ---------------------------------------------------------------- */
/*  Result panel                                                    */
/* ---------------------------------------------------------------- */
function showResult(d) {
  const s = d.spec;
  el("r-title").textContent = s.titel;
  el("r-sub").textContent = s.beschreibung;

  el("r-estimate").innerHTML =
    `<span class="badge">⏱️ <b>${s.druckzeit}</b></span>` +
    `<span class="badge">⚖️ <b>${d.estimate.mass_g} g</b></span>` +
    `<span class="badge">📏 <b>${d.estimate.length_m} m</b> Filament</span>`;

  el("r-specs").innerHTML =
    row("Was entsteht", s.teile.join(", ")) +
    row("Grösse", s.masse) +
    row("Material", `${s.material} · biologisch abbaubar`) +
    row("Farbe", s.farbe) +
    row("Drucker", s.drucker) +
    row("Ausrichtung", s.ausrichtung) +
    row("Schätzung", s.schaetzmethode);

  el("r-checks").innerHTML = d.validation.checks
    .map((c) => `<li><span class="dot dot--${c.status}"></span>` +
      `<span><span class="lbl">${c.label}:</span> <span class="dtl">${c.detail}</span></span></li>`)
    .join("");

  const notes = [...(d.spec.hinweise || [])];
  const notesEl = el("r-notes");
  if (notes.length) {
    notesEl.hidden = false;
    notesEl.innerHTML = `<b>Hinweise</b>` + notes.map((n) => `<p>${n}</p>`).join("");
  } else { notesEl.hidden = true; }

  if (TEAM && d.team && d.team.price) {
    const p = d.team.price;
    el("team-price").innerHTML =
      `<span class="badge">💰 Produktionskosten <b>CHF ${p.total_chf.toFixed(2)}</b></span>` +
      `<span class="badge">Material <b>CHF ${p.material_chf.toFixed(2)}</b></span>` +
      `<span class="badge">Energie <b>CHF ${p.energy_chf.toFixed(2)}</b></span>`;
    el("team-price-note").textContent = p.note;
  }

  el("dl-3mf").href = `${API}${d.downloads["3mf"]}`;
  el("dl-stl").href = `${API}${d.downloads.stl}`;
}

const row = (dt, dd) => `<div><dt>${dt}</dt><dd>${dd}</dd></div>`;

/* Precise = ask the backend to slice the real STL for exact numbers. */
el("precise").addEventListener("click", () => generate({ precise: true }));

/* ---------------------------------------------------------------- */
/*  Send to team (Phase 1: prefilled e-mail)                        */
/* ---------------------------------------------------------------- */
el("send-team").addEventListener("click", () => {
  const d = state.lastResult;
  if (!d) return;
  const subject = `Konfigurator-Anfrage: ${d.spec.titel}`;
  const body =
    `Hallo Druckts?-Team\n\nIch habe im Konfigurator folgendes Objekt entworfen:\n\n` +
    `${d.spec.klartext}\n\n` +
    `Bitte meldet euch mit einer Offerte. Die Druckdatei (3MF/STL) hänge ich an.\n\nDanke!`;
  window.location.href =
    `mailto:druckts@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});

/* ---------------------------------------------------------------- */
/*  three.js viewer                                                 */
/* ---------------------------------------------------------------- */
let renderer, scene, camera, controls, currentMesh, plate;

function setStatus(msg) {
  const s = el("viewer-status");
  if (msg) { s.hidden = false; s.textContent = msg; } else { s.hidden = true; }
}

function initViewer() {
  const host = el("viewer-canvas");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(40, 1, 1, 6000);
  camera.position.set(160, 150, 220);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  host.appendChild(renderer.domElement);
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 30, 0);
  controls.addEventListener("change", requestRender);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9bb6b0, 1.05));
  const key = new THREE.DirectionalLight(0xffffff, 1.4);
  key.position.set(120, 220, 160);
  scene.add(key);
  resize();
  window.addEventListener("resize", resize);
  requestRender();
}

function rebuildPlate() {
  if (plate) { scene.remove(plate); }
  const p = currentPrinter();
  const bx = p?.build_volume_mm?.x || 250;
  const by = p?.build_volume_mm?.y || 210;
  plate = new THREE.Group();
  const grid = new THREE.GridHelper(Math.max(bx, by), 14, 0x6fb9b1, 0xd8e6e3);
  plate.add(grid);
  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(bx, by)),
    new THREE.LineBasicMaterial({ color: 0x6fb9b1 }));
  edge.rotation.x = -Math.PI / 2;
  plate.add(edge);
  scene.add(plate);
  requestRender();
}

function resize() {
  const host = el("viewer-canvas");
  const w = host.clientWidth || 600, h = host.clientHeight || 450;
  renderer.setSize(w, h, false);
  camera.aspect = w / h; camera.updateProjectionMatrix();
  requestRender();
}

let _frameQueued = false;
function requestRender() { if (!_frameQueued) { _frameQueued = true; requestAnimationFrame(renderFrame); } }
function renderFrame() {
  _frameQueued = false;
  const moving = controls.update();
  renderer.render(scene, camera);
  if (moving) requestRender();
}

function applyColor() {
  if (currentMesh) { currentMesh.material.color.set(colorHex(state.color)); requestRender(); }
}

async function loadPreview(url) {
  const buf = await fetch(url).then((r) => r.arrayBuffer());
  const geom = new STLLoader().parse(buf);
  geom.rotateX(-Math.PI / 2);          // trimesh Z-up → three.js Y-up
  geom.computeVertexNormals();
  geom.computeBoundingBox();
  const bb = geom.boundingBox;
  geom.translate(-(bb.min.x + bb.max.x) / 2, -bb.min.y, -(bb.min.z + bb.max.z) / 2);

  if (currentMesh) {
    scene.remove(currentMesh);
    currentMesh.geometry.dispose();
    currentMesh.material.dispose();
  }
  const mat = new THREE.MeshStandardMaterial({
    color: colorHex(state.color), roughness: 0.55, metalness: 0.0,
  });
  currentMesh = new THREE.Mesh(geom, mat);
  scene.add(currentMesh);
  frameObject(geom);
}

function frameObject(geom) {
  geom.computeBoundingBox();
  const size = new THREE.Vector3();
  geom.boundingBox.getSize(size);
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim * 2.2 + 60;
  const cy = size.y / 2;
  controls.target.set(0, cy, 0);
  camera.position.set(dist * 0.7, cy + dist * 0.65, dist * 0.95);
  camera.updateProjectionMatrix();
  requestRender();
}

boot();
