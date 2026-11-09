# Page skeleton

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  AppBar.vue                                                                                  │
├──────────────┬────────────────────────────────────────────────────┬──────────────────────────┤
│  PLANTVIEW   │  Line_Speed_30  >  Process Overview                │  ● live · 5 s · 16:42:11 │
│              │                                                    │  Readings 2139/2139      │
├──────────────┴────────────────────────────────────────────────────┴──────────────────────────┤
│  bind: logo/crumb (static) · dot ← ws.connected + pulse · conn ← ws.state                    │
│        refresh ← replay.speed · lastUpd ← latest.ts · prog ← manifest.total_readings         │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  PageTitle.vue                                                                               │
├──────────────────────────────────────────────────┬───────────────────────────────────────────┤
│  h1    Line Speed 30 · Process Overview           │  [17 Apr 2026 · 12:09–18:06]             │
│  meta  Line_Speed_30 replay · 17 Apr 2026         │  [Start] [Speed▼] [Live|15m|30m|45m|Full]│
│                                                   │  [Export CSV]                            │
├──────────────────────────────────────────────────┴───────────────────────────────────────────┤
│  children:  DateRange.vue · ReplayControls.vue · WindowTabs.vue · ExportButton.vue           │
│  bind:      manifest.display_name · manifest.first_ts/last_ts · history.window               │
│  actions:   ReplayControls → ws.send('replay.start' | 'replay.pause' | 'replay.speed')       │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  KpiRow.vue                                                                                  │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬────────────────────────┤
│ KpiCard #1  │ KpiCard #2  │ KpiCard #3  │ KpiCard #4  │ KpiCard #5  │ KpiCard #6             │
│ Oil temp    │ Delta T     │ Burner load │ Moisture    │ Paddle spd  │ Oil level              │
│ 183.6 °C    │ 25.2 °C     │ 91.7 %      │ 1.36 unit n/a│ 63.0 unit n/a│ 176.3 unit n/a       │
│ [sparkline] │ [sparkline] │ [sparkline] │ [sparkline] │ [sparkline] │ [sparkline]            │
│ ● Normal    │ ● Normal    │ ● At limit  │ ● Out-of-bd │ ● Normal    │ ● Normal               │
│ 176–191     │ 20.1–28.7   │ 15–100      │ 0.68–1.72   │ 46–181      │ 174–187                │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴────────────────────────┤
│  bind per card:  value ← latest.values.<key>  ·  unit ← constants.KPI_DEFS                   │
│                  status ← derive(latest.status, limits)                                      │
│                  sparkline ← history.series.<key>.slice(-60)                                 │
│                  so-far ← stats.signal.<key>.min / max                                       │
│  animations:     useAnimatedValue on .val · Sparkline redraws on every frame                 │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  ChartNav.vue                                                                                │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  [❶ Delta T]  [❷ ΔT vs Burner SP]  [❸ ΔT vs Oil Level]  [❹ Burner Load]  [❺ Moisture]        │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  bind:   tabs ← constants.CHARTS (5 entries)                                                 │
│          active ← route.query.chart                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  ChartPanel.vue                                                                              │
├───────────────────────────────────────────────────────────────────────┬──────────────────────┤
│  ptitle  Chart 2 · ΔT vs Burner SP (oil set temperature)              │ — ΔT   — SP          │
│  psub    Operator note (unverified): Oil Set Temperature should not…  │ legend               │
├───────────────────────────────────────────────────────────────────────┴──────────────────────┤
│  EChart.vue  (vue-echarts · ECharts 5.5.0)                                                   │
│                                                                                              │
│   26 ┤                     ╱╲                                                                │
│      │         ╱╲         ╱  ╲    ╱╲                                                         │
│   25 ┤   ╱╲   ╱  ╲   ╱╲  ╱    ╲  ╱  ╲                                                        │
│      │  ╱  ╲ ╱    ╲ ╱  ╲╱      ╲╱    ╲                                                       │
│   24 ┤ ╱    ╳      ╳                  ╲                                                      │
│      └───────────────────────────────────────────────►                                       │
│        12:09   12:34   12:59   13:24   13:49   14:14                                         │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  pstat    ΔT: 25.20 °C  +0.03    │    Burner SP: 184.94 °C  +0.00                            │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  bind:    title / sub / legend ← constants.CHARTS[active]                                    │
│           series ← history.series filtered to chart.series[*].k via useChartOptions          │
│           pstat ← latest.values[k] + delta vs previous frame                                 │
│  animate: ECharts animationDurationUpdate = 500                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┬─────────────────────────────────────────┐
│  AlarmsTable.vue                                   │  EventFeed.vue                          │
├────────────────────────────────────────────────────┼─────────────────────────────────────────┤
│  Active Alarms            2 active · prov. limits  │  Event History · Real-time     ● LIVE   │
├──────┬──────────────────────────────────┬──────────┼──────┬──────────────────────────────────┤
│ SEV  │ MESSAGE                          │ TIME     │ TIME │ EVENT + TAG                      │
├──────┼──────────────────────────────────┼──────────┼──────┼──────────────────────────────────┤
│ CRIT │ Moisture 1.32 above 1.30         │ 14:44    │ 14:44│ Moisture 1.32 above 1.30 · CRIT  │
│ WARN │ Burner load at 100%              │ 15:41    │ 15:41│ Burner load at 100% · WARN       │
│      │                                  │          │ 12:13│ Oil set point raised · INFO      │
│      │                                  │          │ 12:09│ Live stream started · SYS        │
│      │ [Ack] ← new                      │          │      │                                  │
├──────┴──────────────────────────────────┴──────────┼──────┴──────────────────────────────────┤
│  bind:  items ← alarms.active                      │  bind:  items ← events (WS broadcast)   │
│         severity ↦ .sev.crit / .warn / .info       │         tag ↦ .etag.ok/warn/crit/info/sys│
│         Ack → ws.send('alarm.ack', { alarm_id })   │  animate: evIn slide-in per new row     │
└────────────────────────────────────────────────────┴─────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┬───────────────────────────────┐
│  HistoryTable.vue                                            │  StatsTable.vue               │
├──────────────────────────────────────────────────────────────┼───────────────────────────────┤
│  Historical Readings · Last 12 samples · 12 samples          │  Statistics · readings so far │
├───────┬───────┬──────┬───────┬───────┬───────┬──────┬───┬───┼──────────┬──────┬──────┬────── ┤
│ TIME  │BURN PV│ ΔT   │OIL LVL│STACK  │MOIST  │PADDLE│XV │ST │ SIGNAL   │ MIN  │ AVG  │ MAX   │
├───────┼───────┼──────┼───────┼───────┼───────┼──────┼───┼───┼──────────┼──────┼──────┼────── ┤
│ 18:06 │186.4  │27.4  │180.5  │506.6  │1.134  │62.07 │CL │OK │ Oil tmp  │176.3 │184.9 │191.6  │
│ 18:05 │186.4  │27.3  │181.0  │506.5  │1.134  │62.07 │CL │OK │ Delta T  │20.1  │25.1  │28.7   │
│ 18:04 │186.3  │27.4  │179.5  │506.5  │1.134  │62.07 │CL │OK │ Burner   │15.3  │82.1  │100.0  │
│ 18:03 │186.6  │26.9  │181.3  │510.4  │1.097  │62.07 │OP │WARN│Moisture │0.68  │1.10  │1.72   │
│  …    │  …    │  …   │  …    │  …    │  …    │  …   │…  │…  │ Paddle   │46.5  │62.4  │181.0  │
│       │       │      │       │       │       │      │   │   │ Oil lvl  │174.4 │181.9 │187.6  │
├───────┴───────┴──────┴───────┴───────┴───────┴──────┴───┴───┼──────────┴──────┴──────┴────── ┤
│  bind:  rows ← history.series reversed (top 12)             │  bind:  ← stats.signal.<key>   │
│         STATUS flag ↦ .flag.ok/warn/crit                    │         .min .avg .max .out   │
│  animate: tr:first-child .fresh flash on new frame           │                               │
└──────────────────────────────────────────────────────────────┴───────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  StatusBar.vue                                                                               │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  Simulated stream · Line_Speed_30 replay        Source time · no tz · Cycle 1                │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│  bind:  cycle ← replay.cycle · mode text ← ws.state                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘

```Component tree (parent → child arrows)```

App.vue
│
├── AppBar.vue ─────────────────────────────────► stores/telemetry, stores/replay, useTelemetrySocket
│
├── <RouterView>
│   │
│   └── ProcessOverview.vue
│       │
│       ├── PageTitle.vue
│       │   ├── DateRange.vue ───────────────────► stores/manifest
│       │   ├── ReplayControls.vue ──────────────► useControlSocket → ws.send
│       │   ├── WindowTabs.vue ──────────────────► stores/history.window
│       │   └── ExportButton.vue ────────────────► api/export.js
│       │
│       ├── KpiRow.vue
│       │   └── KpiCard.vue  ×6
│       │       ├── Sparkline.vue ───────────────► composables/useSparkline
│       │       └── useAnimatedValue() ──────────► composables/useAnimatedValue
│       │
│       ├── ChartNav.vue ────────────────────────► constants.CHARTS
│       │
│       ├── ChartPanel.vue
│       │   └── EChart.vue ──────────────────────► vue-echarts
│       │       └── useChartOptions() ───────────► composables/useChartOptions
│       │
│       ├── AlarmsTable.vue ─────────────────────► stores/alarms + ws.send(alarm.ack)
│       ├── EventFeed.vue ───────────────────────► stores/telemetry.events
│       │
│       ├── HistoryTable.vue ────────────────────► stores/history (top 12)
│       └── StatsTable.vue ──────────────────────► stores/telemetry.stats
│
└── StatusBar.vue ───────────────────────────────► stores/replay, stores/telemetry

```Data flow diagram ```

   ┌───────────────────────────────────────────────────────────────────────────────────────┐
   │  Flask  /ws/v1  (single WebSocket · flask-sock)                                       │
   │    → frame "latest"        every ~10 s (data cadence)                                 │
   │    → frame "ack"           reply to a command                                         │
   │    → frame "replay.state"  broadcast  ┐                                               │
   │    → frame "alarm.acked"   broadcast  ┘                                               │
   └─────────────────────────────────────┬─────────────────────────────────────────────────┘
                                         │
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────────────────┐
   │  composables/useTelemetrySocket.js                                                    │
   │    latest.value   ← latest frame                                                      │
   │    connected      ← true / false                                                      │
   │    pulse          ← counter, +1 per frame                                             │
   │    reconnect      ← exponential backoff 0.5 s → 10 s                                  │
   └─────────────┬─────────────────────────────────────────────────┬───────────────────────┘
                 │                                                 │
                 ▼                                                 ▼
   ┌─────────────────────────────┐                 ┌──────────────────────────────────────┐
   │  stores/telemetry.js        │                 │  stores/alarms.js                    │
   │    latest                   │                 │    active                            │
   │    status                   │                 │    events                            │
   │    stats                    │                 │    ack (from broadcast)              │
   │    pulse                    │                 │                                      │
   └──────┬────────────────┬─────┘                 └─────────────────┬────────────────────┘
          │                │                                         │
          ▼                ▼                                         ▼
   ┌─────────────┐  ┌────────────┐                          ┌──────────────────────┐
   │  KpiRow     │  │  AppBar    │                          │  AlarmsTable         │
   │  ChartPanel │  │  StatusBar │                          │  EventFeed           │
   └─────────────┘  └────────────┘                          └──────────────────────┘
          ▲
          │
          │           ┌──────────────────────────────────────────────────────────────┐
          │           │  HTTP GET once on page load                                  │
          └───────────┤    /api/v1/history?window=full&limit=5000                    │
                      │    /api/v1/stats                                             │
                      │    /api/v1/manifest                                          │
                      │    /api/v1/alarms?active=true                                │
                      └──────────────────┬───────────────────────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────────┐
                              │  HistoryTable (seed 12)  │
                              │  StatsTable   (seed all) │
                              └──────────────────────────┘