const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

async function request(path) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new Error("Unable to reach the Flask API server.");
  }

  let result;

  try {
    result = await response.json();
  } catch {
    throw new Error(`Invalid API response (${response.status}).`);
  }

  if (!response.ok) {
    throw new Error(
      result.error || `API request failed (${response.status}).`
    );
  }

  return result;
}

async function downloadCsv(path, fallbackFilename) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new Error("Unable to reach the Flask API server.");
  }

  if (!response.ok) {
    let message = `CSV export failed (${response.status}).`;

    try {
      const result = await response.json();
      message = result.error || message;
    } catch {
      // Keep the HTTP error message when the response is not JSON.
    }

    throw new Error(message);
  }

  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") || "";
  const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
  const filename = filenameMatch?.[1] || fallbackFilename;

  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(objectUrl);
}

function addHistoricalScope(params, { cycleId, start, end, hourStart } = {}) {
  if (cycleId) params.set("cycle_id", cycleId);
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  if (hourStart) params.set("hour_start", hourStart);
  return params;
}

export const telemetryApi = {
  async getHealth() {
    let response;
    try {
      response = await fetch(`${API_BASE_URL}/api/health`);
    } catch {
      throw new Error("Unable to reach the Flask API server.");
    }

    let result;
    try {
      result = await response.json();
    } catch {
      throw new Error(`Invalid health response (${response.status}).`);
    }

    if (response.ok || response.status === 503) {
      return result;
    }

    throw new Error(result.error || `Health check failed (${response.status}).`);
  },

  getLatest(lineId = "line30") {
    const params = new URLSearchParams({ line_id: lineId });
    return request(`/api/telemetry/latest?${params}`);
  },

  getHistory({ lineId = "line30", limit = 100, cycleId, start, end } = {}) {
    const params = new URLSearchParams({ line_id: lineId, limit: String(limit) });
    addHistoricalScope(params, { cycleId, start, end });
    return request(`/api/telemetry/history?${params}`);
  },

  getStatistics({ lineId = "line30", field, cycleId, start, end } = {}) {
    if (!field) throw new Error("A telemetry field is required for statistics.");
    const params = new URLSearchParams({ line_id: lineId, field });
    addHistoricalScope(params, { cycleId, start, end });
    return request(`/api/telemetry/statistics?${params}`);
  },

  getHourlySummary({ lineId = "line30", hours, cycleId, hourStart } = {}) {
    const params = new URLSearchParams({ line_id: lineId });
    if (hours !== undefined && hours !== null) params.set("hours", String(hours));
    addHistoricalScope(params, { cycleId, hourStart });
    return request(`/api/summary/hourly?${params}`);
  },

  getEvents({ lineId = "line30", limit = 100, cycleId, start, end } = {}) {
    const params = new URLSearchParams({ line_id: lineId, limit: String(limit) });
    addHistoricalScope(params, { cycleId, start, end });
    return request(`/api/events?${params}`);
  },

  getReplayCycles({ lineId = "line30", limit = 50 } = {}) {
    const params = new URLSearchParams({ line_id: lineId, limit: String(limit) });
    return request(`/api/history/cycles?${params}`);
  },

  downloadHourlySummary({ lineId = "line30", hours, cycleId, hourStart } = {}) {
    const params = new URLSearchParams({ line_id: lineId });
    if (hours !== undefined && hours !== null) params.set("hours", String(hours));
    addHistoricalScope(params, { cycleId, hourStart });
    return downloadCsv(`/api/exports/hourly-summary.csv?${params}`, "line30-hourly-summary.csv");
  },

  downloadReadings({ lineId = "line30", cycleId, start, end } = {}) {
    const params = new URLSearchParams({ line_id: lineId });
    addHistoricalScope(params, { cycleId, start, end });
    return downloadCsv(`/api/exports/readings.csv?${params}`, "line30-historical-readings.csv");
  },

  downloadEvents({ lineId = "line30", cycleId, start, end } = {}) {
    const params = new URLSearchParams({ line_id: lineId });
    addHistoricalScope(params, { cycleId, start, end });
    return downloadCsv(`/api/exports/events.csv?${params}`, "line30-event-history.csv");
  },
};
