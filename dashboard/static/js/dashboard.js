/* ==========================================================================
   Remote Board Monitoring — Dashboard Logic
   ==========================================================================
   Sections:
     1. Configuration (thresholds, chart settings)
    2. Data-handling layer (telemetry store and backend polling)
     3. Status / severity detection
     4. Chart rendering
     5. Live value + summary card rendering
     6. Alerts table
     7. CSV export
     8. Bootstrap
   ========================================================================== */

(() => {
  "use strict";

  /* ------------------------------------------------------------------ *
   * 1. CONFIGURATION
   *
   * Single source of truth for thresholds. Referenced everywhere else —
   * never hard-code a threshold number outside this object.
   * ------------------------------------------------------------------ */

  const thresholds = {
    temperature: {
      warning: 55,
      critical: 60,
    },
    pressure: {
      warningHigh: 1040,
      criticalHigh: 1050,
    },
    imu: {
      warning: 12 / 9.81,
      critical: 15 / 9.81,
    },
  };

  const CONFIG = {
    deviceId: "NODE-001",
    maxHistoryPoints: 40,     // points kept per chart / stat window
    maxAlerts: 25,            // rows kept in the alerts table
    updateIntervalMs: 2000,
    apiBaseUrl: "",
  };

  /* ------------------------------------------------------------------ *
   * 2. DATA-HANDLING LAYER
   *
   * Everything downstream (charts, cards, alerts) consumes telemetry
   * only through `store` and `onTelemetry`. This is the seam to swap
   * mock data for a real backend without touching the rest of the UI.
   * ------------------------------------------------------------------ */

  const store = {
    history: [],           // array of telemetry frames, oldest first
    listeners: [],
    lastId: 0,
  };

  function onTelemetry(callback) {
    store.listeners.push(callback);
  }

  function pushTelemetry(frame) {
    store.history.push(frame);
    store.lastId = Math.max(store.lastId, frame.id || 0);
    if (store.history.length > CONFIG.maxHistoryPoints) {
      store.history.shift();
    }
    store.listeners.forEach((cb) => cb(frame, store.history));
  }

  /**
   * Expected telemetry frame shape (matches the backend contract):
   * {
   *   device_id: "NODE-001",
   *   timestamp: "2026-09-25T10:42:18",
   *   temperature: 42.6,
   *   pressure: 1012.4,
   *   imu: {
   *     accel_x, accel_y, accel_z,
   *     gyro_x, gyro_y, gyro_z
   *   }
   * }
   */

  function normalizeDatabaseRow(row) {
    const accelerationInG = (value) => Number.isFinite(value) ? value / 9.81 : null;

    return {
      id: row.id,
      device_id: CONFIG.deviceId,
      timestamp: row.timestamp,
      temperature: row.temperature,
      pressure: row.pressure,
      imu: {
        accel_x: accelerationInG(row.accel_x),
        accel_y: accelerationInG(row.accel_y),
        accel_z: accelerationInG(row.accel_z),
        gyro_x: row.gyro_x,
        gyro_y: row.gyro_y,
        gyro_z: row.gyro_z,
      },
      status: {
        temperature: row.temperature_status?.toLowerCase(),
        pressure: row.pressure_status?.toLowerCase(),
        imu: row.imu_status?.toLowerCase(),
      },
    };
  }

  async function refreshTelemetry() {
    try {
      const response = await fetch(`${CONFIG.apiBaseUrl}/telemetry?limit=${CONFIG.maxHistoryPoints}`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`Telemetry endpoint returned ${response.status}`);

      const payload = await response.json();
      const frames = payload.telemetry.slice().reverse().map(normalizeDatabaseRow);
      if (store.history.length === 0) {
        store.history = frames;
        if (frames.length) {
          store.lastId = frames[frames.length - 1].id;
          store.listeners.forEach((callback) => callback(frames[frames.length - 1], store.history));
        }
      } else {
        frames.filter((frame) => frame.id > store.lastId).forEach(pushTelemetry);
      }

      setConnectionState("online");
    } catch (error) {
      setConnectionState("offline");
    }
  }

  let pollingTimer = null;

  function startBackendPolling() {
    refreshTelemetry();
    pollingTimer = setInterval(refreshTelemetry, CONFIG.updateIntervalMs);
  }

  function stopBackendPolling() {
    if (pollingTimer) clearInterval(pollingTimer);
  }

  /* ------------------------------------------------------------------ *
   * 3. STATUS / SEVERITY DETECTION
   * ------------------------------------------------------------------ */

  function imuRms(imu) {
    if (!imu || ![imu.accel_x, imu.accel_y, imu.accel_z].every(Number.isFinite)) return NaN;
    return Math.sqrt(imu.accel_x ** 2 + imu.accel_y ** 2 + imu.accel_z ** 2);
  }

  function temperatureStatus(value) {
    if (!Number.isFinite(value)) return "sensor_failure";
    if (value > thresholds.temperature.critical) return "critical";
    if (value > thresholds.temperature.warning) return "warning";
    return "normal";
  }

  function pressureStatus(value) {
    if (!Number.isFinite(value)) return "sensor_failure";
    if (value > thresholds.pressure.criticalHigh) return "critical";
    if (value > thresholds.pressure.warningHigh) return "warning";
    return "normal";
  }

  function imuStatus(imu) {
    if (!imu || ![imu.accel_x, imu.accel_y, imu.accel_z].every(Number.isFinite)) return "sensor_failure";
    const maximumAcceleration = Math.max(Math.abs(imu.accel_x), Math.abs(imu.accel_y), Math.abs(imu.accel_z));
    if (maximumAcceleration > thresholds.imu.critical) return "critical";
    if (maximumAcceleration > thresholds.imu.warning) return "warning";
    return "normal";
  }

  function statusFor(frame, sensor, fallback) {
    return frame.status?.[sensor] || fallback();
  }

  function formatNumber(value, decimals) {
    return Number.isFinite(value) ? value.toFixed(decimals) : "--";
  }

  function seriesValue(frame, key) {
    return key.startsWith("accel_") ? frame.imu?.[key] : frame[key];
  }

  /* ------------------------------------------------------------------ *
   * 4. CHART RENDERING
   *
  * Uses native Canvas; no external chart library is required.
   * ------------------------------------------------------------------ */

  const charts = {};

  function initCharts() {
    charts.temperature = createCanvasChart("temperatureChart", {
      title: "Temperature",
      unit: "°C",
      series: [{ key: "temperature", label: "Temperature", className: "temp" }],
      warning: thresholds.temperature.warning,
      critical: thresholds.temperature.critical,
      warningDirection: "high",
    });

    charts.pressure = createCanvasChart("pressureChart", {
      title: "Barometer",
      unit: "hPa",
      series: [{ key: "pressure", label: "Pressure", className: "pressure" }],
      warning: thresholds.pressure.warningHigh,
      critical: thresholds.pressure.criticalHigh,
      warningDirection: "high",
    });

    charts.imu = createCanvasChart("imuChart", {
      title: "IMU Acceleration",
      unit: "g",
      series: [
        { key: "accel_x", label: "X", className: "imu-x" },
        { key: "accel_y", label: "Y", className: "imu-y" },
        { key: "accel_z", label: "Z", className: "imu-z" },
      ],
    });
  }

  function createCanvasChart(id, config) {
    const canvas = document.getElementById(id);
    const wrap = canvas?.parentElement;
    if (!canvas || !wrap) return null;

    const dpr = window.devicePixelRatio || 1;

    function resize() {
      const width = Math.max(280, wrap.clientWidth);
      const height = Math.max(150, wrap.clientHeight);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    }

    resize();
    window.addEventListener("resize", resize);

    return { canvas, config, dpr };
  }

  function drawAllCharts(history) {
    drawCanvasChart(charts.temperature, history);
    drawCanvasChart(charts.pressure, history);
    drawCanvasChart(charts.imu, history);
  }

  function drawCanvasChart(chart, history) {
    if (!chart || !history.length) return;

    const { canvas, config, dpr } = chart;
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const pad = { top: 12, right: 14, bottom: 28, left: 42 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    const values = [];
    config.series.forEach((series) => {
      history.forEach((frame) => {
        const value = seriesValue(frame, series.key);

        if (Number.isFinite(value)) values.push(value);
      });
    });

    if (Number.isFinite(config.warning)) values.push(config.warning);
    if (Number.isFinite(config.critical)) values.push(config.critical);

    let min = Math.min(...values);
    let max = Math.max(...values);

    if (config.warningDirection === "low") {
      min = Math.min(min, config.critical, config.warning);
      max = Math.max(max, ...values);
    }

    if (!values.length) {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "#8a93a3";
      ctx.font = "12px Segoe UI, Arial";
      ctx.fillText("No sensor readings", 12, 24);
      return;
    }

    const range = Math.max(max - min, 1);
    min -= range * 0.08;
    max += range * 0.08;

    // Grid
    ctx.strokeStyle = "#eef1f5";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#8a93a3";
    ctx.font = "10px Segoe UI, Arial";

    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (plotH * i) / 4;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();

      const value = max - ((max - min) * i) / 4;
      ctx.fillText(formatChartNumber(value), 4, y + 3);
    }

    // Threshold lines
    if (Number.isFinite(config.warning)) {
      drawThreshold(ctx, config.warning, min, max, pad, plotW, plotH, "#b7791f", "Warning");
    }
    if (Number.isFinite(config.critical)) {
      drawThreshold(ctx, config.critical, min, max, pad, plotW, plotH, "#c0322a", "Critical");
    }

    // Data series
    const seriesColors = ["#2563eb", "#7c3aed", "#0891b2"];

    config.series.forEach((series, seriesIndex) => {
      const points = history.map((frame, index) => {
        const value = seriesValue(frame, series.key);
        if (!Number.isFinite(value)) return null;

        const x = pad.left + (history.length === 1 ? plotW / 2 : (plotW * index) / (history.length - 1));
        const y = pad.top + ((max - value) / (max - min)) * plotH;
        return { x, y };
      });

      ctx.strokeStyle = seriesColors[seriesIndex % seriesColors.length];
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.beginPath();

      let drawing = false;
      points.forEach((point) => {
        if (!point) {
          drawing = false;
        } else if (drawing) {
          ctx.lineTo(point.x, point.y);
        } else {
          ctx.moveTo(point.x, point.y);
          drawing = true;
        }
      });

      ctx.stroke();
    });

    // X-axis labels
    ctx.fillStyle = "#8a93a3";
    ctx.font = "10px Segoe UI, Arial";

    const labelCount = Math.min(5, history.length);
    for (let i = 0; i < labelCount; i++) {
      const index = Math.round((history.length - 1) * (i / Math.max(labelCount - 1, 1)));
      const x = pad.left + (plotW * index) / Math.max(history.length - 1, 1);
      ctx.fillText(formatTime(history[index].timestamp), x - 18, height - 8);
    }

    // Legend
    let legendX = pad.left;
    const legendY = 8;
    config.series.forEach((series, index) => {
      ctx.fillStyle = seriesColors[index % seriesColors.length];
      ctx.fillRect(legendX, legendY, 9, 2);
      ctx.fillStyle = "#5b6577";
      ctx.fillText(series.label, legendX + 13, legendY + 4);
      legendX += 50;
    });
  }

  function drawThreshold(ctx, value, min, max, pad, plotW, plotH, color, label) {
    if (value < min || value > max) return;
    const y = pad.top + ((max - value) / (max - min)) * plotH;

    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(pad.left + plotW, y);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = color;
    ctx.font = "9px Segoe UI, Arial";
    ctx.fillText(label, pad.left + 4, y - 4);
  }

  function formatChartNumber(value) {
    if (Math.abs(value) >= 100) return value.toFixed(0);
    if (Math.abs(value) >= 10) return value.toFixed(1);
    return value.toFixed(2);
  }

  function updateCharts(history) {
    drawAllCharts(history);
  }

  /* ------------------------------------------------------------------ *
   * 5. LIVE VALUE + SUMMARY CARD RENDERING
   * ------------------------------------------------------------------ */

  function stats(values) {
    values = values.filter(Number.isFinite);
    if (!values.length) return { min: NaN, max: NaN, avg: NaN };
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    return { min, max, avg };
  }

  function setStatusBadge(el, status) {
    el.dataset.status = status;
    el.textContent = status.split("_").map(capitalize).join(" ");
  }

  function setTrend(el, series) {
    if (series.length < 2) {
      el.dataset.direction = "flat";
      el.textContent = "—";
      return;
    }
    const delta = series[series.length - 1] - series[series.length - 2];
    if (Math.abs(delta) < 0.001) {
      el.dataset.direction = "flat";
      el.textContent = "—";
    } else if (delta > 0) {
      el.dataset.direction = "up";
      el.textContent = "▲";
    } else {
      el.dataset.direction = "down";
      el.textContent = "▼";
    }
  }

  function renderLiveValues(frame, history) {
    // ---- Temperature ----
    const tempSeries = history.map((f) => f.temperature).filter(Number.isFinite);
    const tempStat = stats(tempSeries);
    const tStatus = statusFor(frame, "temperature", () => temperatureStatus(frame.temperature));

    $("#tempCurrentValue").textContent = formatNumber(frame.temperature, 1);
    $("#tempBigValue").textContent = formatNumber(frame.temperature, 1);
    $("#tempMin").textContent = `${formatNumber(tempStat.min, 1)} °C`;
    $("#tempMax").textContent = `${formatNumber(tempStat.max, 1)} °C`;
    $("#tempAvg").textContent = `${formatNumber(tempStat.avg, 1)} °C`;
    setStatusBadge($("#tempStatusBadge"), tStatus);
    setStatusBadge(document.querySelector('[data-sensor="temperature"] .status-badge'), tStatus);
    setTrend($("#tempTrend"), tempSeries);

    // ---- Pressure ----
    const pressureSeries = history.map((f) => f.pressure).filter(Number.isFinite);
    const pressureStat = stats(pressureSeries);
    const pStatus = statusFor(frame, "pressure", () => pressureStatus(frame.pressure));

    $("#pressureCurrentValue").textContent = formatNumber(frame.pressure, 1);
    $("#pressureBigValue").textContent = formatNumber(frame.pressure, 1);
    $("#pressureMin").textContent = `${formatNumber(pressureStat.min, 1)} hPa`;
    $("#pressureMax").textContent = `${formatNumber(pressureStat.max, 1)} hPa`;
    $("#pressureAvg").textContent = `${formatNumber(pressureStat.avg, 1)} hPa`;
    setStatusBadge($("#pressureStatusBadge"), pStatus);
    setStatusBadge(document.querySelector('[data-sensor="pressure"] .status-badge'), pStatus);
    setTrend($("#pressureTrend"), pressureSeries);

    // ---- IMU ----
    const rms = imuRms(frame.imu);
    const rmsSeries = history.map((f) => imuRms(f.imu));
    const iStatus = statusFor(frame, "imu", () => imuStatus(frame.imu));

    $("#imuCurrentValue").textContent = formatNumber(rms, 2);
    $("#accelX").textContent = `${formatNumber(frame.imu.accel_x, 2)} g`;
    $("#accelY").textContent = `${formatNumber(frame.imu.accel_y, 2)} g`;
    $("#accelZ").textContent = `${formatNumber(frame.imu.accel_z, 2)} g`;
    $("#gyroX").textContent = `${formatNumber(frame.imu.gyro_x, 2)} °/s`;
    $("#gyroY").textContent = `${formatNumber(frame.imu.gyro_y, 2)} °/s`;
    $("#gyroZ").textContent = `${formatNumber(frame.imu.gyro_z, 2)} °/s`;
    $("#imuRmsValue").textContent = formatNumber(rms, 2);
    setStatusBadge($("#imuStatusBadge"), iStatus);
    setStatusBadge(document.querySelector('[data-sensor="imu"] .status-badge'), iStatus);
    setTrend($("#imuTrend"), rmsSeries);

    $("#lastUpdated").textContent = formatTime(frame.timestamp, true);
  }

  /* ------------------------------------------------------------------ *
   * 6. ALERTS TABLE
   * ------------------------------------------------------------------ */

  const alerts = [];
  const lastStatusBySensor = { temperature: "normal", pressure: "normal", imu: "normal" };

  function maybeRaiseAlert(sensorKey, label, value, unit, status, thresholdText) {
    const previous = lastStatusBySensor[sensorKey];
    lastStatusBySensor[sensorKey] = status;

    if (status === "normal") return; // no alert for normal readings
    if (status === previous) return; // only log on transition, avoid spam

    const messages = {
      warning: `${label} approaching threshold`,
      critical: `${label} exceeded critical limit`,
      sensor_failure: `${label} sensor is unavailable`,
    };

    alerts.unshift({
      time: formatTime(new Date().toISOString(), true),
      sensor: label,
      value: `${value} ${unit}`,
      threshold: thresholdText,
      severity: status,
      active: true,
      message: messages[status],
    });

    if (alerts.length > CONFIG.maxAlerts) alerts.pop();
    renderAlerts();
  }

  function renderAlerts() {
    const tbody = $("#alertsTableBody");
    if (alerts.length === 0) {
      tbody.innerHTML = `<tr class="alerts-empty-row"><td colspan="7">No alerts recorded yet.</td></tr>`;
      $("#alertCount").textContent = "0 active";
      return;
    }

    tbody.innerHTML = alerts
      .map(
        (a) => `
        <tr>
          <td>${a.time}</td>
          <td>${a.sensor}</td>
          <td>${a.value}</td>
          <td>${a.threshold}</td>
          <td><span class="severity-pill" data-severity="${a.severity}">${capitalize(a.severity)}</span></td>
          <td><span class="row-status" data-active="${a.active}">${a.active ? "Active" : "Resolved"}</span></td>
          <td>${a.message}</td>
        </tr>`
      )
      .join("");

    const activeCount = alerts.filter((a) => a.active).length;
    $("#alertCount").textContent = `${activeCount} active`;
  }

  function evaluateAlerts(frame) {
    const tStatus = statusFor(frame, "temperature", () => temperatureStatus(frame.temperature));
    maybeRaiseAlert(
      "temperature",
      "Temperature",
      formatNumber(frame.temperature, 1),
      "°C",
      tStatus,
      tStatus === "sensor_failure"
        ? "Sensor unavailable"
        : tStatus === "critical"
          ? `>${thresholds.temperature.critical}°C`
          : `>${thresholds.temperature.warning}°C`
    );

    const pStatus = statusFor(frame, "pressure", () => pressureStatus(frame.pressure));
    maybeRaiseAlert(
      "pressure",
      "Barometer",
      formatNumber(frame.pressure, 1),
      "hPa",
      pStatus,
      pStatus === "sensor_failure"
        ? "Sensor unavailable"
        : pStatus === "critical"
          ? `>${thresholds.pressure.criticalHigh}hPa`
          : `>${thresholds.pressure.warningHigh}hPa`
    );

    const rms = imuRms(frame.imu);
    const iStatus = statusFor(frame, "imu", () => imuStatus(frame.imu));
    maybeRaiseAlert(
      "imu",
      "IMU",
      formatNumber(rms, 2),
      "g",
      iStatus,
      iStatus === "sensor_failure"
        ? "Sensor unavailable"
        : iStatus === "critical"
          ? `Max axis >${thresholds.imu.critical.toFixed(2)}g`
          : `Max axis >${thresholds.imu.warning.toFixed(2)}g`
    );
  }

  /* ------------------------------------------------------------------ *
   * 7. CSV EXPORT
   *
  * Downloads a filtered CSV from the backend.
   * ------------------------------------------------------------------ */

  async function requestCsvExport({ sensor, start, end }) {
    const params = new URLSearchParams({ sensor, start: start || "", end: end || "" });

    const endpoint = `${CONFIG.apiBaseUrl}/export/csv?${params.toString()}`;

    try {
      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`Export endpoint returned ${response.status}`);
      const blob = await response.blob();
      downloadBlob(blob, buildExportFilename(sensor));
      return { ok: true, source: "backend" };
    } catch (err) {
      // Backend not reachable yet — export what's currently in memory
      // so the interface stays functional during frontend development.
      const csv = buildCsvFromHistory(sensor, start, end);
      downloadBlob(new Blob([csv], { type: "text/csv" }), buildExportFilename(sensor));
      return { ok: true, source: "local-fallback", error: err.message };
    }
  }

  function buildCsvFromHistory(sensor, start, end) {
    const startTime = start ? new Date(start).getTime() : -Infinity;
    const endTime = end ? new Date(end).getTime() : Infinity;

    const rows = store.history.filter((f) => {
      const t = new Date(f.timestamp).getTime();
      return t >= startTime && t <= endTime;
    });

    const header = [
      "timestamp",
      "device_id",
      ...(sensor === "all" || sensor === "temperature" ? ["temperature_c"] : []),
      ...(sensor === "all" || sensor === "pressure" ? ["pressure_hpa"] : []),
      ...(sensor === "all" || sensor === "imu"
        ? ["accel_x_g", "accel_y_g", "accel_z_g", "gyro_x_dps", "gyro_y_dps", "gyro_z_dps"]
        : []),
    ];

    const lines = [header.join(",")];
    rows.forEach((f) => {
      const cols = [f.timestamp, f.device_id];
      if (sensor === "all" || sensor === "temperature") cols.push(f.temperature);
      if (sensor === "all" || sensor === "pressure") cols.push(f.pressure);
      if (sensor === "all" || sensor === "imu") {
        cols.push(f.imu.accel_x, f.imu.accel_y, f.imu.accel_z, f.imu.gyro_x, f.imu.gyro_y, f.imu.gyro_z);
      }
      lines.push(cols.join(","));
    });

    return lines.join("\n");
  }

  function buildExportFilename(sensor) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `telemetry_${sensor}_${stamp}.csv`;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function bindExportForm() {
    const form = $("#exportForm");
    const statusEl = $("#exportStatus");
    const button = $("#exportButton");

    form.addEventListener("submit", async (evt) => {
      evt.preventDefault();
      const sensor = $("#exportSensor").value;
      const start = $("#exportStart").value;
      const end = $("#exportEnd").value;

      button.disabled = true;
      statusEl.dataset.state = "";
      statusEl.textContent = "Preparing export…";

      try {
        const result = await requestCsvExport({ sensor, start, end });
        statusEl.dataset.state = "success";
        statusEl.textContent =
          result.source === "backend"
            ? "Export complete."
            : "Exported browser-held readings; backend export was unavailable.";
      } catch (err) {
        statusEl.dataset.state = "error";
        statusEl.textContent = `Export failed: ${err.message}`;
      } finally {
        button.disabled = false;
      }
    });
  }

  /* ------------------------------------------------------------------ *
   * 8. BOOTSTRAP
   * ------------------------------------------------------------------ */

  function $(selector) {
    return document.querySelector(selector);
  }

  function round(value, decimals) {
    const factor = 10 ** decimals;
    return Math.round(value * factor) / factor;
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function formatTime(isoString, withDate = false) {
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return "--";
    if (withDate) {
      return d.toLocaleString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  function setConnectionState(state) {
    const el = $("#connectionStatus");
    el.dataset.state = state;
    el.querySelector(".status-text").textContent = state.toUpperCase();
  }

  function init() {
    initCharts();
    bindExportForm();
    setConnectionState("offline");

    onTelemetry((frame, history) => {
      updateCharts(history);
      renderLiveValues(frame, history);
      evaluateAlerts(frame);
    });

    startBackendPolling();
    window.addEventListener("beforeunload", stopBackendPolling);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
