export type Status = "ok" | "stale" | "no_data";

export interface MachineStatus {
  machine_id: number;
  machine_name: string;
  last_seen: string | null;
  age_seconds: number | null;
  readings_last_minute: number;
  status: Status;
}

export interface Overview {
  server_time: string;
  stale_after_seconds: number;
  machines: MachineStatus[];
}

export interface Reading {
  reading_id: number;
  machine_id: number;
  machine_name: string;
  sensor_tag: string;
  sensor_value: number;
  timestamp: string;
}

export interface SeriesPoint {
  timestamp: string;
  sensor_value: number;
}

export type TagInfo = { name?: string; unit?: string };
