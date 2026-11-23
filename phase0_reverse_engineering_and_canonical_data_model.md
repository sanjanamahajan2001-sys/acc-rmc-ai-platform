# ACC RMC AI Platform — Phase 0: Exhaustive Reverse Engineering & Domain Discovery Specification

> **Strict Notice**: This document contains 100% pure reverse engineering facts derived strictly from inspecting the raw Excel workbooks in `data/raw/`. All inferred architecture and proposed implementation details have been isolated into Phase 1 recommendations.

## 1. Executive Summary Fact Sheet

The ACC Ready-Mix Concrete (RMC) raw data repository consists of 6 core production workbooks categorized into two primary engineering domains:

1. **Batching Plant SCADA Logs & Dispatch Records** (`data/raw/batching_reports/`)
2. **Quality Assurance Laboratory & Mix Optimization Forecasts** (`data/raw/ft7_certificates/`)

## 2. Complete Workbook Inventory

| File Path | Sheet Count | Named Ranges Count | Total Populate Cells (Approx) | Primary Engineering Role |
| :--- | :--- | :--- | :--- | :--- |
| `batching_reports/01.06.26-K.xlsx` | 17 | 0 | High | Raw Production/QA Workbook |
| `batching_reports/02.06.26-K.xlsx` | 17 | 0 | High | Raw Production/QA Workbook |
| `batching_reports/03.02.26-K.xlsx` | 18 | 0 | High | Raw Production/QA Workbook |
| `batching_reports/04.02.26-K.xlsx` | 18 | 0 | High | Raw Production/QA Workbook |
| `ft7_certificates/FT7R5.xlsx` | 10 | 0 | High | Raw Production/QA Workbook |
| `ft7_certificates/StrenghtTrendR5.xlsx` | 19 | 16 | High | Raw Production/QA Workbook |


## 3. Exhaustive Worksheet-by-Worksheet Analysis

### Workbook: `batching_reports/01.06.26-K.xlsx`

#### Worksheet: `Batching Report`
- **Max Bounds**: Rows 1–3536, Columns 1–26 (A–Z)
- **Populated Rows**: 1305
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str, float` | `False` | `Summary of batch reports `, `Del. note nr.`, `6196.0` |
| 2 | **B** | `datetime, str, time, float` | `False` | `Customer`, `ADHISH - ADHISH CONSTRUCT`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `MIRAMAR`, `Formula name: ADHISH CONS` |
| 4 | **D** | `str, float` | `False` | `Truckmixer code`, `GA07F7625`, `Vol. mass.:` |
| 5 | **E** | `str, float` | `False` | `Theor.`, `4680.0`, `4524.0` |
| 6 | **F** | `str, float` | `False` | `%Moi`, `1.01`, `0.0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.2`, `0.6` |
| 9 | **I** | `str, float` | `False` | `Corr.`, `4544.0`, `4499.0` |
| 10 | **J** | `str, float` | `False` | `Batched`, `4526.0`, `4485.0` |
| 11 | **K** | `str, float` | `False` | `Diff.`, `-18.0`, `-14.0` |
| 12 | **L** | `str, float` | `False` | `Er%`, `*-0.4`, `*-0.3` |
| 13 | **M** | `str, float` | `False` | `Net/m3`, `754.0`, `748.0` |
| 14 | **N** | `str, float` | `False` | `Cns.wat`, `-136.0`, `-25.0` |
| 15 | **O** | `str, float` | `False` | `Abs.wat`, `145.0`, `25.0` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Columns`
- **Max Bounds**: Rows 1–1000, Columns 1–9 (A–I)
- **Populated Rows**: 70
- **Merged Cell Ranges**: 0
- **Formula Count**: 128
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `ArrayFormula, str` | `False` | `ADHISH - ADHISH CONSTRUCT`, `ADHISH - NS70302601001736`, `ADHISH - NS70302601001737` |
| 2 | **B** | `str` | `True` | `challan no.`, `1735`, `1736` |
| 3 | **C** | `ArrayFormula, str` | `False` | `Date of casting`, `01-06-26`, `01-06-26` |
| 4 | **D** | `ArrayFormula, str` | `False` | `mix grade`, `M-30`, `M-30` |
| 5 | **E** | `ArrayFormula, str` | `False` | `truck Number`, `GA07F7625`, `GA07F7628` |
| 6 | **F** | `ArrayFormula, str` | `False` | `load size`, `6.00`, `6.00` |
| 7 | **G** | `ArrayFormula, str` | `False` | `time batched`, `06:42:56`, `07:10:18` |
| 8 | **H** | `str` | `True` | `customer`, `ADHISH`, `ADHISH` |
| 9 | **I** | `ArrayFormula, str` | `False` | `Project site`, `MIRAMAR`, `MIRAMAR` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B2` | `=RIGHT(A2,4)` | `1735` |
| `H2` | `=TRIM(LEFT(A2, (FIND("-",A2)-1)))` | `ADHISH` |
| `B3` | `=RIGHT(A3,4)` | `1736` |
| `H3` | `=TRIM(LEFT(A3, (FIND("-",A3)-1)))` | `ADHISH` |
| `B4` | `=RIGHT(A4,4)` | `1737` |
| `H4` | `=TRIM(LEFT(A4, (FIND("-",A4)-1)))` | `ADHISH` |
| `B5` | `=RIGHT(A5,4)` | `1738` |
| `H5` | `=TRIM(LEFT(A5, (FIND("-",A5)-1)))` | `ADHISH` |
| `B6` | `=RIGHT(A6,4)` | `1739` |
| `H6` | `=TRIM(LEFT(A6, (FIND("-",A6)-1)))` | `PRIORITY` |
| `B7` | `=RIGHT(A7,4)` | `1740` |
| `H7` | `=TRIM(LEFT(A7, (FIND("-",A7)-1)))` | `ADHISH` |
| `B8` | `=RIGHT(A8,4)` | `1740` |
| `H8` | `=TRIM(LEFT(A8, (FIND("-",A8)-1)))` | `ADHISH` |
| `B9` | `=RIGHT(A9,4)` | `1741` |
| ... and 113 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1749`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 8
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `200.0` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `Gaja` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `36.84444444` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-40` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `01-06-26`, `1749`, `M-40` |
| 3 | **C** | `str, float` | `True` | `ACC LTD.`, `X258`, `8.64` |
| 4 | **D** | `str, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X260`, `2026-06-29 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `14:39:48`, `Site`, `R.KIRAN` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X262` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `01-06-26` |
| `B25` | `=B24+B27` | `2026-06-08 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-29 00:00:00` |
| `B32` | `=B31/22.5` | `38.04444444` |
| `C32` | `=C31/22.5` | `36.97777778` |
| `D32` | `=D31/22.5` | `35.51111111` |
| `B34` | `=AVERAGE(B32:D32)` | `36.84444444` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1750`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `190.0` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `Gaja` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-30` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `01-06-26`, `1750`, `M-30` |
| 3 | **C** | `str` | `False` | `ACC LTD.`, `X264` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X266`, `2026-06-29 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `14:55:12`, `Site`, `SAPSCON ENGG` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X268` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `01-06-26` |
| `B25` | `=B24+B27` | `2026-06-29 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-29 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1750 2`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 4
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-30` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str` | `True` | `01-06-26`, `1750`, `M-30` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X269`, `2026-06-29 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `14:55:12`, `Site`, `SAPSCON ENGG` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X271` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `01-06-26` |
| `E25` | `=B24+E27` | `2026-06-29 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1753`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `01-06-26`, `1753`, `M-25` |
| 3 | **C** | `str` | `False` | `ACC LTD.`, `X273` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X275`, `2026-06-29 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `16:46:42`, `Site`, `RUBAZ INFRAT` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X277` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `01-06-26` |
| `B25` | `=B24+B27` | `2026-06-29 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-29 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 5`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 6`
- **Max Bounds**: Rows 1–1016, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 7`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 8`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 9`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 10`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 11`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 12`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 13`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 14`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 15`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

### Workbook: `batching_reports/02.06.26-K.xlsx`

#### Worksheet: `Batching Report`
- **Max Bounds**: Rows 1–3568, Columns 1–26 (A–Z)
- **Populated Rows**: 1070
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, float` | `False` | `Summary of batch reports `, `Del. note nr.`, `6225.0` |
| 2 | **B** | `str, time, float` | `False` | `Customer`, `D S CONTRACT - NS70302601`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `BOMBOLIM`, `Formula name: D S CONTRAC` |
| 4 | **D** | `str, float` | `False` | `Truckmixer code`, `GA07F7625`, `Vol. mass.:` |
| 5 | **E** | `str, float` | `False` | `Theor.`, `2872.0`, `2936.0` |
| 6 | **F** | `str, float` | `False` | `%Moi`, `1.01`, `0.0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.5`, `0.6` |
| 9 | **I** | `str, float` | `False` | `Corr.`, `2804.0`, `2920.0` |
| 10 | **J** | `str, float` | `False` | `Batched`, `2879.0`, `2910.0` |
| 11 | **K** | `str, float` | `False` | `Diff.`, `75.0`, `-10.0` |
| 12 | **L** | `str, float` | `False` | `Er%`, `*2.7`, `-0.3` |
| 13 | **M** | `str, float` | `False` | `Net/m3`, `720.0`, `728.0` |
| 14 | **N** | `str, float` | `False` | `Cns.wat`, `-68.0`, `-16.0` |
| 15 | **O** | `str, float` | `False` | `Abs.wat`, `96.0`, `16.0` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Columns`
- **Max Bounds**: Rows 1–1000, Columns 1–9 (A–I)
- **Populated Rows**: 70
- **Merged Cell Ranges**: 0
- **Formula Count**: 127
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `ArrayFormula, str` | `False` | `D S CONTRACT - NS70302601`, `RAJESH - RAJESH CONSTRUCT`, `RAJESH - RAJESH CONSTRUCT` |
| 2 | **B** | `str` | `True` | `challan no.`, `1760`, `1771` |
| 3 | **C** | `ArrayFormula, str` | `False` | `Date of casting`, `02-06-26`, `02-06-26` |
| 4 | **D** | `ArrayFormula, str` | `False` | `mix grade`, `M-40`, `M-30` |
| 5 | **E** | `ArrayFormula, str` | `False` | `truck Number`, `GA07F7625`, `GA07F7632` |
| 6 | **F** | `ArrayFormula, str` | `False` | `load size`, `4.00`, `6.00` |
| 7 | **G** | `ArrayFormula, str` | `False` | `time batched`, `07:49:41`, `08:50:30` |
| 8 | **H** | `str` | `True` | `customer`, `D S CONTRACT`, `RAJESH` |
| 9 | **I** | `ArrayFormula, str` | `False` | `Project site`, `BOMBOLIM`, `CORLIM.` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B2` | `=RIGHT(A2,4)` | `1760` |
| `H2` | `=TRIM(LEFT(A2, (FIND("-",A2)-1)))` | `D S CONTRACT` |
| `B3` | `=RIGHT(A3,4)` | `1771` |
| `H3` | `=TRIM(LEFT(A3, (FIND("-",A3)-1)))` | `RAJESH` |
| `B4` | `=RIGHT(A4,4)` | `TION` |
| `H4` | `=TRIM(LEFT(A4, (FIND("-",A4)-1)))` | `RAJESH` |
| `B5` | `=RIGHT(A5,4)` | `TION` |
| `H5` | `=TRIM(LEFT(A5, (FIND("-",A5)-1)))` | `RAJESH` |
| `B6` | `=RIGHT(A6,4)` | `TION` |
| `H6` | `=TRIM(LEFT(A6, (FIND("-",A6)-1)))` | `RAJESH` |
| `B7` | `=RIGHT(A7,4)` | `TION` |
| `H7` | `=TRIM(LEFT(A7, (FIND("-",A7)-1)))` | `RAJESH` |
| `B8` | `=RIGHT(A8,4)` | `1761` |
| `H8` | `=TRIM(LEFT(A8, (FIND("-",A8)-1)))` | `R.KIRAN` |
| `H9` | `=TRIM(LEFT(A9, (FIND("-",A9)-1)))` | `RAJESH` |
| ... and 112 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1761`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 8
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `36.48888889` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-40` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `02-06-26`, `1761`, `M-40` |
| 3 | **C** | `str, float` | `True` | `ACC LTD.`, `X-294`, `8.6` |
| 4 | **D** | `str, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X-296`, `2026-06-30 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `11:13:15`, `Site`, `R.KIRAN` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X-298` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `02-06-26` |
| `B25` | `=B24+B27` | `2026-06-09 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-30 00:00:00` |
| `B32` | `=B31/22.5` | `37.15555556` |
| `C32` | `=C31/22.5` | `36.66666667` |
| `D32` | `=D31/22.5` | `35.64444444` |
| `B34` | `=AVERAGE(B32:D32)` | `36.48888889` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1762`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `36.43` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-40` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `190.0` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `02-06-26`, `1762`, `M-40` |
| 3 | **C** | `str, float` | `False` | `ACC LTD.`, `X-300`, `8.56` |
| 4 | **D** | `str, float` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X-302`, `2026-06-30 00:00:00`, `28.0` |
| 6 | **F** | `str, float` | `False` | `13:44:19`, `Site`, `190.0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X-304` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `02-06-26` |
| `B25` | `=B24+B27` | `2026-06-30 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-30 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `36.43` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `1766`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 4
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str` | `True` | `02-06-26`, `1766`, `M-25` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X-317`, `2026-06-30 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `16:06:10`, `Site`, `A&B ENTERPRI` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X-319` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `02-06-26` |
| `E25` | `=B24+E27` | `2026-06-30 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 4`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-30` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `680MM` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `02-06-26`, `1771`, `M-30` |
| 3 | **C** | `str` | `False` | `ACC LTD.`, `X 306` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X 308`, `2026-06-30 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `08:50:30`, `Site`, `680MM` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X 310` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `02-06-26` |
| `B25` | `=B24+B27` | `2026-06-09 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-30 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 5`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `RETE` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `700MM` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float` | `True` | `02-06-26`, `1776`, `RETE` |
| 3 | **C** | `str` | `False` | `ACC LTD.`, `X 312` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `X 314`, `2026-06-30 00:00:00`, `28.0` |
| 6 | **F** | `str` | `False` | `11:37:01`, `Site`, `700MM` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm`, `X 316` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `02-06-26` |
| `B25` | `=B24+B27` | `2026-06-09 00:00:00` |
| `E25` | `=B24+E27` | `2026-06-30 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 6`
- **Max Bounds**: Rows 1–1016, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 7`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 8`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 9`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 10`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 11`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 12`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 13`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 14`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 15`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 5
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `#DIV/0!` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `#DIV/0!` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `time, datetime, float, str, int` | `True` | `00:00:00`, `1454`, `0` |
| 3 | **C** | `str` | `False` | `ACC LTD.` |
| 4 | **D** | `str` | `False` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float` | `True` | `1900-01-28 00:00:00`, `28.0`, `#DIV/0!` |
| 6 | **F** | `str, int, time` | `False` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `False` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `B24` | `=B9` | `00:00:00` |
| `B25` | `=B24+B27` | `1900-01-07 00:00:00` |
| `E25` | `=B24+E27` | `1900-01-28 00:00:00` |
| `B34` | `=AVERAGE(B32:D32)` | `#DIV/0!` |
| `E34` | `=AVERAGE(E32:G32)` | `#DIV/0!` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

### Workbook: `batching_reports/03.02.26-K.xlsx`

#### Worksheet: `Batching Report`
- **Max Bounds**: Rows 1–3691, Columns 1–26 (A–Z)
- **Populated Rows**: 1059
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, int` | `False` | `Summary of batch reports `, `Del. note nr.`, `3076` |
| 2 | **B** | `str, float, time, int` | `False` | `Customer`, `PRIORITY - PRIORITY CONST`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `TALIGAO`, `Formula name: PRIORITY CO` |
| 4 | **D** | `str, float, int` | `False` | `Truckmixer code`, `GA 04 T 9209`, `Vol. mass.:` |
| 5 | **E** | `str, float, int` | `False` | `Theor.`, `4338`, `4548` |
| 6 | **F** | `str, int, float` | `False` | `%Moi`, `1.63`, `0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.2`, `0.6` |
| 9 | **I** | `str, float, int` | `False` | `Corr.`, `4273`, `4523` |
| 10 | **J** | `str, float, int` | `False` | `Batched`, `4279`, `4499` |
| 11 | **K** | `str, float, int` | `False` | `Diff.`, `6`, `-24` |
| 12 | **L** | `str, int, float` | `False` | `Er%`, `0.1`, `-0.5` |
| 13 | **M** | `str, float, int` | `False` | `Net/m3`, `713`, `750` |
| 14 | **N** | `str, int` | `False` | `Cns.wat`, `-65`, `-25` |
| 15 | **O** | `str, int` | `False` | `Abs.wat`, `135`, `25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Columns`
- **Max Bounds**: Rows 1–31, Columns 1–39 (A–AM)
- **Populated Rows**: 31
- **Merged Cell Ranges**: 0
- **Formula Count**: 1080
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, int` | `True` | `Client`, `PRIORITY - PRIORITY CONST`, `RAJDEEP - RAJDEEP BUILDER` |
| 2 | **B** | `str` | `True` | `Challan no.`, `7270`, `7271` |
| 3 | **C** | `str` | `False` | `Challan no. (Editable)`, `7270`, `7271` |
| 4 | **D** | `str` | `True` | `Date of casting`, `03-02-26`, `03-02-26` |
| 5 | **E** | `str` | `True` | `Mix grade`, `M-40`, `M-15` |
| 6 | **F** | `str, int` | `True` | `Truck Number`, `GA 04 T 9209`, `GA07F7625` |
| 7 | **G** | `str` | `True` | `Load size`, `6.00`, `6.00` |
| 8 | **H** | `str` | `True` | `Time batched`, `07:53:21`, `08:07:10` |
| 9 | **I** | `str` | `True` | `Customer`, `PRIORITY`, `RAJDEEP` |
| 10 | **J** | `str, int` | `True` | `Project site`, `TALIGAO`, `OLD GOA` |
| 11 | **K** | `str, int` | `True` | `CEMENT 1`, `CEMENT 1`, `CEMENT 1` |
| 12 | **L** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 13 | **M** | `str, int` | `True` | `1 m3`, `135`, `182` |
| 14 | **N** | `str, int` | `True` | `CEMENT 2`, `0`, `0` |
| 15 | **O** | `str, int` | `True` | `UM`, `0`, `0` |
| 16 | **P** | `str, int` | `True` | `1 m3`, `0`, `0` |
| 17 | **Q** | `str, int` | `True` | `CEMENT 3`, `CEMENT 3`, `CEMENT 3` |
| 18 | **R** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 19 | **S** | `str, int` | `True` | `1 m3`, `315`, `78` |
| 20 | **T** | `str, int` | `True` | `Admixture`, `ADMIXTURE 2`, `ADMIXTURE 2` |
| 21 | **U** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 22 | **V** | `str, int, float` | `True` | `1 m3`, `1.5`, `0.72` |
| 23 | **W** | `str, int` | `True` | `Water`, `WATER`, `WATER` |
| 24 | **X** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 25 | **Y** | `str, int` | `True` | `1 m3`, `155`, `155` |
| 26 | **Z** | `str` | `False` | `GGBS(Cement 1) Brand` |
| 27 | **AA** | `str` | `False` | `Cement (2,3) Brand` |
| 28 | **AB** | `str, int` | `True` | `SAND 1`, `0`, `SAND 1` |
| 29 | **AC** | `str, int` | `True` | `UM`, `0`, `Kg` |
| 30 | **AD** | `str, int` | `True` | `1 m3`, `0`, `465` |
| 31 | **AE** | `str, int` | `True` | `SAND 2`, `SAND 2`, `SAND 2` |
| 32 | **AF** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 33 | **AG** | `str, int` | `True` | `1 m3`, `723`, `465` |
| 34 | **AH** | `str, int` | `True` | `10 MM`, `10 MM`, `10 MM` |
| 35 | **AI** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 36 | **AJ** | `str, int` | `True` | `1 m3`, `418`, `450` |
| 37 | **AK** | `str, int` | `True` | `20 MM`, `20 MM`, `20 MM` |
| 38 | **AL** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 39 | **AM** | `str, int` | `True` | `1 m3`, `758`, `695` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `A2` | `=INDEX(CleanedData!B:B, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `PRIORITY - PRIORITY CONSTRUCTION NS70302501007270` |
| `B2` | `=RIGHT(A2,4)` | `7270` |
| `D2` | `=RIGHT(INDEX(CleanedData!B:B, 14 + (ROW('[1]FT7 1'!A1)-1) * 60),8)` | `03-02-26` |
| `E2` | `=RIGHT(INDEX(CleanedData!B:B, 17 + (ROW('[1]FT7 1'!A1)-1) * 60),4)` | `M-40` |
| `F2` | `=INDEX(CleanedData!D:D, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `GA 04 T 9209` |
| `G2` | `=RIGHT(INDEX(CleanedData!B:B, 9 + (ROW('[1]FT7 1'!A1)-1) * 60), 4)` | `6.00` |
| `H2` | `=RIGHT(INDEX(CleanedData!B:B, 15 + (ROW('[1]FT7 1'!A1)-1) * 60), 8)` | `07:53:21` |
| `I2` | `=TRIM(LEFT(A2, (FIND("-",A2)-1)))` | `PRIORITY` |
| `J2` | `=INDEX(CleanedData!C:C, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `TALIGAO` |
| `K2` | `=INDEX(CleanedData!$B:$B, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `CEMENT 1` |
| `L2` | `=INDEX(CleanedData!$C:$C, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `Kg` |
| `M2` | `=INDEX(CleanedData!$D:$D, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `135` |
| `N2` | `=INDEX(CleanedData!$B:$B, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| `O2` | `=INDEX(CleanedData!$C:$C, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| `P2` | `=INDEX(CleanedData!$D:$D, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| ... and 1065 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7274`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `49.87` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `34.62` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `200` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `#NAME?`, `7274` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 101`, `8.64` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 103`, `#NAME?`, `28` |
| 6 | **F** | `str, float, int` | `True` | `#NAME?`, `Site`, `200` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 105` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 101` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 102` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 103` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 104` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 105` |
| `B24` | `=B9` | `#NAME?` |
| `B25` | `=IF(B24="","", B24+B27)` | `#NAME?` |
| `E25` | `=IF(B24="","", B24+E27)` | `#NAME?` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `32.76` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `35.07` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `36.04` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `48.98` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `50.22` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `50.4` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `34.62` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7282`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `33.69` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `22.77` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `200` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `#NAME?`, `7282` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 107`, `8.72` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 109`, `#NAME?`, `28` |
| 6 | **F** | `str, float, int` | `True` | `#NAME?`, `Site`, `200` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 111` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 107` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 108` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 109` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 110` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 111` |
| `B24` | `=B9` | `#NAME?` |
| `B25` | `=IF(B24="","", B24+B27)` | `#NAME?` |
| `E25` | `=IF(B24="","", B24+E27)` | `#NAME?` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `23.91` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `21.91` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `22.49` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `34.49` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `34.93` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `31.64` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `22.77` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7291`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `30.58` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `22.34` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `#NAME?`, `7291` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 113`, `8.56` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 115`, `#NAME?`, `28` |
| 6 | **F** | `str, int, float` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 117` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 113` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 114` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 115` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 116` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 117` |
| `B24` | `=B9` | `#NAME?` |
| `B25` | `=IF(B24="","", B24+B27)` | `#NAME?` |
| `E25` | `=IF(B24="","", B24+E27)` | `#NAME?` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `22.49` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `23.07` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `21.47` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `31.47` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `30.76` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `29.51` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `22.34` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7295`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 15
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `41.15` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `29.58` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `190` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `#NAME?`, `7295` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 119`, `8.64` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 121`, `28`, `8.54` |
| 6 | **F** | `str, float, int` | `True` | `#NAME?`, `Site`, `190` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 123` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 119` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 120` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 121` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 122` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 123` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `31.02` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `28.22` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `29.51` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `41.24` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `39.78` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `42.44` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `29.58` |
| `E34` | `=IF(E32="","", (ROUND(AVERAGE(E32:G32),2)))` | `41.15` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7301`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `31.05` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `21.11` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `160` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `#NAME?`, `7301` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 125`, `8.64` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 127`, `#NAME?`, `28` |
| 6 | **F** | `str, float, int` | `True` | `#NAME?`, `Site`, `160` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 129` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 125` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 126` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 127` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 128` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 129` |
| `B24` | `=B9` | `#NAME?` |
| `B25` | `=IF(B24="","", B24+B27)` | `#NAME?` |
| `E25` | `=IF(B24="","", B24+E27)` | `#NAME?` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `21.73` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `20.71` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `20.89` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `30.76` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `31.02` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `31.38` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `21.11` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 6`
- **Max Bounds**: Rows 1–1000, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 7`
- **Max Bounds**: Rows 1–1000, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 8`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 9`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 10`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 11`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 12`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 13`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 14`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 15`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 16
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `#NAME?` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `#NAME?` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `ArrayFormula, str, int` | `True` | `NS70`, `#NAME?`, `#NAME?` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str` | `True` | `#NAME?`, `Site`, `#NAME?` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| `B32` | `=IF(B31="", "", ROUND((B31/22.5),2))` | `None` |
| `C32` | `=IF(C31="", "", ROUND((C31/22.5),2))` | `None` |
| `D32` | `=IF(D31="", "", ROUND((D31/22.5),2))` | `None` |
| `E32` | `=IF(E31="", "", ROUND((E31/22.5),2))` | `None` |
| `F32` | `=IF(F31="", "", ROUND((F31/22.5),2))` | `None` |
| `G32` | `=IF(G31="", "", ROUND((G31/22.5),2))` | `None` |
| `B34` | `=IF(B32="","", ROUND(AVERAGE(B32:D32),2))` | `None` |
| ... and 1 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `CleanedData`
- **Max Bounds**: Rows 1–1800, Columns 1–15 (A–O)
- **Populated Rows**: 1034
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, int` | `False` | `Summary of batch reports `, `Del. note nr.`, `3076` |
| 2 | **B** | `str, float, int` | `False` | `Customer`, `PRIORITY - PRIORITY CONST`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `TALIGAO`, `Formula name: PRIORITY CO` |
| 4 | **D** | `str, float, int` | `False` | `Truckmixer code`, `GA 04 T 9209`, `Vol. mass.:` |
| 5 | **E** | `str, float, int` | `False` | `Theor.`, `4338`, `2508` |
| 6 | **F** | `str, int, float` | `False` | `%Moi`, `1.63`, `0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.2`, `0.6` |
| 9 | **I** | `str, float, int` | `False` | `Corr.`, `4273`, `2493` |
| 10 | **J** | `str, float, int` | `False` | `Batched`, `4279`, `2502` |
| 11 | **K** | `str, float, int` | `False` | `Diff.`, `6`, `9` |
| 12 | **L** | `str, int, float` | `False` | `Er%`, `0.1`, `0.4` |
| 13 | **M** | `str, float, int` | `False` | `Net/m3`, `713`, `417` |
| 14 | **N** | `str, int` | `False` | `Cns.wat`, `-65`, `-15` |
| 15 | **O** | `str, int` | `False` | `Abs.wat`, `135`, `15` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

### Workbook: `batching_reports/04.02.26-K.xlsx`

#### Worksheet: `Batching Report`
- **Max Bounds**: Rows 1–3888, Columns 1–26 (A–Z)
- **Populated Rows**: 990
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, int` | `False` | `Summary of batch reports `, `Del. note nr.`, `3109` |
| 2 | **B** | `str, float, time, int` | `False` | `Customer`, `ALCON CO - ALCON CONSTRUC`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `RAIBANDER.`, `Formula name: ALCON CONST` |
| 4 | **D** | `str, float, int` | `False` | `Truckmixer code`, `GA07F7624`, `Vol. mass.:` |
| 5 | **E** | `str, float, int` | `False` | `Theor.`, `4530`, `4404` |
| 6 | **F** | `str, int, float` | `False` | `%Moi`, `1.01`, `0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.2`, `0.6` |
| 9 | **I** | `str, float, int` | `False` | `Corr.`, `4435`, `4379` |
| 10 | **J** | `str, float, int` | `False` | `Batched`, `4419`, `4353` |
| 11 | **K** | `str, float, int` | `False` | `Diff.`, `-16`, `-26` |
| 12 | **L** | `str, int, float` | `False` | `Er%`, `-0.4`, `-0.6` |
| 13 | **M** | `str, float, int` | `False` | `Net/m3`, `737`, `726` |
| 14 | **N** | `str, int` | `False` | `Cns.wat`, `-95`, `-25` |
| 15 | **O** | `str, int` | `False` | `Abs.wat`, `140`, `25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Columns`
- **Max Bounds**: Rows 1–23, Columns 1–39 (A–AM)
- **Populated Rows**: 23
- **Merged Cell Ranges**: 0
- **Formula Count**: 792
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `True` | `Client`, `ALCON CO - ALCON CONSTRUC`, `ALCON CO - ALCON CONSTRUC` |
| 2 | **B** | `str` | `True` | `Challan no.`, `7303`, `7304` |
| 3 | **C** | `str` | `False` | `Challan no. (Editable)`, `7303`, `7304` |
| 4 | **D** | `str` | `True` | `Date of casting`, `04-02-26`, `04-02-26` |
| 5 | **E** | `str` | `True` | `Mix grade`, `M-35`, `M-35` |
| 6 | **F** | `str` | `True` | `Truck Number`, `GA07F7624`, `GA 04 T 9209` |
| 7 | **G** | `str` | `True` | `Load size`, `6.00`, `6.00` |
| 8 | **H** | `str` | `True` | `Time batched`, `07:49:31`, `08:05:37` |
| 9 | **I** | `str` | `True` | `Customer`, `ALCON CO`, `ALCON CO` |
| 10 | **J** | `str` | `True` | `Project site`, `RAIBANDER.`, `RAIBANDER.` |
| 11 | **K** | `str` | `True` | `CEMENT 1`, `CEMENT 1`, `CEMENT 1` |
| 12 | **L** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 13 | **M** | `str, int` | `True` | `1 m3`, `120`, `120` |
| 14 | **N** | `str, int` | `True` | `CEMENT 2`, `0`, `0` |
| 15 | **O** | `str, int` | `True` | `UM`, `0`, `0` |
| 16 | **P** | `str, int` | `True` | `1 m3`, `0`, `0` |
| 17 | **Q** | `str, int` | `True` | `CEMENT 3`, `CEMENT 3`, `CEMENT 3` |
| 18 | **R** | `str, int` | `True` | `UM`, `Kg`, `Kg` |
| 19 | **S** | `str, int` | `True` | `1 m3`, `300`, `300` |
| 20 | **T** | `str` | `True` | `Admixture`, `ADMIXTURE 2`, `ADMIXTURE 2` |
| 21 | **U** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 22 | **V** | `str, int, float` | `True` | `1 m3`, `1.26`, `1.26` |
| 23 | **W** | `str` | `True` | `Water`, `WATER`, `WATER` |
| 24 | **X** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 25 | **Y** | `str, int` | `True` | `1 m3`, `160`, `160` |
| 26 | **Z** | `str` | `False` | `GGBS(Cement 1) Brand` |
| 27 | **AA** | `str` | `False` | `Cement (2,3) Brand` |
| 28 | **AB** | `str, int` | `True` | `SAND 1`, `0`, `0` |
| 29 | **AC** | `str, int` | `True` | `UM`, `0`, `0` |
| 30 | **AD** | `str, int` | `True` | `1 m3`, `0`, `0` |
| 31 | **AE** | `str` | `True` | `SAND 2`, `SAND 2`, `SAND 2` |
| 32 | **AF** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 33 | **AG** | `str, int` | `True` | `1 m3`, `755`, `755` |
| 34 | **AH** | `str` | `True` | `10 MM`, `10 MM`, `10 MM` |
| 35 | **AI** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 36 | **AJ** | `str, int` | `True` | `1 m3`, `426`, `426` |
| 37 | **AK** | `str` | `True` | `20 MM`, `20 MM`, `20 MM` |
| 38 | **AL** | `str` | `True` | `UM`, `Kg`, `Kg` |
| 39 | **AM** | `str, int` | `True` | `1 m3`, `734`, `734` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `A2` | `=INDEX(CleanedData!B:B, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `ALCON CO - ALCON CONSTRUCTION NS70302501007303` |
| `B2` | `=RIGHT(A2,4)` | `7303` |
| `D2` | `=RIGHT(INDEX(CleanedData!B:B, 14 + (ROW('[1]FT7 1'!A1)-1) * 60),8)` | `04-02-26` |
| `E2` | `=RIGHT(INDEX(CleanedData!B:B, 17 + (ROW('[1]FT7 1'!A1)-1) * 60),4)` | `M-35` |
| `F2` | `=INDEX(CleanedData!D:D, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `GA07F7624` |
| `G2` | `=RIGHT(INDEX(CleanedData!B:B, 9 + (ROW('[1]FT7 1'!A1)-1) * 60), 4)` | `6.00` |
| `H2` | `=RIGHT(INDEX(CleanedData!B:B, 15 + (ROW('[1]FT7 1'!A1)-1) * 60), 8)` | `07:49:31` |
| `I2` | `=TRIM(LEFT(A2, (FIND("-",A2)-1)))` | `ALCON CO` |
| `J2` | `=INDEX(CleanedData!C:C, 3 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `RAIBANDER.` |
| `K2` | `=INDEX(CleanedData!$B:$B, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `CEMENT 1` |
| `L2` | `=INDEX(CleanedData!$C:$C, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `Kg` |
| `M2` | `=INDEX(CleanedData!$D:$D, 28 + (ROW('[1]FT7 1'!A1)-1) * 60)` | `120` |
| `N2` | `=INDEX(CleanedData!$B:$B, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| `O2` | `=INDEX(CleanedData!$C:$C, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| `P2` | `=INDEX(CleanedData!$D:$D, 29 + (ROW('[1]FT7 1'!D1)-1) * 60)` | `0` |
| ... and 777 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7314`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `37.16` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `37.06` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-30` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `180` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float, int` | `True` | `NS70`, `04-02-26`, `7314` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 131`, `8.54` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 133`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, float, int` | `True` | `11:39:14`, `Site`, `180` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 135` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `11:39:14` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-30` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA07F7624` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `WIBRO` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `5.50` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `VALPAI` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 131` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 132` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 133` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 134` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 135` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7313`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 23
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `GAJA` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `29.17` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `120` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, int` | `True` | `NS70`, `04-02-26`, `7313` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 136`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, float, int` | `True` | `11:29:46`, `Site`, `120` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 138` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `11:29:46` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-25` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA08V5501` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `MARCON` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `6.00` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `CHIMBLE` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 137` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 138` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| `E25` | `=IF(B24="","", B24+E27)` | `2026-03-04 00:00:00` |
| ... and 8 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7304`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `40.31` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `28.58` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-35` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float, int` | `True` | `NS70`, `04-02-26`, `7304` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 140`, `8.6` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 142`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, int, float` | `True` | `08:05:37`, `Site`, `ALCON CO` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 144` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `08:05:37` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-35` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA 04 T 9209` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `ALCON CO` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `6.00` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `RAIBANDER.` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 140` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 141` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 142` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 143` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 144` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7318`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 23
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `SATISH` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `29.84` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `21.07` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `1560` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, float, int` | `True` | `NS70`, `04-02-26`, `7318` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 146`, `8.52` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, float, int` | `True` | `S 148`, `28`, `8.54` |
| 6 | **F** | `str, float, int` | `True` | `14:07:37`, `Site`, `1560` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 150` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `14:07:37` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-25` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA 08 V 4925` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `R B S` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `6.00` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `DECCAN` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 146` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 147` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 148` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 149` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 150` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| `E25` | `=IF(B24="","", B24+E27)` | `None` |
| ... and 8 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7319`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `30.12` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `20.91` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `180` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float, int` | `True` | `NS70`, `04-02-26`, `7319` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 152`, `8.54` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 154`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, float, int` | `True` | `14:17:23`, `Site`, `180` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 156` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `14:17:23` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-25` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA07F7625` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `M V R` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `4.00` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `BAMBOLIM` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 152` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 153` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 154` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 155` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 156` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7321`
- **Max Bounds**: Rows 1–1000, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `29.96` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `20.69` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-25` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `170` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float, int` | `True` | `NS70`, `04-02-26`, `7321` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 158`, `8.48` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 160`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, float, int` | `True` | `15:25:45`, `Site`, `170` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 162` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `15:25:45` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-25` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA07F7632` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `R Z MALPANI` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `4.00` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `MADKAI` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 158` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 159` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 160` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 161` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 162` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `7324`
- **Max Bounds**: Rows 1–1000, Columns 1–33 (A–AG)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `40.65` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `28.85` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `M-35` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `190` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `datetime, str, float, int` | `True` | `NS70`, `04-02-26`, `7324` |
| 3 | **C** | `str, int, float` | `True` | `ACC LTD.`, `S 164`, `8.58` |
| 4 | **D** | `str, int, float` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `datetime, str, float, int` | `True` | `S 166`, `2026-03-04 00:00:00`, `28` |
| 6 | **F** | `str, float, int` | `True` | `18:37:42`, `Site`, `190` |
| 7 | **G** | `str, int, float` | `True` | `Plant`, `150mm`, `S 168` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `18:37:42` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `04-02-26` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `M-35` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `GA 04 T 9209` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `ALCON CO` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `2.30` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `PONDA` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `S 164` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `S 165` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `S 166` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `S 167` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `S 168` |
| `B24` | `=B9` | `04-02-26` |
| `B25` | `=IF(B24="","", B24+B27)` | `2026-02-11 00:00:00` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 8`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 9`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 10`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 11`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 12`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 13`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 14`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `FT7 15`
- **Max Bounds**: Rows 1–1000, Columns 1–25 (A–Y)
- **Populated Rows**: 30
- **Merged Cell Ranges**: 39
- **Formula Count**: 24
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Merged Cell Inventory:
| Merged Range | Top-Left Cell | Top-Left Evaluated Value | Structural Purpose |
| :--- | :--- | :--- | :--- |
| `B16:C16` | Cell (`16,2`) | `` | Layout/Form Header |
| `D10:E10` | Cell (`10,4`) | `Cube casting time` | Layout/Form Header |
| `F10:G10` | Cell (`10,6`) | `` | Layout/Form Header |
| `F16:G16` | Cell (`16,6`) | `` | Layout/Form Header |
| `E34:G34` | Cell (`34,5`) | `` | Layout/Form Header |
| `B18:C18` | Cell (`18,2`) | `` | Layout/Form Header |
| `B34:D34` | Cell (`34,2`) | `` | Layout/Form Header |
| `B12:C12` | Cell (`12,2`) | `0` | Layout/Form Header |
| `F12:G12` | Cell (`12,6`) | `` | Layout/Form Header |
| `B11:C11` | Cell (`11,2`) | `0` | Layout/Form Header |
| ... and 29 more merged ranges | | | |


##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `FT 7 CERTIFICATE OF SAMPL`, `Plant Code`, `Date of Casting` |
| 2 | **B** | `str, int` | `True` | `NS70`, `0`, `0` |
| 3 | **C** | `str` | `True` | `ACC LTD.` |
| 4 | **D** | `str` | `True` | `Time Batched`, `Sample time`, `Cube casting time` |
| 5 | **E** | `str, int` | `True` | `28` |
| 6 | **F** | `str, int, time` | `True` | `00:00:00`, `Site`, `0` |
| 7 | **G** | `str` | `True` | `Plant`, `150mm` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `F8` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!H:H,0)` | `00:00:00` |
| `B9` | `=IF(B10="","", _xlfn.XLOOKUP($B$10,Columns!C:C,Columns!D:D,0))` | `None` |
| `B11` | `=_xlfn.XLOOKUP(B9,Columns!C:C,Columns!E:E,0)` | `0` |
| `B12` | `=_xlfn.XLOOKUP(B10,Columns!C:C,Columns!E:E,0)` | `0` |
| `B13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!F:F,0)` | `0` |
| `F13` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!I:I,0)` | `0` |
| `B14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!G:G,0)` | `0` |
| `F14` | `=_xlfn.XLOOKUP($B$10,Columns!C:C,Columns!J:J,0)` | `0` |
| `C22` | `=IF(B22="","", LEFT(B22,2) & TEXT(RIGHT(B22,3)+1, "000"))` | `None` |
| `D22` | `=IF(C22="","", LEFT(C22,2) & TEXT(RIGHT(C22,3)+1, "000"))` | `None` |
| `E22` | `=IF(D22="","", LEFT(D22,2) & TEXT(RIGHT(D22,3)+1, "000"))` | `None` |
| `F22` | `=IF(E22="","", LEFT(E22,2) & TEXT(RIGHT(E22,3)+1, "000"))` | `None` |
| `G22` | `=IF(F22="","", LEFT(F22,2) & TEXT(RIGHT(F22,3)+1, "000"))` | `None` |
| `B24` | `=B9` | `None` |
| `B25` | `=IF(B24="","", B24+B27)` | `None` |
| ... and 9 more formulas | | |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `CleanedData`
- **Max Bounds**: Rows 1–1320, Columns 1–15 (A–O)
- **Populated Rows**: 990
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str, int` | `False` | `Summary of batch reports `, `Del. note nr.`, `3109` |
| 2 | **B** | `str, float, int` | `False` | `Customer`, `ALCON CO - ALCON CONSTRUC`, `Total` |
| 3 | **C** | `str` | `False` | `Jobsite code`, `RAIBANDER.`, `Formula name: ALCON CONST` |
| 4 | **D** | `str, float, int` | `False` | `Truckmixer code`, `GA07F7624`, `Vol. mass.:` |
| 5 | **E** | `str, float, int` | `False` | `Theor.`, `4530`, `2556` |
| 6 | **F** | `str, int, float` | `False` | `%Moi`, `1.01`, `0` |
| 7 | **G** | `str` | `False` | `M`, `M`, `M` |
| 8 | **H** | `str, float` | `False` | `%Abs`, `3.2`, `0.6` |
| 9 | **I** | `str, float, int` | `False` | `Corr.`, `4435`, `2541` |
| 10 | **J** | `str, float, int` | `False` | `Batched`, `4419`, `2545` |
| 11 | **K** | `str, float, int` | `False` | `Diff.`, `-16`, `4` |
| 12 | **L** | `str, int, float` | `False` | `Er%`, `-0.4`, `0.2` |
| 13 | **M** | `str, float, int` | `False` | `Net/m3`, `737`, `424` |
| 14 | **N** | `str, int` | `False` | `Cns.wat`, `-95`, `-15` |
| 15 | **O** | `str, int` | `False` | `Abs.wat`, `140`, `15` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

### Workbook: `ft7_certificates/FT7R5.xlsx`

#### Worksheet: `Mix Design`
- **Max Bounds**: Rows 1–1272, Columns 1–4 (A–D)
- **Populated Rows**: 1272
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Code`, `Code: GEN JOCEL M-30`, `Code: GEN JOCEL M-30` |
| 2 | **B** | `str` | `False` | `Column2`, `Constituent name`, `SAND 2` |
| 3 | **C** | `str` | `False` | `Column3`, `UM`, `Kg` |
| 4 | **D** | `str` | `False` | `Column4`, `1 m3`, `775` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `28 Day Test (2)`
- **Max Bounds**: Rows 1–127, Columns 1–11 (A–K)
- **Populated Rows**: 127
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: [3, 4, 5, 6, 7, 9, 11, 12, 13, 15, 16, 20, 28, 29, 30, 32, 34, 35, 36, 38, 39, 40, 41, 42, 48, 49, 50, 60, 61, 64, 67, 68, 71, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 87, 89, 90, 91, 93, 94, 95, 96, 99, 100, 102, 103, 106, 107, 108, 109, 110, 111, 112, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127]
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Challan Number`, `0002`, `0005` |
| 2 | **B** | `str` | `False` | `Date of Casting`, `01-04-26`, `01-04-26` |
| 3 | **C** | `str, int, float` | `False` | `28 Day Strenght`, `33.69`, `42.04` |
| 4 | **D** | `str` | `False` | `Grade of Mix`, `M-25`, `M-30` |
| 5 | **E** | `str` | `False` | `GGBS`, `CEMENT 1`, `CEMENT 1` |
| 6 | **F** | `str, int` | `False` | `GGBS Quantity`, `160`, `170` |
| 7 | **G** | `str` | `False` | `OPC`, `CEMENT 3`, `CEMENT 3` |
| 8 | **H** | `str, int` | `False` | `OPC Quantity`, `160`, `200` |
| 9 | **I** | `str` | `False` | `Column17`, `Option 1`, `Option 1` |
| 10 | **J** | `str` | `False` | `Column18` |
| 11 | **K** | `str` | `False` | `Column19` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-10`
- **Max Bounds**: Rows 1–2, Columns 1–4 (A–D)
- **Populated Rows**: 2
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `60 OPC + 160 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `16.76` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `16.76` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `16.76` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-15`
- **Max Bounds**: Rows 1–3, Columns 1–4 (A–D)
- **Populated Rows**: 3
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `260 OPC`, `78 OPC + 182 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `21.1`, `20.46` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `21.1`, `20.46` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `21.1`, `20.46` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-20`
- **Max Bounds**: Rows 1–3, Columns 1–4 (A–D)
- **Populated Rows**: 3
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `150 OPC + 150 GGBS`, `180 OPC + 120 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `29.2`, `26.62` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `29.2`, `26.62` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `29.2`, `26.62` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-25`
- **Max Bounds**: Rows 1–11, Columns 1–4 (A–D)
- **Populated Rows**: 11
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `160 OPC + 160 GGBS`, `224 OPC + 96 GGBS` |
| 2 | **B** | `str, int, float` | `False` | `Average 28 Day Strengh`, `32.61`, `36.46` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `29.63`, `33.05` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `35.21`, `40.09` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-30`
- **Max Bounds**: Rows 1–14, Columns 1–4 (A–D)
- **Populated Rows**: 14
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `200 OPC + 170 GGBS`, `222 OPC + 148 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `41.28`, `41.97` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `40.52`, `38.25` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `42.04`, `46.33` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-35`
- **Max Bounds**: Rows 1–3, Columns 1–4 (A–D)
- **Populated Rows**: 3
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `256 OPC + 172 GGBS`, `210 OPC + 210 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `45.29`, `45.11` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `45.29`, `40.99` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `45.29`, `48.71` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-40`
- **Max Bounds**: Rows 1–6, Columns 1–4 (A–D)
- **Populated Rows**: 6
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `315 OPC + 135 GGBS`, `335 OPC + 100 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `49.26`, `52.44` |
| 3 | **C** | `str, float, int` | `False` | `Minimum 28 Day Strenght`, `42`, `48.44` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `53.38`, `56.99` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-45`
- **Max Bounds**: Rows 1–2, Columns 1–4 (A–D)
- **Populated Rows**: 2
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Mix Ratio`, `336 OPC + 144 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strengh`, `61.23` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght`, `61.23` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght`, `61.23` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

### Workbook: `ft7_certificates/StrenghtTrendR5.xlsx`

#### Worksheet: `Mix Designs`
- **Max Bounds**: Rows 1–1149, Columns 1–5 (A–E)
- **Populated Rows**: 1149
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Code`, `Code: DES M V R M-10`, `Code: DES M V R M-10` |
| 2 | **B** | `str` | `False` | `Grade`, `M-10`, `M-10` |
| 3 | **C** | `str` | `False` | `Constituent name`, `10 MM`, `20 MM` |
| 4 | **D** | `str` | `False` | `UM`, `Kg`, `Kg` |
| 5 | **E** | `str` | `False` | `1 m3`, `480`, `670` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-10`
- **Max Bounds**: Rows 1–3, Columns 1–5 (A–E)
- **Populated Rows**: 3
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `60 OPC + 160 GGBS`, `Grand Total` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `16.33`, `16.33` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght `, `15.9`, `15.9` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght `, `16.76`, `16.76` |
| 5 | **E** | `str, float` | `False` | `Average of Efficiency Rat`, `0.2721666666666666`, `0.2721666666666666` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-10 Mix Trend`
- **Max Bounds**: Rows 1–5, Columns 1–4 (A–D)
- **Populated Rows**: 4
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-04-05 00:00:00` |
| 2 | **B** | `str, float` | `False` | `(All)`, `Mix Design Strenght (28 D`, `16.76` |
| 3 | **C** | `str, float` | `False` | `Average of Average 28 Day`, `16.76`, `16.76` |
| 4 | **D** | `str, float` | `False` | `Target Strenght `, `15.8`, `15.8` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-15`
- **Max Bounds**: Rows 1–9, Columns 1–5 (A–E)
- **Populated Rows**: 9
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `78 OPC + 182 GGBS`, `130 OPC + 130 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `20.48`, `20.63` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght `, `19.47`, `19.91` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght `, `20.93`, `21.35` |
| 5 | **E** | `str, float` | `False` | `Average of Efficiency Rat`, `0.26256410256410256`, `0.1586923076923077` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-15 Mix Trend`
- **Max Bounds**: Rows 1–17, Columns 1–4 (A–D)
- **Populated Rows**: 16
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-01-07 00:00:00` |
| 2 | **B** | `str, float` | `False` | `(All)`, `Mix Design Strenght (28 D`, `21.56` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `21.56`, `20.61` |
| 4 | **D** | `str, float` | `False` | `Target Strenght `, `20.8`, `20.8` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-20`
- **Max Bounds**: Rows 1–4, Columns 1–5 (A–E)
- **Populated Rows**: 4
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `150 OPC + 150 GGBS`, `180 OPC + 120 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `29.22`, `26.31` |
| 3 | **C** | `str, float` | `False` | `Minimum 28 Day Strenght `, `25.44`, `25.64` |
| 4 | **D** | `str, float` | `False` | `Maximum 28 Day Strenght `, `34.19`, `26.74` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.1948`, `0.14616666666666667` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-20 Mix Trend`
- **Max Bounds**: Rows 1–12, Columns 1–4 (A–D)
- **Populated Rows**: 11
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-01-05 00:00:00` |
| 2 | **B** | `str, float` | `False` | `150 OPC + 150 GGBS`, `Mix Design Strenght (28 D`, `26.92` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `29.22`, `29.22` |
| 4 | **D** | `str, float` | `False` | `Average of Target Strengh`, `26.6`, `26.6` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-25`
- **Max Bounds**: Rows 1–22, Columns 1–5 (A–E)
- **Populated Rows**: 22
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `165 OPC + 165 GGBS`, `160 OPC + 160 GGBS` |
| 2 | **B** | `str, int, float` | `False` | `Average 28 Day Strenght`, `33.02`, `31.62` |
| 3 | **C** | `str, float` | `False` | `Average of Minimum 28 Day`, `29.17`, `26.83` |
| 4 | **D** | `str, float` | `False` | `Average of Maximum 28 Day`, `38.83`, `36.62` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.20012121212121214`, `0.197625` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-25 Mix Trend`
- **Max Bounds**: Rows 1–17, Columns 1–4 (A–D)
- **Populated Rows**: 16
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-04-01 00:00:00` |
| 2 | **B** | `str, float` | `False` | `160 OPC + 160 GGBS`, `Mix Design Strenght (28 D`, `33.69` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `31.62`, `31.62` |
| 4 | **D** | `str, float` | `False` | `Target Strenght `, `31.6`, `31.6` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-30`
- **Max Bounds**: Rows 1–32, Columns 1–5 (A–E)
- **Populated Rows**: 32
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `111 OPC + 259 GGBS`, `167 OPC + 203 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `41.05`, `40.85` |
| 3 | **C** | `str, float` | `False` | `Average of Minimum 28 Day`, `41.05`, `37.57` |
| 4 | **D** | `str, float` | `False` | `Average of Maximum 28 Day`, `41.05`, `44.74` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.3698198198198198`, `0.24461077844311377` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-30 Mix Trend`
- **Max Bounds**: Rows 1–51, Columns 1–4 (A–D)
- **Populated Rows**: 50
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-01-01 00:00:00` |
| 2 | **B** | `str, float` | `False` | `185 OPC + 185 GGBS`, `Mix Design Strenght (28 D`, `40.9` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `38.43`, `38.43` |
| 4 | **D** | `str, float` | `False` | `Target Strenght `, `38.25`, `38.25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-35`
- **Max Bounds**: Rows 1–10, Columns 1–5 (A–E)
- **Populated Rows**: 10
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `210 OPC + 210 GGBS`, `256 OPC + 172 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght `, `43.48`, `45.29` |
| 3 | **C** | `str, float` | `False` | `Average of Maximum 28 Day`, `48.71`, `45.29` |
| 4 | **D** | `str, float` | `False` | `Average of Minimum 28 Day`, `31.5`, `45.29` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.20704761904761904`, `0.1769140625` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-35 Mix Trend`
- **Max Bounds**: Rows 1–19, Columns 1–4 (A–D)
- **Populated Rows**: 18
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-01-05 00:00:00` |
| 2 | **B** | `str, float` | `False` | `210 OPC + 210 GGBS`, `Mix Design Strenght (28 D`, `43.88` |
| 3 | **C** | `str, float` | `False` | `Mix Design Strenght (28 D`, `43.48`, `43.48` |
| 4 | **D** | `str, float` | `False` | `Average of Target Strengh`, `43.25`, `43.25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-40`
- **Max Bounds**: Rows 1–7, Columns 1–5 (A–E)
- **Populated Rows**: 7
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `225 OPC + 225 GGBS`, `270 OPC + 180 GGBS` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `47.23`, `52.5` |
| 3 | **C** | `str, float` | `False` | `Average of Maximum 28 Day`, `48.15`, `54.31` |
| 4 | **D** | `str, float` | `False` | `Average of Minimum 28 Day`, `46.68`, `50.68` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.2099111111111111`, `0.19444444444444445` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-40 Mix Trend`
- **Max Bounds**: Rows 1–16, Columns 1–4 (A–D)
- **Populated Rows**: 15
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-03-25 00:00:00` |
| 2 | **B** | `str, float` | `False` | `335 OPC + 100 GGBS`, `Mix Design Strenght (28 D`, `50.275` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `52.19`, `52.19` |
| 4 | **D** | `str, float` | `False` | `Target Strenght `, `48.25`, `48.25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-45`
- **Max Bounds**: Rows 1–3, Columns 1–5 (A–E)
- **Populated Rows**: 3
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Row Labels`, `336 OPC + 144 GGBS`, `Grand Total` |
| 2 | **B** | `str, float` | `False` | `Average 28 Day Strenght`, `61.23`, `61.23` |
| 3 | **C** | `str, float` | `False` | `Average of Minimum 28 Day`, `61.23`, `61.23` |
| 4 | **D** | `str, float` | `False` | `Average of Maximum 28 Day`, `61.23`, `61.23` |
| 5 | **E** | `str, float` | `False` | `Efficiency Ratio `, `0.18223214285714284`, `0.18223214285714284` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `M-45 Mix Trend `
- **Max Bounds**: Rows 1–5, Columns 1–4 (A–D)
- **Populated Rows**: 4
- **Merged Cell Ranges**: 0
- **Formula Count**: 0
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `datetime, str` | `False` | `Mix Ratio`, `Row Labels`, `2026-04-21 00:00:00` |
| 2 | **B** | `str, float` | `False` | `(All)`, `Mix Design Strenght (28 D`, `61.23` |
| 3 | **C** | `str, float` | `False` | `Average 28 Day Strenght`, `61.23`, `61.23` |
| 4 | **D** | `str, float` | `False` | `Average of Target Strengh`, `53.25`, `53.25` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Forecast`
- **Max Bounds**: Rows 1–583, Columns 1–17 (A–Q)
- **Populated Rows**: 583
- **Merged Cell Ranges**: 0
- **Formula Count**: 10
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Grade of mix`, `M-25`, `M-30` |
| 2 | **B** | `str` | `False` | `Date of Casting`, `01-01-26`, `01-01-26` |
| 3 | **C** | `str` | `False` | `Mix Ratio`, `160 OPC + 160 GGBS`, `185 OPC + 185 GGBS` |
| 4 | **D** | `str, int` | `False` | `OPC `, `160`, `185` |
| 5 | **E** | `str, int` | `False` | `GGBS`, `160`, `185` |
| 6 | **F** | `str, int, float` | `False` | `ADMIXTURE 1m3`, `0.9`, `1` |
| 7 | **G** | `str, int` | `False` | `WATER 1m3`, `155`, `160` |
| 8 | **H** | `str, float` | `False` | `W/C Ratio Real`, `0.484`, `0.432` |
| 9 | **I** | `str, int, float` | `True` | `28 Day Strenght`, `29.9`, `42.36` |
| 11 | **K** | `str` | `False` | `R² (Model Fit):`, `Standard Error (MPa):`, `Training Data Points:` |
| 12 | **L** | `str, int, float` | `True` | `Regression Coefficients`, `GGBS Coef`, `0.11540458513741858` |
| 13 | **M** | `str, float` | `True` | `OPC Coef`, `0.13187989822077534` |
| 14 | **N** | `str, float` | `True` | `Intercept`, `-8.399350028168065` |
| 16 | **P** | `str` | `False` | `INPUT YOUR MIX DESIGN:`, `OPC Quantity (kg):`, `GGBS Quantity (kg):` |
| 17 | **Q** | `float, int` | `True` | `150`, `200`, `34.46355173243195` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `L3` | `=INDEX(LINEST(I2:I582,D2:E582,TRUE,FALSE),1,1)` | `0.11540458513741858` |
| `M3` | `=INDEX(LINEST(I2:I582,D2:E582,TRUE,FALSE),1,2)` | `0.13187989822077534` |
| `N3` | `=INDEX(LINEST(I2:I582,D2:E582,TRUE,FALSE),1,3)` | `-8.399350028168065` |
| `L9` | `=INDEX(LINEST(I2:I582,D2:E582,TRUE,TRUE),3,1)` | `0.7278825725677527` |
| `L10` | `=INDEX(LINEST(I2:I582,D2:E582,TRUE,TRUE),3,2)` | `3.811365018867989` |
| `L11` | `=COUNTA(D2:D100457)` | `581` |
| `Q11` | `=$N$3 + ($M$3 * Q6) + (L3 * Q7)` | `34.46355173243195` |
| `Q13` | `=IF(Q6>0, Q11/Q6, 0)` | `0.22975701154954634` |
| `Q15` | `=Q6+Q7` | `350` |
| `I583` | `=SUBTOTAL(101,Forecast[28 Day Strenght])` | `38.24032702237527` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

#### Worksheet: `Forecast 2`
- **Max Bounds**: Rows 1–582, Columns 1–17 (A–Q)
- **Populated Rows**: 582
- **Merged Cell Ranges**: 0
- **Formula Count**: 11
- **Hidden Rows**: []
- **Hidden Columns**: []

##### Column Dictionary:
| Col Index | Letter | Data Types Observed | Has Formulas? | Sample Observed Values |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **A** | `str` | `False` | `Grade of mix`, `M-10`, `M-10` |
| 2 | **B** | `str` | `False` | `Date of Casting`, `05-04-26`, `17-02-26` |
| 3 | **C** | `str` | `False` | `Mix Ratio`, `60 OPC + 160 GGBS`, `60 OPC + 160 GGBS` |
| 4 | **D** | `str, int` | `False` | `OPC `, `60`, `60` |
| 5 | **E** | `str, int` | `False` | `GGBS`, `160`, `160` |
| 6 | **F** | `str, int, float` | `False` | `ADMIXTURE 1m3`, `0.8`, `0.6` |
| 7 | **G** | `str, int` | `False` | `WATER 1m3`, `160`, `160` |
| 8 | **H** | `str, float` | `False` | `W/C Ratio Real`, `0.727`, `0.727` |
| 9 | **I** | `str, int, float` | `False` | `28 Day Strenght`, `16.76`, `15.9` |
| 11 | **K** | `str, float` | `True` | `Regression Coefficients`, `WATER COEF`, `0.11028132451774782` |
| 12 | **L** | `str, int, float` | `True` | `ADMIXTURE COEF`, `3.2457640700208055`, `0.7345508002768097` |
| 13 | **M** | `str, float` | `True` | `GGBS Coef`, `0.10384384032094444` |
| 14 | **N** | `str, float` | `True` | `OPC Coef`, `0.11693971207762441` |
| 15 | **O** | `str, float` | `True` | `Intercept`, `-24.668870689564958` |
| 16 | **P** | `str` | `False` | `INPUT YOUR MIX DESIGN:`, `OPC Quantity (kg):`, `GGBS Quantity (kg):` |
| 17 | **Q** | `float, int` | `True` | `160`, `160`, `0.8` |


##### Formulas Inventory:
| Cell Coordinate | Raw Excel Formula | Evaluated Value |
| :--- | :--- | :--- |
| `K3` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,FALSE),1,1)` | `0.11028132451774782` |
| `L3` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,FALSE),1,2)` | `3.2457640700208055` |
| `M3` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,FALSE),1,3)` | `0.10384384032094444` |
| `N3` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,FALSE),1,4)` | `0.11693971207762441` |
| `O3` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,FALSE),1,5)` | `-24.668870689564958` |
| `L9` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,TRUE),3,1)` | `0.7345508002768097` |
| `L10` | `=INDEX(LINEST(I2:I582,D2:G582,TRUE,TRUE),3,2)` | `3.7709064036385884` |
| `L11` | `=COUNT(I2:I582)` | `581` |
| `Q11` | `=$O$3 + ($Q$6*$N$3) + ($Q$7*$M$3)+ $Q$8*$L$3 + ($Q$9*$K$3)` | `30.898120873062354` |
| `Q13` | `=IF(Q6>0, Q11/Q6, 0)` | `0.1931132554566397` |
| `Q15` | `=Q6+Q7` | `320` |


##### Structural Row Layout Breakdown:
- **Rows 1–5**: Document Title / Form Header Metadata (Observed)
- **Rows 6–20**: Operational Attributes & Material Dosage Sub-tables
- **Rows 21–35**: Cube Specimen Testing & Compressive Strength Logs
- **Rows 36–50**: Laboratory Remarks, Signatures & Capture Stamp Metadata

--- 

## 4. Observed Facts vs Derived Terminology Matrix

| Concept | Source Sheet | Raw Observed Form | Derived Domain Meaning | Status |
| :--- | :--- | :--- | :--- | :--- |
| `Challan No` | `Columns` / `FT7` | `challan no.`, `Challan No.` | Primary Delivery Serial Identifier | **Observed Fact** |
| `OPC + GGBS` | `Forecast` | `160 OPC + 160 GGBS` | Composite Cementitious Binder Proportions | **Observed Fact** |
| `LINEST` Coefficients | `Forecast` | `=INDEX(LINEST(...),1,1)` | Multivariable Strength Prediction Weights | **Observed Fact** |
| `Plant` Entity | N/A | `Plant Code` header | Enterprise Plant Master | **Derived Fact** |
| `PostGIS / Redis` | N/A | None | Database & Feature Store Tech | **Proposed (Phase 1)** |

## 5. Complete RMC Formula & Business Rule Catalog

1. **Compressive Strength Calculation Formula** (`1749` cell `B32`):
   - Excel Formula: `=B31/22.5` (or `=B31/10.0` for 100mm cubes)
   - Engineering Meaning: MPa = Failure Load (kN) * 1000 / Surface Area (mm2)

2. **Water-to-Binder Mass Ratio Formula** (`Forecast` cell `H2`):
   - Excel Formula: `=G2/(D2+E2)`
   - Engineering Meaning: W/B = Water (kg) / (OPC (kg) + GGBS (kg))

3. **Multivariable Linear Regression Formula** (`Forecast` cell `L3`):
   - Excel Formula: `=INDEX(LINEST(I2:I582, D2:E582, TRUE, FALSE), 1, 1)`
   - Engineering Meaning: Least-squares linear estimation of 28-day compressive strength based on binder component dosages.

## 6. Recommended Phase 1 Implementation Boundaries

- **Ingestion Engine**: Implement dual OpenPyXL dynamic loader for template anchor matching.
- **Pydantic Data Contracts**: Define strict Python validation classes for `Delivery`, `Batch`, `FT7`, `CubeSpecimen`.
- **Database Schemas**: Implement PostgreSQL migration scripts (`Alembic`) for transaction tables.