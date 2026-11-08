// ═══════════════════════════════════════════════════════════════════
// LHDC Audiophile Tuner — Client Application Logic
// Supports native APatch / KernelSU WebView bridge & HTTP fallback
// ═══════════════════════════════════════════════════════════════════

const COMBINATIONS = [
  // 500k Series
  {
    id: "combo-500-600",
    bitrate: "500",
    mtu: "600",
    queue: "18",
    frameSize: "314 Bytes",
    batching: "1 frame / packet (0 Batch)",
    badge: "RECOMMENDED STABLE",
    badgeType: "badge-green",
    desc: "Universal standard. Zero packet drops, zero diaphragm pops across all ANC modes, native 96kHz 24-bit audio."
  },
  {
    id: "combo-500-500",
    bitrate: "500",
    mtu: "500",
    queue: "18",
    frameSize: "314 Bytes",
    batching: "1 frame / packet (0 Batch)",
    badge: "LOW LATENCY",
    badgeType: "badge-cyan",
    desc: "Clamped minimum MTU. Identical single-frame packet to MTU 600 with lowest L2CAP buffer footprint."
  },
  {
    id: "combo-500-660",
    bitrate: "500",
    mtu: "660",
    queue: "18",
    frameSize: "314 Bytes",
    batching: "2 frames / packet (Batching Active)",
    badge: "BATCHING TEST",
    badgeType: "badge-amber",
    desc: "Dual-frame aggregation: 2 x 314 = 628 bytes fits within 660 MTU. Tests radio transmission grouping."
  },

  // 900k Series
  {
    id: "combo-900-600",
    bitrate: "900",
    mtu: "600",
    queue: "18",
    frameSize: "564 Bytes",
    batching: "1 frame / packet (0 Batch)",
    badge: "AUDIOPHILE STANDARD",
    badgeType: "badge-cyan",
    desc: "Highest single-frame unbatched rate. Pristine lossless 96kHz playback, best experienced in Normal mode."
  },
  {
    id: "combo-900-660",
    bitrate: "900",
    mtu: "660",
    queue: "18",
    frameSize: "564 Bytes",
    batching: "1 frame / packet (0 Batch)",
    badge: "HIGH HEADROOM",
    badgeType: "badge-cyan",
    desc: "Single-frame 564-byte payload with 96 bytes of MTU buffer slack. Zero batching."
  },
  {
    id: "combo-900-500",
    bitrate: "900",
    mtu: "500",
    queue: "18",
    frameSize: "564 Bytes",
    batching: "OVERFLOW (564 > 500)",
    badge: "⚠️ OVERFLOW RISK",
    badgeType: "badge-red",
    desc: "Stress test: Frame size exceeds MTU. Tests driver handling of underruns and packet truncation."
  },

  // 1000k Series
  {
    id: "combo-1000-660",
    bitrate: "1000",
    mtu: "660",
    queue: "22",
    frameSize: "626 Bytes",
    batching: "1 frame / packet (0 Batch)",
    badge: "1.0 MBPS BLEEDING EDGE",
    badgeType: "badge-amber",
    desc: "Maximum Savitech 1.0 Mbps tier. Single frame fits inside MTU 660. Tests hardware radio limits."
  },
  {
    id: "combo-1000-600",
    bitrate: "1000",
    mtu: "600",
    queue: "22",
    frameSize: "626 Bytes",
    batching: "OVERFLOW (626 > 600)",
    badge: "⚠️ OVERFLOW RISK",
    badgeType: "badge-red",
    desc: "Stress test: 626B frame exceeds 600 MTU by 26 bytes. Tests fallback clamping in encoder."
  },
  {
    id: "combo-1000-500",
    bitrate: "1000",
    mtu: "500",
    queue: "22",
    frameSize: "626 Bytes",
    batching: "OVERFLOW (626 > 500)",
    badge: "⚠️ OVERFLOW RISK",
    badgeType: "badge-red",
    desc: "Stress test: 626B frame exceeds 500 MTU by 126 bytes. High packet drop expected."
  }
];

let state = {
  currentBitrate: "500",
  currentMtu: "600",
  currentQueue: "18",
  currentMode: "NORMAL",
  customBitrate: "500",
  customMtu: "600",
  customQueue: "18"
};

// ── Root Command Dispatcher (APatch ksu.exec & HTTP Fallback) ──────
async function runCommand(cmd) {
  if (window.ksu && typeof window.ksu.exec === "function") {
    return window.ksu.exec(cmd);
  }
  if (typeof ksu !== "undefined" && typeof ksu.exec === "function") {
    return ksu.exec(cmd);
  }
  try {
    const res = await fetch(`/api/exec?cmd=${encodeURIComponent(cmd)}`);
    return await res.text();
  } catch (e) {
    try {
      const res2 = await fetch(`http://127.0.0.1:9092/api/exec?cmd=${encodeURIComponent(cmd)}`);
      return await res2.text();
    } catch (_e) {}
  }
  return "";
}

// ── API Fetch Helpers ──────────────────────────────────────────────
async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) return await res.json();
  } catch (e) {
    try {
      const res2 = await fetch("http://127.0.0.1:9092/api/status");
      if (res2.ok) return await res2.json();
    } catch (_e) {}
  }

  // Fallback to ksu.exec directly if HTTP server unavailable
  try {
    const br = (await runCommand("/data/adb/apd resetprop persist.bluetooth.lhdc_bitrate")).trim() || "500";
    const mtu = (await runCommand("/data/adb/apd resetprop persist.bluetooth.lhdc_mtu")).trim() || "600";
    const q = (await runCommand("/data/adb/apd resetprop persist.bluetooth.lhdc_max_queue")).trim() || "18";
    return { bitrate: br, mtu: mtu, max_queue: q, anc_mode: "NORMAL", battery_left: 80, battery_right: 80, battery_case: 0 };
  } catch (_e) {
    return null;
  }
}

async function applySettings(bitrate, mtu, maxQueue, restartBt) {
  try {
    const url = `/api/set?bitrate=${bitrate}&mtu=${mtu}&max_queue=${maxQueue}&restart_bt=${restartBt}`;
    const res = await fetch(url);
    if (res.ok) return await res.json();
  } catch (e) {
    try {
      const url2 = `http://127.0.0.1:9092/api/set?bitrate=${bitrate}&mtu=${mtu}&max_queue=${maxQueue}&restart_bt=${restartBt}`;
      const res2 = await fetch(url2);
      if (res2.ok) return await res2.json();
    } catch (_e) {}
  }

  // Fallback via shell execution
  await runCommand(`/data/adb/apd resetprop -n persist.bluetooth.lhdc_bitrate ${bitrate}`);
  await runCommand(`/data/adb/apd resetprop -n persist.bluetooth.lhdc_mtu ${mtu}`);
  await runCommand(`/data/adb/apd resetprop -n persist.bluetooth.lhdc_max_queue ${maxQueue}`);
  if (restartBt) {
    await runCommand("pkill -f com.android.bluetooth");
  }
  return { success: true };
}

// ── Toast Notification ─────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2800);
}

// ── UI Rendering ───────────────────────────────────────────────────
function renderCombinations() {
  const container = document.getElementById("combos-container");
  container.innerHTML = "";

  COMBINATIONS.forEach(c => {
    const isActive = (state.currentBitrate === c.bitrate && state.currentMtu === c.mtu);
    const card = document.createElement("div");
    card.className = `combo-card ${isActive ? "active-combo" : ""}`;
    card.id = c.id;

    card.innerHTML = `
      <div class="combo-header">
        <div class="combo-title">
          <span>${c.bitrate} kbps</span>
          <span style="color:var(--text-dim);font-weight:400;">@</span>
          <span>MTU ${c.mtu}</span>
        </div>
        <span class="badge ${c.badgeType}">${c.badge}</span>
      </div>
      <div class="combo-details">
        <span>Frame: ${c.frameSize}</span>
        <span>•</span>
        <span>${c.batching}</span>
      </div>
      <div class="combo-desc">${c.desc}</div>
      <div class="combo-actions">
        <button class="btn-apply-combo" onclick="onApplyCombo('${c.bitrate}', '${c.mtu}', '${c.queue}', false)">Apply Live</button>
        <button class="btn-apply-restart" onclick="onApplyCombo('${c.bitrate}', '${c.mtu}', '${c.queue}', true)">Apply & Restart BT</button>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateTelemetryUI(data) {
  if (!data) return;

  state.currentBitrate = data.bitrate || "500";
  state.currentMtu = data.mtu || "600";
  state.currentQueue = data.max_queue || "18";
  state.currentMode = (data.anc_mode || "NORMAL").toUpperCase();

  document.getElementById("telem-bitrate").textContent = `${state.currentBitrate}k`;
  document.getElementById("telem-mtu").textContent = state.currentMtu;
  
  const modeEl = document.getElementById("telem-mode");
  modeEl.textContent = state.currentMode;
  if (state.currentMode === "NORMAL") modeEl.style.color = "var(--accent-green)";
  else if (state.currentMode === "ANC") modeEl.style.color = "var(--accent-amber)";
  else modeEl.style.color = "var(--accent-cyan)";

  // Battery
  document.getElementById("telem-batt-l").textContent = data.battery_left > 0 ? `${data.battery_left}%` : "--";
  document.getElementById("telem-batt-r").textContent = data.battery_right > 0 ? `${data.battery_right}%` : "--";
  document.getElementById("telem-batt-c").textContent = data.battery_case > 0 ? `${data.battery_case}%` : "--";

  // ANC mode buttons
  document.querySelectorAll(".btn-anc").forEach(b => b.classList.remove("active"));
  if (state.currentMode === "NORMAL") document.getElementById("mode-normal").classList.add("active");
  else if (state.currentMode === "ANC") document.getElementById("mode-anc").classList.add("active");
  else if (state.currentMode === "TRANSPARENCY") document.getElementById("mode-transparency").classList.add("active");

  // Highlight active combination card
  renderCombinations();
}

async function refreshTelemetry() {
  const data = await fetchStatus();
  updateTelemetryUI(data);
  fetchLogs();
}

async function fetchLogs() {
  try {
    let text = "";
    try {
      const res = await fetch("/api/logcat");
      if (res.ok) text = await res.text();
    } catch (_e) {
      const res2 = await fetch("http://127.0.0.1:9092/api/logcat");
      if (res2.ok) text = await res2.text();
    }

    if (!text) {
      text = await runCommand("logcat -d -t 25 -s LHDC_V5_SHIM:V");
    }

    if (text) {
      const view = document.getElementById("terminal-view");
      const lines = text.trim().split("\n");
      const formatted = lines.map(line => {
        let cls = "";
        if (line.includes("congested") || line.includes("W LHDC")) cls = "warn";
        else if (line.includes("clean") || line.includes("healthy")) cls = "clean";
        return `<div class="log-entry ${cls}">${escapeHtml(line)}</div>`;
      }).join("");
      view.innerHTML = formatted || "Awaiting frame encoding...";
      view.scrollTop = view.scrollHeight;
    }
  } catch (_e) {}
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ── Action Handlers ────────────────────────────────────────────────
async function onApplyCombo(bitrate, mtu, queue, restartBt) {
  showToast(`Applying ${bitrate} kbps @ MTU ${mtu}...`);
  await applySettings(bitrate, mtu, queue, restartBt);
  if (restartBt) {
    showToast(`Applied ${bitrate}k @ MTU ${mtu} • Bluetooth restarting...`);
  } else {
    showToast(`Live switched to ${bitrate} kbps @ MTU ${mtu}!`);
  }
  setTimeout(refreshTelemetry, restartBt ? 2500 : 600);
}

async function setAncMode(mode) {
  showToast(`Switching ANC mode to ${mode}...`);
  try {
    await fetch(`/api/set_anc?mode=${mode}`);
  } catch (_e) {
    try {
      await fetch(`http://127.0.0.1:9092/api/set_anc?mode=${mode}`);
    } catch (_e2) {
      await runCommand(`am broadcast -a com.music.bypass.ACTION_SET_ANC_MODE -p com.music.bypass --es extra_mode ${mode}`);
    }
  }
  setTimeout(refreshTelemetry, 500);
}

async function applyCustom(restartBt) {
  const br = state.customBitrate;
  const mtu = state.customMtu;
  const q = state.customQueue;

  showToast(`Applying Custom: ${br}k @ MTU ${mtu} (Queue: ${q})...`);
  await applySettings(br, mtu, q, restartBt);
  if (restartBt) {
    showToast(`Custom applied • Bluetooth restarting...`);
  } else {
    showToast(`Custom live applied!`);
  }
  setTimeout(refreshTelemetry, restartBt ? 2500 : 600);
}

// ── Segmented Control Wire-up ──────────────────────────────────────
function setupSegmented(containerId, labelId, suffix, onSelect) {
  const container = document.getElementById(containerId);
  const btns = container.querySelectorAll(".seg-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const val = btn.getAttribute("data-val");
      document.getElementById(labelId).textContent = `${val} ${suffix}`;
      onSelect(val);
    });
  });
}

// ── Initialization ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  renderCombinations();

  setupSegmented("seg-bitrate", "lbl-custom-br", "kbps", val => state.customBitrate = val);
  setupSegmented("seg-mtu", "lbl-custom-mtu", "", val => state.customMtu = val);
  setupSegmented("seg-queue", "lbl-custom-q", "Packets", val => state.customQueue = val);

  document.getElementById("btn-refresh").addEventListener("click", () => {
    showToast("Refreshing live telemetry...");
    refreshTelemetry();
  });

  document.getElementById("btn-clear-logs").addEventListener("click", () => {
    document.getElementById("terminal-view").innerHTML = "Logs cleared.";
  });

  refreshTelemetry();
  setInterval(refreshTelemetry, 2500);
});
