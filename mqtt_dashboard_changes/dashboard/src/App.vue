<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, reactive, ref, shallowRef, watch } from "vue";
import { fetchLatest, fetchOverview, fetchSeries, fetchTagInfo } from "./api";
import { useLiveStream } from "./useLiveStream";
import MachineGrid from "./components/MachineGrid.vue";
import LatestTable from "./components/LatestTable.vue";
import TrendChart from "./components/TrendChart.vue";
import type { MachineStatus, Reading, SeriesPoint, TagInfo } from "./types";

const MAX_POINTS = 2000;

const machines = ref<MachineStatus[]>([]);
const staleAfter = ref(60);
const skewMs = ref(0); // server clock - browser clock
const now = ref(Date.now());
const latest = reactive(new Map<string, Reading>()); // key machine_id:tag
const tags = ref<Record<string, TagInfo>>({});
const selectedMachine = ref<number | null>(null);
const selectedTag = ref<string | null>(null);
const points = shallowRef<SeriesPoint[]>([]);
const minutes = ref(30);
const error = ref<string | null>(null);

const lastSeen = reactive(new Map<number, number>()); // machine_id -> ms (sensor time)
const perMinute = reactive(new Map<number, number[]>()); // machine_id -> arrival times (ms)

function onReadings(batch: Reading[]) {
  const arrival = Date.now();
  let add: SeriesPoint[] = [];
  for (const r of batch) {
    latest.set(`${r.machine_id}:${r.sensor_tag}`, r);
    const t = new Date(r.timestamp).getTime();
    if (t > (lastSeen.get(r.machine_id) ?? 0)) lastSeen.set(r.machine_id, t);
    const arr = perMinute.get(r.machine_id) ?? [];
    arr.push(arrival);
    perMinute.set(r.machine_id, arr);
    if (r.machine_id === selectedMachine.value && r.sensor_tag === selectedTag.value) {
      add.push({ timestamp: r.timestamp, sensor_value: r.sensor_value });
    }
  }
  if (add.length) points.value = [...points.value, ...add].slice(-MAX_POINTS);
}

const { connected, start } = useLiveStream(onReadings);

const liveMachines = computed<MachineStatus[]>(() =>
  machines.value.map((m) => {
    const seen = lastSeen.get(m.machine_id) ?? (m.last_seen ? new Date(m.last_seen).getTime() : null);
    if (seen === null) return { ...m, status: "no_data", age_seconds: null };
    const age = Math.max(0, (now.value + skewMs.value - seen) / 1000);
    const recent = (perMinute.get(m.machine_id) ?? []).filter((t) => now.value - t < 60_000).length;
    return {
      ...m,
      age_seconds: age,
      status: age > staleAfter.value ? "stale" : "ok",
      readings_last_minute: lastSeen.has(m.machine_id) ? recent : m.readings_last_minute,
    };
  }),
);

const machineReadings = computed(() =>
  [...latest.values()]
    .filter((r) => r.machine_id === selectedMachine.value)
    .sort((a, b) => a.sensor_tag.localeCompare(b.sensor_tag, undefined, { numeric: true })),
);

const chartLabel = computed(() => {
  const t = selectedTag.value;
  return t ? tags.value[t]?.name || `Tag ${t}` : "";
});

async function refreshOverview() {
  try {
    const o = await fetchOverview();
    machines.value = o.machines;
    staleAfter.value = o.stale_after_seconds;
    skewMs.value = new Date(o.server_time).getTime() - Date.now();
    error.value = null;
    if (selectedMachine.value === null && o.machines.length) selectedMachine.value = o.machines[0].machine_id;
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function loadSeries() {
  if (selectedMachine.value === null || !selectedTag.value) return;
  try {
    points.value = await fetchSeries(selectedMachine.value, selectedTag.value, minutes.value);
  } catch (e) {
    error.value = (e as Error).message;
  }
}

watch([selectedMachine, selectedTag, minutes], loadSeries);
watch(selectedMachine, () => (selectedTag.value = null));
watch(machineReadings, (rows) => {
  if (!selectedTag.value && rows.length) selectedTag.value = rows[0].sensor_tag;
});

let tick: number, poll: number;
onMounted(async () => {
  tags.value = await fetchTagInfo();
  await refreshOverview();
  for (const r of await fetchLatest()) latest.set(`${r.machine_id}:${r.sensor_tag}`, r);
  start();
  tick = window.setInterval(() => (now.value = Date.now()), 1000);
  poll = window.setInterval(refreshOverview, 15000); // safety net; SSE does the live work
});
onBeforeUnmount(() => {
  clearInterval(tick);
  clearInterval(poll);
});

const summary = computed(() => {
  const c = { ok: 0, stale: 0, no_data: 0 };
  for (const m of liveMachines.value) c[m.status]++;
  return c;
});
</script>

<template>
  <header>
    <h1>Machine Monitor</h1>
    <div class="badges">
      <span class="badge ok">{{ summary.ok }} OK</span>
      <span class="badge stale">{{ summary.stale }} stale</span>
      <span class="badge none">{{ summary.no_data }} no data</span>
      <span class="badge" :class="connected ? 'ok' : 'stale'">{{ connected ? "LIVE" : "reconnecting…" }}</span>
    </div>
  </header>

  <p v-if="error" class="error">Backend problem: {{ error }}</p>

  <MachineGrid :machines="liveMachines" :selected-id="selectedMachine" @select="(id) => (selectedMachine = id)" />

  <section class="split">
    <LatestTable :readings="machineReadings" :tags="tags" :selected-tag="selectedTag" @select="(t) => (selectedTag = t)" />
    <div class="panel">
      <div class="panel-head">
        <h2>{{ chartLabel || "Pick a tag" }}</h2>
        <select v-model.number="minutes">
          <option :value="5">5 min</option>
          <option :value="30">30 min</option>
          <option :value="120">2 h</option>
          <option :value="360">6 h</option>
        </select>
      </div>
      <TrendChart v-if="selectedTag" :points="points" :label="chartLabel" />
    </div>
  </section>
</template>
