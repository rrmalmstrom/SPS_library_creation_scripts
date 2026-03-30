# SPS Initiate Project Folder and Make Sort Plate Labels

## Overview

`SPS_initiate_project_folder_and_make_sort_plate_labels.py` is the **first script run** in the SPS library creation workflow. It creates the standardized project folder structure, reads sample metadata, generates sort plate names, assigns incremental barcodes, and produces a BarTender-compatible label file for printing sort plate labels.

The script supports both **first runs** (new projects) and **subsequent runs** (adding plates to an existing project), automatically detecting which mode to use based on the presence of the project database.

---

## Features

- **Automatic run-type detection**: First run vs. subsequent run based on `project_summary.db`
- **Automatic CSV detection**: Finds `sample_metadtata.csv` (or any valid CSV) in the working directory
- **Standardized folder creation**: Creates the full SPS project folder hierarchy on first run
- **Simplified incremental barcodes**: `BASE-1`, `BASE-2`, … with optional custom base barcode via CLI
- **Echo/Hamilton label variants**: `eBASE-N` and `hBASE-N` generated at print time
- **BarTender file generation**: Reverse-ordered, interleaved echo/hamilton pairs with separators
- **Two-table SQLite database**: `sample_metadata` and `individual_plates` tables in `project_summary.db`
- **Timestamped file archiving**: Prevents overwrites on subsequent runs
- **Custom plates support**: File-based input via `custom_plate_names.txt`
- **Additional standard plates**: File-based input via `additional_standard_plates.txt`
- **Workflow manager integration**: Creates `.workflow_status/<script_name>.success` marker on completion

---

## Requirements

### Environment
- **Conda environment**: `sip-lims`
- **Python version**: 3.11+
- **Required packages**:
  - `pandas` — data manipulation
  - `sqlalchemy` — SQLite database access
  - `pathlib` — modern path handling (stdlib)
  - `argparse` — CLI argument parsing (stdlib)
  - `shutil`, `random`, `datetime` — stdlib utilities

---

## Project Folder Structure Created

Running this script on a new project creates the following directory tree in the working directory:

```
project_root/
├── 1_make_barcode_labels/
│   ├── bartender_barcode_labels/          ← BarTender .txt files moved here
│   └── previously_process_label_input_files/
│       ├── custom_plates/                 ← processed custom_plate_names.txt files
│       └── standard_plates/              ← processed additional_standard_plates.txt files
├── 2_sort_plates_and_amplify_genomes/
│   ├── A_sort_plate_layouts/
│   └── B_WGA_results/
├── 3_make_library_analyze_fa/
├── 4_pooling/
└── archived_files/                        ← timestamped database and CSV backups
```

---

## Input Files

### 1. Sample Metadata CSV (`sample_metadtata.csv`) — First Run Only
Place in the working directory before running. Required columns:

| Column | Description |
|--------|-------------|
| `Proposal` | Proposal identifier |
| `Project` | Project code (e.g., `BP9735`) |
| `Sample` | Sample name (e.g., `SitukAM`) |
| `Number_of_sorted_plates` | Integer count of sort plates for this sample |

Additional columns (optional but expected):
`Collection Year`, `Collection Month`, `Collection Day`, `Sample Isolated From`, `Latitude`, `Longitude`, `Depth (m)`, `Elevation (m)`, `Country`

### 2. Custom Plate Names (`custom_plate_names.txt`) — Optional, Any Run
One plate name per line. Each name must be **< 20 characters**.

**First run**: place in working directory.  
**Subsequent runs**: place in `1_make_barcode_labels/`.

```
Rex_badass_custom.1
MA_test_44.1
Custom_Plate_Name
```

### 3. Additional Standard Plates (`additional_standard_plates.txt`) — Optional, Subsequent Runs Only
One entry per line in `PROJECT_SAMPLE:COUNT` format.

**Subsequent runs only**: place in `1_make_barcode_labels/`.

```
BP9735_SitukAM:2
BP9735_WCBP1PR:1
```

This adds 2 more plates to `BP9735_SitukAM` and 1 more to `BP9735_WCBP1PR`, continuing plate numbering from where the previous run left off.

---

## Usage

### First Run (New Project)
```bash
conda activate sip-lims
cd /path/to/project_directory

# With auto-generated base barcode:
python SPS_initiate_project_folder_and_make_sort_plate_labels.py

# With custom base barcode (5-char, starts with letter, uppercase):
python SPS_initiate_project_folder_and_make_sort_plate_labels.py REX12
```

When prompted:
- `Add custom plates? (y/n):` — enter `y` to read `custom_plate_names.txt`, `n` to skip

### Subsequent Run (Adding Plates)
```bash
conda activate sip-lims
cd /path/to/project_directory
python SPS_initiate_project_folder_and_make_sort_plate_labels.py
```

When prompted:
- `Add additional standard plates to existing samples? (y/n):` — reads `1_make_barcode_labels/additional_standard_plates.txt`
- `Add custom plates? (y/n):` — reads `1_make_barcode_labels/custom_plate_names.txt`

---

## Barcode System

| Format | Example | Description |
|--------|---------|-------------|
| Base barcode | `REX12` | 5-char alphanumeric; first char must be a letter |
| Standard | `REX12-1`, `REX12-2` | Sequential per plate |
| Echo variant | `eREX12-1` | Lowercase `e` prefix; used for Echo liquid handler label |
| Hamilton variant | `hREX12-1` | Lowercase `h` prefix; used for Hamilton liquid handler label |

Barcodes continue incrementally across subsequent runs (e.g., if run 1 ended at `REX12-6`, run 2 starts at `REX12-7`).

---

## Output Files

### BarTender Label File
**`BARTENDER_sort_plate_labels_<timestamp>.txt`** — moved to `1_make_barcode_labels/bartender_barcode_labels/` after creation.

Format: reverse-ordered (highest barcode number first), interleaved echo/hamilton pairs separated by blank lines, with BarTender header and footer.

### Database
**`project_summary.db`** — SQLite database with two tables:
- `sample_metadata` — one row per sample from the input CSV
- `individual_plates` — one row per plate with barcode, plate name, project, sample, plate number, timestamp

A timestamped copy is archived to `archived_files/` before each update.

### CSV Exports
**`sample_metadata.csv`** and **`individual_plates.csv`** — regenerated after each run. Previous versions are archived to `archived_files/` with timestamps.

### Workflow Status Marker
**`.workflow_status/SPS_initiate_project_folder_and_make_sort_plate_labels.success`** — created on successful completion for workflow manager integration.

---

## Algorithm Details

### First Run Flow
1. Create full project folder structure (11 directories)
2. Auto-detect and read `sample_metadtata.csv`
3. Generate standard plate names (`PROJECT_SAMPLE.N`)
4. Optionally add custom plates from `custom_plate_names.txt`
5. Generate incremental barcodes (random or custom base)
6. Validate barcode uniqueness
7. Save to database, generate BarTender file, organize files, export CSVs

### Subsequent Run Flow
1. Ensure folder structure exists (no-op if already present)
2. Read existing database to get current plates and barcodes
3. Optionally add additional standard plates (continuing plate numbering)
4. Optionally add custom plates
5. Continue barcode numbering from highest existing barcode
6. Validate uniqueness across old + new barcodes
7. Append new plates to database, generate BarTender file for new plates only, organize files, export updated CSVs

---

## Error Handling

All errors follow the `FATAL ERROR:` prefix convention and call `sys.exit()` (no exit codes):

| Condition | Behavior |
|-----------|----------|
| Missing required CSV columns | FATAL ERROR + list of missing columns |
| Invalid `Number_of_sorted_plates` values | FATAL ERROR |
| No valid CSV found in working directory | FATAL ERROR |
| Multiple valid CSVs found | FATAL ERROR (ambiguous input) |
| Invalid custom base barcode format | FATAL ERROR with format rules |
| Duplicate barcodes generated | FATAL ERROR |
| Custom plate name ≥ 20 characters | FATAL ERROR |
| Invalid `additional_standard_plates.txt` format | FATAL ERROR with format example |
| Database read/write failure | FATAL ERROR |
| Folder creation failure | FATAL ERROR |

---

## Troubleshooting

### "FATAL ERROR: No sample metadata CSV file found"
- Ensure `sample_metadtata.csv` (note the typo — two `t`s in `metadtata`) is in the working directory on first run.
- On subsequent runs the CSV is not needed; the database is used instead.

### "FATAL ERROR: Multiple valid sample metadata CSV files found"
- Remove all but one valid CSV from the working directory.

### "FATAL ERROR: Invalid custom base barcode"
- Must be exactly 5 characters, first character a letter (A–Z), all uppercase letters or digits.
- Valid examples: `REX12`, `ABCD1`, `TEST9`

### "FATAL ERROR: Custom plates requested but 'custom_plate_names.txt' file not found"
- First run: create `custom_plate_names.txt` in the working directory.
- Subsequent run: create it in `1_make_barcode_labels/`.

### "EOFError" when piping input
- The script uses interactive `input()` prompts. Run it in an interactive terminal rather than piping stdin through `conda run`.

---

## Version History

### Current Version (SPS — March 2026)
- Renamed and adapted from `initiate_project_folder_and_make_sort_plate_labels.py` (capsule_sort_scripts)
- **Updated folder structure**: `2_sort_plates_and_amplify_genomes/` (with `A_sort_plate_layouts/` and `B_WGA_results/` subfolders), `3_make_library_analyze_fa/`, `4_pooling/` replacing the old `2_library_creation/`, `3_FA_analysis/`, `4_plate_selection_and_pooling/`
- **Updated `folders` dict keys**: `sort_plates_and_amplify`, `make_library_analyze_fa`, `pooling`, `sort_plate_layouts`, `wga_results`

### Previous Version (capsule_sort_scripts)
- Used `2_library_creation/`, `3_FA_analysis/`, `4_plate_selection_and_pooling/` folder names
- No `A_sort_plate_layouts/` or `B_WGA_results/` subfolders

---

**Author**: SPS Lab  
**Last Updated**: March 2026  
**Conda Environment**: `sip-lims`
