// PLANTVIEW | Line 30
// Frontend source contract for KPI cards, process charts, and hourly status.

export const LINE_ID = "line30";

// Stable telemetry payload fields used by charts and KPIs.
export const TELEMETRY_FIELDS = {
  burnerSP: "Burner SP",
  deltaT: "DeltaT",
  burnerOutputLoad: "Burner Output Load",
  moisture: "Moisture PV",
  paddleSpeed: "Paddle Speed",
  oilLevel: "oil Level PV",
};

export const SECTOR_DISCIPLINES = [
  "Mechatronics",
  "Thermodynamics",
  "Process control",
  "Materials handling",
  "Power distribution",
  "Environmental",
];

export const OPERATING_BAND = {
  moisture: { low: 1.10, high: 1.30, unit: "fraction" },
  deltaT: { low: 0, high: 25, unit: "°C" },
  burnerOutputLoad: { low: 0, high: 100, unit: "%" },
  burnerPV: { low: 0, high: 100, unit: "°C" },
  paddleSpeed: { low: 0, high: 60, unit: "rpm" },
};

export const KPI_DEFINITIONS = [
  {
    id: "oil-temperature",
    label: "Oil Temperature",
    field: TELEMETRY_FIELDS.burnerPV,
    unit: "°C",
    accent: "blue",
    displayField: TELEMETRY_FIELDS.burnerPV,
    chartField: TELEMETRY_FIELDS.burnerPV,
    band: OPERATING_BAND.burnerPV,
  },
  {
    id: "delta-t",
    label: "Delta T",
    field: TELEMETRY_FIELDS.deltaT,
    unit: "°C",
    accent: "cyan",
    displayField: TELEMETRY_FIELDS.deltaT,
    chartField: TELEMETRY_FIELDS.deltaT,
    band: OPERATING_BAND.deltaT,
  },
  {
    id: "burner-load",
    label: "Burner Load",
    field: TELEMETRY_FIELDS.burnerOutputLoad,
    unit: "%",
    accent: "orange",
    displayField: TELEMETRY_FIELDS.burnerOutputLoad,
    chartField: TELEMETRY_FIELDS.burnerOutputLoad,
    band: OPERATING_BAND.burnerOutputLoad,
  },
  {
    id: "moisture",
    label: "Moisture",
    field: TELEMETRY_FIELDS.moisture,
    unit: "",
    accent: "violet",
    displayField: TELEMETRY_FIELDS.moisture,
    chartField: TELEMETRY_FIELDS.moisture,
    band: OPERATING_BAND.moisture,
  },
  {
    id: "paddle-speed",
    label: "Paddle Speed",
    field: TELEMETRY_FIELDS.paddleSpeed,
    unit: "",
    accent: "teal",
    displayField: TELEMETRY_FIELDS.paddleSpeed,
    chartField: TELEMETRY_FIELDS.paddleSpeed,
    band: OPERATING_BAND.paddleSpeed,
  },
  {
    id: "oil-level",
    label: "Oil Level",
    field: TELEMETRY_FIELDS.oilLevel,
    unit: "",
    accent: "slate",
    displayField: TELEMETRY_FIELDS.oilLevel,
    chartField: TELEMETRY_FIELDS.oilLevel,
    band: OPERATING_BAND.oilLevel,
  },
];

export const CHART_CONFIG = [
  {
    id: "delta-t",
    label: "Delta T",
    subtitle: "Temperature differential over time",
    type: "TIME_SERIES",
    chartField: TELEMETRY_FIELDS.deltaT,
    yName: "Delta T",
  },
  {
    id: "delta-t-burner",
    label: "Delta T vs Burner SP",
    subtitle: "Temperature differential against burner setpoint",
    type: "PROCESS_RELATIONSHIP",
    xChartField: TELEMETRY_FIELDS.burnerSP,
    yChartField: TELEMETRY_FIELDS.deltaT,
    xName: "Burner SP",
    yName: "Delta T",
  },
  {
    id: "delta-t-oil",
    label: "Delta T vs Oil Level",
    subtitle: "Temperature differential against oil level",
    type: "PROCESS_RELATIONSHIP",
    xChartField: TELEMETRY_FIELDS.oilLevel,
    yChartField: TELEMETRY_FIELDS.deltaT,
    xName: "Oil Level",
    yName: "Delta T",
  },
  {
    id: "burner-load",
    label: "Burner Load",
    subtitle: "Burner output load over time",
    type: "TIME_SERIES",
    chartField: TELEMETRY_FIELDS.burnerOutputLoad,
    yName: "Burner Output Load",
  },
  {
    id: "moisture",
    label: "Moisture",
    subtitle: "Moisture process value over time",
    type: "TIME_SERIES",
    chartField: TELEMETRY_FIELDS.moisture,
    yName: "Moisture PV",
  },
];

// Hourly window states used by the process overview and summary view.
export const HOURLY_STATUS = {
  LIVE: "live",
  PROGRESS: "progress",
  COMPLETE: "complete",
  NO_DATA: "no-data",
};
