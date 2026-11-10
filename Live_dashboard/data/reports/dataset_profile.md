# Line Speed 30 - Dataset Profiling Report

Source workbook: `Line_Speed_30.xlsx`

## 1. Workbook inventory

| Worksheet | Rows (including header) | Columns | State |
| --- | ---: | ---: | --- |
| Line_Speed_30 | 2140 | 35 | visible |
| Sheet1 | 55 | 15 | visible |

## 2. Worksheet: Line_Speed_30

- Data rows: 2,139
- Columns: 35
- Duplicate complete rows: 0

### Column profile

| Column | Data type | Missing | Missing % | Unique | Constant |
| --- | --- | ---: | ---: | ---: | --- |
| ;Date | str | 0 | 0.0% | 1 | True |
| Time | object | 0 | 0.0% | 2139 | False |
| Millitm | int64 | 0 | 0.0% | 915 | False |
| DeltaT | float64 | 0 | 0.0% | 2132 | False |
| Burner Output Load | float64 | 0 | 0.0% | 1673 | False |
| Burner PV | float64 | 0 | 0.0% | 2123 | False |
| Burner SP | float64 | 0 | 0.0% | 822 | False |
| {[PLC1]Input.Analogue.AT6802.O_Filtered} | float64 | 0 | 0.0% | 2137 | False |
| oil Level PV | float64 | 0 | 0.0% | 2129 | False |
| {[PLC1]Input.Analogue.TT4401.O_Filtered} | int64 | 0 | 0.0% | 1 | True |
| {[PLC1]Input.Analogue.TT5101.O_Filtered} | float64 | 0 | 0.0% | 2127 | False |
| Air Inlet To Burner | float64 | 0 | 0.0% | 2128 | False |
| Heat Exchanger Stack Temp | float64 | 0 | 0.0% | 2132 | False |
| APH Outlet | float64 | 0 | 0.0% | 2134 | False |
| Ambient Air Temp | float64 | 0 | 0.0% | 2104 | False |
| Oil Inlet Temperature | float64 | 0 | 0.0% | 2129 | False |
| {[PLC1]Input.Analogue.TT6102.O_Filtered} | float64 | 0 | 0.0% | 2135 | False |
| {[PLC1]Input.Analogue.TT7101.O_Filtered} | float64 | 0 | 0.0% | 2136 | False |
| {[PLC1]Input.Analogue.TT7102.O_Filtered} | float64 | 0 | 0.0% | 2134 | False |
| {[PLC1]Input.Analogue.TT7103.O_Filtered} | float64 | 0 | 0.0% | 2119 | False |
| Pump Loading | float64 | 0 | 0.0% | 2122 | False |
| Pump Load PV | float64 | 0 | 0.0% | 2117 | False |
| Pump load SP | float64 | 0 | 0.0% | 6 | False |
| {[PLC1]MoistureControl.I_MoistureHighSetpoint1} | float64 | 0 | 0.0% | 1 | True |
| {[PLC1]MoistureControl.I_MoistureHighSetpoint2} | float64 | 0 | 0.0% | 1 | True |
| {[PLC1]MoistureControl.I_MoistureLowSetpoint1} | float64 | 0 | 0.0% | 1 | True |
| {[PLC1]MoistureControl.I_MoistureLowSetpoint2} | float64 | 0 | 0.0% | 1 | True |
| {[PLC1]MoistureControl.O_SpeedPIDCV} | float64 | 0 | 0.0% | 779 | False |
| Moisture PV | float64 | 0 | 0.0% | 2139 | False |
| {[PLC1]MoistureControl.O_SpeedPIDSP} | float64 | 0 | 0.0% | 1 | True |
| {[PLC1]MoistureControl.O_TempPIDCV} | float64 | 0 | 0.0% | 822 | False |
| {[PLC1]MoistureControl.O_TempPIDPV} | float64 | 0 | 0.0% | 2139 | False |
| {[PLC1]MoistureControl.O_TempPIDSP} | float64 | 0 | 0.0% | 1 | True |
| Paddle Speed | float64 | 0 | 0.0% | 794 | False |
| {[PLC1]Valve.XV6601.OM_Open} | int64 | 0 | 0.0% | 2 | False |

### Possible date/time columns

`;Date`, `Time`, `Millitm`

## 2. Worksheet: Sheet1

- Data rows: 54
- Columns: 10
- Duplicate complete rows: 50

### Column profile

| Column | Data type | Missing | Missing % | Unique | Constant |
| --- | --- | ---: | ---: | ---: | --- |
| Unnamed: 0 | str | 52 | 96.3% | 2 | False |
| Unnamed: 1 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 2 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 3 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 4 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 5 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 6 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 7 | float64 | 54 | 100.0% | 0 | True |
| Unnamed: 8 | str | 53 | 98.15% | 1 | False |
| Unnamed: 9 | str | 53 | 98.15% | 1 | False |

### Possible date/time columns

No obvious candidates found.
