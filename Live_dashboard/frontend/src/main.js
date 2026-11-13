import { createApp } from "vue";
import { createPinia } from "pinia";

import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent,
} from "echarts/components";

import App from "./App.vue";
import "./style.css";

use([
  CanvasRenderer,
  LineChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkLineComponent,
]);

const app = createApp(App);

app.use(createPinia());
app.mount("#app");
