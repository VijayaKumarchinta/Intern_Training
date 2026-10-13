import type { Overview, Reading, SeriesPoint, TagInfo } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const fetchOverview = () => getJson<Overview>("/dashboard/overview");
export const fetchLatest = () => getJson<Reading[]>("/dashboard/latest");
export const fetchSeries = (machineId: number, tag: string, minutes: number) =>
  getJson<SeriesPoint[]>(
    `/dashboard/series?machine_id=${machineId}&sensor_tag=${encodeURIComponent(tag)}&minutes=${minutes}`,
  );
export const fetchTagInfo = () =>
  getJson<Record<string, TagInfo>>("/tags.json").catch(() => ({}));
