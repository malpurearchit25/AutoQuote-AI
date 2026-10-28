"use strict";
(() => {
  const $ = (id) => document.getElementById(id);
  const form = $("assessmentForm"), make = $("carMake"), model = $("carModel");
  const image = $("previewImg"), canvas = $("overlayCanvas"), button = $("analyseButton");
  const state = { file: null, url: null, result: null, vehicles: {}, busy: false,
    controller: null, version: 0, mode: "model", imageReady: false, serviceReady: false };
  const money = (n) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
  const text = (tag, value, className) => { const el = document.createElement(tag); el.textContent = value; if (className) el.className = className; return el; };

  function message(value = "") { $("errorMessage").textContent = value; $("errorMessage").hidden = !value; }
  function updateButton() { button.disabled = state.busy || !state.serviceReady || !state.imageReady || !state.file || !make.value || !model.value; }
  function clearResults() {
    state.result = null;
    $("results").hidden = true; $("emptyState").hidden = false;
    $("resultTag").textContent = "AWAITING PHOTO";
    $("resultSubtitle").textContent = "The details, in one place.";
    canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
  }
  function invalidate() {
    state.version++;
    if (state.controller) state.controller.abort();
    state.controller = null; state.busy = false;
    $("resultCard").setAttribute("aria-busy", "false");
    button.textContent = state.mode === "demo" ? "Show sample assessment ↗" : "Analyse image ↗";
    clearResults(); message(); updateButton();
  }
  function removeFile() {
    invalidate();
    state.file = null; state.imageReady = false;
    if (state.url) URL.revokeObjectURL(state.url);
    state.url = null; image.removeAttribute("src"); $("fileInput").value = "";
    $("previewWrap").hidden = true; $("fileDetails").hidden = true; $("dropZone").hidden = false;
    $("formStatus").textContent = "Choose a vehicle and add an image to get started.";
    updateButton();
  }
  function chooseFile(file) {
    if (!file) return;
    removeFile();
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) return message("Choose a JPEG, PNG or WebP image.");
    if (file.size > 10 * 1024 * 1024) return message("This image exceeds 10 MB. Choose a smaller image.");
    if (!file.size) return message("This file is empty. Choose another image.");
    state.file = file; state.url = URL.createObjectURL(file);
    const version = state.version;
    image.onload = () => {
      if (version !== state.version) return;
      if (image.naturalWidth * image.naturalHeight > 20_000_000) { removeFile(); return message("Choose an image smaller than 20 megapixels."); }
      state.imageReady = true; $("previewWrap").hidden = false; drawBoxes(); updateButton();
    };
    image.onerror = () => { if (version === state.version) { removeFile(); message("This image could not be opened. Choose another file."); } };
    image.src = state.url;
    $("fileName").textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    $("fileDetails").hidden = false; $("dropZone").hidden = true;
    $("formStatus").textContent = "Image selected. Choose your vehicle, then start the assessment.";
  }
  function drawBoxes() {
    const width = image.clientWidth, height = image.clientHeight;
    if (!width || !height) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio);
    if (!state.result) return;
    const scaleX = width / state.result.image.width, scaleY = height / state.result.image.height;
    state.result.detections.forEach((detection, index) => {
      const [x1, y1, x2, y2] = detection.bbox;
      ctx.strokeStyle = "#ff651c"; ctx.lineWidth = 2;
      ctx.strokeRect(x1 * scaleX, y1 * scaleY, (x2 - x1) * scaleX, (y2 - y1) * scaleY);
      ctx.fillStyle = "#080808"; ctx.fillRect(x1 * scaleX, Math.max(0, y1 * scaleY - 22), 27, 22);
      ctx.fillStyle = "#ffffff"; ctx.font = "bold 12px sans-serif";
      ctx.fillText(String(index + 1), x1 * scaleX + 8, Math.max(16, y1 * scaleY - 6));
    });
  }
  function renderResult(result) {
    state.result = result;
    $("emptyState").hidden = true; $("results").hidden = false;
    $("resultTag").textContent = result.mode === "demo" ? "DEMO EXAMPLE" : "ASSESSMENT READY";
    $("resultSubtitle").textContent = result.mode === "demo" ? "Illustrative sample results, not image analysis." : "Review the findings with your workshop.";
    $("estimateLabel").textContent = result.mode === "demo" ? "Sample estimate · demo" : result.unpriced_count ? "Subtotal of priced items" : "Illustrative repair estimate";
    $("totalCost").textContent = result.detections.length ? money(result.total_cost) : "Not available";
    $("vehicleSummary").textContent = `${result.car_info.make} ${result.car_info.model}`;
    $("unpricedNotice").hidden = !result.unpriced_count;
    $("unpricedNotice").textContent = `${result.unpriced_count} damage type(s) need a workshop quote and are excluded from this subtotal.`;
    $("noDamageNotice").hidden = result.detections.length !== 0;
    $("detectionCount").textContent = `${result.detections.length} detection(s)`;
    $("costItems").replaceChildren();
    result.items.forEach((item) => {
      const row = text("div", "", "cost-item"), details = document.createElement("div");
      details.append(text("strong", item.label), text("small", `${item.price_basis} · ${item.detection_count} region(s), grouped once`));
      row.append(details, text("strong", item.estimated_cost === null ? "Needs inspection" : money(item.estimated_cost), "item-price"));
      $("costItems").append(row);
    });
    $("confidenceList").replaceChildren(...result.detections.map((d, i) => text("li", `${i + 1}. ${d.class_name.replaceAll("_", " ")} — ${(d.confidence * 100).toFixed(0)}% confidence`)));
    $("reportNotes").hidden = !result.description;
    $("reportNotesText").textContent = result.description;
    $("estimateDisclaimer").textContent = result.disclaimer;
    $("formStatus").textContent = result.mode === "demo" ? "Sample assessment ready. Demo results do not describe your image." : "Assessment ready. Review the findings on your photo.";
    drawBoxes();
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (button.disabled || !form.reportValidity()) return;
    invalidate(); state.busy = true; updateButton();
    $("resultCard").setAttribute("aria-busy", "true");
    button.textContent = "Analysing…"; $("formStatus").textContent = "Processing your image. The first analysis may take longer while the model loads.";
    const version = state.version, controller = new AbortController(); state.controller = controller;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 120000);
    const data = new FormData(form); data.set("file", state.file);
    try {
      const response = await fetch("/predict", { method: "POST", body: data, signal: controller.signal });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "Check the vehicle details and try again.");
      if (version === state.version) renderResult(result);
    } catch (error) {
      if (version === state.version) {
        message(timedOut ? "Analysis timed out. The server may still be processing; wait a moment and retry." : error.name === "AbortError" ? "Analysis cancelled." : error.message || "Could not reach the server.");
        $("formStatus").textContent = "Assessment incomplete. Your image is ready to retry.";
      }
    } finally {
      clearTimeout(timeout);
      if (version === state.version) {
        state.busy = false; state.controller = null; updateButton();
        $("resultCard").setAttribute("aria-busy", "false");
        button.textContent = state.mode === "demo" ? "Show sample assessment ↗" : "Analyse image ↗";
      }
    }
  });

  $("fileInput").addEventListener("change", (event) => chooseFile(event.target.files[0]));
  $("dropZone").addEventListener("click", () => $("fileInput").click());
  for (const type of ["dragenter", "dragover"]) $("dropZone").addEventListener(type, (event) => { event.preventDefault(); $("dropZone").classList.add("dragging"); });
  for (const type of ["dragleave", "drop"]) $("dropZone").addEventListener(type, (event) => { event.preventDefault(); $("dropZone").classList.remove("dragging"); });
  $("dropZone").addEventListener("drop", (event) => chooseFile(event.dataTransfer.files[0]));
  $("removeFile").addEventListener("click", removeFile);
  make.addEventListener("change", () => {
    invalidate(); model.replaceChildren(new Option("Select model", ""));
    for (const name of state.vehicles[make.value] || []) model.add(new Option(name, name));
    model.disabled = !make.value; updateButton();
  });
  model.addEventListener("change", invalidate);
  $("damageDescription").addEventListener("input", invalidate);
  new ResizeObserver(drawBoxes).observe(image);
  $("downloadReport").addEventListener("click", () => {
    if (!state.result) return;
    const r = state.result;
    const lines = ["AUTOQUOTE AI — ASSESSMENT REPORT", `Generated: ${new Date().toISOString()}`,
      r.mode === "demo" ? "DEMO: FIXED SAMPLE RESULTS. NOT AN ANALYSIS OF YOUR IMAGE." : "Model-generated assessment",
      `Vehicle: ${r.car_info.make} ${r.car_info.model}`, "", ...r.items.map((i) => `${i.label}: ${i.estimated_cost === null ? "Needs inspection" : `INR ${i.estimated_cost}`} (${i.price_basis}; ${i.detection_count} regions grouped once)`),
      "", r.detections.length ? `Priced subtotal: INR ${r.total_cost}` : "No supported damage detected; no estimate available.",
      `Unpriced damage types: ${r.unpriced_count}`, "", `Notes: ${r.description || "None"}`, "", r.disclaimer];
    const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "autoquote-assessment.txt";
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  async function initialize() {
    try {
      const responses = await Promise.all([fetch("/api/health"), fetch("/api/vehicles")]);
      if (responses.some((response) => !response.ok)) throw new Error("Service unavailable. Refresh to try again.");
      const [health, vehicles] = await Promise.all(responses.map((response) => response.json()));
      state.mode = health.mode; state.vehicles = vehicles;
      state.serviceReady = health.model_status !== "missing";
      $("demoNotice").hidden = health.mode !== "demo";
      $("setupNotice").hidden = health.model_status !== "missing";
      $("serviceStatus").textContent = health.mode === "demo" ? "Demo mode" : health.model_status === "missing" ? "Model setup needed" : "Model available";
      make.replaceChildren(new Option("Select manufacturer", ""));
      for (const name of Object.keys(vehicles)) make.add(new Option(name, name));
      make.disabled = false; invalidate();
    } catch (error) { $("serviceStatus").textContent = "Service offline"; message(error.message); }
  }
  initialize();
})();
