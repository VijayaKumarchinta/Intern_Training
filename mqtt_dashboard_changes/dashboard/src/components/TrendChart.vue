<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import uPlot from "uplot";
import "uplot/dist/uPlot.min.css";
import type { SeriesPoint } from "../types";

const props = defineProps<{ points: SeriesPoint[]; label: string }>();
const el = ref<HTMLDivElement | null>(null);
let plot: uPlot | null = null;

const toData = (pts: SeriesPoint[]): uPlot.AlignedData => [
  pts.map((p) => new Date(p.timestamp).getTime() / 1000),
  pts.map((p) => p.sensor_value),
];

function build() {
  if (!el.value) return;
  plot?.destroy();
  plot = new uPlot(
    {
      width: el.value.clientWidth,
      height: 280,
      series: [{}, { label: props.label, stroke: "#2563eb", width: 2, points: { show: false } }],
      scales: { x: { time: true } },
    },
    toData(props.points),
    el.value,
  );
}

onMounted(() => {
  build();
  window.addEventListener("resize", build);
});
onBeforeUnmount(() => {
  window.removeEventListener("resize", build);
  plot?.destroy();
});
watch(() => props.label, build);
watch(() => props.points, (pts) => plot?.setData(toData(pts)), { deep: false });
</script>

<template>
  <div ref="el" class="chart" />
</template>
