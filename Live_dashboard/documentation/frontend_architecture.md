# 2. Frontend Architecture and Codebase Explanation

## 2.1 Responsibilities

The frontend is a single-page Vue 3 + Vite application. It has no page
navigation and no server-side rendering. Its only persistent connection to the
backend is a Socket.IO client. Everything else is chart data, history tables,
and CSV export handling.

## 2.2 Entry point and dependency graph

```text
index.html
  -> main.js
       -> createApp(App.vue)
            -> createPinia()
            -> import "./style.css"
  -> App.vue
       -> useTelemetryStore (Pinia)
       -> ProcessChart.vue
       -> HourlySummaryView.vue (history view only)
  -> telemetryStore.js
       -> telemetryApi (frontend/src/services/api.js)
       -> telemetrySocket (frontend/src/services/socket.js)
```

`package.json` declares the runtime dependencies:

- `vue` / `vue-echarts` — UI framework and charting
- `echarts` — visualization engine
- `pinia` — global state store
- `socket.io-client` — WebSocket transport

`vite.config.js` enables Vue SFC compilation. The environment base URL is
`src/services/api.js` and the Socket.IO URL is `src/services/socket.js`.

## 2.3 File-by-file map

### `src/main.js`

Creates the Vue app and installs Pinia. All application state is then owned by
`useTelemetryStore`.

### `src/App.vue`

The single root component. It does two jobs:

1. Renders the global chrome: brand topbar, connection status, clock,
   system health strip, KPI cards, live charts, operation activity, and error
   banner.
2. Routes between the two views:

| View | State | What is shown |
| --- | --- | --- |
| `overview` | `telemetry.activeView === "overview"` | KPI cards, live charts, activity list, refresh timer |
| `history` | `telemetry.activeView === "history"` | `HourlySummaryView` with all summary/reads/events props |

`App.vue` also exposes the small export handlers (`exportHourlySummary`,
`exportReadings`, `exportEvents`) that delegate to the store.

### `src/components/ProcessChart.vue`

A thin ECharts wrapper. It receives a chart config object and an array of
records, then:

1. Filters to records that have `event_ts` and `payload`.
2. Sorts chronologically.
3. Builds `seriesData` depending on the chart `id`:
   - `delta-t-burner` -> scatter of `Burner SP` vs `DeltaT`
   - `delta-t-oil` -> scatter of `oil Level PV` vs `DeltaT`
   - others -> line chart of `field` vs timestamp
4. Renders a tooltip, axis, sampling, moisture mark lines, and chart grid.

### `src/stores/telemetryStore.js`

The state container for the entire application. Pinia is used so the store is
shared between `App.vue` and child components.

Key state groups:

- Live telemetry state: `history`, `latestReading`, `currentCycleId`
- Historical view state: `hourlySummary`, `selectedHourSummary`,
  `recentReadings`, `events`, `replayCycles`, selection indices
- Loading and error state: `isLoading`, `hasLoaded`, `summaryError`,
  `readingsError`, `eventsError`, `exportError`
- Connection health state: `socketStatus`, `serverStatus`,
  `databaseStatus`, `mqttStatus`
- Refresh coordination state: `pendingTelemetry`, `pendingEvents`,
  `refreshTimer`, `refreshInProgress`

Key actions:

| Action | Purpose |
| --- | --- |
| `mergeRecords` | Deduplicates records by `replay_cycle_id:message_id`, keeps the newest 500, and updates `latestReading` |
| `handleTelemetryUpdate` | Queues a live record only when the active view is `overview` |
| `handleOperationalEvent` | Queues live events only when the active view is `overview` |
| `loadHealth`, `loadHistory`, `loadReplayCycles`, `loadCycleSummary`, `loadSelectedHour` | HTTP data loading actions |
| `selectCycle`, `selectHour`, `moveSelectedHour` | Historical view navigation |
| `flushPendingUpdates` | Applies queued live updates in one batch |
| `refreshDashboard` | Five-second overview refresh |
| `refreshHistoryView` | Full reload of the history view |
| `startRefreshTimer` / `stopRefreshTimer` | Interval lifecycle |
| `setActiveView` | View switching and timer coordination |
| `exportHourlySummary` / `exportReadings` / `exportEvents` | CSV download dispatch |
| `initialize` / `stop` | Socket lifecycle and cleanup |

### `src/services/api.js`

Provides `telemetryApi` with HTTP convenience methods:

- `getHealth()`
- `getLatest(lineId)`
- `getHistory({ lineId, limit, cycleId, start, end })`
- `getStatistics({ lineId, field, start, end })`
- `getHourlySummary({ lineId, hours, cycleId, hourStart })`
- `getEvents({ lineId, limit, cycleId, start, end })`
- `getReplayCycles({ lineId, limit })`
- `downloadHourlySummary(...)`
- `downloadReadings(...)`
- `downloadEvents(...)`

The `request` helper throws clear errors for network failures and non-JSON
responses. CSV downloads are handled separately by `downloadCsv`, which uses
the `Content-Disposition` header to name the file.

### `src/services/socket.js`

Creates a Socket.IO client with `transports: ["websocket"]`, `autoConnect:
false`, infinite reconnection, and a 10-second connection timeout. It exports
a single singleton: `telemetrySocket`.

### `src/components/HourlySummaryView.vue`

The historical drill-down view. It receives all data and navigation through
props and emits named events. It renders:

1. Cycle picker and replay status
2. Hourly summary table with AVG/MIN/MAX per metric and burner-at-100% duration
3. Selected-hour KPI statistics
4. Historical readings table
5. Operational events table
6. CSV export buttons

### `src/utils/templates.js`

A source contract describing which payload fields are consumed by the UI.
This keeps the UI and backend aligned on field names such as `Burner PV` and
`oil Level PV`.

## 2.4 State flow

```text
WebSocket
  -> telemetryStore
       -> mergeRecords (live), flushPendingUpdates
       -> render: App.vue / HourlySummaryView.vue
```

Live records are only merged into the live chart state when the user is on the
overview. Events are only merged into the history event list when the user is
on the history view. This prevents historical drill-down from being flooded by
irrelevant live telemetry.

## 2.5 Design decisions

- **Single Socket.IO connection**: one persistent connection replaces
  repeated HTTP polling for live data.
- **Pinia singleton store**: shared state across route-like view switching
  without URL routing.
- **Event-driven live updates**: immutable-ish reducers merge records and
  queue updates so the browser is not blocked by many small re-renders.
- **Explicit versioned exports**: CSV export is a client-generated download
  that fetches a server endpoint; the endpoint is also usable directly from a
  browser.
