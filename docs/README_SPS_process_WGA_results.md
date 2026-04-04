# SPS Process WGA Results — Script 2 Design Specification

## Overview

`SPS_process_WGA_results.py` is **Script 2** in the SPS library creation workflow. It sits between:

- **Script 1** (`SPS_initiate_project_folder_and_make_sort_plate_labels.py`) — which creates the project folder structure, generates plate layout CSVs, and populates `project_summary.db`
- **Script 3** (`SPS_process_WGA_results_and_make_SPITS.py`) — which takes a processed MDA results CSV and generates SPITS sequencing submission input

Script 2 reads all amplification kinetics files produced after WGA (Whole Genome Amplification / MDA), filters to passing wells, assigns destination library plate numbers, and writes a consolidated summary CSV that Script 3 uses as its primary input.

---

## Coding Style

This script follows the **functional programming style** used throughout this codebase — not object-oriented. All logic is implemented as standalone functions (not classes or methods). This is consistent with all other Python scripts in this workspace (e.g., `SPS_initiate_project_folder_and_make_sort_plate_labels.py`, `SPS_process_WGA_results_and_make_SPITS.py`, `SPS_rework_first_attempt_NEW.py`).

---

## Development Approach: Test-Driven Development (TDD)

Implementation must follow a **TDD approach with incremental testing** — do not build the entire script at once and then test. Instead:

1. Write a function (or small group of related functions)
2. Write automated tests for that function (using `pytest` or `unittest`)
3. Run the tests and confirm they pass
4. Perform a **manual test** against the real test data folder at:
   `/Users/RRMalmstrom/Desktop/Programming/Python/test_data_folders_for_SPS_scripts/boncat_peterson/`
5. Only then proceed to the next function

This applies to every stage: input reading, validation, filtering, sorting, column renaming, `Dest_plate` assignment, and output writing. Each stage should be verified before moving on.

Automated tests should be placed in a `tests/` directory (e.g., `tests/test_SPS_process_WGA_results.py`) and use small synthetic DataFrames or copies of the test data files as fixtures — not the live test data folder directly.

---

## Position in Workflow

```
Script 1: SPS_initiate_project_folder_and_make_sort_plate_labels.py
  └─► Creates: project_summary.db (tables: sample_metadata, individual_plates)
  └─► Creates: 2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/<plate_name>_plate_layout.csv
  └─► Creates: 2_sort_plates_and_amplify_genomes/B_WGA_results/  (empty — user places kinetics files here)

[WET LAB: Sort cells → Run MDA/WGA → Generate amplification kinetics files]

Script 2: SPS_process_WGA_results.py  ← THIS SCRIPT
  └─► Reads: project_summary.db (individual_plates table)
  └─► Reads: 2_sort_plates_and_amplify_genomes/B_WGA_results/*_amplification_kinetics_summary.csv
  └─► Validates: corresponding plate layout CSVs exist in A_sort_plate_layouts/
  └─► Writes: 2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/summary_MDA_results.csv

Script 3: SPS_process_WGA_results_and_make_SPITS.py
  └─► Reads: summary_MDA_results.csv (produced by Script 2)
  └─► Reads: project_summary.db (individual_plates table — for echo_id lookup)
  └─► Writes: output.csv (SPITS format), project_summary.csv, project_summary.db (updated)
```

---

## Usage

```bash
conda activate sip-lims
cd /path/to/project_directory
python SPS_process_WGA_results.py
```

No command-line arguments are required. The script auto-detects all input files from the project directory structure.

---

## Input Files

### 1. `project_summary.db` (SQLite database — project root)

Read via SQLAlchemy. The script queries the **`individual_plates`** table, which has the following columns:

| Column | Description |
|---|---|
| `plate_name` | Full plate name (e.g., `509735_WCBP1PR.1`) |
| `project` | Proposal/project identifier |
| `sample` | Group/sample abbreviation |
| `plate_number` | Integer plate number within the group |
| `is_custom` | Boolean — whether this is a custom plate |
| `barcode` | Echo liquid handler plate barcode (e.g., `MKD50-1`) |
| `created_timestamp` | ISO timestamp of plate creation |

The `barcode` column is used to **order plates** before concatenation (see Processing section). It is also the source of the `echo_id` that Script 3 will look up (Script 3 modification — see below).

### 2. Amplification Kinetics Files (`B_WGA_results/*_amplification_kinetics_summary.csv`)

One file per sort plate that has been amplified. Files are placed here manually by the user after WGA runs.

**Filename format:** `<plate_name>_amplification_kinetics_summary.csv`
**Example:** `509735_WCBP1PR.1_amplification_kinetics_summary.csv`

The plate name embedded in the filename (everything before `_amplification_kinetics_summary.csv`) must match the `Plate_ID` column inside the file.

**Columns (13 total, clean header on line 1):**

| Column | Type | Description |
|---|---|---|
| `Plate_ID` | string | Plate name (e.g., `509735_WCBP1PR.1`) |
| `Well_Row` | string | Row letter (e.g., `D`) |
| `Well_Col` | integer | Column number (e.g., `2`) |
| `Well` | string | Combined well position (e.g., `D2`) |
| `Sample` | string | Sample/group abbreviation |
| `Type` | string | Well type: `sample`, `neg_cntrl` (no `unused` rows present) |
| `number_of_cells/capsules` | numeric | Cell count sorted into well |
| `Group_1` | string | Replicate group label (e.g., `Rep1`, `Sheath_fluid`) |
| `Group_2` | string | Sort gate label (e.g., `BONCAT+`, `SYTO+`) |
| `Group_3` | string | Additional grouping (usually empty) |
| `Delta_Fluorescence` | float | Fluorescence increase during amplification |
| `Crossing_Point` | float | CP value from amplification kinetics (lower = better amplification) |
| `Pass_Fail` | string | `Pass` or `Fail` — MDA amplification result |

**Notes:**
- The file contains **only non-unused wells** — `sample` and `neg_cntrl` rows only. `unused` wells are not present.
- The file may have a UTF-8 BOM (`\ufeff`) at the start — pandas `read_csv` should handle this with `encoding='utf-8-sig'` or equivalent.

### 3. Plate Layout Files (`A_sort_plate_layouts/*_plate_layout.csv`) — Validation Only

One file per sort plate, created by Script 1. These files are **not read for data** — they are only checked for existence as a validation step.

**Filename format:** `<plate_name>_plate_layout.csv`

The script verifies that for every kinetics file found, a corresponding layout file exists. If a layout file is missing, the script terminates with a `FATAL ERROR`.

---

## Output Files

### `summary_MDA_results.csv`

**Location:** `2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/`

This directory is created by Script 2 if it does not already exist.

**Columns (14 total, in this order):**

| Column | Source | Notes |
|---|---|---|
| `Plate_id` | `Plate_ID` from kinetics file | Renamed to lowercase `i` for Script 3 compatibility |
| `Well` | `Well` from kinetics file | |
| `Row` | `Well_Row` from kinetics file | Renamed for Script 3 compatibility |
| `Col` | `Well_Col` from kinetics file | Renamed for Script 3 compatibility; integer |
| `Sample` | `Sample` from kinetics file | |
| `Type` | `Type` from kinetics file | `neg_cntrl` remapped to `negative`; `sample` unchanged |
| `number_of_cells/capsules` | `number_of_cells/capsules` from kinetics file | |
| `Group_1` | `Group_1` from kinetics file | |
| `Group_2` | `Group_2` from kinetics file | |
| `Group_3` | `Group_3` from kinetics file | |
| `Delta_Fluorescence` | `Delta_Fluorescence` from kinetics file | |
| `Crossing_Point` | `Crossing_Point` from kinetics file | |
| `Pass_Fail` | `Pass_Fail` from kinetics file | All rows in output have `Pass_Fail == 'Pass'` (applies to all row types equally) |
| `Dest_plate` | Computed by Script 2 | Integer starting at 1; assigned in 83-row bins |

---

## Processing Pipeline

```
1. Read project_summary.db → individual_plates table
   └─► Build plate_name → barcode lookup dict
   └─► Build ordered list of plate names sorted by barcode value

2. Scan B_WGA_results/ for *_amplification_kinetics_summary.csv files
   └─► Extract plate name from each filename
   └─► Verify corresponding *_plate_layout.csv exists in A_sort_plate_layouts/
       └─► FATAL ERROR + sys.exit() if any layout file is missing
   └─► Verify Plate_ID column inside kinetics file matches plate name from filename
       └─► FATAL ERROR + sys.exit() if mismatch found

3. For each kinetics file (processed in barcode order from individual_plates):
   └─► Read CSV with encoding='utf-8-sig' to handle BOM
   └─► Filter: keep only rows where Pass_Fail == 'Pass' (applies to all row types equally)
   └─► Sort filtered rows by Crossing_Point ascending (lowest CP first)

4. Concatenate all per-plate DataFrames vertically (in barcode order)

5. Rename columns for Script 3 compatibility:
   └─► Plate_ID → Plate_id
   └─► Well_Row → Row
   └─► Well_Col → Col

6. Remap Type values:
   └─► neg_cntrl → negative
   └─► sample → sample (unchanged)

7. Assign Dest_plate integers:
   └─► Sequentially number rows 0, 1, 2, ... across the full concatenated DataFrame
   └─► Dest_plate = (row_index // 83) + 1
   └─► Result: rows 0–82 → Dest_plate 1, rows 83–165 → Dest_plate 2, etc.
   └─► A single source plate CAN span multiple Dest_plate values if it has >83 rows
       (Script 3's checkSourcePlateDistribution() constraint is removed — see below)

8. Select and reorder columns to final output order:
   Plate_id, Well, Row, Col, Sample, Type, number_of_cells/capsules,
   Group_1, Group_2, Group_3, Delta_Fluorescence, Crossing_Point, Pass_Fail, Dest_plate

9. Create output directory C_WGA_summary_and_SPITS/ if it does not exist

10. Write summary_MDA_results.csv to C_WGA_summary_and_SPITS/

11. Create .workflow_status/SPS_process_WGA_results.success marker file
```

---

## Dest_plate Assignment Logic

The `Dest_plate` integer determines which library preparation plate each sample will be assigned to in Script 3. Assignment is fully automatic:

- All rows (samples + neg_cntrls) count equally toward the 83-row limit
- Rows are filled sequentially: the first 83 rows get `Dest_plate = 1`, the next 83 get `Dest_plate = 2`, and so on
- A source plate is **not** kept together — if a source plate contributes more than 83 rows, it will be split across multiple `Dest_plate` values
- The order of rows is determined by: (1) plate barcode order from `individual_plates` table, then (2) `Crossing_Point` ascending within each plate

**Example with 3 kinetics files:**

| Plate | Barcode | Passing rows | Dest_plate assignment |
|---|---|---|---|
| `509735_WCBP1PR.1` | `MKD50-1` | 72 rows | rows 0–71 → Dest_plate 1 |
| `509735_SitukAM.1` | `MKD50-7` | 60 rows | rows 72–82 → Dest_plate 1 (11 rows), rows 83–131 → Dest_plate 2 (49 rows) |
| `509735_SitukPR.2` | `MKD50-6` | 55 rows | rows 132–186 → Dest_plate 2 (remaining) + Dest_plate 3 |

---

## Validation and Error Handling

All errors use `FATAL ERROR:` prefix and call `sys.exit()` with no exit code, consistent with other scripts in this workspace.

| Condition | Behavior |
|---|---|
| `project_summary.db` not found in project root | FATAL ERROR + sys.exit() |
| `individual_plates` table missing from database | FATAL ERROR + sys.exit() |
| No `*_amplification_kinetics_summary.csv` files found in `B_WGA_results/` | FATAL ERROR + sys.exit() |
| Kinetics file found but corresponding `*_plate_layout.csv` missing from `A_sort_plate_layouts/` | FATAL ERROR listing missing files + sys.exit() |
| `Plate_ID` column value inside kinetics file does not match plate name from filename | FATAL ERROR listing mismatches + sys.exit() |
| Kinetics file plate name not found in `individual_plates` table | FATAL ERROR listing unmatched plates + sys.exit() |
| Output file already exists | Overwrite silently (no archiving needed — script is run once per project) |

---

## Required Modifications to Script 3 (`SPS_process_WGA_results_and_make_SPITS.py`)

The following changes to Script 3 are required to work with Script 2's output and the new workflow:

### 1. Remove `checkSourcePlateDistribution()`
This function aborts if any source plate appears in more than one `Dest_plate`. Since Script 2 now controls `Dest_plate` assignment and intentionally allows source plate splitting, this check must be removed from Script 3's processing pipeline.

### 2. Replace Echo Barcodes CSV input with database lookup
Script 3 currently requires a second input file (`SingleCell Query - Echo Barcodes.csv`) to map `Plate_id` values to Echo barcodes. This file is no longer needed. Instead, Script 3 should:
- Read `project_summary.db` from the project root
- Query the `individual_plates` table
- Look up `barcode` by matching `plate_name` to `Plate_id`
- Use this `barcode` value as the `echo_id`

The `addEchoId()` function should be replaced with a new function that performs this database lookup.

### 3. Update `importSCdata()` column reading
Script 3 currently reads only 6 columns via `usecols`. The new `summary_MDA_results.csv` has 14 columns. Script 3 should still read only the columns it needs (`Plate_id`, `Well`, `Type`, `Dest_plate`, `Row`, `Col`) — the extra columns are for user reference only and can be ignored by Script 3.

### 4. Update `Type` value handling
Script 3 currently expects `Type` values of `'sample'` or `'negative'`. Script 2 outputs `'negative'` (remapped from `neg_cntrl`). Verify Script 3's type-checking logic accepts `'negative'` correctly.

---

## Dependencies

```python
import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine
from datetime import datetime
```

---

## Conda Environment

`sip-lims` (same as all other scripts in this workflow)

---

## Test Data

A dummy project folder for testing is located at:
```
/Users/RRMalmstrom/Desktop/Programming/Python/test_data_folders_for_SPS_scripts/boncat_peterson/
```

This folder contains:
- `project_summary.db` with `individual_plates` table (8 plates, barcodes `MKD50-1` through `MKD50-8`)
- `2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/` — 8 plate layout CSVs
- `2_sort_plates_and_amplify_genomes/B_WGA_results/` — 3 kinetics files:
  - `509735_WCBP1PR.1_amplification_kinetics_summary.csv`
  - `509735_SitukAM.1_amplification_kinetics_summary.csv`
  - `509735_SitukPR.2_amplification_kinetics_summary.csv`

Note: Only 3 of the 8 plates have kinetics files — this is intentional and valid. The script processes only the plates that have kinetics files.

---

## Notes

- Script 2 is designed to be run **once per project**, after all intended WGA amplification runs are complete. It does not support incremental/subsequent runs.
- The `C_WGA_summary_and_SPITS/` output directory is created by Script 2 if it does not exist.
- Plates are processed in barcode order (from `individual_plates` table) to ensure deterministic, reproducible `Dest_plate` assignment.
- The `Crossing_Point` sort (ascending) within each plate prioritizes the best-amplified samples (lowest CP = strongest amplification) for earlier library plate positions.

---

**Author:** SPS Lab  
**Last Updated:** April 2026  
**Conda Environment:** `sip-lims`
