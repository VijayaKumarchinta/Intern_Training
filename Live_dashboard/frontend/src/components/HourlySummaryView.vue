<script setup>
import { computed } from "vue";

const props = defineProps({
  summary: { type: Object, default: null },
  selectedHourSummary: { type: Object, default: null },
  cycles: { type: Array, default: () => [] },
  selectedCycleId: { type: String, default: null },
  selectedHourStart: { type: String, default: null },
  selectedHourIndex: { type: Number, default: -1 },
  canPreviousHour: Boolean,
  canNextHour: Boolean,
  cyclesLoading: Boolean,
  cyclesError: { type: String, default: null },
  recentReadings: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
  summaryLoading: Boolean,
  readingsLoading: Boolean,
  eventsLoading: Boolean,
  summaryError: { type: String, default: null },
  readingsError: { type: String, default: null },
  eventsError: { type: String, default: null },
  exporting: {
    type: Object,
    default: () => ({ hourlySummary: false, readings: false, events: false }),
  },
  exportError: { type: String, default: null },
});

const emit = defineEmits([
  "select-cycle",
  "select-hour",
  "previous-hour",
  "next-hour",
  "export-hourly",
  "export-readings",
  "export-events",
]);

const metrics = [
  { key: "oil_temperature", prefix: "burner_pv", label: "Oil Temperature", field: "Burner PV", unit: "°C" },
  { key: "delta_t", prefix: "delta_t", label: "Delta T", field: "DeltaT", unit: "°C" },
  { key: "burner_load", prefix: "burner_load", label: "Burner Load", field: "Burner Output Load", unit: "%" },
  { key: "moisture", prefix: "moisture", label: "Moisture", field: "Moisture PV", unit: "" },
  { key: "paddle_speed", prefix: "paddle_speed", label: "Paddle Speed", field: "Paddle Speed", unit: "" },
  { key: "oil_level", prefix: "oil_level", label: "Oil Level", field: "oil Level PV", unit: "" },
];

const summaryRows = computed(() =>
  Array.isArray(props.summary?.data) ? props.summary.data : []
);
const selectedStatistics = computed(
  () => props.selectedHourSummary?.statistics ?? {}
);
const selectedCycle = computed(
  () =>
    props.cycles.find(
      (cycle) => cycle.replay_cycle_id === props.selectedCycleId
    ) || null
);

function formatValue(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "—";
}

function formatDuration(value) {
  const seconds = Number(value);
  if (!Number.isFinite(seconds) || seconds <= 0) return "0s";
  const total = Math.floor(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remaining = total % 60;
  if (hours)
    return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(remaining).padStart(2, "0")}s`;
  if (minutes) return `${minutes}m ${String(remaining).padStart(2, "0")}s`;
  return `${remaining}s`;
}

function formatTimestamp(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function formatHour(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function severityClass(severity) {
  const value = String(severity || "").toLowerCase();
  if (value === "critical") return "severity-critical";
  if (value === "high") return "severity-high";
  if (value === "warning") return "severity-warning";
  if (value === "info") return "severity-info";
  return "severity-default";
}

function stateClass(state) {
  const value = String(state || "").toLowerCase();
  if (value === "active") return "event-active";
  if (value === "cleared") return "event-cleared";
  return "";
}

function cycleLabel(cycle) {
  const number =
    cycle.replay_cycle_number == null ? "—" : `#${cycle.replay_cycle_number}`;
  const stamp = cycle.first_event_ts
    ? formatTimestamp(cycle.first_event_ts)
    : "Timestamp unavailable";
  return `${number} · ${cycle.status} · ${stamp} · ${cycle.persisted_records}/${cycle.expected_records ?? "?"}`;
}
</script>

<template>
  <div class="history-view">
    <section class="history-heading">
      <div>
        <div class="section-kicker">PRODUCTION ANALYTICS</div>
        <h1>Hourly Summary & History</h1>
        <p class="history-description">
          Complete replay-cycle performance, hourly drill-down, telemetry readings and operational events.
        </p>
      </div>
    </section>

    <section class="history-window panel-card">
      <div class="cycle-picker">
        <label class="history-label" for="replay-cycle-select">REPLAY CYCLE</label>
        <select
          id="replay-cycle-select"
          :value="selectedCycleId || ''"
          :disabled="cyclesLoading || !cycles.length"
          @change="emit('select-cycle', $event.target.value)"
        >
          <option v-if="!cycles.length" value="">No replay cycles available</option>
          <option
            v-for="cycle in cycles"
            :key="cycle.replay_cycle_id"
            :value="cycle.replay_cycle_id"
          >
            {{ cycleLabel(cycle) }}
          </option>
        </select>
      </div>
      <div class="history-window-meta">
        <div>
          <span class="history-label">REPLAY STATUS</span>
          <strong>{{ selectedCycle?.status || (cyclesLoading ? "Loading" : "No cycle") }}</strong>
        </div>
        <div>
          <span class="history-label">PERSISTED / EXPECTED</span>
          <strong>
            {{
              selectedCycle
                ? `${selectedCycle.persisted_records} / ${selectedCycle.expected_records ?? "Unknown"}`
                : "—"
            }}
          </strong>
        </div>
        <div>
          <span class="history-label">SOURCE EVENT WINDOW</span>
          <strong>
            {{
              selectedCycle
                ? `${formatTimestamp(selectedCycle.first_event_ts)} — ${formatTimestamp(selectedCycle.last_event_ts)}`
                : "—"
            }}
          </strong>
        </div>
      </div>
    </section>

    <div v-if="cyclesError" class="history-error">
      <strong>Unable to load replay cycles</strong>
      <span>{{ cyclesError }}</span>
    </div>
    <div v-if="selectedCycle?.status_reason" class="cycle-reason">
      <strong>{{ selectedCycle.status }}</strong>
      <span>{{ selectedCycle.status_reason }}</span>
    </div>

    <section class="history-section">
      <div class="history-section-heading">
        <div>
          <div class="section-kicker">HOURLY PERFORMANCE</div>
          <h2>Hourly Process Summary</h2>
          <p>
            All available source-event hours in the selected replay cycle. Select a row to inspect that hour.
          </p>
        </div>
        <button
          type="button"
          class="history-button primary-button"
          :disabled="exporting.hourlySummary || !selectedCycleId"
          @click="emit('export-hourly')"
        >
          {{ exporting.hourlySummary ? "Preparing..." : "Export cycle summary CSV" }}
        </button>
      </div>
      <div v-if="summaryLoading && !summaryRows.length" class="history-state">
        <span class="loading-ring"></span>Loading hourly summary...
      </div>
      <div v-else-if="summaryError" class="history-error">
        <strong>Unable to load hourly summary</strong>
        <span>{{ summaryError }}</span>
      </div>
      <div v-else-if="!summaryRows.length" class="history-state">
        No hourly summary data is available for this replay cycle.
      </div>
      <div v-else class="table-scroll panel-card">
        <table class="history-table hourly-table">
          <thead>
            <tr>
              <th class="sticky-column">Hour</th>
              <th>Samples</th>
              <th v-for="metric in metrics" :key="metric.key">
                {{ metric.label }}
                <span v-if="metric.unit" class="table-unit">{{ metric.unit }}</span>
                <span class="table-subheading">AVG / MIN / MAX</span>
              </th>
              <th>Burner at 100%</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in summaryRows"
              :key="row.hour_start"
              :class="{ 'selected-hour-row': row.hour_start === selectedHourStart }"
              @click="emit('select-hour', row.hour_start)"
            >
              <td class="sticky-column hour-cell">
                <button
                  type="button"
                  class="hour-select"
                  :aria-pressed="row.hour_start === selectedHourStart"
                  @click.stop="emit('select-hour', row.hour_start)"
                >
                  {{ formatHour(row.hour_start) }}
                </button>
              </td>
              <td class="numeric-cell">
                {{ Number(row.sample_count || 0).toLocaleString("en-IN") }}
              </td>
              <td v-for="metric in metrics" :key="metric.key">
                <div class="metric-triplet">
                  <span>{{ formatValue(row[`${metric.prefix}_average`]) }}</span>
                  <span>{{ formatValue(row[`${metric.prefix}_minimum`]) }}</span>
                  <span>{{ formatValue(row[`${metric.prefix}_maximum`]) }}</span>
                </div>
              </td>
              <td class="duration-cell">
                {{ formatDuration(row.burner_at_100_seconds) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="history-section">
      <div class="history-section-heading">
        <div>
          <div class="section-kicker">SELECTED HOUR</div>
          <h2>Hourly Process Indicators</h2>
          <p>
            {{ selectedHourStart ? formatHour(selectedHourStart) : "Select an hour from the summary above" }}
            · {{ selectedHourSummary?.sample_count?.toLocaleString("en-IN") ?? "—" }} samples
          </p>
        </div>
        <div class="hour-navigation">
          <button
            type="button"
            class="history-button secondary-button"
            :disabled="!canPreviousHour || summaryLoading"
            @click="emit('previous-hour')"
          >
            Previous hour
          </button>
          <button
            type="button"
            class="history-button secondary-button"
            :disabled="!canNextHour || summaryLoading"
            @click="emit('next-hour')"
          >
            Next hour
          </button>
        </div>
      </div>
      <div v-if="!selectedHourStart" class="history-state">
        Choose an hourly row to load its six KPIs, readings and operational events.
      </div>
      <div v-else-if="summaryLoading && !selectedHourSummary" class="history-state">
        <span class="loading-ring"></span>Loading selected-hour statistics...
      </div>
      <div v-else-if="summaryError" class="history-error">{{ summaryError }}</div>
      <div v-else class="statistics-grid">
        <article v-for="metric in metrics" :key="metric.key" class="statistic-card panel-card">
          <div class="statistic-title">{{ metric.label }}</div>
          <div class="statistic-field">{{ metric.field }}</div>
          <div class="statistic-values">
            <div>
              <span>AVERAGE</span>
              <strong>{{ formatValue(selectedStatistics[metric.key]?.average) }}</strong>
            </div>
            <div>
              <span>MINIMUM</span>
              <strong>{{ formatValue(selectedStatistics[metric.key]?.minimum) }}</strong>
            </div>
            <div>
              <span>MAXIMUM</span>
              <strong>{{ formatValue(selectedStatistics[metric.key]?.maximum) }}</strong>
            </div>
          </div>
          <div v-if="metric.unit" class="statistic-unit">Values in {{ metric.unit }}</div>
        </article>
      </div>
    </section>

    <section class="history-section">
      <div class="history-section-heading">
        <div>
          <div class="section-kicker">SELECTED-HOUR TELEMETRY</div>
          <h2>Historical Readings</h2>
          <p>All persisted readings in the selected hour, ordered by event timestamp.</p>
        </div>
        <button
          type="button"
          class="history-button primary-button"
          :disabled="exporting.readings || !selectedHourStart"
          @click="emit('export-readings')"
        >
          {{ exporting.readings ? "Preparing..." : "Export selected-hour readings" }}
        </button>
      </div>
      <div v-if="readingsLoading" class="history-state">
        <span class="loading-ring"></span>Loading historical readings...
      </div>
      <div v-else-if="readingsError" class="history-error">
        <strong>Unable to load historical readings</strong>
        <span>{{ readingsError }}</span>
      </div>
      <div v-else-if="!recentReadings.length" class="history-state">
        No readings are available for the selected hour.
      </div>
      <div v-else class="table-scroll panel-card">
        <table class="history-table readings-table">
          <thead>
            <tr>
              <th>Event Time</th>
              <th>Source Row</th>
              <th>Burner PV °C</th>
              <th>Delta T °C</th>
              <th>Burner Load %</th>
              <th>Moisture</th>
              <th>Paddle Speed</th>
              <th>Oil Level</th>
              <th>Received At</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in recentReadings" :key="record.id">
              <td class="timestamp-cell">{{ formatTimestamp(record.event_ts) }}</td>
              <td>{{ record.payload?.source_row ?? "—" }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.["Burner PV"]) }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.DeltaT) }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.["Burner Output Load"]) }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.["Moisture PV"]) }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.["Paddle Speed"]) }}</td>
              <td class="numeric-cell">{{ formatValue(record.payload?.["oil Level PV"]) }}</td>
              <td class="timestamp-cell">{{ formatTimestamp(record.received_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="history-section">
      <div class="history-section-heading">
        <div>
          <div class="section-kicker">SELECTED-HOUR EVENTS</div>
          <h2>Operational Event History</h2>
          <p>Persisted alarm transitions filtered by the selected replay cycle and event hour.</p>
        </div>
        <button
          type="button"
          class="history-button primary-button"
          :disabled="exporting.events || !selectedHourStart"
          @click="emit('export-events')"
        >
          {{ exporting.events ? "Preparing..." : "Export selected-hour events" }}
        </button>
      </div>
      <div v-if="eventsLoading" class="history-state">
        <span class="loading-ring"></span>Loading operational events...
      </div>
      <div v-else-if="eventsError" class="history-error">
        <strong>Unable to load event history</strong>
        <span>{{ eventsError }}</span>
      </div>
      <div v-else-if="!events.length" class="history-state">
        No operational events were recorded during the selected hour.
      </div>
      <div v-else class="table-scroll panel-card">
        <table class="history-table events-table">
          <thead>
            <tr>
              <th>Event Time</th>
              <th>Severity</th>
              <th>Event Code</th>
              <th>State</th>
              <th>Title / Description</th>
              <th>Cycle</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="event in events" :key="event.id">
              <td class="timestamp-cell">{{ formatTimestamp(event.event_ts) }}</td>
              <td>
                <span class="severity-tag" :class="severityClass(event.severity)">
                  {{ event.severity || "—" }}
                </span>
              </td>
              <td class="event-code">{{ event.event_code || "—" }}</td>
              <td>
                <span class="event-state" :class="stateClass(event.state)">
                  {{ event.state || "—" }}
                </span>
              </td>
              <td class="event-description">
                <strong>{{ event.title || "Operational event" }}</strong>
                <span>{{ event.description || "—" }}</span>
              </td>
              <td class="cycle-cell">{{ event.replay_cycle_id || "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="exportError" class="history-error export-error" role="status">
      <strong>CSV export failed</strong>
      <span>{{ exportError }}</span>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  display: flex;
  flex-direction: column;
  gap: 30px;
  min-width: 0;
}

.history-heading,
.history-section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
}

.history-heading h1 {
  margin: 7px 0 6px;
  color: var(--text-primary);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.7px;
}

.history-description,
.history-section-heading p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.history-button {
  min-height: 36px;
  padding: 0 13px;
  border: 1px solid transparent;
  border-radius: 5px;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.history-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.primary-button {
  color: #ffffff;
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

.primary-button:hover:not(:disabled) {
  background: var(--accent-hover);
}

.secondary-button {
  color: var(--text-primary);
  background: var(--background-surface);
  border-color: var(--border-default);
}

.secondary-button:hover:not(:disabled) {
  background: var(--background-hover);
}

.history-window {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 17px 20px;
}

.history-window > div,
.history-window-meta > div {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.history-window strong {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 650;
  overflow-wrap: anywhere;
}

.history-label {
  color: var(--text-muted);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.7px;
}

.history-window-meta {
  display: flex;
  gap: 34px;
}

.history-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.history-section-heading h2 {
  margin: 5px 0 4px;
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.25px;
}

.table-scroll {
  width: 100%;
  overflow: auto;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: 7px;
}

.history-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  color: var(--text-primary);
  font-size: 11px;
  text-align: left;
}

.history-table th {
  padding: 12px 11px;
  color: #ffffff;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--border-default);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.35px;
  white-space: nowrap;
}

.history-table td {
  padding: 12px 11px;
  background: var(--background-surface);
  border-bottom: 1px solid var(--border-default);
  white-space: nowrap;
  vertical-align: middle;
}

.history-table tbody tr:last-child td {
  border-bottom: 0;
}

.history-table tbody tr:hover td {
  background: var(--background-hover);
}

.table-unit {
  color: #9eb3c8;
  font-size: 9px;
  font-weight: 600;
}

.table-subheading {
  display: block;
  margin-top: 4px;
  color: #9eb3c8;
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 0.25px;
}

.hourly-table {
  min-width: 1170px;
}

.hourly-table .sticky-column {
  position: sticky;
  left: 0;
  z-index: 1;
  background: var(--background-surface);
  border-right: 1px solid var(--border-default);
}

.hourly-table thead .sticky-column {
  z-index: 2;
  background: var(--topbar-bg);
  color: #ffffff;
}

.hour-cell {
  color: var(--text-primary);
  font-weight: 700;
}

.hour-select {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--accent-primary);
  font-weight: 700;
  cursor: pointer;
}

.hour-select:hover {
  text-decoration: underline;
}

.metric-triplet {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-variant-numeric: tabular-nums;
}

.metric-triplet span:first-child {
  color: var(--text-primary);
  font-weight: 700;
}

.metric-triplet span:nth-child(2),
.metric-triplet span:nth-child(3) {
  color: var(--text-secondary);
  font-size: 10px;
}

.numeric-cell,
.duration-cell {
  font-variant-numeric: tabular-nums;
}

.duration-cell {
  color: var(--text-primary);
  font-weight: 700;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 13px;
}

.statistic-card {
  min-width: 0;
  padding: 16px;
}

.statistic-title {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 750;
}

.statistic-field {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 10px;
}

.statistic-values {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 17px;
}

.statistic-values > div {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.statistic-values span {
  color: var(--text-muted);
  font-size: 8px;
  font-weight: 750;
  letter-spacing: 0.4px;
}

.statistic-values strong {
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.statistic-unit {
  margin-top: 12px;
  color: var(--text-muted);
  font-size: 9px;
}

.readings-table {
  min-width: 1050px;
}

.events-table {
  min-width: 850px;
}

.timestamp-cell {
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.event-code {
  color: var(--text-primary);
  font-weight: 700;
}

.event-description {
  min-width: 220px;
  max-width: 360px;
  white-space: normal !important;
}

.event-description strong,
.event-description span {
  display: block;
}

.event-description strong {
  color: var(--text-primary);
  font-size: 11px;
}

.event-description span {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 10px;
  line-height: 1.5;
}

.cycle-cell {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-muted);
  font-size: 9px;
}

.severity-tag,
.event-state {
  display: inline-flex;
  align-items: center;
  padding: 4px 7px;
  border-radius: 4px;
  color: #ffffff;
  font-size: 9px;
  font-weight: 750;
  text-transform: uppercase;
}

.severity-critical,
.severity-high {
  background: var(--danger-hover);
}

.severity-warning {
  background: var(--warning-hover);
}

.severity-info {
  background: var(--info-hover);
}

.severity-default {
  background: var(--slate-color);
}

.event-active {
  background: var(--success-hover);
}

.event-cleared {
  background: var(--text-muted);
}

.history-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 11px;
  min-height: 110px;
  padding: 20px;
  background: var(--background-surface);
  border: 1px dashed var(--border-default);
  border-radius: 7px;
  color: var(--text-muted);
  font-size: 11px;
  text-align: center;
}

.history-error {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 13px 15px;
  border: 1px solid #f5c2c2;
  border-radius: 6px;
  color: var(--danger-color);
  background: #fdf2f2;
  font-size: 11px;
}

.history-error strong {
  font-weight: 750;
}

.export-error {
  margin-top: -10px;
}

.loading-ring {
  width: 15px;
  height: 15px;
  flex: 0 0 auto;
  border: 2px solid var(--border-default);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: history-spin 0.8s linear infinite;
}

@keyframes history-spin {
  to {
    transform: rotate(360deg);
  }
}

.cycle-picker {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 280px;
  flex: 1 1 320px;
}

.cycle-picker select {
  min-height: 36px;
  max-width: 100%;
  padding: 0 10px;
  background: var(--background-surface);
  border: 1px solid var(--border-default);
  border-radius: 5px;
  color: var(--text-primary);
}

.hour-navigation {
  display: flex;
  gap: 7px;
}

.hourly-table tbody tr {
  cursor: pointer;
}

.hourly-table tbody tr.selected-hour-row td,
.hourly-table tbody tr.selected-hour-row .sticky-column {
  background: var(--background-active);
}

.cycle-reason {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 11px 14px;
  background: var(--background-surface);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 11px;
}

.cycle-reason strong {
  color: var(--text-primary);
}

@media (max-width: 900px) {
  .statistics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .history-window {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 600px) {
  .history-heading,
  .history-section-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .history-window-meta {
    flex-wrap: wrap;
    gap: 18px;
  }
  .statistics-grid {
    grid-template-columns: 1fr;
  }
  .statistic-values strong {
    font-size: 14px;
  }
  .cycle-picker {
    min-width: 100%;
  }
  .hour-navigation {
    flex-wrap: wrap;
  }
}
</style>