<script setup lang="ts">
import type { MachineStatus } from "../types";

defineProps<{ machines: MachineStatus[]; selectedId: number | null }>();
defineEmits<{ select: [id: number] }>();

function age(s: number | null) {
  if (s === null) return "no data";
  if (s < 90) return `${Math.round(s)}s ago`;
  return `${Math.round(s / 60)}m ago`;
}
</script>

<template>
  <div class="grid">
    <button
      v-for="m in machines"
      :key="m.machine_id"
      class="card"
      :class="[m.status, { selected: m.machine_id === selectedId }]"
      @click="$emit('select', m.machine_id)"
    >
      <span class="dot" />
      <strong>{{ m.machine_name }}</strong>
      <small>{{ m.status === "ok" ? "OK" : m.status === "stale" ? "STALE" : "NO DATA" }} · {{ age(m.age_seconds) }}</small>
      <small>{{ m.readings_last_minute }} readings / min</small>
    </button>
  </div>
</template>
