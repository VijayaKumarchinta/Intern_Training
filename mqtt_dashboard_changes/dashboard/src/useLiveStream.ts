import { onBeforeUnmount, ref } from "vue";
import type { Reading } from "./types";

/** Subscribes to /dashboard/stream (SSE). EventSource reconnects by itself and
 *  resends Last-Event-ID, so no readings are lost across a reconnect. */
export function useLiveStream(onReadings: (batch: Reading[]) => void) {
  const connected = ref(false);
  const lastEventAt = ref<number | null>(null);
  let source: EventSource | null = null;

  function start() {
    source = new EventSource("/dashboard/stream");
    source.onopen = () => (connected.value = true);
    source.onerror = () => (connected.value = false); // browser retries on its own
    source.addEventListener("hello", () => (lastEventAt.value = Date.now()));
    source.addEventListener("readings", (e) => {
      lastEventAt.value = Date.now();
      onReadings(JSON.parse((e as MessageEvent).data) as Reading[]);
    });
  }

  function stop() {
    source?.close();
    source = null;
  }

  onBeforeUnmount(stop);
  return { connected, lastEventAt, start, stop };
}
