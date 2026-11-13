import { defineStore } from "pinia";
import { telemetryApi } from "../services/api";
import { telemetrySocket } from "../services/socket";

const LINE_ID = "line30";
const HISTORY_LIMIT = 500;
const EVENT_HISTORY_LIMIT = 500;
const REFRESH_INTERVAL_MS = 5000;

function getRecordKey(record) {
  if (record.replay_cycle_id && record.message_id) {
    return `${record.replay_cycle_id}:${record.message_id}`;
  }
  return String(record.id);
}

function compareRecords(a, b) {
  const timestampDifference =
    new Date(a.event_ts).getTime() - new Date(b.event_ts).getTime();
  if (timestampDifference !== 0) {
    return timestampDifference;
  }
  return Number(a.id) - Number(b.id);
}

function getLatestById(records) {
  return records.reduce((latest, candidate) => {
    if (!latest) return candidate;
    return Number(candidate.id) >= Number(latest.id) ? candidate : latest;
  }, null);
}

function getHourEndIso(hourStartIso) {
  if (!hourStartIso) return null;
  const match = String(hourStartIso).match(
    /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})/
  );
  if (!match) return null;
  const date = new Date(`${hourStartIso}Z`);
  if (Number.isNaN(date.getTime())) return null;
  date.setUTCHours(date.getUTCHours() + 1);
  return date.toISOString().slice(0, 19);
}

export const useTelemetryStore = defineStore("telemetry", {
  state: () => ({
    lineId: LINE_ID,

    // Live process telemetry
    history: [],
    latestReading: null,
    currentCycleId: null,

    // Hourly summary and historical view
    hourlySummary: null,
    selectedHourSummary: null,
    recentReadings: [],
    events: [],
    replayCycles: [],
    selectedCycleId: null,
    selectedHourStart: null,
    selectedHourIndex: -1,
    activeView: "overview",
    cyclesLoading: false,
    cyclesError: null,
    historyRequestToken: 0,

    // Main dashboard loading state
    isLoading: false,
    hasLoaded: false,
    error: null,

    // History view loading states
    summaryLoading: false,
    readingsLoading: false,
    eventsLoading: false,

    // History view errors
    summaryError: null,
    readingsError: null,
    eventsError: null,

    // CSV export state
    exporting: {
      hourlySummary: false,
      readings: false,
      events: false,
    },
    exportError: null,

    // Connection health
    socketStatus: "disconnected",
    databaseStatus: "unknown",
    mqttStatus: "unknown",
    serverStatus: "unknown",

    lastUpdateAt: null,
    started: false,
    socketListenersBound: false,

    // Universal 5-second refresh timer
    refreshTimer: null,
    refreshCheckInProgress: false,
  }),

  getters: {
    connectionStatus: (state) => {
      if (state.socketStatus === "connected") return "live";
      if (state.socketStatus === "connecting") return "connecting";
      if (state.socketStatus === "reconnecting") return "reconnecting";
      return "disconnected";
    },

    recordCount: (state) => state.history.length,
    eventCount: (state) => state.events.length,

    selectedCycle: (state) =>
      state.replayCycles.find(
        (cycle) => cycle.replay_cycle_id === state.selectedCycleId
      ) || null,

    canPreviousHour: (state) => state.selectedHourIndex > 0,

    canNextHour: (state) =>
      state.selectedHourIndex >= 0 &&
      state.selectedHourIndex < (state.hourlySummary?.data?.length ?? 0) - 1,
  },

  actions: {
    mergeRecords(records, { live = false } = {}) {
      if (!Array.isArray(records) || records.length === 0) {
        return;
      }

      const validRecords = records.filter(
        (record) =>
          record &&
          record.event_ts &&
          record.message_id &&
          record.replay_cycle_id &&
          record.payload &&
          record.id !== undefined &&
          record.id !== null
      );

      if (validRecords.length === 0) {
        return;
      }

      const newestIncomingRecord = getLatestById(validRecords);
      const incomingCycleId = newestIncomingRecord.replay_cycle_id;

      if (this.currentCycleId !== incomingCycleId) {
        this.history = [];
        this.latestReading = null;
        this.currentCycleId = incomingCycleId;
      }

      const cycleRecords = validRecords.filter(
        (record) => record.replay_cycle_id === this.currentCycleId
      );

      const recordMap = new Map();
      for (const record of this.history) {
        if (record.replay_cycle_id === this.currentCycleId) {
          recordMap.set(getRecordKey(record), record);
        }
      }
      for (const record of cycleRecords) {
        recordMap.set(getRecordKey(record), record);
      }

      this.history = Array.from(recordMap.values())
        .sort(compareRecords)
        .slice(-HISTORY_LIMIT);

      const latestCandidates = [this.latestReading, ...cycleRecords].filter(
        (record) =>
          record &&
          record.replay_cycle_id === this.currentCycleId &&
          record.id !== undefined &&
          record.id !== null
      );

      this.latestReading = getLatestById(latestCandidates);

      if (live && this.latestReading) {
        this.lastUpdateAt =
          this.latestReading.received_at || new Date().toISOString();
      }
    },

    bindSocketListeners() {
      if (this.socketListenersBound) return;
      this.socketListenersBound = true;

      telemetrySocket.on("connect", () => {
        this.socketStatus = "connected";
        this.error = null;
        telemetrySocket.emit("join_line", { line_id: this.lineId });
      });

      telemetrySocket.on("disconnect", () => {
        this.socketStatus = "disconnected";
      });

      telemetrySocket.io.on("reconnect_attempt", () => {
        this.socketStatus = "reconnecting";
      });

      telemetrySocket.io.on("reconnect", () => {
        this.socketStatus = "connected";
        this.error = null;
        telemetrySocket.emit("join_line", { line_id: this.lineId });
        this.loadHistory().catch(() => {});
      });

      telemetrySocket.on("connect_error", () => {
        if (this.socketStatus !== "reconnecting") {
          this.socketStatus = "disconnected";
        }
      });

      telemetrySocket.on("telemetry_update", (data) => {
        if (!data || data.line_id !== this.lineId) return;
        this.mergeRecords([data], { live: true });
        this.hasLoaded = true;
      });

      telemetrySocket.on("operational_event", (data) => {
        if (!data || data.line_id !== this.lineId || data.id == null) return;
        if (
          this.activeView === "history" &&
          this.selectedCycleId &&
          data.replay_cycle_id === this.selectedCycleId
        ) {
          const exists = this.events.some((e) => String(e.id) === String(data.id));
          if (!exists) {
            this.events = [data, ...this.events].slice(0, EVENT_HISTORY_LIMIT);
          }
        }
      });
    },

    connectSocket() {
      this.bindSocketListeners();
      if (telemetrySocket.connected) {
        this.socketStatus = "connected";
        telemetrySocket.emit("join_line", { line_id: this.lineId });
      } else {
        this.socketStatus = "connecting";
        telemetrySocket.connect();
      }
    },

    async loadHealth() {
      try {
        const result = await telemetryApi.getHealth();
        this.serverStatus = result.status === "healthy" ? "healthy" : "degraded";
        this.databaseStatus = result.database || "unknown";
        this.mqttStatus = result.mqtt || "unknown";
        return result;
      } catch (error) {
        this.serverStatus = "unhealthy";
        this.databaseStatus = "disconnected";
        this.mqttStatus = "disconnected";
        return null;
      }
    },

    // Universal 5-second background timer covering both views
    startRefreshTimer() {
      if (this.refreshTimer) return;
      this.refreshTimer = setInterval(async () => {
        if (this.refreshCheckInProgress) return;
        this.refreshCheckInProgress = true;

        try {
          // Always poll system health metrics in the background
          await this.loadHealth();

          if (this.activeView === "overview") {
            // Refresh overview history & cycles every 5 seconds
            await Promise.all([
              this.loadHistory(),
              this.loadReplayCycles(),
            ]);
          } else if (this.activeView === "history") {
            // Refresh history view data every 5 seconds automatically
            await this.refreshHistoryView();
          }
        } finally {
          this.refreshCheckInProgress = false;
        }
      }, REFRESH_INTERVAL_MS);
    },

    stopRefreshTimer() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
      this.refreshCheckInProgress = false;
    },

    async loadHistory() {
      const cycleAtRequest = this.currentCycleId;
      try {
        const result = await telemetryApi.getHistory({
          lineId: this.lineId,
          limit: HISTORY_LIMIT,
        });

        if (
          this.currentCycleId !== null &&
          this.currentCycleId !== cycleAtRequest
        ) {
          return result;
        }

        const rows = Array.isArray(result.data) ? result.data : [];
        this.mergeRecords(rows, { live: false });
        if (!this.lastUpdateAt && this.latestReading?.received_at) {
          this.lastUpdateAt = this.latestReading.received_at;
        }
        this.hasLoaded = true;
        return result;
      } catch (error) {
        this.error = error.message || "Unable to load initial telemetry history.";
        this.hasLoaded = true;
        return null;
      }
    },

    async loadReplayCycles() {
      this.cyclesLoading = true;
      this.cyclesError = null;

      try {
        const result = await telemetryApi.getReplayCycles({
          lineId: this.lineId,
          limit: 50,
        });

        const cycles = Array.isArray(result.cycles)
          ? result.cycles
          : Array.isArray(result.data)
            ? result.data
            : [];

        this.replayCycles = cycles;

        const hasCurrent = cycles.some(
          (c) => c.replay_cycle_id === this.selectedCycleId
        );
        if (!hasCurrent) {
          this.selectedCycleId = cycles[0]?.replay_cycle_id ?? null;
        }
      } catch (error) {
        this.cyclesError = error.message || "Unable to load replay cycles.";
        this.replayCycles = [];
      } finally {
        this.cyclesLoading = false;
      }
    },

    async loadCycleSummary(token) {
      if (!this.selectedCycleId) {
        this.hourlySummary = null;
        this.selectedHourStart = null;
        this.selectedHourSummary = null;
        this.selectedHourIndex = -1;
        return;
      }

      this.summaryLoading = true;
      this.summaryError = null;

      try {
        const result = await telemetryApi.getHourlySummary({
          lineId: this.lineId,
          cycleId: this.selectedCycleId,
        });

        if (token !== undefined && token !== this.historyRequestToken) return;

        this.hourlySummary = result;
        const rows = Array.isArray(result.data) ? result.data : [];

        if (rows.length === 0) {
          this.selectedHourStart = null;
          this.selectedHourIndex = -1;
          this.selectedHourSummary = null;
          return;
        }

        const existingIndex = rows.findIndex(
          (row) => row.hour_start === this.selectedHourStart
        );
        const targetIndex = existingIndex >= 0 ? existingIndex : 0;

        this.selectedHourIndex = targetIndex;
        this.selectedHourStart = rows[targetIndex].hour_start;
      } catch (error) {
        if (token !== undefined && token !== this.historyRequestToken) return;
        this.summaryError = error.message || "Unable to load hourly summary.";
        this.hourlySummary = null;
        this.selectedHourStart = null;
        this.selectedHourIndex = -1;
        this.selectedHourSummary = null;
      } finally {
        if (token === undefined || token === this.historyRequestToken) {
          this.summaryLoading = false;
        }
      }
    },

    async loadSelectedHourDetails(token) {
      if (!this.selectedCycleId || !this.selectedHourStart) {
        this.selectedHourSummary = null;
        this.recentReadings = [];
        this.events = [];
        return;
      }

      const start = this.selectedHourStart;
      const end = getHourEndIso(start);

      this.readingsLoading = true;
      this.eventsLoading = true;
      this.readingsError = null;
      this.eventsError = null;

      const [hourStatsRes, readingsRes, eventsRes] = await Promise.allSettled([
        telemetryApi.getHourlySummary({
          lineId: this.lineId,
          cycleId: this.selectedCycleId,
          hourStart: start,
        }),
        telemetryApi.getHistory({
          lineId: this.lineId,
          limit: HISTORY_LIMIT,
          cycleId: this.selectedCycleId,
          start,
          end,
        }),
        telemetryApi.getEvents({
          lineId: this.lineId,
          limit: EVENT_HISTORY_LIMIT,
          cycleId: this.selectedCycleId,
          start,
          end,
        }),
      ]);

      if (token !== undefined && token !== this.historyRequestToken) return;

      if (hourStatsRes.status === "fulfilled") {
        this.selectedHourSummary = hourStatsRes.value;
      } else {
        this.selectedHourSummary = null;
        this.summaryError =
          hourStatsRes.reason?.message || "Unable to load selected hour statistics.";
      }

      if (readingsRes.status === "fulfilled") {
        const rows = Array.isArray(readingsRes.value.data)
          ? readingsRes.value.data
          : [];
        this.recentReadings = [...rows].sort(compareRecords);
      } else {
        this.recentReadings = [];
        this.readingsError =
          readingsRes.reason?.message || "Unable to load historical readings.";
      }

      if (eventsRes.status === "fulfilled") {
        this.events = Array.isArray(eventsRes.value.data)
          ? eventsRes.value.data
          : [];
      } else {
        this.events = [];
        this.eventsError =
          eventsRes.reason?.message || "Unable to load operational events.";
      }

      this.readingsLoading = false;
      this.eventsLoading = false;
    },

    async refreshHistoryView() {
      const token = ++this.historyRequestToken;
      await this.loadReplayCycles();
      if (token !== this.historyRequestToken) return;

      await this.loadCycleSummary(token);
      if (token !== this.historyRequestToken) return;

      await this.loadSelectedHourDetails(token);
    },

    async setActiveView(view) {
      this.activeView = view;
      if (view === "history") {
        await this.refreshHistoryView();
      }
    },

    async selectCycle(cycleId) {
      this.selectedCycleId = cycleId || null;
      this.selectedHourStart = null;
      this.selectedHourSummary = null;
      this.selectedHourIndex = -1;
      this.recentReadings = [];
      this.events = [];

      if (this.activeView === "history") {
        const token = ++this.historyRequestToken;
        await this.loadCycleSummary(token);
        if (token !== this.historyRequestToken) return;
        await this.loadSelectedHourDetails(token);
      }
    },

    async selectHour(hourStart) {
      this.selectedHourStart = hourStart;
      const rows = Array.isArray(this.hourlySummary?.data)
        ? this.hourlySummary.data
        : [];
      this.selectedHourIndex = rows.findIndex(
        (row) => row.hour_start === hourStart
      );

      if (this.activeView === "history") {
        const token = ++this.historyRequestToken;
        await this.loadSelectedHourDetails(token);
      }
    },

    async moveSelectedHour(delta) {
      const rows = this.hourlySummary?.data;
      if (!Array.isArray(rows) || rows.length === 0) return;

      const nextIndex = this.selectedHourIndex + delta;
      if (nextIndex < 0 || nextIndex >= rows.length) return;

      await this.selectHour(rows[nextIndex].hour_start);
    },

    async exportHourlySummary() {
      if (!this.selectedCycleId) return;
      this.exporting.hourlySummary = true;
      this.exportError = null;

      try {
        await telemetryApi.downloadHourlySummary({
          lineId: this.lineId,
          cycleId: this.selectedCycleId,
        });
      } catch (error) {
        this.exportError = error.message || "Export failed.";
      } finally {
        this.exporting.hourlySummary = false;
      }
    },

    async exportReadings() {
      if (!this.selectedCycleId || !this.selectedHourStart) return;
      this.exporting.readings = true;
      this.exportError = null;

      try {
        await telemetryApi.downloadReadings({
          lineId: this.lineId,
          cycleId: this.selectedCycleId,
          start: this.selectedHourStart,
          end: getHourEndIso(this.selectedHourStart),
        });
      } catch (error) {
        this.exportError = error.message || "Export failed.";
      } finally {
        this.exporting.readings = false;
      }
    },

    async exportEvents() {
      if (!this.selectedCycleId || !this.selectedHourStart) return;
      this.exporting.events = true;
      this.exportError = null;

      try {
        await telemetryApi.downloadEvents({
          lineId: this.lineId,
          cycleId: this.selectedCycleId,
          start: this.selectedHourStart,
          end: getHourEndIso(this.selectedHourStart),
        });
      } catch (error) {
        this.exportError = error.message || "Export failed.";
      } finally {
        this.exporting.events = false;
      }
    },

    async initialize() {
      if (this.started) return;
      this.started = true;
      this.isLoading = true;
      this.error = null;

      this.connectSocket();

      await Promise.all([
        this.loadHealth(),
        this.loadHistory(),
        this.loadReplayCycles(),
      ]);

      this.isLoading = false;
      
      // Start the universal 5-second automatic refresh timer
      this.startRefreshTimer();
    },

    stop() {
      this.started = false;
      this.stopRefreshTimer();
      this.socketStatus = "disconnected";
      this.error = null;

      if (telemetrySocket.connected) {
        telemetrySocket.emit("leave_line", { line_id: this.lineId });
      }
      telemetrySocket.disconnect();
    },
  },
});