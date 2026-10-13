<script setup lang="ts">
import { computed, ref } from "vue";
import type { Reading, TagInfo } from "../types";

const props = defineProps<{
  readings: Reading[];
  tags: Record<string, TagInfo>;
  selectedTag: string | null;
}>();
defineEmits<{ select: [tag: string] }>();

const filter = ref("");
const rows = computed(() => {
  const q = filter.value.trim().toLowerCase();
  return props.readings.filter((r) => {
    if (!q) return true;
    const info = props.tags[r.sensor_tag];
    return r.sensor_tag.includes(q) || (info?.name ?? "").toLowerCase().includes(q);
  });
});
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <h2>Latest values</h2>
      <input v-model="filter" placeholder="Filter tag or name" />
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Tag</th><th>Name</th><th class="num">Value</th><th>Updated</th></tr>
        </thead>
        <tbody>
          <tr
            v-for="r in rows"
            :key="r.sensor_tag"
            :class="{ selected: r.sensor_tag === selectedTag }"
            @click="$emit('select', r.sensor_tag)"
          >
            <td>{{ r.sensor_tag }}</td>
            <td>{{ tags[r.sensor_tag]?.name || "—" }}</td>
            <td class="num">{{ r.sensor_value }} {{ tags[r.sensor_tag]?.unit ?? "" }}</td>
            <td>{{ new Date(r.timestamp).toLocaleTimeString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
