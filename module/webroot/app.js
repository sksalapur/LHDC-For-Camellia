const API_BASES = ["", "http://127.0.0.1:9092"];
const LIVE_FILE = "/data/misc/bluetooth/lhdc_live.json";

function showToast(msg) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
}

function ksuExec(cmd) {
  const api = (window.ksu && typeof window.ksu.exec === "function")
    ? window.ksu
    : (typeof ksu !== "undefined" && typeof ksu.exec === "function" ? ksu : null);
  if (!api) return Promise.resolve("");
  try {
    const out = api.exec(cmd);
    if (out && typeof out.then === "function") return out;
    return Promise.resolve(String(out || ""));
  } catch (_) {
    return Promise.resolve("");
  }
}

async function apiGet(path) {
  for (const base of API_BASES) {
    try {
      const res = await fetch(`${base}${path}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch (_) {}
  }
  return null;
}

async function fetchLiveStatus() {
  const data = await apiGet("/api/live");
  if (data) return data;

  // Lightweight APatch WebView ksu.exec fallback (zero dumpsys/logcat)
  const raw = await ksuExec(
    `BR=$(getprop persist.bluetooth.lhdc_bitrate); MTU=$(getprop persist.bluetooth.lhdc_mtu); ` +
    `ABR=$(getprop persist.vendor.bluetooth.lhdc_abr); LIVE=""; ` +
    `[ -r "${LIVE_FILE}" ] && IFS= read -r LIVE < "${LIVE_FILE}"; ` +
    `printf '%s\t%s\t%s\t%s' "\${BR:-500}" "\${MTU:-660}" "\${ABR:-true}" "$LIVE"`
  );
  if (!raw) return null;
  const parts = raw.split("\t");
  const cfgBr = parseInt(parts[0], 10) || 500;
  const cfgMtu = parseInt(parts[1], 10) || 660;
  const cfgAbr = parts[2] !== "false" && parts[2] !== "0";
  let parsed = {};
  try {
    if (parts[3] && parts[3].trim().startsWith("{")) parsed = JSON.parse(parts[3].trim());
  } catch (_) {}
  return {
    active: Boolean(parsed.active),
    codec: parsed.codec || "LHDC V5",
    negotiated_bitrate_kbps: parsed.negotiated_bitrate_kbps || 0,
    target_bitrate_kbps: parsed.target_bitrate_kbps || cfgBr,
    negotiated_mtu: parsed.negotiated_mtu || cfgMtu,
    sample_rate: parsed.sample_rate || 48000,
    bits_per_sample: parsed.bits_per_sample || 24,
    abr_enabled: parsed.abr_enabled !== undefined ? Boolean(parsed.abr_enabled) : cfgAbr,
    configured_abr_enabled: cfgAbr,
    abr_stepped_down: Boolean(parsed.abr_stepped_down),
    queue_len: parsed.queue_len || 0,
    configured_bitrate_kbps: cfgBr,
    configured_mtu: cfgMtu
  };
}

let currentAbrEnabled = true;

function renderStatus(d) {
  if (!d) return;

  const isConnected = Boolean(d.active);
  const ageSec = d.updated_at ? (Math.floor(Date.now() / 1000) - Number(d.updated_at)) : 9999;
  const isStreaming = isConnected && ageSec <= 5;
  const cfgBr = d.configured_bitrate_kbps || d.target_bitrate_kbps || 500;
  const negBr = (isStreaming && d.negotiated_bitrate_kbps > 0) ? d.negotiated_bitrate_kbps : cfgBr;
  const negMtu = (isConnected && d.negotiated_mtu > 0) ? d.negotiated_mtu : (d.configured_mtu || 660);
  const cfgAbr = (d.configured_abr_enabled !== undefined ? d.configured_abr_enabled : d.abr_enabled) !== false;
  const liveAbr = isStreaming ? (d.abr_enabled !== false) : cfgAbr;
  currentAbrEnabled = cfgAbr;

  const streamPill = document.getElementById("stream-pill");
  if (isStreaming) {
    streamPill.textContent = "STREAMING";
    streamPill.className = "badge badge-green";
  } else if (isConnected) {
    streamPill.textContent = "IDLE / PAUSED";
    streamPill.className = "badge badge-cyan";
  } else {
    streamPill.textContent = "STANDBY";
    streamPill.className = "badge badge-dim";
  }

  const abrPill = document.getElementById("abr-pill");
  if (!cfgAbr) {
    abrPill.textContent = "ABR OFF (LOCKED)";
    abrPill.className = "badge badge-dim";
  } else if (isStreaming && d.abr_stepped_down) {
    abrPill.textContent = "ABR STEPPED DOWN";
    abrPill.className = "badge badge-amber";
  } else if (liveAbr) {
    abrPill.textContent = "ABR ACTIVE";
    abrPill.className = "badge badge-green";
  } else {
    abrPill.textContent = "ABR ENABLING";
    abrPill.className = "badge badge-cyan";
  }

  const abrSwitch = document.getElementById("abr-switch");
  if (abrSwitch) abrSwitch.checked = cfgAbr;
  const abrDesc = document.getElementById("abr-toggle-desc");
  if (abrDesc) {
    abrDesc.textContent = cfgAbr
      ? "On: Dynamically steps down on RF congestion and auto-recovers."
      : "Off: Strictly locked to your selected bitrate without auto-throttling.";
  }

  document.getElementById("val-neg-br").textContent = isStreaming ? `${negBr} kbps` : "-- kbps";
  document.getElementById("sub-target-br").textContent = isStreaming
    ? `${cfgAbr ? "Ceiling" : "Locked"}: ${cfgBr} kbps`
    : `${cfgAbr ? "Target" : "Locked"}: ${cfgBr} kbps (Play audio)`;

  document.getElementById("val-neg-mtu").textContent = String(negMtu);
  document.getElementById("sub-mtu-mode").textContent =
    (isStreaming ? negBr : cfgBr) <= 500 && negMtu >= 660 ? "2-Frame Batched" : "Single-Frame Unbatched";

  const khz = ((d.sample_rate || 48000) / 1000).toFixed(0);
  document.getElementById("val-format").textContent = `${khz}k / ${d.bits_per_sample || 24}b`;
  document.getElementById("sub-codec").textContent = d.codec || "LHDC V5";

  const q = Number(d.queue_len || 0);
  document.getElementById("val-queue").textContent = `${q} / 80`;
  document.getElementById("sub-abr-state").textContent = !cfgAbr
    ? "Fixed Lock"
    : (isStreaming ? (d.abr_stepped_down ? "Congestion Step-Down" : "Healthy Margin") : "Waiting Audio");

  document.querySelectorAll(".preset-card").forEach((btn) => {
    const val = Number(btn.getAttribute("data-br"));
    btn.classList.toggle("active", val === Number(cfgBr));
  });
}

async function applyBitrate(kbps) {
  const res = await apiGet(`/api/set?bitrate=${kbps}`);
  if (!res || !res.success) {
    await ksuExec(
      `RP=/data/adb/ap/bin/resetprop; [ -x "$RP" ] || RP=resetprop; ` +
      `$RP -n persist.bluetooth.lhdc_bitrate ${kbps}; ` +
      `$RP -n persist.bluetooth.lhdc_mtu 660; ` +
      `printf '%s\\n' "${kbps}" > /data/adb/modules/lhdc_codec_old/target_bitrate`
    );
  }
  const abrNow = (res && res.abr_enabled !== undefined) ? res.abr_enabled : currentAbrEnabled;
  showToast(`Bitrate set to ${kbps} kbps @ 660 MTU (${abrNow ? "ABR" : "Fixed"})`);
  setTimeout(refresh, 180);
}

async function toggleAbr(enabled) {
  const flag = enabled ? "true" : "false";
  currentAbrEnabled = Boolean(enabled);
  const res = await apiGet(`/api/abr?enabled=${flag}`);
  if (!res || !res.success) {
    await ksuExec(
      `RP=/data/adb/ap/bin/resetprop; [ -x "$RP" ] || RP=resetprop; ` +
      `$RP -n persist.vendor.bluetooth.lhdc_abr ${flag}; ` +
      `$RP -n vendor.bluetooth.lhdc.abr ${flag}; ` +
      `printf '%s\\n' "${flag}" > /data/adb/modules/lhdc_codec_old/target_abr`
    );
  }
  showToast(enabled ? "Adaptive Bitrate (ABR) Enabled" : "ABR Disabled — Fixed Bitrate Locked");
  setTimeout(refresh, 180);
}

function copyEndpoint() {
  const url = "http://127.0.0.1:9092/api/live";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(() => showToast("Copied endpoint URL")).catch(() => showToast(url));
  } else {
    showToast(url);
  }
}

async function refresh() {
  const status = await fetchLiveStatus();
  renderStatus(status);
}

document.addEventListener("DOMContentLoaded", () => {
  refresh();
  setInterval(refresh, 1000);
});
