<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { useTelemetryStore } from "./stores/telemetryStore";
import ProcessChart from "./components/ProcessChart.vue";
import HourlySummaryView from "./components/HourlySummaryView.vue";

const telemetry = useTelemetryStore();
const activeView = computed(() => telemetry.activeView);

const latestPayload = computed(
  () => telemetry.latestReading?.payload ?? {}
);

const kpis = computed(() => [
  { label: "Oil Temperature", field: "Burner PV", value: latestPayload.value["Burner PV"], unit: "°C", accent: "blue" },
  { label: "Delta T", field: "DeltaT", value: latestPayload.value.DeltaT, unit: "°C", accent: "cyan" },
  { label: "Burner Load", field: "Burner Output Load", value: latestPayload.value["Burner Output Load"], unit: "%", accent: "orange" },
  { label: "Moisture", field: "Moisture PV", value: latestPayload.value["Moisture PV"], unit: "", accent: "violet" },
  { label: "Paddle Speed", field: "Paddle Speed", value: latestPayload.value["Paddle Speed"], unit: "", accent: "teal" },
  { label: "Oil Level", field: "oil Level PV", value: latestPayload.value["oil Level PV"], unit: "", accent: "slate" },
]);

const charts = [
  { id: "delta-t", title: "Delta T", subtitle: "Temperature differential over time", type: "TIME SERIES", field: "DeltaT" },
  { id: "delta-t-burner", title: "Delta T vs Burner SP", subtitle: "Temperature differential against burner setpoint", type: "PROCESS RELATIONSHIP", field: "Burner SP · DeltaT" },
  { id: "delta-t-oil", title: "Delta T vs Oil Level", subtitle: "Temperature differential against oil level", type: "PROCESS RELATIONSHIP", field: "oil Level PV · DeltaT" },
  { id: "burner-load", title: "Burner Load", subtitle: "Burner output load over time", type: "TIME SERIES", field: "Burner Output Load" },
  { id: "moisture", title: "Moisture", subtitle: "Moisture process value over time", type: "TIME SERIES", field: "Moisture PV" },
];

const activity = computed(() =>
  [...telemetry.history]
    .sort((a, b) => Number(b.id) - Number(a.id))
    .slice(0, 6)
);

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "—";
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

function formatClock(value) {
  if (!value) return "Waiting for telemetry";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString("en-IN", { hour12: false });
}

function statusLabel(value) {
  const labels = {
    live: "SOCKET CONNECTED",
    connecting: "CONNECTING",
    reconnecting: "RECONNECTING",
    disconnected: "DISCONNECTED",
  };
  return labels[value] || "DISCONNECTED";
}

async function openHistoryView() {
  if (activeView.value === "history") return;
  await telemetry.setActiveView("history");
}

function refreshHistoryView() {
  return telemetry.refreshHistoryView();
}

function exportHourlySummary() {
  return telemetry.exportHourlySummary();
}

function exportReadings() {
  return telemetry.exportReadings();
}

function exportEvents() {
  return telemetry.exportEvents();
}

onMounted(() => telemetry.initialize());
onBeforeUnmount(() => telemetry.stop());
</script>

<template>
  <div class="plantview">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
        <div>
          <div class="brand-name">PLANT<span>VIEW</span></div>
          <div class="brand-caption">INDUSTRIAL MONITORING</div>
        </div>
      </div>

      <div class="topbar-center">
        <span class="breadcrumb-muted">PLANT OPERATIONS</span>
        <span class="breadcrumb-divider">/</span>
        <strong>Line 30</strong>
        <span class="line-chip">PROCESS LINE</span>
      </div>

      <div class="topbar-right">
        <div class="connection-indicator" :class="telemetry.connectionStatus">
          <span class="status-dot"></span>
          {{ statusLabel(telemetry.connectionStatus) }}
        </div>
        <div class="topbar-divider"></div>
        <div class="clock-block">
          <span class="clock-label">LAST RECEIVED</span>
          <strong>{{ formatClock(telemetry.lastUpdateAt) }}</strong>
        </div>
      </div>
    </header>

    <main class="dashboard">
      <nav class="view-navigation" aria-label="Dashboard views">
        <button
          type="button"
          class="view-navigation-button"
          :class="{ active: activeView === 'overview' }"
          :aria-current="activeView === 'overview' ? 'page' : undefined"
          @click="telemetry.setActiveView('overview')"
        >
          Process Overview
        </button>

        <button
          type="button"
          class="view-navigation-button"
          :class="{ active: activeView === 'history' }"
          :aria-current="activeView === 'history' ? 'page' : undefined"
          @click="openHistoryView"
        >
          Hourly Summary & History
        </button>
      </nav>

      <template v-if="activeView === 'overview'">
        <section class="page-heading">
          <div>
            <div class="eyebrow">PRODUCTION MONITORING <span>•</span> LINE 30</div>
            <h1>Process Overview</h1>
            <p class="page-description">
              Live process telemetry, operating conditions and historical trends.
            </p>
          </div>

          <div class="heading-meta">
            <div class="meta-item">
              <span class="meta-label">RECORDS IN VIEW</span>
              <strong>{{ telemetry.recordCount.toLocaleString("en-IN") }}</strong>
            </div>
            <div class="meta-item">
              <span class="meta-label">LATEST EVENT TIME</span>
              <strong>{{ formatTimestamp(telemetry.latestReading?.event_ts) }}</strong>
            </div>
          </div>
        </section>

        <section class="system-strip" aria-label="System health">
          <div class="system-strip-title">SYSTEM HEALTH</div>

          <div class="system-health-item">
            <span class="health-indicator" :class="telemetry.serverStatus"></span>
            <span>API</span>
            <strong>{{ telemetry.serverStatus.toUpperCase() }}</strong>
          </div>

          <div class="system-health-item">
            <span class="health-indicator" :class="telemetry.databaseStatus"></span>
            <span>DATABASE</span>
            <strong>{{ telemetry.databaseStatus.toUpperCase() }}</strong>
          </div>

          <div class="system-health-item">
            <span class="health-indicator" :class="telemetry.mqttStatus"></span>
            <span>MQTT BROKER</span>
            <strong>{{ telemetry.mqttStatus.toUpperCase() }}</strong>
          </div>

          <div class="system-strip-spacer"></div>
          <div class="source-label">
            <span class="source-icon">i</span>
            TELEMETRY SOURCE <strong>MQTT · LINE 30</strong>
          </div>
        </section>

        <section class="section-block">
          <div class="section-heading">
            <div>
              <div class="section-kicker">AT A GLANCE</div>
              <h2>Key Process Indicators</h2>
            </div>
            <span class="section-note">LATEST RECEIVED READING</span>
          </div>

          <div class="kpi-grid">
            <article
              v-for="item in kpis"
              :key="item.field"
              class="kpi-card"
              :class="'accent-' + item.accent"
            >
              <div class="kpi-topline">
                <span class="kpi-label">{{ item.label }}</span>
                <span class="kpi-indicator"></span>
              </div>

              <div class="kpi-value">
                {{ formatValue(item.value) }}
                <span v-if="item.unit" class="kpi-unit">{{ item.unit }}</span>
              </div>

              <div class="kpi-field">{{ item.field }}</div>
            </article>
          </div>
        </section>

        <section class="section-block charts-section">
          <div class="section-heading">
            <div>
              <div class="section-kicker">PROCESS ANALYTICS</div>
              <h2>Live Trends & Relationships</h2>
            </div>

            <div class="chart-section-meta">
              <span class="live-key"></span>
              <span>SOCKET STREAM</span>
              <span class="chart-window">UP TO 500 RECORDS</span>
            </div>
          </div>

          <div class="chart-grid">
            <article
              v-for="(chart, index) in charts"
              :key="chart.id"
              class="chart-card"
              :class="{ 'chart-card-featured': index === 0 }"
            >
              <div class="chart-card-header">
                <div>
                  <div class="chart-type">{{ chart.type }}</div>
                  <h3>{{ chart.title }}</h3>
                  <p>{{ chart.subtitle }}</p>
                </div>
                <span class="chart-index">0{{ index + 1 }}</span>
              </div>

              <div class="chart-canvas">
                <div
                  v-if="telemetry.isLoading && !telemetry.hasLoaded"
                  class="chart-empty"
                >
                  <span class="loading-ring"></span>
                  <span>Loading historical telemetry</span>
                </div>

                <ProcessChart
                  v-else
                  :chart="chart"
                  :records="telemetry.history"
                />
              </div>

              <div class="chart-card-footer">
                <span>FIELD <strong>{{ chart.field }}</strong></span>
                <span>{{ telemetry.recordCount }} POINTS AVAILABLE</span>
              </div>
            </article>
          </div>
        </section>

        <section class="section-block operations-section">
          <div class="section-heading">
            <div>
              <div class="section-kicker">OPERATIONS</div>
              <h2>Operational Activity</h2>
            </div>
          </div>

          <div class="operations-grid">
            <article class="panel-card">
              <div class="panel-heading">
                <div>
                  <h3>Alarm Management</h3>
                  <p>Process alarm state and acknowledgement</p>
                </div>
                <span class="integration-tag">MOISTURE RULE</span>
              </div>

              <div class="empty-panel">
                <div class="empty-panel-icon">!</div>
                <div>
                  <strong>Moisture alarm monitoring configured</strong>
                  <p>
                    LOW alarm below 1.10; HIGH alarm above 1.30. Values from 1.10 through 1.30 are within the operating range. Alarm transitions are persisted in operational event history.
                  </p>
                </div>
              </div>
            </article>

            <article class="panel-card">
              <div class="panel-heading">
                <div>
                  <h3>Telemetry Activity</h3>
                  <p>Most recently received process records</p>
                </div>
                <span class="activity-count">{{ activity.length }} RECORDS</span>
              </div>

              <div v-if="activity.length" class="activity-list">
                <div
                  v-for="record in activity"
                  :key="record.id"
                  class="activity-row"
                >
                  <span class="activity-marker"></span>

                  <div class="activity-main">
                    <strong>Telemetry record received</strong>
                    <span>
                      Cycle {{ record.replay_cycle_number ?? "—" }} · Record #{{ record.id }}
                    </span>
                  </div>

                  <div class="activity-time">
                    <strong>{{ formatClock(record.received_at) }}</strong>
                    <span>{{ formatValue(record.payload?.DeltaT) }} °C ΔT</span>
                  </div>
                </div>
              </div>

              <div v-else class="activity-empty">
                Waiting for the first telemetry record.
              </div>
            </article>
          </div>
        </section>

        <section v-if="telemetry.error" class="error-banner" role="status">
          <strong>Dashboard notice</strong>
          <span>{{ telemetry.error }}</span>
        </section>
      </template>

      <HourlySummaryView
        v-else
        :summary="telemetry.hourlySummary"
        :selected-hour-summary="telemetry.selectedHourSummary"
        :cycles="telemetry.replayCycles"
        :selected-cycle-id="telemetry.selectedCycleId"
        :selected-hour-start="telemetry.selectedHourStart"
        :selected-hour-index="telemetry.selectedHourIndex"
        :can-previous-hour="telemetry.canPreviousHour"
        :can-next-hour="telemetry.canNextHour"
        :cycles-loading="telemetry.cyclesLoading"
        :cycles-error="telemetry.cyclesError"
        :recent-readings="telemetry.recentReadings"
        :events="telemetry.events"
        :summary-loading="telemetry.summaryLoading"
        :readings-loading="telemetry.readingsLoading"
        :events-loading="telemetry.eventsLoading"
        :summary-error="telemetry.summaryError"
        :readings-error="telemetry.readingsError"
        :events-error="telemetry.eventsError"
        :exporting="telemetry.exporting"
        :export-error="telemetry.exportError"
        @refresh="refreshHistoryView"
        @select-cycle="telemetry.selectCycle"
        @select-hour="telemetry.selectHour"
        @previous-hour="telemetry.moveSelectedHour(-1)"
        @next-hour="telemetry.moveSelectedHour(1)"
        @export-hourly="exportHourlySummary"
        @export-readings="exportReadings"
        @export-events="exportEvents"
      />

      <footer class="dashboard-footer">
        <span>PLANTVIEW <b>·</b> LINE 30 MONITORING</span>
        <span>Event time and server receipt time are shown separately.</span>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.view-navigation {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 22px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-default);
}

.view-navigation-button {
  min-height: 36px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  color: var(--text-secondary);
  background: transparent;
  font: inherit;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.view-navigation-button:hover {
  color: var(--text-primary);
  background: var(--background-hover);
}

.view-navigation-button.active {
  color: var(--accent-primary);
  background: var(--background-surface);
  border-color: var(--accent-primary);
  box-shadow: 0 1px 2px rgba(20, 40, 61, 0.05);
}

.view-navigation-button:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

@media (max-width: 600px) {
  .view-navigation {
    overflow-x: auto;
  }

  .view-navigation-button {
    flex: 0 0 auto;
    padding: 0 11px;
  }
}
</style>
