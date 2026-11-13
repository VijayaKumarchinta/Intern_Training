<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";

const props = defineProps({
  chart: {
    type: Object,
    required: true,
  },
  records: {
    type: Array,
    default: () => [],
  },
});

function numericValue(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

const points = computed(() => {
  return [...props.records]
    .filter((record) => record?.event_ts && record?.payload)
    .sort(
      (a, b) =>
        new Date(a.event_ts).getTime() -
        new Date(b.event_ts).getTime()
    );
});

const seriesData = computed(() => {
  const config = props.chart;

  if (config.id === "delta-t-burner") {
    return points.value
      .map((record) => [
        numericValue(record.payload["Burner SP"]),
        numericValue(record.payload["DeltaT"]),
      ])
      .filter(([x, y]) => x !== null && y !== null);
  }

  if (config.id === "delta-t-oil") {
    return points.value
      .map((record) => [
        numericValue(record.payload["oil Level PV"]),
        numericValue(record.payload["DeltaT"]),
      ])
      .filter(([x, y]) => x !== null && y !== null);
  }

  return points.value
    .map((record) => [
      new Date(record.event_ts).getTime(),
      numericValue(record.payload[config.field]),
    ])
    .filter(([timestamp, value]) =>
      Number.isFinite(timestamp) && value !== null
    );
});

const isScatter = computed(() =>
  ["delta-t-burner", "delta-t-oil"].includes(props.chart.id)
);

const option = computed(() => {
  const scatter = isScatter.value;

  const xAxis = scatter
    ? {
        type: "value",
        name: props.chart.id === "delta-t-burner" ? "Burner SP" : "Oil Level",
        nameLocation: "middle",
        nameGap: 30,
        axisLabel: { color: "#8493a2", fontSize: 10 },
        splitLine: { lineStyle: { color: "#edf1f5" } },
        axisLine: { lineStyle: { color: "#dce4eb" } },
      }
    : {
        type: "time",
        axisLabel: {
          color: "#8493a2",
          fontSize: 10,
          hideOverlap: true,
        },
        splitLine: { show: false },
        axisLine: { lineStyle: { color: "#dce4eb" } },
      };

  const yAxis = {
    type: "value",
    name: scatter ? "Delta T" : "",
    axisLabel: {
      color: "#8493a2",
      fontSize: 10,
    },
    splitLine: {
      lineStyle: { color: "#edf1f5" },
    },
    axisLine: { show: false },
    scale: true,
  };

  const series = {
    type: scatter ? "scatter" : "line",
    data: seriesData.value,
    symbol: scatter ? "circle" : "none",
    symbolSize: scatter ? 7 : 5,
    smooth: !scatter,
    sampling: "lttb",
    emphasis: {
      focus: "series",
    },
    itemStyle: {
      color: "#3287c8",
    },
    lineStyle: {
      color: "#3287c8",
      width: 2,
    },
    areaStyle: scatter
      ? undefined
      : { color: "rgba(50, 135, 200, 0.07)" },
    ...(props.chart.id === "moisture"
      ? {
          markLine: {
            silent: true,
            symbol: ["none", "none"],
            label: {
              color: "#a27b35",
              fontSize: 9,
            },
            lineStyle: {
              color: "#d4a34f",
              type: "dashed",
              width: 1,
            },
            data: [
              { yAxis: 1.10, name: "Lower limit" },
              { yAxis: 1.30, name: "Upper limit" },
            ],
          },
        }
      : {}),
  };

  return {
    animation: false,
    grid: {
      top: 20,
      right: 22,
      bottom: 42,
      left: 52,
      containLabel: true,
    },
    tooltip: {
      trigger: scatter ? "item" : "axis",
      backgroundColor: "#172b40",
      borderWidth: 0,
      textStyle: {
        color: "#ffffff",
        fontSize: 11,
      },
      ...(scatter
        ? {
            formatter(params) {
              return [
                `${xAxis.name}: ${Number(params.value[0]).toFixed(2)}`,
                `Delta T: ${Number(params.value[1]).toFixed(2)} °C`,
              ].join("<br/>");
            },
          }
        : {
            formatter(params) {
              const point = Array.isArray(params) ? params[0] : params;
              const date = new Date(point.value[0]);

              return [
                date.toLocaleString("en-IN"),
                `${props.chart.title}: ${Number(point.value[1]).toFixed(2)}`,
              ].join("<br/>");
            },
          }),
    },
    xAxis,
    yAxis,
    series: [series],
    dataZoom: scatter
      ? []
      : [
          {
            type: "inside",
            filterMode: "none",
          },
        ],
  };
});
</script>

<template>
  <div class="process-chart">
    <VChart
    v-if="seriesData.length"
    :option="option"
    :init-options="{ renderer: 'canvas' }"
    autoresize
    class="echart-instance"
  />
    <div v-else class="chart-empty">
      <span class="empty-mark">—</span>
      <span>No telemetry records available</span>
    </div>
  </div>
</template>
