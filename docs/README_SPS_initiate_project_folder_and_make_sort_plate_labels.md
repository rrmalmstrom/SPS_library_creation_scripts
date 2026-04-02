# SPS Initiate Project Folder and Make Sort Plate Labels

## Overview

`SPS_initiate_project_folder_and_make_sort_plate_labels.py` is the **first script run** in the SPS library creation workflow. It creates the standardized project folder structure, reads sample metadata, generates sort plate names, assigns incremental barcodes, and produces a BarTender-compatible label file for printing sort plate labels.

The script supports both **first runs** (new projects) and **subsequent runs** (adding plates to an existing project), automatically detecting which mode to use based on the presence of the project database.

---

## Features

- **Experiment type selection**: Interactive prompt on first run selects Standard SPS-CE, Standard BONCAT, or Other — applies appropriate validation and plate-generation logic; stored in database and loaded automatically on subsequent runs
- **Fail-fast validation**: All interactive prompts and CSV validation run *before* any folders are created on disk — a wrong experiment type or bad CSV leaves no side-effects
- **Automatic run-type detection**: First run vs. subsequent run based on `project_summary.db`
- **Automatic CSV detection**: Finds `sample_metadata.csv` (or any valid CSV) in the working directory
- **Standardized folder creation**: Creates the full SPS project folder hierarchy on first run
- **Simplified incremental barcodes**: `BASE-1`, `BASE-2`, … with optional custom base barcode via CLI
- **BarTender file generation**: Reverse-ordered with BarTender header and footer
- **Two-table SQLite database**: `sample_metadata` and `individual_plates` tables in `project_summary.db`
- **Timestamped file archiving**: Prevents overwrites on subsequent runs
- **Custom plates support**: ~~File-based input via `custom_plate_names.txt`~~ **[DISABLED]** — interactive prompt is commented out; code is fully preserved (see [Disabled Features](#disabled-features))
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

## Experiment Type Selection

On every **first run**, the script opens an interactive prompt asking the user to select the experiment type. This happens **before** any CSV validation or folder creation:

```
Select input file type:
  1) Standard SPS-CE
  2) Standard BONCAT
  3) Other

Enter 1, 2, or 3:
```

- Only `1`, `2`, or `3` are accepted. Any other input terminates the script immediately with a `FATAL ERROR` message and no filesystem side-effects.
- The selected type is stored in the `experiment_type` column of the `sample_metadata` table in `project_summary.db`.
- On **subsequent runs** the type is read automatically from the database — the prompt is skipped entirely and the script prints: `Experiment type: Standard SPS-CE (loaded from project database)`

### How the experiment type affects processing

| Type | Internal value | `Group_or_abrvSample` meaning | Plate generation | Extra validation |
|------|---------------|-------------------------------|-----------------|-----------------|
| Standard SPS-CE | `std_sps` | Unique abbreviated sample name per row | 1 row → N plates | Each `Group_or_abrvSample` must be unique across all rows |
| Standard BONCAT | `std_boncat` | Group label shared by multiple samples sorted onto the same plate | 1 unique group → N plates (rows within the group are deduplicated) | Each group must have ≥ 2 rows; `Number_of_sorted_plates` must be consistent within each group |
| Other | `other` | Unique abbreviated sample name per row | 1 row → N plates (same as SPS-CE) | Each `Group_or_abrvSample` must be unique across all rows |

---

### Standard SPS-CE (Mode 1)

Each row in the metadata CSV represents a **single, distinct sample**. `Group_or_abrvSample` is a short abbreviation for that sample and must be unique across all rows. Duplicate group names would produce colliding plate names and are rejected with a FATAL ERROR.

**Example CSV:**
```
Proposal,Group_or_abrvSample,Sample_full,...,Number_of_sorted_plates
777777,Dog,Dog445566,...,2
777777,Cat,Cat009977,...,2
777777,Mouse,Mouse224466,...,2
```

**Plate labels generated (6 total):**
```
777777_Dog.1    777777_Dog.2
777777_Cat.1    777777_Cat.2
777777_Mouse.1  777777_Mouse.2
```

---

### Standard BONCAT (Mode 2)

In BONCAT experiments, multiple individual samples (e.g., BONCAT+ and SYTO+ replicates) are sorted together onto the **same physical plate**. `Group_or_abrvSample` identifies the **group** — all rows sharing the same group value will be sorted onto the same set of plates. Plate labels are generated **once per unique `(Proposal, Group_or_abrvSample)` combination**, not once per row.

`Number_of_sorted_plates` applies to the **group as a whole** (i.e., how many physical plates the entire group is sorted onto), not to each individual sample row. All rows within the same group must have the same `Number_of_sorted_plates` value.

**Validation rules specific to BONCAT:**
- Every `Group_or_abrvSample` value must appear in **at least 2 rows** (at least 2 distinct `Sample_full` values per group). A group with only 1 sample is rejected with a FATAL ERROR.
- All rows sharing the same `(Proposal, Group_or_abrvSample)` must have the **same `Number_of_sorted_plates`** value. Inconsistent values within a group are rejected with a FATAL ERROR.

**Example CSV (12 rows, 4 groups of 3 samples each):**
```
Proposal,Group_or_abrvSample,Sample_full,...,Number_of_sorted_plates
509735,WCBP1PR,W-PM-166,...,2
509735,WCBP1PR,W-PM-173,...,2
509735,WCBP1PR,W-PM-181,...,2
509735,WCBP1AM,W-AM-169,...,2
...
```

**Plate labels generated (8 total — 4 groups × 2 plates each):**
```
509735_WCBP1PR.1    509735_WCBP1PR.2
509735_WCBP1AM.1    509735_WCBP1AM.2
509735_SitukPR.1    509735_SitukPR.2
509735_SitukAM.1    509735_SitukAM.2
```

All 12 individual sample rows are preserved in the `sample_metadata` table of the database (with `experiment_type = boncat`), while only 8 plate records are created in `individual_plates`.

---

### Other (Mode 3)

Applies the same validation and plate-generation logic as Standard SPS-CE. Each row must have a unique `Group_or_abrvSample` value. The experiment type is stored as `other` in the database, making it available to downstream scripts that may need to branch on experiment type.

When the user selects mode 3, the script prints a notice immediately after the selection:

```
ℹ️  NOTE: For 'Other' experiment type, the script will generate barcode
   labels only. Plate layout files will NOT be created automatically.
   You will need to create plate layout files manually.
```

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

> **Note:** Folders are only created after the experiment type selection and CSV validation both pass. A wrong experiment type or invalid CSV terminates the script before any folders are written to disk.

---

## Input Files

### 1. Sample Metadata CSV (`sample_metadata.csv`) — First Run Only
Place in the working directory before running. Required columns (identical for all experiment types):

| Column | Description | Validation |
|--------|-------------|------------|
| `Proposal` | Proposal identifier (e.g., `509735`) | Must be < 9 characters |
| `Group_or_abrvSample` | Short group or sample abbreviation (e.g., `WCBP1PR`) | Must be < 9 characters; letters and numbers only (no symbols or spaces) |
| `Sample_full` | Full sample name (e.g., `W-PM-166`) | No restrictions |
| `Number_of_sorted_plates` | Integer count of sort plates | Must be a valid integer; for BONCAT must be consistent within each group |

Additional columns (optional but expected):
`Collection Year`, `Collection Month`, `Collection Day`, `Sample Isolated From`, `Latitude`, `Longitude`, `Depth (m)`, `Elevation (m)`, `Country`

> **Note:** The `Project` column has been removed. `Proposal` now serves as the project-level identifier and is used as the prefix in plate names (e.g., `509735_WCBP1PR.1`).

### 2. Custom Plate Names (`custom_plate_names.txt`) — **CURRENTLY DISABLED**

> ⚠️ **This feature is disabled.** The interactive prompt that asks `Add custom plates? (y/n):` has been commented out. The script will never ask this question and will never read `custom_plate_names.txt`. All underlying code (`read_custom_plates_file()`, `get_custom_plates()`, and the processing blocks in `process_first_run()` / `process_subsequent_run()`) is preserved and can be re-enabled — see [Disabled Features](#disabled-features).

### 3. Additional Standard Plates (`additional_standard_plates.txt`) — Optional, Subsequent Runs Only
One entry per line in `PROPOSAL_GROUP:COUNT` format.

**Subsequent runs only**: place in `1_make_barcode_labels/`.

```
509735_SitukAM:2
509735_WCBP1PR:1
```

This adds 2 more plates to `509735_SitukAM` and 1 more to `509735_WCBP1PR`, continuing plate numbering from where the previous run left off. The key must match the `Proposal` and `Group_or_abrvSample` values from the original metadata CSV.

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
1. `Enter 1, 2, or 3:` — select experiment type (required; invalid input terminates the script with no filesystem side-effects)

> **Note:** The `Add custom plates? (y/n):` prompt is **disabled**. It will not appear during a first run.

### Subsequent Run (Adding Plates)
```bash
conda activate sip-lims
cd /path/to/project_directory
python SPS_initiate_project_folder_and_make_sort_plate_labels.py
```

The experiment type is loaded automatically from the database (no prompt). When prompted:
- `Add additional standard plates to existing samples? (y/n):` — reads `1_make_barcode_labels/additional_standard_plates.txt`

> **Note:** The `Add custom plates? (y/n):` prompt is **disabled**. It will not appear during a subsequent run.

---

## Barcode System

| Format | Example | Description |
|--------|---------|-------------|
| Base barcode | `REX12` | 5-char alphanumeric; first char must be a letter |
| Standard | `REX12-1`, `REX12-2` | Sequential per plate |

Barcodes continue incrementally across subsequent runs (e.g., if run 1 ended at `REX12-6`, run 2 starts at `REX12-7`).

---

## Output Files

### BarTender Label File
**`BARTENDER_sort_plate_labels_<timestamp>.txt`** — moved to `1_make_barcode_labels/bartender_barcode_labels/` after creation.

Format: reverse-ordered (highest barcode number first) with BarTender header and footer.

### Plate Layout CSV Files *(Standard SPS-CE and Standard BONCAT only)*
One CSV file per plate is written to **`2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/`** in the project directory.

**Filename format:** `<plate_name>_plate_layout.csv`
**Examples:** `777777_Dog.1_plate_layout.csv`, `509735_WCBP1PR.2_plate_layout.csv`

Each file is a filled-in copy of the appropriate 384-well template:

| Experiment type | Template used |
|-----------------|---------------|
| Standard SPS-CE | `standar_sort_plate_layouts/standard_384_SPS_plate_layout.csv` |
| Standard BONCAT | `standar_sort_plate_layouts/standard_BONCAT_384_plate_layout.csv` |

The templates are resolved relative to the **script's own directory** (not the project working directory), so the script can be called from any project folder.

**Fields populated per plate:**

| Column | Value written |
|--------|---------------|
| `Plate_ID` | Plate name (e.g., `777777_Dog.1`) — filled on **every** row |
| `Sample` | `Group_or_abrvSample` abbreviation (e.g., `Dog`) — filled on all rows where `Type != unused` (i.e., `sample`, `neg_cntrl`, `pos_cntrl`, and any other active well types) |
| All other columns | Copied unchanged from the template (controls, unused wells, `Group_1`, etc.) |

**Notes:**
- Layout files are **not** generated for custom plates (added via `custom_plate_names.txt`).
- Layout files are **not** generated when experiment type is **Other** (mode 3).
- On subsequent runs, layout files are generated for newly added plates only.
- If a layout file already exists for a plate being generated, the script terminates with a **FATAL ERROR** rather than overwriting it.

### Database
**`project_summary.db`** — SQLite database with two tables:
- `sample_metadata` — one row per sample from the input CSV, including `experiment_type` column
- `individual_plates` — one row per plate with barcode, plate name, project, sample, plate number, timestamp

A timestamped copy is archived to `archived_files/` before each update.

### CSV Exports
**`sample_metadata.csv`** and **`individual_plates.csv`** — regenerated after each run. Previous versions are archived to `archived_files/` with timestamps. `sample_metadata.csv` includes the `experiment_type` column for downstream script use.

### Workflow Status Marker
**`.workflow_status/SPS_initiate_project_folder_and_make_sort_plate_labels.success`** — created on successful completion for workflow manager integration.

---

## Algorithm Details

---

## Disabled Features

### Custom Plates (`custom_plate_names.txt`)

The ability to add custom (non-standard) plate names during an interactive session has been **temporarily disabled**. The interactive `y/n` prompt (`Add custom plates?`) no longer appears on first or subsequent runs.

**What is disabled:**
- The `while True:` loop inside [`get_custom_plates()`](../SPS_initiate_project_folder_and_make_sort_plate_labels.py) that prompts the user
- The custom-plate concatenation blocks inside `process_first_run()` and `process_subsequent_run()`

**What is preserved (fully intact, just unreachable):**
- [`read_custom_plates_file()`](../SPS_initiate_project_folder_and_make_sort_plate_labels.py) — reads and validates `custom_plate_names.txt`
- [`get_custom_plates()`](../SPS_initiate_project_folder_and_make_sort_plate_labels.py) — function exists; returns `[]` immediately
- All custom-plate processing logic in `manage_input_files()` and `create_project_folder_structure()` (the `custom_plates/` subfolder is still created)

**To re-enable:**
1. Open `SPS_initiate_project_folder_and_make_sort_plate_labels.py`
2. In `get_custom_plates()`: remove the `return []` early-return line and uncomment the `while True:` block
3. In `process_first_run()`: uncomment the `if custom_plates:` block
4. In `process_subsequent_run()`: uncomment the `if custom_plates:` block
5. Update this README to remove the disabled notices

---

### First Run Flow
1. Parse CLI arguments; print header
2. Read database → not found → `is_first_run = True`
3. Prompt user to select experiment type (1 = SPS-CE, 2 = BONCAT, 3 = Other); invalid input → FATAL ERROR, no folders created
4. Detect and read `sample_metadata.csv`; apply shared validation (required columns, character limits, integer check)
5. Apply experiment-type-specific validation:
   - **SPS-CE / Other**: `Group_or_abrvSample` must be unique across all rows
   - **BONCAT**: each group must have ≥ 2 rows; `Number_of_sorted_plates` must be consistent within each group
6. **Create project folder structure** (only reached if all validation passes)
7. Stamp `experiment_type` onto the metadata DataFrame
8. Generate plate names:
   - **SPS-CE / Other**: one set of N plates per row
   - **BONCAT**: one set of N plates per unique `(Proposal, Group_or_abrvSample)` group
9. Optionally add custom plates from `custom_plate_names.txt`
10. Generate incremental barcodes (random or custom base); validate uniqueness
11. Save to database, generate BarTender file, organize files, export CSVs

### Subsequent Run Flow
1. Parse CLI arguments; print header
2. Read database → found → `is_first_run = False`
3. Load `experiment_type` from `sample_metadata` table (no prompt shown)
4. Skip CSV detection and validation entirely
5. Ensure folder structure exists (no-op if already present)
6. Optionally add additional standard plates (continuing plate numbering)
7. Optionally add custom plates
8. Continue barcode numbering from highest existing barcode; validate uniqueness across old + new
9. Append new plates to database, generate BarTender file for new plates only, organize files, export updated CSVs

---

## Error Handling

All errors follow the `FATAL ERROR:` prefix convention and call `sys.exit()` (no exit codes):

| Condition | Behavior |
|-----------|----------|
| Invalid experiment type selection (not 1, 2, or 3) | FATAL ERROR — script terminates immediately, no folders created |
| Missing required CSV columns | FATAL ERROR + list of missing columns |
| `Proposal` value ≥ 9 characters | FATAL ERROR + list of invalid values |
| `Group_or_abrvSample` value ≥ 9 characters | FATAL ERROR + list of invalid values |
| `Group_or_abrvSample` contains non-alphanumeric characters | FATAL ERROR + list of invalid values |
| Invalid `Number_of_sorted_plates` values | FATAL ERROR |
| **SPS-CE / Other**: duplicate `Group_or_abrvSample` values | FATAL ERROR + list of duplicates |
| **BONCAT**: group with fewer than 2 sample rows | FATAL ERROR + list of singleton groups |
| **BONCAT**: inconsistent `Number_of_sorted_plates` within a group | FATAL ERROR + list of inconsistent groups |
| No valid CSV found in working directory | FATAL ERROR |
| Multiple valid CSVs found | FATAL ERROR (ambiguous input) |
| Invalid custom base barcode format | FATAL ERROR with format rules |
| Duplicate barcodes generated | FATAL ERROR |
| Custom plate name ≥ 20 characters | FATAL ERROR |
| Invalid `additional_standard_plates.txt` format | FATAL ERROR with format example |
| Database read/write failure | FATAL ERROR |
| Folder creation failure | FATAL ERROR |
| Plate layout template CSV not found in script directory | FATAL ERROR |
| Plate layout output file already exists for a plate being generated | FATAL ERROR — script terminates; remove or rename the conflicting file |

---

## Troubleshooting

### "FATAL ERROR: Invalid selection" at experiment type prompt
- Enter exactly `1`, `2`, or `3` and press Enter. Any other input (including blank) terminates the script.
- Re-run the script and enter the correct number.

### "FATAL ERROR: No sample metadata CSV file found"
- Ensure `sample_metadata.csv` is in the working directory on first run.
- On subsequent runs the CSV is not needed; the database is used instead.

### "FATAL ERROR: Multiple valid sample metadata CSV files found"
- Remove all but one valid CSV from the working directory.

### "FATAL ERROR: Duplicate 'Group_or_abrvSample' values found" (SPS-CE / Other)
- Each row must have a unique `Group_or_abrvSample`. If two samples share the same abbreviation, rename one of them.
- If you intended to run a BONCAT experiment, re-run and select option `2` instead.

### "FATAL ERROR: ... groups have fewer than 2 samples" (BONCAT)
- Every `Group_or_abrvSample` value must appear in at least 2 rows. A group with only one sample row is not valid for BONCAT mode.
- If you intended to run a standard SPS-CE experiment, re-run and select option `1` instead.

### "FATAL ERROR: Inconsistent 'Number_of_sorted_plates' values within BONCAT groups"
- All rows sharing the same `Group_or_abrvSample` must have the same `Number_of_sorted_plates` value. Correct the CSV so all rows in each group agree.

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

### Current Version (SPS — April 2026)
- **Plate layout CSV generation**: For Standard SPS-CE and Standard BONCAT runs, one `<plate_name>_plate_layout.csv` is written to `2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/` for every standard plate generated (custom plates and Other mode are excluded). Templates are read from `standar_sort_plate_layouts/` relative to the script file; output is written to the project working directory. A FATAL ERROR is raised if an output file already exists.
- **Experiment type selection**: Interactive prompt at start of first run selects Standard SPS-CE, Standard BONCAT, or Other; stored in database and loaded automatically on subsequent runs (no re-prompting)
- **Fail-fast ordering**: Experiment type prompt and CSV validation now run *before* folder creation — invalid input leaves no filesystem side-effects
- **BONCAT plate generation**: Group-based deduplication — plate labels generated once per unique `(Proposal, Group_or_abrvSample)` pair rather than once per row
- **Mode-specific validation**: SPS-CE and Other enforce unique `Group_or_abrvSample` per row; BONCAT enforces ≥ 2 rows per group and consistent `Number_of_sorted_plates` within each group
- **`experiment_type` column**: Added to `sample_metadata` table and CSV export for downstream script use
- **`process_subsequent_run()` signature**: Accepts `experiment_type` parameter for future type-specific logic

### Previous Version (SPS — April 2026)
- **New CSV format**: Replaced `Project` and `Sample` columns with `Group_or_abrvSample` and `Sample_full`
- **`Project` column removed**: `Proposal` now serves as the project-level prefix in plate names (e.g., `509735_WCBP1PR.1`)
- **New validations**: `Proposal` must be < 9 characters; `Group_or_abrvSample` must be < 9 characters and contain only letters and numbers
- **`additional_standard_plates.txt` format updated**: Keys now use `PROPOSAL_GROUP` format (e.g., `509735_WCBP1PR:2`) instead of `PROJECT_SAMPLE`

### Previous Version (SPS — March 2026)
- Renamed and adapted from `initiate_project_folder_and_make_sort_plate_labels.py` (capsule_sort_scripts)
- **Updated folder structure**: `2_sort_plates_and_amplify_genomes/` (with `A_sort_plate_layouts/` and `B_WGA_results/` subfolders), `3_make_library_analyze_fa/`, `4_pooling/`
- CSV format used `Proposal`, `Project`, `Sample` columns; plate names were `PROJECT_SAMPLE.N`

### Previous Version (capsule_sort_scripts)
- Used `2_library_creation/`, `3_FA_analysis/`, `4_plate_selection_and_pooling/` folder names
- No `A_sort_plate_layouts/` or `B_WGA_results/` subfolders

---

**Author**: SPS Lab
**Last Updated**: April 2026
**Conda Environment**: `sip-lims`
