const APP_STORAGE_KEY = "ckd-dual-mode-settings";
const CALIBRATION_CAVEAT = "Probability estimates reflect model-level calibration (Brier = 0.021) and should be interpreted as decision support, not clinical diagnosis.";
const EMPTY_ATTRIBUTION_MESSAGE = "Feature-level attribution requires a live endpoint with SHAP export enabled.";

const MODES = {
  clinical: {
    label: "Clinical Intake Mode",
    routeLabel: "/predict/clinical",
    title: "Clinical intake form",
    intro: "Use clinically familiar variables for a product-facing workflow. This mode assumes the backend accepts native clinical inputs or performs intake-to-model translation.",
    sectionOrder: ["clinical_core", "clinical_labs", "clinical_history"]
  },
  research: {
    label: "Research Inference Mode",
    routeLabel: "/predict/research",
    title: "Research inference form",
    intro: "Use the schema-aligned feature space from the current #336 modeling line. This mode is the most direct path for connecting the existing prediction workflow.",
    sectionOrder: ["research_screening", "research_findings", "research_labs", "research_history"]
  }
};

const SECTIONS = {
  clinical_core: {
    title: "Core demographics and intake",
    fields: [
      { key: "age", label: "Age", type: "number", min: 18, max: 95, step: "1", placeholder: "e.g. 55" },
      { key: "sex", label: "Sex", type: "select", options: ["male", "female"] },
      { key: "sbp", label: "Systolic blood pressure", type: "number", min: 70, max: 240, step: "1", placeholder: "e.g. 130" },
      { key: "dbp", label: "Diastolic blood pressure", type: "number", min: 40, max: 140, step: "1", placeholder: "e.g. 80" },
      { key: "bmi", label: "BMI", type: "number", min: 10, max: 60, step: "0.1", placeholder: "e.g. 24.5" }
    ]
  },
  clinical_labs: {
    title: "Clinical laboratory profile",
    fields: [
      { key: "egfr", label: "eGFR", type: "number", min: 1, max: 140, step: "0.1", placeholder: "e.g. 65" },
      { key: "uacr", label: "UACR", type: "number", min: 0, max: 5000, step: "0.1", placeholder: "e.g. 30" },
      { key: "hba1c", label: "HbA1c", type: "number", min: 3, max: 20, step: "0.1", placeholder: "e.g. 7.2" },
      { key: "scr", label: "Serum creatinine", type: "number", min: 0.1, max: 20, step: "0.1", placeholder: "e.g. 1.2" },
      { key: "potassium", label: "Potassium", type: "number", min: 1.5, max: 8, step: "0.1", placeholder: "e.g. 4.2" }
    ]
  },
  clinical_history: {
    title: "Clinical history and comorbidity",
    fields: [
      { key: "dm", label: "Diabetes mellitus", type: "select", options: ["no", "yes"] },
      { key: "htn", label: "Hypertension", type: "select", options: ["no", "yes"] },
      { key: "cvd", label: "Cardiovascular disease", type: "select", options: ["no", "yes"] },
      { key: "proteinuria_flag", label: "Proteinuria history", type: "select", options: ["no", "yes"] }
    ]
  },
  research_screening: {
    title: "Demographics and urine screening",
    fields: [
      { key: "age", label: "Age", type: "number", min: 2, max: 90, step: "1", placeholder: "e.g. 55" },
      { key: "sg", label: "Specific gravity", type: "select", options: ["1.005", "1.01", "1.015", "1.02", "1.025"] },
      { key: "al", label: "Albumin", type: "select", options: ["0", "1", "2", "3", "4", "5"] },
      { key: "su", label: "Sugar", type: "select", options: ["0", "1", "2", "3", "4", "5"] }
    ]
  },
  research_findings: {
    title: "Urinalysis and clinical findings",
    fields: [
      { key: "rbc", label: "Red blood cells", type: "select", options: ["normal", "abnormal"] },
      { key: "pc", label: "Pus cell", type: "select", options: ["normal", "abnormal"] },
      { key: "pcc", label: "Pus cell clumps", type: "select", options: ["notpresent", "present"] },
      { key: "ba", label: "Bacteria", type: "select", options: ["notpresent", "present"] },
      { key: "appet", label: "Appetite", type: "select", options: ["good", "poor"] },
      { key: "pe", label: "Pedal edema", type: "select", options: ["no", "yes"] },
      { key: "ane", label: "Anemia", type: "select", options: ["no", "yes"] }
    ]
  },
  research_labs: {
    title: "Blood chemistry and hematology",
    fields: [
      { key: "bgr", label: "Blood glucose random", type: "number", min: 22, max: 490, step: "0.1", placeholder: "e.g. 148" },
      { key: "bu", label: "Blood urea", type: "number", min: 1.5, max: 391, step: "0.1", placeholder: "e.g. 44" },
      { key: "sc", label: "Serum creatinine", type: "number", min: 0.4, max: 76, step: "0.1", placeholder: "e.g. 1.6" },
      { key: "sod", label: "Sodium", type: "number", min: 4.5, max: 163, step: "0.1", placeholder: "e.g. 137" },
      { key: "pot", label: "Potassium", type: "number", min: 2.5, max: 47, step: "0.1", placeholder: "e.g. 4.5" },
      { key: "hemo", label: "Hemoglobin", type: "number", min: 3.1, max: 17.8, step: "0.1", placeholder: "e.g. 12.4" },
      { key: "pcv", label: "Packed cell volume", type: "number", min: 9, max: 54, step: "1", placeholder: "e.g. 38" },
      { key: "wbcc", label: "White blood cell count", type: "number", min: 2200, max: 26400, step: "1", placeholder: "e.g. 7800" },
      { key: "rbcc", label: "Red blood cell count", type: "number", min: 2.1, max: 8, step: "0.1", placeholder: "e.g. 4.5" }
    ]
  },
  research_history: {
    title: "Comorbidities and context",
    fields: [
      { key: "htn", label: "Hypertension", type: "select", options: ["no", "yes"] },
      { key: "dm", label: "Diabetes mellitus", type: "select", options: ["no", "yes"] },
      { key: "cad", label: "Coronary artery disease", type: "select", options: ["no", "yes"] }
    ]
  }
};

const EXAMPLES = {
  clinical: [
    {
      name: "high-risk clinical example",
      caseId: "CKD-CLIN-HIGH",
      patientName: "王OO",
      clinicalNote: "High-risk intake simulation",
      values: {
        age: "72", sex: "male", sbp: "168", dbp: "96", bmi: "31.4", egfr: "28", uacr: "950", hba1c: "9.4", scr: "2.8", potassium: "5.4", dm: "yes", htn: "yes", cvd: "yes", proteinuria_flag: "yes"
      }
    },
    {
      name: "lower-risk clinical example",
      caseId: "CKD-CLIN-LOW",
      patientName: "林OO",
      clinicalNote: "Lower-risk intake simulation",
      values: {
        age: "38", sex: "female", sbp: "112", dbp: "72", bmi: "22.1", egfr: "95", uacr: "5", hba1c: "5.2", scr: "0.8", potassium: "4.1", dm: "no", htn: "no", cvd: "no", proteinuria_flag: "no"
      }
    }
  ],
  research: [
    {
      name: "high-risk research example",
      caseId: "CKD-RES-HIGH",
      patientName: "陳OO",
      clinicalNote: "High-risk research simulation",
      values: {
        age: "66", sg: "1.01", al: "4", su: "2", rbc: "abnormal", pc: "abnormal", pcc: "present", ba: "present", appet: "poor", pe: "yes", ane: "yes", bgr: "242", bu: "118", sc: "4.6", sod: "132", pot: "5.6", hemo: "8.9", pcv: "28", wbcc: "14200", rbcc: "3.1", htn: "yes", dm: "yes", cad: "yes"
      }
    },
    {
      name: "lower-risk research example",
      caseId: "CKD-RES-LOW",
      patientName: "張OO",
      clinicalNote: "Lower-risk research simulation",
      values: {
        age: "41", sg: "1.025", al: "0", su: "0", rbc: "normal", pc: "normal", pcc: "notpresent", ba: "notpresent", appet: "good", pe: "no", ane: "no", bgr: "106", bu: "24", sc: "0.9", sod: "140", pot: "4.2", hemo: "14.2", pcv: "44", wbcc: "7200", rbcc: "5.1", htn: "no", dm: "no", cad: "no"
      }
    }
  ]
};

const exampleCursor = {
  clinical: 0,
  research: 0
};

const ui = {
  htmlRoot: document.documentElement,
  modeClinical: document.getElementById("modeClinical"),
  modeResearch: document.getElementById("modeResearch"),
  miniModeClinical: document.getElementById("miniModeClinical"),
  miniModeResearch: document.getElementById("miniModeResearch"),
  historyList: document.getElementById("historyList"),
  clearHistory: document.getElementById("clearHistory"),
  toastViewport: document.getElementById("toastViewport"),
  shortcutHelp: document.getElementById("shortcutHelp"),
  themeToggle: document.getElementById("themeToggle"),
  loadExample: document.getElementById("loadExample"),
  readinessBadge: document.getElementById("readinessBadge"),
  readinessIcon: document.querySelector("#readinessBadge .readiness-icon"),
  shortcutModal: document.getElementById("shortcutModal"),
  closeShortcutModal: document.getElementById("closeShortcutModal"),
  commandPalette: document.getElementById("commandPalette"),
  closeCommandPalette: document.getElementById("closeCommandPalette"),
  commandSearch: document.getElementById("commandSearch"),
  commandList: document.getElementById("commandList"),
  modeSelector: document.getElementById("modeSelector"),
  caseSummary: document.getElementById("caseSummary"),
  modeSchemaPanel: document.getElementById("modeSchemaPanel"),
  reviewPanel: document.getElementById("reviewPanel"),
  journeyCounter: document.getElementById("journeyCounter"),
  journeySteps: document.querySelector(".journey-steps"),
  stepMode: document.getElementById("stepMode"),
  stepCase: document.getElementById("stepCase"),
  stepInput: document.getElementById("stepInput"),
  stepReview: document.getElementById("stepReview"),
  stepPrev: document.getElementById("stepPrev"),
  stepNext: document.getElementById("stepNext"),
  activeModeLabel: document.getElementById("activeModeLabel"),
  activeModeDescription: document.getElementById("activeModeDescription"),
  activeRouteLabel: document.getElementById("activeRouteLabel"),
  activeRouteDescription: document.getElementById("activeRouteDescription"),
  activeFieldCount: document.getElementById("activeFieldCount"),
  activeFieldDescription: document.getElementById("activeFieldDescription"),
  schemaTitle: document.getElementById("schemaTitle"),
  schemaIntro: document.getElementById("schemaIntro"),
  formSections: document.getElementById("formSections"),
  connectionStatus: document.getElementById("connectionStatus"),
  responseMode: document.getElementById("responseMode"),
  completionValue: document.getElementById("completionValue"),
  completionProgress: document.getElementById("completionProgress"),
  brandCompletionValue: document.getElementById("brandCompletionValue"),
  brandCompletionProgress: document.getElementById("brandCompletionProgress"),
  reviewModeLabel: document.getElementById("reviewModeLabel"),
  reviewModeHint: document.getElementById("reviewModeHint"),
  reviewCompletion: document.getElementById("reviewCompletion"),
  apiBaseUrl: document.getElementById("apiBaseUrl"),
  clinicalPath: document.getElementById("clinicalPath"),
  researchPath: document.getElementById("researchPath"),
  requestEnvelope: document.getElementById("requestEnvelope"),
  mockMode: document.getElementById("mockMode"),
  payloadPreview: document.getElementById("payloadPreview"),
  riskScore: document.getElementById("riskScore"),
  calibrationCaveat: document.getElementById("calibrationCaveat"),
  mockModeBanner: document.getElementById("mockModeBanner"),
  riskBand: document.getElementById("riskBand"),
  predictionLabel: document.getElementById("predictionLabel"),
  modelVersion: document.getElementById("modelVersion"),
  predictionTimestamp: document.getElementById("predictionTimestamp"),
  servingRoute: document.getElementById("servingRoute"),
  resultHeadline: document.getElementById("resultHeadline"),
  resultSubheadline: document.getElementById("resultSubheadline"),
  actionHeadline: document.getElementById("actionHeadline"),
  actionBody: document.getElementById("actionBody"),
  reportHeadline: document.getElementById("reportHeadline"),
  reportBody: document.getElementById("reportBody"),
  exportReportTitle: document.getElementById("exportReportTitle"),
  exportReportMeta: document.getElementById("exportReportMeta"),
  stageCapture: document.getElementById("stageCapture"),
  stageRoute: document.getElementById("stageRoute"),
  stageResponse: document.getElementById("stageResponse"),
  resultMessage: document.getElementById("resultMessage"),
  clinicalNotes: document.getElementById("clinicalNotes"),
  explanationList: document.getElementById("explanationList"),
  reportSnapshot: document.getElementById("reportSnapshot"),
  waterfallChart: document.getElementById("waterfallChart"),
  reportPreview: document.getElementById("reportPreview"),
  formattedReportPreview: document.getElementById("formattedReportPreview"),
  previewTabFormatted: document.getElementById("previewTabFormatted"),
  previewTabRaw: document.getElementById("previewTabRaw"),
  gaugePanel: document.querySelector(".gauge-panel"),
  gaugeShell: document.querySelector(".gauge-shell"),
  gaugeProgress: document.getElementById("gaugeProgress"),
  resultPanel: document.getElementById("resultPanel")
};

let settings = loadSettings();
let activeMode = settings.defaultMode || "clinical";
const navItems = Array.from(document.querySelectorAll(".nav-item"));
const FLOW_STEP_IDS = ["modeSelector", "caseSummary", "modeSchemaPanel", "reviewPanel"];
const stepButtons = [ui.stepMode, ui.stepCase, ui.stepInput, ui.stepReview];
let currentStepIndex = 0;
let latestReportPayload = null;
let currentPreviewTab = "formatted";
let predictionHistory = [];
let toastCounter = 0;
let scoreAnimationFrame = null;
let stepTransitionTimeout = null;
let commandPaletteIndex = 0;
let commandActions = [];
const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const RESULT_REVEAL_ITEMS = Array.from(document.querySelectorAll(".result-panel .reveal-item"));
const RESULT_SKELETON_TARGETS = Array.from(document.querySelectorAll(".result-skeleton-target"));
const GAUGE_RADIUS = 84;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;
const COMPLETION_RADIUS = 18;
const COMPLETION_CIRCUMFERENCE = 2 * Math.PI * COMPLETION_RADIUS;

initializeGauge();
initializeCompletionRings();
renderMode(activeMode);
hydrateSettings();
renderStepState();
updateConnectionBadge();
updateCompletion();
setPreviewTab("formatted");
renderHistory();
updatePrintHeader();
initializeCommandPalette();

ui.formSections.addEventListener("input", () => updateCompletion());
ui.formSections.addEventListener("focusout", (event) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLSelectElement) {
    validateFieldInput(event.target);
  }
});

ui.modeClinical.addEventListener("click", () => switchMode("clinical"));
ui.modeResearch.addEventListener("click", () => switchMode("research"));
ui.miniModeClinical.addEventListener("click", () => switchMode("clinical"));
ui.miniModeResearch.addEventListener("click", () => switchMode("research"));
ui.previewTabFormatted.addEventListener("click", () => setPreviewTab("formatted"));
ui.previewTabRaw.addEventListener("click", () => setPreviewTab("raw"));
ui.shortcutHelp.addEventListener("click", openShortcutModal);
ui.closeShortcutModal.addEventListener("click", closeShortcutModal);
ui.shortcutModal.addEventListener("click", (event) => {
  if (event.target === ui.shortcutModal) {
    closeShortcutModal();
  }
});
ui.closeCommandPalette.addEventListener("click", closeCommandPalette);
ui.commandPalette.addEventListener("click", (event) => {
  if (event.target === ui.commandPalette) {
    closeCommandPalette();
  }
});
ui.themeToggle.addEventListener("click", toggleTheme);
ui.readinessBadge.addEventListener("click", () => setStep(2));
ui.commandSearch.addEventListener("input", () => {
  commandPaletteIndex = 0;
  renderCommandList(ui.commandSearch.value.trim());
});
ui.commandList.addEventListener("click", (event) => {
  const row = event.target instanceof HTMLElement ? event.target.closest("[data-command-index]") : null;
  if (!row) return;
  runCommandAction(Number(row.dataset.commandIndex));
});
ui.clearHistory.addEventListener("click", clearPredictionHistory);
ui.historyList.addEventListener("click", (event) => {
  const trigger = event.target instanceof HTMLElement ? event.target.closest("[data-history-index]") : null;
  if (!trigger) return;
  loadHistoryEntry(Number(trigger.dataset.historyIndex));
});
document.getElementById("caseId").addEventListener("input", () => updatePrintHeader());

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const targetId = item.dataset.target;
    const target = targetId ? document.getElementById(targetId) : null;
    setActiveNav(targetId);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

document.addEventListener("keydown", handleWorkspaceShortcuts);

stepButtons.forEach((button, index) => {
  button.addEventListener("click", () => setStep(index));
});

ui.stepPrev.addEventListener("click", () => setStep(currentStepIndex - 1));
ui.stepNext.addEventListener("click", () => {
  if (currentStepIndex < FLOW_STEP_IDS.length - 1) {
    setStep(currentStepIndex + 1);
    return;
  }
  document.getElementById("runPrediction").click();
});

document.querySelectorAll("[data-step-jump]").forEach((button) => {
  button.addEventListener("click", () => setStep(Number(button.dataset.stepJump)));
});

document.querySelectorAll("[data-review-run]").forEach((button) => {
  button.addEventListener("click", () => document.getElementById("runPrediction").click());
});

document.getElementById("copyReportSummary").addEventListener("click", async () => {
  if (!latestReportPayload) {
    setResultMessage("No report is available yet. Run a prediction first.", "info");
    return;
  }

  setActiveNav("exportPanel");

  const summaryText = [
    latestReportPayload.title,
    latestReportPayload.meta,
    latestReportPayload.summary,
    `Action: ${latestReportPayload.action}`,
    `Top signals: ${latestReportPayload.signals.join(", ") || "None returned"}`,
    `Serving route: ${latestReportPayload.route}`
  ].join("\n");

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(summaryText);
      setResultMessage("Prediction summary copied to clipboard.", "success");
      return;
    }
  } catch {}

  setResultMessage("Clipboard access is unavailable in this environment.", "error");
});

document.getElementById("downloadReportJson").addEventListener("click", () => {
  if (!latestReportPayload) {
    setResultMessage("No report is available yet. Run a prediction first.", "info");
    return;
  }
  setActiveNav("exportPanel");
  downloadBlob(JSON.stringify(latestReportPayload, null, 2), "application/json", buildExportFilename("json"));
  setResultMessage("JSON report exported.", "success");
});

document.getElementById("downloadReportHtml").addEventListener("click", () => {
  if (!latestReportPayload) {
    setResultMessage("No report is available yet. Run a prediction first.", "info");
    return;
  }
  setActiveNav("exportPanel");
  downloadBlob(buildReportHtml(latestReportPayload), "text/html", buildExportFilename("html"));
  setResultMessage("HTML report exported.", "success");
});

document.getElementById("saveConnection").addEventListener("click", () => {
  settings = readSettingsFromUI();
  settings.defaultMode = activeMode;
  persistSettings(settings);
  updateConnectionBadge();
  updateModeSummary();
  setActiveNav("settingsPanel");
  setResultMessage("Adapter settings saved. The active mode will use the corresponding route when you submit a prediction.", "success");
});

document.getElementById("loadExample").addEventListener("click", () => {
  const example = fillExample(activeMode);
  updateCompletion();
  refreshValidationState();
  setResultMessage(`${MODES[activeMode].label} ${example.name} loaded. Review the values, then run prediction.`, "info");
});

document.getElementById("resetForm").addEventListener("click", () => {
  clearCurrentModeInputs();
  updateCompletion();
  refreshValidationState();
  resetResultPanels();
  setResultMessage("Current mode inputs have been reset.", "info");
});

document.getElementById("runPrediction").addEventListener("click", async () => {
  settings = readSettingsFromUI();
  settings.defaultMode = activeMode;
  persistSettings(settings);
  updateConnectionBadge();
  updateModeSummary();

  const inputs = collectModePayload(activeMode);
  const requestBody = buildRequestBody(activeMode, inputs, settings);
  ui.payloadPreview.textContent = JSON.stringify(requestBody, null, 2);
  updateCompletion(inputs);
  setStep(FLOW_STEP_IDS.length - 1);
  setRunningState(true);
  setResultLoading(true);
  setResultMessage("Submitting prediction request...", "info");

  try {
    const response = await requestPrediction(activeMode, inputs, settings);
    renderPrediction(response, inputs, activeMode, settings);
  } catch (error) {
    setResponseStages("idle");
    setResultLoading(false, true);
    setResultMessage(error.message, "error");
  } finally {
    setRunningState(false);
  }
});

function initializeGauge() {
  ui.gaugeProgress.style.strokeDasharray = `${GAUGE_CIRCUMFERENCE}`;
  ui.gaugeProgress.style.strokeDashoffset = `${GAUGE_CIRCUMFERENCE}`;
}

function initializeCompletionRings() {
  [ui.completionProgress, ui.brandCompletionProgress].forEach((ring) => {
    ring.style.strokeDasharray = `${COMPLETION_CIRCUMFERENCE}`;
    ring.style.strokeDashoffset = `${COMPLETION_CIRCUMFERENCE}`;
  });
}

function openShortcutModal() {
  closeCommandPalette();
  ui.shortcutModal.hidden = false;
}

function closeShortcutModal() {
  ui.shortcutModal.hidden = true;
}

function initializeCommandPalette() {
  commandActions = [
    { name: "Run prediction", shortcut: "Ctrl+Enter", handler: () => document.getElementById("runPrediction").click() },
    { name: "Load example", shortcut: "Ctrl+L", handler: () => document.getElementById("loadExample").click() },
    { name: "Reset form", shortcut: "—", handler: () => document.getElementById("resetForm").click() },
    { name: "Switch to Clinical mode", shortcut: "—", handler: () => switchMode("clinical") },
    { name: "Switch to Research mode", shortcut: "—", handler: () => switchMode("research") },
    { name: "Export JSON", shortcut: "—", handler: () => document.getElementById("downloadReportJson").click() },
    { name: "Export HTML", shortcut: "—", handler: () => document.getElementById("downloadReportHtml").click() },
    { name: "Toggle dark mode", shortcut: "—", handler: () => toggleTheme() },
    { name: "Open shortcuts", shortcut: "⌨", handler: () => openShortcutModal() }
  ];
  renderCommandList("");
}

function openCommandPalette() {
  closeShortcutModal();
  ui.commandPalette.hidden = false;
  ui.commandSearch.value = "";
  commandPaletteIndex = 0;
  renderCommandList("");
  window.setTimeout(() => ui.commandSearch.focus(), 0);
}

function closeCommandPalette() {
  ui.commandPalette.hidden = true;
}

function renderCommandList(query) {
  const normalized = query.toLowerCase();
  const filtered = commandActions
    .map((action, index) => ({ ...action, originalIndex: index }))
    .filter((action) => !normalized || action.name.toLowerCase().includes(normalized));

  if (!filtered.length) {
    ui.commandList.innerHTML = `<div class="command-empty">No matching command.</div>`;
    return;
  }

  commandPaletteIndex = Math.min(commandPaletteIndex, filtered.length - 1);
  ui.commandList.innerHTML = filtered.map((action, index) => `
    <button class="command-item ${index === commandPaletteIndex ? "active" : ""}" type="button" data-command-index="${action.originalIndex}">
      <span class="command-name">${escapeHtml(action.name)}</span>
      <span class="command-shortcut">${escapeHtml(action.shortcut)}</span>
    </button>
  `).join("");
}

function moveCommandSelection(direction) {
  const items = Array.from(ui.commandList.querySelectorAll(".command-item"));
  if (!items.length) return;
  commandPaletteIndex = (commandPaletteIndex + direction + items.length) % items.length;
  items.forEach((item, index) => item.classList.toggle("active", index === commandPaletteIndex));
  items[commandPaletteIndex].scrollIntoView({ block: "nearest" });
}

function runCommandAction(index) {
  const action = commandActions[index];
  if (!action) return;
  closeCommandPalette();
  action.handler();
}

function toggleTheme() {
  const nextTheme = ui.htmlRoot.getAttribute("data-theme") === "dark" ? "light" : "dark";
  if (nextTheme === "dark") {
    ui.htmlRoot.setAttribute("data-theme", "dark");
  } else {
    ui.htmlRoot.removeAttribute("data-theme");
  }
}

function setPreviewTab(tab) {
  currentPreviewTab = tab;
  ui.previewTabFormatted.classList.toggle("active", tab === "formatted");
  ui.previewTabRaw.classList.toggle("active", tab === "raw");
  ui.formattedReportPreview.classList.toggle("active", tab === "formatted");
  ui.reportPreview.classList.toggle("active", tab === "raw");
}

function handleWorkspaceShortcuts(event) {
  const isModifier = event.ctrlKey || event.metaKey;

  if (event.key === "Escape") {
    if (!ui.shortcutModal.hidden) {
      closeShortcutModal();
      return;
    }
    if (!ui.commandPalette.hidden) {
      closeCommandPalette();
      return;
    }
  }

  if (!ui.commandPalette.hidden) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveCommandSelection(1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveCommandSelection(-1);
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const active = ui.commandList.querySelector(".command-item.active");
      if (active) {
        runCommandAction(Number(active.dataset.commandIndex));
      }
      return;
    }
  }

  if (!isModifier) return;

  const key = event.key.toLowerCase();

  if (key === "k") {
    event.preventDefault();
    if (ui.commandPalette.hidden) {
      openCommandPalette();
    } else {
      closeCommandPalette();
    }
    return;
  }

  if (key === "enter") {
    event.preventDefault();
    document.getElementById("runPrediction").click();
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    setStep(currentStepIndex - 1);
    return;
  }

  if (event.key === "ArrowRight") {
    event.preventDefault();
    setStep(currentStepIndex + 1);
    return;
  }

  if (key === "e") {
    event.preventDefault();
    setActiveNav("exportPanel");
    document.getElementById("exportPanel").scrollIntoView({ behavior: REDUCED_MOTION ? "auto" : "smooth", block: "start" });
    return;
  }

  if (key === "l") {
    event.preventDefault();
    document.getElementById("loadExample").click();
  }
}

function switchMode(mode) {
  activeMode = mode;
  renderMode(mode);
  settings.defaultMode = mode;
  persistSettings(settings);
  updateCompletion();
  resetResultPanels();
  setResultMessage(`${MODES[mode].label} is now active.`, "info");
}

function renderMode(mode) {
  ui.modeClinical.classList.toggle("active", mode === "clinical");
  ui.modeResearch.classList.toggle("active", mode === "research");
  ui.miniModeClinical.classList.toggle("active", mode === "clinical");
  ui.miniModeResearch.classList.toggle("active", mode === "research");
  renderFormSections(mode);
  updateModeSummary();
  updateReviewPanel();
  updateExampleButtonLabel();
  renderStepState();
}

function setActiveNav(targetId) {
  navItems.forEach((item) => {
    item.classList.toggle("active", item.dataset.target === targetId);
  });
}

function setStep(index) {
  const nextIndex = Math.max(0, Math.min(FLOW_STEP_IDS.length - 1, index));
  if (nextIndex === currentStepIndex) {
    const samePanel = document.getElementById(FLOW_STEP_IDS[nextIndex]);
    if (samePanel) {
      samePanel.scrollIntoView({ behavior: REDUCED_MOTION ? "auto" : "smooth", block: "start" });
    }
    return;
  }

  const previousPanel = document.getElementById(FLOW_STEP_IDS[currentStepIndex]);
  const nextPanel = document.getElementById(FLOW_STEP_IDS[nextIndex]);

  if (stepTransitionTimeout) {
    window.clearTimeout(stepTransitionTimeout);
    stepTransitionTimeout = null;
  }

  if (previousPanel) {
    previousPanel.classList.remove("panel-entering");
    previousPanel.classList.add("panel-leaving");
  }

  const swapPanels = () => {
    if (previousPanel) {
      previousPanel.classList.remove("panel-leaving", "active");
    }
    currentStepIndex = nextIndex;
    renderStepState();
    if (nextPanel) {
      nextPanel.classList.add("panel-entering");
      nextPanel.scrollIntoView({ behavior: REDUCED_MOTION ? "auto" : "smooth", block: "start" });
      if (!REDUCED_MOTION) {
        window.setTimeout(() => nextPanel.classList.remove("panel-entering"), 280);
      } else {
        nextPanel.classList.remove("panel-entering");
      }
    }
  };

  if (REDUCED_MOTION) {
    swapPanels();
    return;
  }

  stepTransitionTimeout = window.setTimeout(() => {
    swapPanels();
    stepTransitionTimeout = null;
  }, 180);
}

function renderStepState() {
  ui.journeyCounter.textContent = `Step ${currentStepIndex + 1} / ${FLOW_STEP_IDS.length}`;
  const journeyProgress = FLOW_STEP_IDS.length <= 1 ? 0 : (currentStepIndex / (FLOW_STEP_IDS.length - 1)) * 100;
  ui.journeySteps.style.setProperty("--journey-progress", `${journeyProgress}%`);
  stepButtons.forEach((button, index) => {
    const isActive = index === currentStepIndex;
    button.classList.toggle("active", isActive);
    button.classList.toggle("completed", index < currentStepIndex);
    button.setAttribute("aria-selected", String(isActive));
  });

  FLOW_STEP_IDS.forEach((id, index) => {
    const panel = document.getElementById(id);
    if (panel) {
      panel.classList.toggle("active", index === currentStepIndex);
    }
  });

  ui.stepPrev.disabled = currentStepIndex === 0;
  ui.stepPrev.textContent = currentStepIndex === FLOW_STEP_IDS.length - 1 ? "Back to inputs" : "Back";
  ui.stepNext.textContent = currentStepIndex === FLOW_STEP_IDS.length - 1 ? "Run from review" : "Next step";
}

function renderFormSections(mode) {
  const sections = MODES[mode].sectionOrder.map((sectionKey) => {
    const section = SECTIONS[sectionKey];
    return `
      <section class="form-section">
        <h3>${escapeHtml(section.title)}</h3>
        <div class="form-grid">
          ${section.fields.map(renderField).join("")}
        </div>
      </section>
    `;
  }).join("");
  ui.formSections.innerHTML = sections;
  refreshValidationState();
}

function renderField(field) {
  if (field.type === "select") {
    return `
      <label class="field">
        <span>${escapeHtml(field.label)} <code>${escapeHtml(field.key)}</code></span>
        <select name="${escapeHtml(field.key)}">
          <option value="">Leave empty</option>
          ${field.options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("")}
        </select>
      </label>
    `;
  }

  return `
    <label class="field">
      <span>${escapeHtml(field.label)} <code>${escapeHtml(field.key)}</code></span>
      <input
        name="${escapeHtml(field.key)}"
        type="number"
        inputmode="decimal"
        step="${escapeHtml(field.step || "any")}"
        min="${escapeHtml(field.min ?? "")}" 
        max="${escapeHtml(field.max ?? "")}" 
        placeholder="${escapeHtml(field.placeholder || "")}"
      >
    </label>
  `;
}

function getActiveFields() {
  return MODES[activeMode].sectionOrder.flatMap((sectionKey) => SECTIONS[sectionKey].fields);
}

function getFieldsForMode(mode) {
  return MODES[mode].sectionOrder.flatMap((sectionKey) => SECTIONS[sectionKey].fields);
}

function getCurrentCaseContext() {
  return {
    caseId: document.getElementById("caseId").value.trim(),
    patientName: document.getElementById("patientName").value.trim(),
    clinicalNote: document.getElementById("clinicalNote").value.trim()
  };
}

function collectModePayload(mode) {
  return MODES[mode].sectionOrder.reduce((acc, sectionKey) => {
    SECTIONS[sectionKey].fields.forEach((field) => {
      const input = document.querySelector(`[name='${field.key}']`);
      const raw = input ? input.value.trim() : "";
      if (!raw) {
        acc[field.key] = null;
      } else {
        acc[field.key] = field.type === "number" ? Number(raw) : raw;
      }
    });
    return acc;
  }, {});
}

function buildRequestBody(mode, inputs, currentSettings) {
  const envelopeKey = currentSettings.requestEnvelope || "inputs";
  return {
    mode,
    [envelopeKey]: inputs,
    context: {
      case_id: document.getElementById("caseId").value.trim() || null,
      patient_name: document.getElementById("patientName").value.trim() || null,
      clinical_note: document.getElementById("clinicalNote").value.trim() || null
    }
  };
}

function buildApiUrl(baseUrl, route) {
  const normalizedBase = String(baseUrl || "").replace(/\/+$/, "");
  const normalizedRoute = String(route || "").replace(/^\/+/, "");
  if (!normalizedBase) {
    return normalizedRoute;
  }
  return `${normalizedBase}/${normalizedRoute}`;
}

async function requestPrediction(mode, inputs, currentSettings) {
  if (currentSettings.useMockPrediction) {
    await delay(700);
    return buildMockResponse(mode, inputs);
  }

  if (!currentSettings.apiBaseUrl) {
    throw new Error("API base URL is empty. Either enable mock mode or provide a live backend endpoint.");
  }

  const route = mode === "clinical" ? currentSettings.clinicalPath : currentSettings.researchPath;
  const url = buildApiUrl(currentSettings.apiBaseUrl, route);
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildRequestBody(mode, inputs, currentSettings))
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Prediction request failed (${response.status}): ${text || "No response body"}`);
  }

  const data = await response.json();
  return normalizeResponse(data, mode, route, false);
}

function buildMockResponse(mode, inputs) {
  const score = mode === "clinical" ? calculateClinicalRisk(inputs) : calculateResearchRisk(inputs);
  const explanation = mode === "clinical" ? buildClinicalExplanation(inputs) : buildResearchExplanation(inputs);
  return normalizeResponse({
    risk_score: score,
    prediction_label: score >= 0.7 ? "high_risk" : score >= 0.4 ? "moderate_risk" : "lower_risk",
    model_version: mode === "clinical" ? "clinical-mock-preview" : "research-mock-preview",
    timestamp: new Date().toISOString(),
    notes: mode === "clinical"
      ? "Mock clinical response generated locally. Replace with a real clinical backend when your intake-to-inference route is ready."
      : "Mock research response generated locally. Replace with the current schema-aligned backend route when available.",
    explanation
  }, mode, mode === "clinical" ? settings.clinicalPath : settings.researchPath, true);
}

function calculateClinicalRisk(inputs) {
  let score = 0.2;
  if (typeof inputs.age === "number") score += Math.min(inputs.age / 400, 0.12);
  if (inputs.dm === "yes") score += 0.12;
  if (inputs.htn === "yes") score += 0.11;
  if (inputs.cvd === "yes") score += 0.08;
  if (inputs.proteinuria_flag === "yes") score += 0.1;
  if (typeof inputs.scr === "number") score += Math.min(inputs.scr / 10, 0.15);
  if (typeof inputs.egfr === "number") score -= Math.max(0, (inputs.egfr - 45) / 250);
  if (typeof inputs.uacr === "number") score += Math.min(inputs.uacr / 1200, 0.14);
  if (typeof inputs.hba1c === "number") score += Math.min(inputs.hba1c / 40, 0.09);
  if (typeof inputs.sbp === "number") score += Math.min(Math.max(inputs.sbp - 120, 0) / 300, 0.08);
  return clampScore(score);
}

function calculateResearchRisk(inputs) {
  let score = 0.18;
  if (inputs.htn === "yes") score += 0.11;
  if (inputs.dm === "yes") score += 0.11;
  if (inputs.cad === "yes") score += 0.05;
  if (inputs.pe === "yes") score += 0.07;
  if (inputs.ane === "yes") score += 0.08;
  if (inputs.appet === "poor") score += 0.05;
  if (inputs.pc === "abnormal") score += 0.05;
  if (inputs.rbc === "abnormal") score += 0.05;
  if (typeof inputs.al === "number") score += inputs.al * 0.05;
  if (typeof inputs.su === "number") score += inputs.su * 0.03;
  if (typeof inputs.sc === "number") score += Math.min(inputs.sc / 16, 0.16);
  if (typeof inputs.bu === "number") score += Math.min(inputs.bu / 260, 0.12);
  if (typeof inputs.bgr === "number") score += Math.min(inputs.bgr / 1000, 0.08);
  if (typeof inputs.hemo === "number") score -= Math.max(0, (inputs.hemo - 11) * 0.022);
  if (typeof inputs.pcv === "number") score -= Math.max(0, (inputs.pcv - 35) * 0.005);
  if (typeof inputs.rbcc === "number") score -= Math.max(0, (inputs.rbcc - 4) * 0.03);
  if (typeof inputs.sg === "number") score -= Math.max(0, (inputs.sg - 1.01) * 7.5);
  return clampScore(score);
}

function buildClinicalExplanation(inputs) {
  const items = [];
  if (typeof inputs.uacr === "number" && inputs.uacr >= 30) items.push({ feature: "UACR", message: "Albuminuria burden is contributing positive signal to the clinical risk estimate.", contribution: 0.14 });
  if (typeof inputs.egfr === "number" && inputs.egfr <= 60) items.push({ feature: "eGFR", message: "Reduced eGFR is contributing positive signal to the clinical risk estimate.", contribution: 0.12 });
  if (typeof inputs.scr === "number" && inputs.scr >= 1.2) items.push({ feature: "serum creatinine", message: "Elevated serum creatinine is increasing the clinical risk score.", contribution: 0.11 });
  if (inputs.dm === "yes") items.push({ feature: "diabetes mellitus", message: "Diabetes mellitus is contributing to the clinical risk profile.", contribution: 0.09 });
  if (inputs.htn === "yes") items.push({ feature: "hypertension", message: "Hypertension is contributing to the clinical risk profile.", contribution: 0.08 });
  return items.slice(0, 5);
}

function buildResearchExplanation(inputs) {
  const items = [];
  if (typeof inputs.hemo === "number") {
    items.push(inputs.hemo < 11
      ? { feature: "hemoglobin", message: "Lower hemoglobin is pushing the research-mode score upward and aligns with the anemia-related risk signal.", contribution: 0.14 }
      : { feature: "hemoglobin", message: "Higher hemoglobin is acting as a protective signal in the current research-mode profile.", contribution: -0.06 });
  }
  if (typeof inputs.pcv === "number") {
    items.push(inputs.pcv < 35
      ? { feature: "packed cell volume", message: "Lower packed cell volume is contributing positive signal to the research-mode estimate.", contribution: 0.11 }
      : { feature: "packed cell volume", message: "Higher packed cell volume is acting as a stabilizing signal in the current profile.", contribution: -0.05 });
  }
  if (typeof inputs.sc === "number" && inputs.sc >= 1.5) items.push({ feature: "serum creatinine", message: "Elevated serum creatinine is pushing the research-mode score upward.", contribution: 0.16 });
  if (typeof inputs.sg === "number") {
    items.push(inputs.sg <= 1.01
      ? { feature: "specific gravity", message: "Lower urine specific gravity is contributing positive signal to the research-mode estimate.", contribution: 0.09 }
      : { feature: "specific gravity", message: "Higher urine specific gravity is acting as a protective signal in the current profile.", contribution: -0.04 });
  }
  if (typeof inputs.bu === "number" && inputs.bu >= 40) items.push({ feature: "blood urea", message: "Higher blood urea is contributing to the upward prediction signal.", contribution: 0.12 });
  if (typeof inputs.al === "number" && inputs.al >= 2) items.push({ feature: "albumin", message: "Albumin level is adding positive signal to the research-mode estimate.", contribution: 0.1 });
  if (inputs.htn === "yes") items.push({ feature: "hypertension", message: "Hypertension is contributing to the upward research-mode risk signal.", contribution: 0.09 });
  if (inputs.dm === "yes") items.push({ feature: "diabetes mellitus", message: "Diabetes mellitus is contributing to the upward research-mode risk signal.", contribution: 0.09 });
  return items.slice(0, 5);
}

function normalizeResponse(data, mode, route, isMock) {
  return {
    mode,
    route,
    isMock,
    riskScore: Number(data.risk_score ?? data.score ?? data.probability ?? 0),
    predictionLabel: String(data.prediction_label ?? data.label ?? "unknown"),
    modelVersion: String(data.model_version ?? data.version ?? "unknown"),
    timestamp: String(data.timestamp ?? new Date().toISOString()),
    notes: String(data.notes ?? "Prediction completed successfully."),
    explanation: normalizeExplanation(Array.isArray(data.explanation) ? data.explanation : [])
  };
}

function normalizeExplanation(items) {
  const fallbackContributions = [0.16, 0.13, 0.1, 0.08, 0.06];
  return items.slice(0, 6).map((item, index) => {
    const feature = String(item.feature ?? `feature_${index + 1}`);
    const message = String(item.message ?? "No explanation note returned.");
    let contribution = Number(item.contribution);

    if (Number.isNaN(contribution)) {
      const lowerMessage = message.toLowerCase();
      const isProtective = lowerMessage.includes("protect") || lowerMessage.includes("lower") || lowerMessage.includes("decreas");
      contribution = fallbackContributions[index] ?? 0.05;
      if (isProtective) {
        contribution *= -1;
      }
    }

    return {
      feature,
      message,
      contribution,
      direction: contribution >= 0 ? "positive" : "negative"
    };
  });
}

function renderPrediction(result, inputs, mode, currentSettings, options = {}) {
  setActiveNav("resultPanel");
  const riskPercent = Math.round(result.riskScore * 100);
  const bandClass = result.riskScore >= 0.7 ? "risk-high" : result.riskScore >= 0.4 ? "risk-mid" : "risk-low";
  const bandLabel = result.riskScore >= 0.7 ? "High-risk profile" : result.riskScore >= 0.4 ? "Moderate-risk profile" : "Lower-risk profile";
  const narrative = buildResultNarrative(result, inputs, mode);
  const reportPayload = buildReportPayload(result, inputs, mode, narrative);

  setResultLoading(false);
  ui.riskScore.textContent = REDUCED_MOTION ? `${riskPercent}%` : "0%";
  ui.riskBand.className = `risk-band ${bandClass}`;
  ui.riskBand.textContent = bandLabel;
  ui.predictionLabel.textContent = result.predictionLabel;
  ui.modelVersion.textContent = result.modelVersion;
  ui.predictionTimestamp.textContent = formatTimestamp(result.timestamp);
  ui.servingRoute.textContent = result.route || (mode === "clinical" ? currentSettings.clinicalPath : currentSettings.researchPath);
  ui.responseMode.textContent = result.isMock ? "Mock response" : "Live API response";
  ui.responseMode.className = `status-chip ${result.isMock ? "warning" : "live"}`;
  ui.mockModeBanner.hidden = !result.isMock;
  ui.calibrationCaveat.hidden = false;
  setResponseStages("done");
  ui.resultHeadline.textContent = narrative.headline;
  ui.resultSubheadline.textContent = narrative.summary;
  ui.actionHeadline.textContent = narrative.actionTitle;
  ui.actionBody.textContent = narrative.actionBody;
  ui.reportHeadline.textContent = narrative.reportTitle;
  ui.reportBody.textContent = narrative.reportBody;
  ui.exportReportTitle.textContent = reportPayload.title;
  ui.exportReportMeta.textContent = reportPayload.meta;
  setResultMessage(result.notes, "success", { toast: !options.skipToast });
  renderNotes(result, inputs, mode);
  renderExplanation(result.explanation);
  renderReportSnapshot(result, inputs, mode, narrative, reportPayload);
  renderWaterfallChart(result, reportPayload);
  renderReportPreview(reportPayload);
  renderFormattedReportPreview(reportPayload);
  latestReportPayload = reportPayload;
  updatePrintHeader(result.timestamp);
  if (!options.skipHistory) {
    pushHistoryEntry({ result, inputs, mode, narrative, reportPayload, caseContext: getCurrentCaseContext() });
  }
  triggerResultReveal();
  animateGauge(result.riskScore);
  animateRiskScoreNumber(riskPercent);
  updateCompletion(inputs);
}

function buildResultNarrative(result, inputs, mode) {
  const riskPercent = Math.round(result.riskScore * 100);
  const modeLabel = mode === "clinical" ? "clinical intake route" : "research inference route";

  if (result.riskScore >= 0.7) {
    return {
      headline: `Higher-risk output on the ${modeLabel}`,
      summary: `The submitted profile landed in the higher-risk band at ${riskPercent}%. The returned result should be reviewed with the dominant renal markers and the current case context together.`,
      actionTitle: "Escalate to focused review",
      actionBody: "Review the strongest markers first, confirm data completeness, and decide whether this case should move into closer follow-up or more urgent clinician attention.",
      reportTitle: "High-priority report draft ready",
      reportBody: "The report snapshot should emphasize the elevated risk band, the primary contributing signals, and the serving mode used for this prediction."
    };
  }

  if (result.riskScore >= 0.4) {
    return {
      headline: `Moderate-risk output on the ${modeLabel}`,
      summary: `The profile currently falls into a moderate-risk band at ${riskPercent}%. The result is actionable, but it should be framed as a guided interpretation rather than a stand-alone decision.`,
      actionTitle: "Plan short-interval follow-up",
      actionBody: "Check the returning signal summary, review the renal markers with the intake context, and decide whether repeat measurement or nearer follow-up is warranted.",
      reportTitle: "Structured monitoring report ready",
      reportBody: "The report snapshot should capture the moderate-risk band, key markers, and a cautious interpretation note for follow-up use."
    };
  }

  return {
    headline: `Lower-risk output on the ${modeLabel}`,
    summary: `The submitted profile currently returns a lower-risk band at ${riskPercent}%. The result can support reassurance, but it still needs to sit alongside clinical judgment and context.`,
    actionTitle: "Maintain routine review",
    actionBody: "Keep the result visible in the record, confirm that no key markers were omitted, and continue with routine clinical interpretation or standard monitoring cadence.",
    reportTitle: "Routine summary report ready",
    reportBody: "The report snapshot should record the lower-risk band, the serving route, and the key returned signals without overstating certainty."
  };
}

function renderNotes(result, inputs, mode) {
  const notes = [];

  if (result.riskScore >= 0.7) {
    notes.push({ tone: "danger-note", title: "Higher-risk output", body: "The submitted profile falls into the higher-risk range. This should trigger closer review of renal markers and context before action." });
  } else if (result.riskScore >= 0.4) {
    notes.push({ tone: "warning-note", title: "Moderate-risk output", body: "The submitted profile falls into the moderate-risk range. Review the main signal drivers and consider short-interval follow-up." });
  } else {
    notes.push({ tone: "success-note", title: "Lower-risk output", body: "The submitted profile falls into the lower-risk range in the current model path. This does not replace clinical judgment." });
  }

  if (mode === "clinical") {
    if (typeof inputs.egfr === "number" && inputs.egfr <= 60) {
      notes.push({ tone: "warning-note", title: "Renal function watch", body: "Lower eGFR is present in the intake profile and should be reviewed with serum creatinine and albuminuria context." });
    }
    if (typeof inputs.uacr === "number" && inputs.uacr >= 30) {
      notes.push({ tone: "warning-note", title: "Albuminuria signal", body: "UACR is elevated in the current profile and may strengthen CKD risk interpretation." });
    }
    notes.push({ tone: "neutral-note", title: "Signal context", body: "Serum creatinine and albuminuria remain core renal markers in the current product-facing intake route and should be reviewed together." });
    notes.push({ tone: "neutral-note", title: "Mode caveat", body: "Clinical intake mode assumes a backend that either supports native clinical inputs or performs validated intake-to-model translation." });
  } else {
    if (typeof inputs.sc === "number" && inputs.sc >= 1.5) {
      notes.push({ tone: "warning-note", title: "Renal marker watch", body: "Serum creatinine is above the common low-risk range and is contributing to the current research-mode risk estimate." });
    }
    notes.push({ tone: "neutral-note", title: "Signal context", body: "Hemoglobin, packed cell volume, and serum creatinine remain among the strongest signals surfaced in the current research-mode path." });
    notes.push({ tone: "neutral-note", title: "Mode scope", body: "Research inference mode is aligned to the current #336 schema and is the most direct path for connecting the existing backend model." });
  }

  ui.clinicalNotes.innerHTML = notes.map((note) => `
    <div class="note-card ${note.tone}">
      <span>${escapeHtml(note.title)}</span>
      <strong>${escapeHtml(note.body)}</strong>
    </div>
  `).join("");
}

function renderExplanation(explanation) {
  if (!explanation.length) {
    ui.explanationList.innerHTML = `<div class="explanation-card empty-card">${escapeHtml(EMPTY_ATTRIBUTION_MESSAGE)}</div>`;
    return;
  }

  const maxContribution = Math.max(...explanation.map((item) => Math.abs(item.contribution)), 0.01);

  ui.explanationList.innerHTML = `
    <div class="signal-chart">
      ${explanation.map((item, index) => {
        const width = Math.max(12, Math.round((Math.abs(item.contribution) / maxContribution) * 100));
        const contributionLabel = `${item.contribution >= 0 ? "+" : ""}${item.contribution.toFixed(2)}`;
        return `
          <div class="signal-row">
            <div class="signal-name">${escapeHtml(item.feature)}</div>
            <div class="signal-bar-track">
              <div class="signal-bar ${item.direction === "positive" ? "is-positive" : "is-negative"}" style="width:${width}%; transition-delay:${index * 100}ms"></div>
            </div>
            <div class="signal-score">${escapeHtml(contributionLabel)}</div>
          </div>
        `;
      }).join("")}
    </div>
  `;

  animateBarTargets(ui.explanationList);
}

function renderReportSnapshot(result, inputs, mode, narrative, reportPayload) {
  const caseId = document.getElementById("caseId").value.trim() || "Unspecified case";
  const modeLabel = mode === "clinical" ? "Clinical intake mode" : "Research inference mode";
  const routeLabel = result.route || (mode === "clinical" ? settings.clinicalPath : settings.researchPath);
  ui.reportSnapshot.innerHTML = `
    <div class="report-row">
      <span>Case</span>
      <strong>${escapeHtml(caseId)}</strong>
    </div>
    <div class="report-row">
      <span>Mode</span>
      <strong>${escapeHtml(modeLabel)}</strong>
    </div>
    <div class="report-row">
      <span>Serving route</span>
      <strong>${escapeHtml(routeLabel)}</strong>
    </div>
    <div class="report-row">
      <span>Summary</span>
      <strong>${escapeHtml(narrative.headline)}</strong>
    </div>
    <div class="report-row">
      <span>Report note</span>
      <strong>${escapeHtml(narrative.reportBody)}</strong>
    </div>
    <div class="report-row">
      <span>Guidance line</span>
      <strong>${escapeHtml(reportPayload.guidanceLine)}</strong>
    </div>
  `;
}

function buildReportPayload(result, inputs, mode, narrative) {
  const caseId = document.getElementById("caseId").value.trim() || "CKD-OPS-UNSPECIFIED";
  const patientName = document.getElementById("patientName").value.trim() || "Unspecified patient";
  const modeLabel = mode === "clinical" ? "Clinical intake mode" : "Research inference mode";
  const routeLabel = result.route || (mode === "clinical" ? settings.clinicalPath : settings.researchPath);
  const signalList = result.explanation.map((item) => item.feature);
  const topSignals = result.explanation.slice(0, 3);
  const timestamp = formatTimestamp(result.timestamp);
  const predictionLabel = result.predictionLabel;
  const numericScore = Math.max(0, Math.min(1, result.riskScore));
  const riskBand = numericScore >= 0.7 ? "high" : numericScore >= 0.4 ? "mid" : "low";

  return {
    title: `CKD prediction report for ${caseId}`,
    meta: `${modeLabel} · ${timestamp} · ${predictionLabel}`,
    caseId,
    patientName,
    mode: modeLabel,
    route: routeLabel,
    timestamp,
    timestampIso: result.timestamp,
    score: `${Math.round(result.riskScore * 100)}%`,
    scoreNumeric: numericScore,
    label: predictionLabel,
    riskBand,
    modelVersion: result.modelVersion,
    summary: narrative.summary,
    action: narrative.actionBody,
    guidanceLine: narrative.actionTitle,
    reportNote: narrative.reportBody,
    serviceNote: result.notes,
    signals: signalList,
    explanation: result.explanation,
    topSignals
  };
}

function renderReportPreview(report) {
  const rawReport = {
    case_id: report.caseId,
    patient_name: report.patientName,
    mode: report.mode,
    route: report.route,
    score: report.scoreNumeric,
    score_label: report.label,
    guidance: report.guidanceLine,
    summary: report.summary,
    report_note: report.reportNote,
    service_note: report.serviceNote,
    model_version: report.modelVersion,
    timestamp: report.timestampIso,
    explanation: report.explanation
  };

  ui.reportPreview.innerHTML = `
    <section class="report-preview-section">
      <span>Raw report payload</span>
      <strong>${escapeHtml(report.title)}</strong>
      <p>This tab mirrors the structured payload that can be copied or exported.</p>
      <pre class="code-block">${escapeHtml(JSON.stringify(rawReport, null, 2))}</pre>
    </section>
  `;
}

function renderFormattedReportPreview(report) {
  const scoreBadgeClass = report.riskBand === "high" ? "high" : report.riskBand === "mid" ? "mid" : "low";
  const signalMarkup = report.topSignals.length
    ? `
      <div class="mini-signal-list">
        ${report.topSignals.map((item) => {
          const width = `${Math.max(14, Math.round(Math.abs(item.contribution) * 100))}%`;
          const label = `${item.contribution >= 0 ? "+" : ""}${item.contribution.toFixed(2)}`;
          return `
            <div class="mini-signal-row">
              <span class="mini-signal-name">${escapeHtml(item.feature)}</span>
              <div class="mini-signal-track">
                <div class="mini-signal-bar ${item.direction === "positive" ? "is-positive" : "is-negative"}" data-target-width="${width}"></div>
              </div>
              <span class="mini-signal-score">${escapeHtml(label)}</span>
            </div>
          `;
        }).join("")}
      </div>
    `
    : `<div class="report-preview-empty">No explanation items were returned for this response.</div>`;

  ui.formattedReportPreview.innerHTML = `
    <article class="formatted-report-card">
      <header class="formatted-report-header">
        <div>
          <p class="eyebrow">Live report preview</p>
          <h3>${escapeHtml(report.caseId)}</h3>
          <div class="formatted-report-meta">
            <div>${escapeHtml(report.patientName)}</div>
            <div>${escapeHtml(report.mode)} · ${escapeHtml(report.timestamp)}</div>
          </div>
        </div>
        <span class="score-badge ${scoreBadgeClass}">${escapeHtml(report.score)} ${escapeHtml(report.label)}</span>
      </header>

      <section class="report-preview-section">
        <span>Clinical guidance</span>
        <strong>${escapeHtml(report.guidanceLine)}</strong>
        <p>${escapeHtml(report.action)}</p>
      </section>

      <section class="report-preview-section">
        <span>Top 3 signals</span>
        ${signalMarkup}
      </section>

      <section class="report-preview-section">
        <span>Serving snapshot</span>
        <strong>${escapeHtml(report.route)}</strong>
        <p>${escapeHtml(report.serviceNote)}</p>
      </section>
    </article>
  `;

  animateBarTargets(ui.formattedReportPreview);
}

function renderWaterfallChart(result, report) {
  if (!report.explanation.length) {
    ui.waterfallChart.innerHTML = `<div class="waterfall-empty">No explanation items yet. Run a prediction to build the contribution path.</div>`;
    return;
  }

  const baseline = 0.2;
  let runningScore = baseline;
  const rows = [{
    label: "Base risk",
    value: baseline,
    start: 0,
    end: baseline,
    direction: "baseline"
  }];

  report.explanation.slice(0, 5).forEach((item) => {
    const nextScore = Math.max(0, Math.min(1, runningScore + item.contribution));
    rows.push({
      label: item.feature,
      value: item.contribution,
      start: Math.min(runningScore, nextScore),
      end: Math.max(runningScore, nextScore),
      direction: item.direction === "negative" ? "negative" : "positive"
    });
    runningScore = nextScore;
  });

  rows.push({
    label: "Predicted risk",
    value: result.riskScore,
    start: 0,
    end: result.riskScore,
    direction: "baseline"
  });

  ui.waterfallChart.innerHTML = `
    <div class="waterfall-card">
      <h3>Contribution waterfall</h3>
      <div class="waterfall-stack">
        ${rows.map((row, index) => {
          const width = `${Math.max(8, row.direction === "baseline" ? Math.round(row.end * 100) : Math.round((row.end - row.start) * 100))}%`;
          const left = `${Math.round(row.start * 100)}%`;
          const labelValue = row.label === "Predicted risk"
            ? `${Math.round(result.riskScore * 100)}%`
            : row.label === "Base risk"
              ? `${Math.round(baseline * 100)}%`
              : `${row.value >= 0 ? "+" : ""}${row.value.toFixed(2)}`;
          return `
            <div class="waterfall-row">
              <div class="waterfall-label">
                <span>${escapeHtml(row.label)}</span>
                <span>${escapeHtml(labelValue)}</span>
              </div>
              <div class="waterfall-track">
                <div class="waterfall-segment is-${row.direction}" data-target-width="${width}" data-target-left="${left}" data-delay="${index * 100}"></div>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  if (!REDUCED_MOTION) {
    requestAnimationFrame(() => {
      ui.waterfallChart.querySelectorAll(".waterfall-segment").forEach((segment) => {
        segment.style.transitionDelay = `${segment.dataset.delay || 0}ms`;
        segment.style.left = segment.dataset.targetLeft || "0%";
        segment.style.width = segment.dataset.targetWidth || "0%";
      });
    });
  } else {
    ui.waterfallChart.querySelectorAll(".waterfall-segment").forEach((segment) => {
      segment.style.left = segment.dataset.targetLeft || "0%";
      segment.style.width = segment.dataset.targetWidth || "0%";
    });
  }
}

function updateModeSummary() {
  const modeMeta = MODES[activeMode];
  const activeFields = getActiveFields();
  const fieldCount = activeFields.length;
  const routeLabel = activeMode === "clinical" ? (settings.clinicalPath || MODES.clinical.routeLabel) : (settings.researchPath || MODES.research.routeLabel);
  ui.activeModeLabel.textContent = modeMeta.label;
  ui.activeModeDescription.textContent = modeMeta.intro;
  ui.activeRouteLabel.textContent = routeLabel;
  ui.activeRouteDescription.textContent = activeMode === "clinical"
    ? "Route used for clinically familiar intake fields."
    : "Route used for the current #336 schema-aligned inference path.";
  ui.activeFieldCount.textContent = `${fieldCount} fields`;
  ui.activeFieldDescription.textContent = activeMode === "clinical"
    ? "Clinical adapter uses 14 directly entered fields and maps them into the 23-feature research space for downstream inference."
    : "Research mode exposes all 23 predictors directly for schema-aligned inference and experiment parity.";
  ui.schemaTitle.textContent = modeMeta.title;
  ui.schemaIntro.textContent = modeMeta.intro;
  ui.reviewModeLabel.textContent = modeMeta.label;
  ui.reviewModeHint.textContent = `${settings.useMockPrediction ? "Mock adapter" : "Live adapter"} will submit through ${routeLabel}.`;
}

function fillExample(mode) {
  clearCurrentModeInputs();
  const examples = EXAMPLES[mode];
  const example = examples[exampleCursor[mode] % examples.length];
  exampleCursor[mode] = (exampleCursor[mode] + 1) % examples.length;
  getActiveFields().forEach((field) => {
    const input = document.querySelector(`[name='${field.key}']`);
    if (input) input.value = example.values[field.key] ?? "";
  });

  document.getElementById("caseId").value = example.caseId;
  document.getElementById("patientName").value = example.patientName;
  document.getElementById("clinicalNote").value = example.clinicalNote;
  updatePrintHeader();
  updateExampleButtonLabel();
  return example;
}

function updateExampleButtonLabel() {
  if (!ui.loadExample) return;
  const nextExample = EXAMPLES[activeMode][exampleCursor[activeMode] % EXAMPLES[activeMode].length];
  const toneLabel = nextExample.name.includes("high-risk") ? "Load high-risk example" : "Load lower-risk example";
  ui.loadExample.textContent = toneLabel;
  ui.loadExample.title = toneLabel;
}

function updateReviewPanel(payload = collectModePayload(activeMode)) {
  ui.reviewModeLabel.textContent = MODES[activeMode].label;
  ui.reviewModeHint.textContent = `${settings.useMockPrediction ? "Mock adapter" : "Live adapter"} will use ${activeMode === "clinical" ? settings.clinicalPath : settings.researchPath}.`;
  ui.payloadPreview.textContent = JSON.stringify(buildRequestBody(activeMode, payload, settings), null, 2);
}

function clearCurrentModeInputs() {
  getActiveFields().forEach((field) => {
    const input = document.querySelector(`[name='${field.key}']`);
    if (input) input.value = "";
  });
}

function setRunningState(isRunning) {
  const button = document.getElementById("runPrediction");
  button.disabled = isRunning;
  button.classList.toggle("is-loading", isRunning);
  button.textContent = isRunning ? "Running prediction" : "Run prediction";
  if (isRunning) {
    ui.responseMode.textContent = "Request in progress";
    ui.responseMode.className = "status-chip warning";
    setResponseStages("running");
  }
}

function setResultMessage(message, kind = "info", options = {}) {
  if (typeof kind === "boolean") {
    kind = kind ? "error" : "info";
  }

  const mergedOptions = {
    toast: true,
    persist: true,
    ...options
  };

  if (mergedOptions.persist) {
    ui.resultMessage.textContent = message;
    ui.resultMessage.dataset.status = kind;
  }

  if (mergedOptions.toast) {
    pushToast(message, kind);
  }
}

function pushToast(message, kind = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${kind}`;
  toast.innerHTML = `
    <span class="toast-icon" aria-hidden="true">${getToastIcon(kind)}</span>
    <div class="toast-copy">${escapeHtml(message)}</div>
    <button class="toast-close" type="button" aria-label="Dismiss notification">✕</button>
  `;

  toast.querySelector(".toast-close").addEventListener("click", () => dismissToast(toast));
  ui.toastViewport.appendChild(toast);

  if (!REDUCED_MOTION) {
    requestAnimationFrame(() => toast.classList.add("is-visible"));
  } else {
    toast.classList.add("is-visible");
  }

  while (ui.toastViewport.children.length > 3) {
    dismissToast(ui.toastViewport.firstElementChild, true);
  }

  window.setTimeout(() => dismissToast(toast), 4000);
}

function dismissToast(toast, immediate = false) {
  if (!(toast instanceof HTMLElement) || !toast.isConnected) return;
  if (immediate || REDUCED_MOTION) {
    toast.remove();
    return;
  }

  toast.classList.add("is-leaving");
  window.setTimeout(() => {
    if (toast.isConnected) {
      toast.remove();
    }
  }, 220);
}

function getToastIcon(kind) {
  if (kind === "success") return "✓";
  if (kind === "error") return "!";
  return "i";
}

function animateRiskScoreNumber(targetPercent) {
  if (scoreAnimationFrame) {
    window.cancelAnimationFrame(scoreAnimationFrame);
  }

  if (REDUCED_MOTION) {
    ui.riskScore.textContent = `${targetPercent}%`;
    return;
  }

  const duration = 600;
  const start = performance.now();
  const step = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    ui.riskScore.textContent = `${Math.round(targetPercent * eased)}%`;
    if (progress < 1) {
      scoreAnimationFrame = window.requestAnimationFrame(step);
      return;
    }
    ui.riskScore.textContent = `${targetPercent}%`;
    scoreAnimationFrame = null;
  };

  scoreAnimationFrame = window.requestAnimationFrame(step);
}

function setResultLoading(isLoading, hardReset = false) {
  if (isLoading) {
    ui.resultPanel.classList.add("is-animating");
  }
  RESULT_SKELETON_TARGETS.forEach((target) => {
    target.classList.toggle("skeleton-active", isLoading);
  });

  if (isLoading) {
    RESULT_REVEAL_ITEMS.forEach((item) => item.classList.remove("revealed"));
    return;
  }

  if (REDUCED_MOTION || hardReset) {
    ui.resultPanel.classList.remove("is-animating");
  }
}

function animateGauge(score) {
  const clamped = Math.max(0, Math.min(1, score));
  const offset = GAUGE_CIRCUMFERENCE * (1 - clamped);
  const color = clamped > 0.7 ? "#d75b5b" : clamped >= 0.4 ? "#c78a24" : "#2db88b";

  ui.gaugeProgress.style.stroke = color;

  if (REDUCED_MOTION) {
    ui.gaugeProgress.style.strokeDashoffset = `${offset}`;
    return;
  }

  ui.gaugeProgress.style.strokeDashoffset = `${GAUGE_CIRCUMFERENCE}`;
  requestAnimationFrame(() => {
    ui.gaugeProgress.style.strokeDashoffset = `${offset}`;
  });

  ui.gaugeShell.classList.remove("pulse");
  window.setTimeout(() => {
    ui.gaugeShell.classList.add("pulse");
    window.setTimeout(() => ui.gaugeShell.classList.remove("pulse"), 420);
  }, 800);
}

function triggerResultReveal() {
  if (REDUCED_MOTION) {
    RESULT_REVEAL_ITEMS.forEach((item) => item.classList.add("revealed"));
    ui.resultPanel.classList.remove("is-animating");
    return;
  }

  requestAnimationFrame(() => {
    RESULT_REVEAL_ITEMS.forEach((item) => item.classList.add("revealed"));
  });

  window.setTimeout(() => {
    ui.resultPanel.classList.remove("is-animating");
  }, 760);
}

function setCompletionRing(ring, valueNode, completed, total, isCompact = false) {
  if (!ring || !valueNode) return;

  const safeTotal = Math.max(total, 1);
  const progress = Math.max(0, Math.min(1, completed / safeTotal));
  const circumference = isCompact ? COMPLETION_CIRCUMFERENCE : COMPLETION_CIRCUMFERENCE;
  const offset = circumference * (1 - progress);

  ring.style.stroke = progress >= 1 ? "var(--mint)" : "var(--blue)";
  ring.style.strokeDashoffset = `${offset}`;
  valueNode.textContent = `${completed}/${total}`;
}

function updateHistoryTimestampLabel(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "--:--";
  return date.toLocaleTimeString("zh-TW", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
}

function pushHistoryEntry(entry) {
  predictionHistory.unshift({
    ...entry,
    result: JSON.parse(JSON.stringify(entry.result)),
    inputs: JSON.parse(JSON.stringify(entry.inputs)),
    reportPayload: JSON.parse(JSON.stringify(entry.reportPayload)),
    caseContext: { ...(entry.caseContext || {}) },
    timestampLabel: updateHistoryTimestampLabel(entry.result.timestamp)
  });
  predictionHistory = predictionHistory.slice(0, 5);
  renderHistory();
}

function renderHistory() {
  if (!predictionHistory.length) {
    ui.historyList.innerHTML = `<div class="history-empty">Run a prediction to build the recent session history.</div>`;
    return;
  }

  ui.historyList.innerHTML = predictionHistory.map((entry, index) => {
    const score = Math.round(entry.result.riskScore * 100);
    const scoreClass = entry.result.riskScore >= 0.7 ? "high" : entry.result.riskScore >= 0.4 ? "mid" : "low";
    return `
      <button class="history-item" type="button" data-history-index="${index}">
        <div class="history-item-top">
          <strong class="history-score ${scoreClass}">${score}%</strong>
          <span class="history-time">${escapeHtml(entry.timestampLabel)}</span>
        </div>
        <div class="history-mode">${escapeHtml(MODES[entry.mode].label)}</div>
      </button>
    `;
  }).join("");
}

function clearPredictionHistory() {
  predictionHistory = [];
  renderHistory();
  setResultMessage("Session history cleared.", "info");
}

function loadHistoryEntry(index) {
  const entry = predictionHistory[index];
  if (!entry) return;

  if (activeMode !== entry.mode) {
    activeMode = entry.mode;
    settings.defaultMode = entry.mode;
    persistSettings(settings);
    renderMode(entry.mode);
  }

  document.getElementById("caseId").value = entry.caseContext?.caseId || "CKD-OPS-0001";
  document.getElementById("patientName").value = entry.caseContext?.patientName || "";
  document.getElementById("clinicalNote").value = entry.caseContext?.clinicalNote || "";
  populateInputsForMode(entry.mode, entry.inputs);
  updateCompletion(entry.inputs);
  renderPrediction(entry.result, entry.inputs, entry.mode, settings, { skipHistory: true, skipToast: true });
  setResultMessage("Loaded prediction from session history.", "info");
}

function populateInputsForMode(mode, payload) {
  getFieldsForMode(mode).forEach((field) => {
    const input = document.querySelector(`[name='${field.key}']`);
    if (!input) return;
    const value = payload[field.key];
    input.value = value === null || value === undefined ? "" : String(value);
  });
  refreshValidationState();
}

function ensureFieldFeedback(fieldNode) {
  let feedback = fieldNode.querySelector(".field-feedback");
  if (!feedback) {
    feedback = document.createElement("small");
    feedback.className = "field-feedback";
    fieldNode.appendChild(feedback);
  }
  return feedback;
}

function validateFieldInput(input) {
  const fieldNode = input.closest(".field");
  if (!fieldNode) return;

  fieldNode.classList.remove("field-warning", "field-valid");
  const existingFeedback = fieldNode.querySelector(".field-feedback");
  if (!(input instanceof HTMLInputElement) || input.type !== "number") {
    if (existingFeedback) {
      existingFeedback.textContent = "";
    }
    return;
  }

  const feedback = ensureFieldFeedback(fieldNode);
  feedback.textContent = "";

  const raw = input.value.trim();
  if (!raw) return;

  const numericValue = Number(raw);
  const min = input.min !== "" ? Number(input.min) : null;
  const max = input.max !== "" ? Number(input.max) : null;

  if (Number.isNaN(numericValue)) return;

  if ((min !== null && numericValue < min) || (max !== null && numericValue > max)) {
    fieldNode.classList.add("field-warning");
    feedback.textContent = `Value outside expected range (${min ?? "?"}–${max ?? "?"})`;
    return;
  }

  fieldNode.classList.add("field-valid");
}

function refreshValidationState() {
  ui.formSections.querySelectorAll(".field input, .field select").forEach((input) => {
    validateFieldInput(input);
  });
}

function resetResultPanels() {
  if (scoreAnimationFrame) {
    window.cancelAnimationFrame(scoreAnimationFrame);
    scoreAnimationFrame = null;
  }
  ui.riskScore.textContent = "--";
  ui.riskBand.className = "risk-band risk-neutral";
  ui.riskBand.textContent = "No prediction yet";
  ui.predictionLabel.textContent = "--";
  ui.modelVersion.textContent = "--";
  ui.predictionTimestamp.textContent = "--";
  ui.servingRoute.textContent = "--";
  ui.resultHeadline.textContent = "Prediction not run yet";
  ui.resultSubheadline.textContent = "Submit a request to generate a structured interpretation summary for the active mode.";
  ui.actionHeadline.textContent = "Awaiting prediction";
  ui.actionBody.textContent = "The workspace will propose an immediate action cue after the prediction result arrives.";
  ui.reportHeadline.textContent = "No report prepared";
  ui.reportBody.textContent = "A concise report snapshot will be assembled from the latest response, route, and signal summary.";
  ui.exportReportTitle.textContent = "Prediction report not prepared";
  ui.exportReportMeta.textContent = "Run a prediction to assemble a structured report with summary, guidance, signal explanation, and serving metadata.";
  ui.responseMode.textContent = "Awaiting request";
  ui.responseMode.className = "status-chip neutral";
  ui.gaugeProgress.style.stroke = "var(--mint)";
  ui.gaugeProgress.style.strokeDashoffset = `${GAUGE_CIRCUMFERENCE}`;
  ui.gaugeShell.classList.remove("pulse");
  ui.mockModeBanner.hidden = true;
  ui.calibrationCaveat.hidden = true;
  ui.clinicalNotes.innerHTML = `<div class="note-card neutral-note">Submit a prediction to generate clinical notes.</div>`;
  ui.explanationList.innerHTML = `<div class="explanation-card empty-card">${escapeHtml(EMPTY_ATTRIBUTION_MESSAGE)}</div>`;
  ui.reportSnapshot.innerHTML = `
    <div class="report-row">
      <span>Case</span>
      <strong>Pending</strong>
    </div>
    <div class="report-row">
      <span>Mode</span>
      <strong>Pending</strong>
    </div>
    <div class="report-row">
      <span>Summary</span>
      <strong>No prediction summary available yet.</strong>
    </div>
  `;
  ui.waterfallChart.innerHTML = `<div class="waterfall-empty">No explanation items yet. Run a prediction to build the contribution path.</div>`;
  ui.reportPreview.innerHTML = `<div class="report-preview-empty">No raw report preview yet. Submit a prediction to build the report surface.</div>`;
  ui.formattedReportPreview.innerHTML = `<div class="report-preview-empty">No formatted report preview yet. Submit a prediction to build the report surface.</div>`;
  setPreviewTab("formatted");
  setResultLoading(false, true);
  ui.resultPanel.classList.remove("is-animating");
  latestReportPayload = null;
  setResponseStages("idle");
}

function buildExportFilename(extension) {
  const caseId = (document.getElementById("caseId").value.trim() || "ckd_report").replace(/[^a-zA-Z0-9_-]+/g, "_");
  return `${caseId}_prediction_report.${extension}`;
}

function downloadBlob(content, mimeType, filename) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildReportHtml(report) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${escapeHtml(report.title)}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; color: #10223c; line-height: 1.6; }
    h1 { margin-bottom: 8px; }
    .meta { color: #5f718a; margin-bottom: 24px; }
    .section { margin-top: 24px; padding: 18px; border: 1px solid #d9e3f0; border-radius: 14px; background: #f8fbff; }
    .label { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #3f63d1; font-weight: 700; }
    .value { font-size: 18px; font-weight: 700; margin-top: 6px; }
  </style>
</head>
<body>
  <h1>${escapeHtml(report.title)}</h1>
  <div class="meta">${escapeHtml(report.meta)}</div>
  <div class="section">
    <div class="label">Summary</div>
    <div class="value">${escapeHtml(report.label)} · ${escapeHtml(report.score)}</div>
    <p>${escapeHtml(report.summary)}</p>
  </div>
  <div class="section">
    <div class="label">Clinical guidance</div>
    <div class="value">${escapeHtml(report.guidanceLine)}</div>
    <p>${escapeHtml(report.action)}</p>
  </div>
  <div class="section">
    <div class="label">Report note</div>
    <p>${escapeHtml(report.reportNote)}</p>
  </div>
  <div class="section">
    <div class="label">Top signals</div>
    <p>${escapeHtml(report.signals.join(", ") || "No explanation items returned")}</p>
  </div>
  <div class="section">
    <div class="label">Serving metadata</div>
    <p>Mode: ${escapeHtml(report.mode)}</p>
    <p>Route: ${escapeHtml(report.route)}</p>
    <p>Model version: ${escapeHtml(report.modelVersion)}</p>
    <p>Timestamp: ${escapeHtml(report.timestamp)}</p>
  </div>
</body>
</html>`.trim();
}

function hydrateSettings() {
  ui.apiBaseUrl.value = settings.apiBaseUrl;
  ui.clinicalPath.value = settings.clinicalPath;
  ui.researchPath.value = settings.researchPath;
  ui.requestEnvelope.value = settings.requestEnvelope;
  ui.mockMode.checked = settings.useMockPrediction;
}

function readSettingsFromUI() {
  return {
    apiBaseUrl: ui.apiBaseUrl.value.trim(),
    clinicalPath: ui.clinicalPath.value.trim() || MODES.clinical.routeLabel,
    researchPath: ui.researchPath.value.trim() || MODES.research.routeLabel,
    requestEnvelope: ui.requestEnvelope.value.trim() || "inputs",
    useMockPrediction: ui.mockMode.checked,
    defaultMode: activeMode
  };
}

function persistSettings(current) {
  localStorage.setItem(APP_STORAGE_KEY, JSON.stringify(current));
}

function loadSettings() {
  const raw = localStorage.getItem(APP_STORAGE_KEY);
  if (!raw) {
    return { ...window.CKD_CONFIG };
  }
  try {
    const parsed = JSON.parse(raw);
    const merged = { ...window.CKD_CONFIG, ...parsed };

    if (!merged.apiBaseUrl && window.CKD_CONFIG.apiBaseUrl) {
      merged.apiBaseUrl = window.CKD_CONFIG.apiBaseUrl;
    }
    if (!merged.clinicalPath && window.CKD_CONFIG.clinicalPath) {
      merged.clinicalPath = window.CKD_CONFIG.clinicalPath;
    }
    if (!merged.researchPath && window.CKD_CONFIG.researchPath) {
      merged.researchPath = window.CKD_CONFIG.researchPath;
    }
    if (!merged.requestEnvelope && window.CKD_CONFIG.requestEnvelope) {
      merged.requestEnvelope = window.CKD_CONFIG.requestEnvelope;
    }

    return merged;
  } catch {
    return { ...window.CKD_CONFIG };
  }
}

function updateConnectionBadge() {
  if (settings.useMockPrediction) {
    ui.connectionStatus.textContent = "Mock mode";
    ui.connectionStatus.className = "status-chip warning";
  } else {
    ui.connectionStatus.textContent = "Live endpoint";
    ui.connectionStatus.className = "status-chip live";
  }
}

function setResponseStages(state) {
  [ui.stageCapture, ui.stageRoute, ui.stageResponse].forEach((node) => {
    node.classList.remove("response-step-active", "response-step-live");
  });

  if (state === "idle") {
    ui.stageCapture.classList.add("response-step-active");
    return;
  }

  if (state === "running") {
    ui.stageCapture.classList.add("response-step-live");
    ui.stageRoute.classList.add("response-step-active");
    return;
  }

  if (state === "done") {
    ui.stageCapture.classList.add("response-step-live");
    ui.stageRoute.classList.add("response-step-live");
    ui.stageResponse.classList.add("response-step-active");
  }
}

function updateCompletion(payload = collectModePayload(activeMode)) {
  const completed = Object.values(payload).filter((value) => value !== null && value !== "").length;
  const total = getActiveFields().length;
  const summary = `${completed} / ${total}`;
  ui.reviewCompletion.textContent = summary;
  setCompletionRing(ui.completionProgress, ui.completionValue, completed, total);
  setCompletionRing(ui.brandCompletionProgress, ui.brandCompletionValue, completed, total, true);
  updateReadinessBadge(completed, total);
  updateReviewPanel(payload);
}

function updateReadinessBadge(completed, total) {
  ui.readinessBadge.classList.remove("is-empty", "is-partial", "is-complete");
  ui.readinessBadge.classList.add(
    completed === 0 ? "is-empty" : completed >= total ? "is-complete" : "is-partial"
  );
  ui.readinessIcon.textContent = completed === 0 ? "○" : completed >= total ? "✓" : "◐";
  const label = `${completed} of ${total} fields completed`;
  ui.readinessBadge.title = label;
  ui.readinessBadge.setAttribute("aria-label", label);
}

function updatePrintHeader(timestamp = new Date().toISOString()) {
  const caseId = document.getElementById("caseId").value.trim() || "CKD-CASE";
  const formattedDate = formatTimestamp(timestamp);
  document.body.setAttribute("data-print-header", `CKD Risk Prediction Report — ${caseId} — ${formattedDate}`);
}

function animateBarTargets(root) {
  const targets = root.querySelectorAll("[data-target-width]");
  if (!targets.length) return;

  if (REDUCED_MOTION) {
    targets.forEach((bar) => {
      bar.style.width = bar.dataset.targetWidth;
      if (bar.dataset.targetLeft) {
        bar.style.left = bar.dataset.targetLeft;
      }
    });
    return;
  }

  requestAnimationFrame(() => {
    targets.forEach((bar) => {
      bar.style.width = bar.dataset.targetWidth;
      if (bar.dataset.targetLeft) {
        bar.style.left = bar.dataset.targetLeft;
      }
    });
  });
}

function clampScore(value) {
  return Math.max(0.02, Math.min(0.98, Number(value.toFixed(3))));
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-TW", {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"
  });
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
