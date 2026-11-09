# Frontend Documentation

Vue 3 implementation reproducing the HTML dashboard visual direction and operator workflow.

## Component Hierarchy (8 components + App root)

- App.vue - Composition root, coordinates layout
- AppBar.vue - Brand, breadcrumb, connection indicator, source clock, reading counter
- DashboardToolbar.vue - Dataset range, replay controls, historical window, export
- KpiRow.vue - Six KPI cards (desktop) / three cards (mobile)
- KpiCard.vue - Individual KPI with value, unit, sparkline, alarm status
- ChartNav.vue - Five chart view selector items
- ChartPanel.vue - ECharts visualization with title, legend, current value, delta, data table
- OperationsGrid.vue - Alarms table + Event feed side-by-side

## Seven Composables

- useTelemetrySocket.js - WebSocket connection, reconnection
- useControlSocket.js - Send replay/alarm commands, correlate acks
- useAnimatedValue.js - Animate KPI value transitions
- useHistoryWindow.js - Load historical readings for selected window
- useChartOptions.js - Construct ECharts configurations
- useSparkline.js - Maintain and render KPI sparklines
- useFormatters.js - Time, number, unit and delta formatting

## Five Chart Views

1. Delta T
2. Delta T vs Burner SP
3. Delta T vs Oil Level
4. Burner Load
5. Moisture

## Visual Design System

- Light grey background (#F4F6F9)
- White content panels (#FFFFFF)
- Dark navy header (#0F1B2D)
- Blue primary accent (#2563EB)
- Status colors: Green/Amber/Red/Grey/Blue
