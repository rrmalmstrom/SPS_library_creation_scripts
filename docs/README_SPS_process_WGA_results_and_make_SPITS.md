# SPS Process WGA Results and Make SPITS — Script 3

## Overview

`SPS_process_WGA_results_and_make_SPITS.py` is **Script 3** in the SPS library creation workflow. It processes the consolidated MDA results CSV produced by Script 2 and generates formatted output files for laboratory information management systems, including SPITS sequencing submission input, a project summary CSV, and an updated SQLite database.

This script was previously named `enhanced_generate_SPITS_input.py` and has been renamed to follow the `SPS_` prefix convention used by all other workflow scripts.

## Features

### Core Functionality
- **Single Cell Data Processing**: Imports and processes `summary_MDA_results.csv` produced by Script 2
- **Illumina Index Assignment**: Automatically assigns PE17-PE20 Illumina index sets with sequential numbering
- **Plate Format Conversion**: Handles both 96-well and 384-well plate formats with automatic conversion
- **SPITS Format Generation**: Creates properly formatted CSV files for laboratory workflows

### Key Changes from Previous Version
- **Renamed**: `enhanced_generate_SPITS_input.py` → `SPS_process_WGA_results_and_make_SPITS.py` (follows SPS_ prefix convention)
- **CLI updated**: Now takes 1 argument (`summary_MDA_results.csv`) instead of 2
- **Echo IDs from database**: `lookupEchoIdFromDatabase()` replaces the old `addEchoId()` function — Echo barcodes are now looked up from `project_summary.db` (`individual_plates` table) instead of requiring a separate Echo Barcodes CSV file
- **`checkSourcePlateDistribution()` removed**: This function previously aborted if any source plate appeared in more than one `Dest_plate`. It has been removed because Script 2 now controls `Dest_plate` assignment and intentionally allows source plates to span multiple destination plates
- **Database Integration**: Creates SQLite database with processed data using SQLAlchemy
- **Project Summary Files**: Generates CSV and database files following SPS workflow patterns
- **Extended Metadata**: Adds 12 new metadata columns with automatic population for negative controls
- **Individual Illumina Indexes**: Creates properly formatted individual index names (e.g., PE17_E01)

### Code Quality
- **Constants Documentation**: Magic numbers replaced with documented constants
- **Improved Error Messages**: Consistent, informative error formatting
- **Better Function Names**: Descriptive function names (e.g., `assignPlatePositions`)
- **Organized Code Structure**: Hardcoded lists moved to constants section

## Position in Workflow

```
Script 1: SPS_initiate_project_folder_and_make_sort_plate_labels.py
  └─► Creates: project_summary.db (tables: sample_metadata, individual_plates)
  └─► Creates: 2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/<plate_name>_plate_layout.csv
  └─► Creates: 2_sort_plates_and_amplify_genomes/B_WGA_results/  (empty — user places kinetics files here)

[WET LAB: Sort cells → Run MDA/WGA → Generate amplification kinetics files]

Script 2: SPS_process_WGA_results.py
  └─► Reads: project_summary.db (individual_plates table)
  └─► Reads: 2_sort_plates_and_amplify_genomes/B_WGA_results/*_amplification_kinetics_summary.csv
  └─► Writes: 2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/summary_MDA_results.csv

Script 3: SPS_process_WGA_results_and_make_SPITS.py  ← THIS SCRIPT
  └─► Reads: summary_MDA_results.csv (from 2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/, produced by Script 2)
  └─► Reads: project_summary.db (individual_plates table — for echo_id lookup)
  └─► Writes: output.csv (SPITS format), project_summary.csv, project_summary.db (updated)
```

## Usage

```bash
python SPS_process_WGA_results_and_make_SPITS.py <summary_MDA_results.csv>
```

### Example
```bash
python SPS_process_WGA_results_and_make_SPITS.py summary_MDA_results.csv
```

The script takes exactly **1 command-line argument**: the path to `summary_MDA_results.csv` produced by Script 2 (located in `2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/`).

## Input Files

### 1. `summary_MDA_results.csv` (produced by Script 2)
Located in `2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/`. Script 3 reads only the columns it needs:
- `Plate_id`: Source plate identifier
- `Well`: Well position (e.g., A1, B2)
- `Type`: Sample type (`'sample'` or `'negative'`)
- `Dest_plate`: Destination plate number (integer, assigned by Script 2)
- `Row`: Row letter (A-H)
- `Col`: Column number (1-24)

### 2. `project_summary.db` (SQLite database — project root)
Read automatically from the current working directory. The script queries the **`individual_plates`** table to look up Echo liquid handler plate barcodes by matching `plate_name` to `Plate_id`. The `barcode` column value is used as the `echo_id` for each plate.

> **Note:** A separate Echo Barcodes CSV file is no longer required. Echo IDs are now looked up directly from `project_summary.db`.

## Output Files

### 1. `output.csv` (SPITS Format)
Main output file with 30 columns including:
- Sample information and metadata
- Illumina index assignments
- Plate and well positions
- 12 new metadata columns for sample tracking

### 2. `project_summary.csv`
Database-compatible summary with 9 columns:
- `internal_name`: Plate_id + Well
- `plate_id`: Source plate identifier
- `echo_id`: Echo barcode (from `project_summary.db`)
- `source_well`: Well position
- `type`: Sample type
- `dest_plate`: Destination plate
- `dest_well_384`: 384-well format position
- `Illumina_index_set`: Index set (PE17-PE20)
- `Illumina_index`: Individual index (e.g., PE17_E01)

### 3. `project_summary.db`
SQLite database containing the same data as `project_summary.csv` in a `project_summary` table, with two columns renamed: `dest_plate` → `Destination_plate_name` and `dest_well_384` → `Destination_Well`.

## Constants and Configuration

### Sample Limits
- `MAX_SAMPLES_PER_PLATE = 83`: Maximum samples per plate (each Illumina index set has at least 83 validated indexes)
- `NUM_ILLUMINA_INDEX_SETS = 4`: Number of available index sets (PE17-PE20)

### Illumina Index Sets
The script uses four Illumina index sets with specific excluded wells:
- **PE17**: Excludes A1, H1, A12, H12, B2, B5
- **PE18**: Excludes A1, H1, A12, H12, D1, C2, H2, G3, C4, D4, C5, C10
- **PE19**: Excludes A1, H1, A12, H12, A4, B4, B6, A9, A10
- **PE20**: Excludes A1, H1, A12, H12, D2, B3, E7, C9, E10, A11, D11, E11, C12

## Validation and Error Handling

### Automatic Validations
1. **Sample Count**: Maximum 83 samples per destination plate
2. **Index Assignment**: Validates proper Illumina index assignment
3. **Echo ID Mapping**: Ensures all source plates have corresponding echo IDs in `project_summary.db`

> **Note:** Source plate distribution validation (`checkSourcePlateDistribution()`) has been removed. Script 2 controls `Dest_plate` assignment and intentionally allows source plates to span multiple destination plates.

### Error Messages
All error messages follow a consistent format:
- Start with `"ERROR:"` prefix
- Provide clear description of the problem
- Include troubleshooting guidance
- End with `"Aborting script."`

## Metadata Columns

### Standard Columns
- `Sample_name`: Auto-generated based on sample type
- `DNA_conc`: Default value (10)
- `Sample_vol`: Default value (25)
- `Sample_container`: '384'
- `Sample_format`: 'MDA reaction buffer'
- `DNAse_treated`: 'N'
- `Biosafety_cat`: 'Metagenome (Environmental)'
- `Isolation_method`: 'flow sorting'

### New Metadata Columns (Auto-populated for Negative Controls)
- `Collection_Year`: Current year
- `Collection_Month`: Current month (full name)
- `Collection_Day`: Current day
- `Sample_Isolated_From`: 'MDA reagents'
- `Collection_Site`: 'MDA reagents'
- `Latitude`: '37.87606'
- `Longitude`: '-122.25166'
- `Depth`: '0'
- `Maximum_depth`: (empty)
- `Elevation`: '75'
- `Maximum_elevation`: (empty)
- `Country`: 'USA'

## Dependencies

```python
import pandas as pd
import numpy as np
import sys
import random
import string
from sqlalchemy import create_engine
from pathlib import Path
from datetime import datetime
```

## Function Overview

### Data Import and Validation
- `importSCdata()`: Imports and sorts input CSV data
- `countLibsPerPlate()`: Validates sample count per plate (max 83 per destination plate)

> **Removed:** `checkSourcePlateDistribution()` — this function previously aborted if any source plate appeared in more than one `Dest_plate`. Removed because Script 2 now controls `Dest_plate` assignment and intentionally allows source plates to span multiple destination plates.

### Plate and Index Management
- `assignLibPlateID()`: Generates unique destination plate IDs
- `assignPlatePositions()`: Assigns sequential positions within plates
- `makeConversionKey()`: Creates 96-well to 384-well conversion mappings
- `makeIlluminaIndexSetToUse()`: Sets up Illumina index assignments
- `assignIlluminaIndex()`: Assigns specific indexes to samples

### Data Enhancement
- `lookupEchoIdFromDatabase()`: Looks up Echo barcodes from `project_summary.db` (`individual_plates` table). Replaces the old `addEchoId()` function which required a separate Echo Barcodes CSV file.
- `addSPITScolumns()`: Adds required SPITS columns and metadata
- `createIndividualIlluminaIndex()`: Creates formatted individual index names

### Output Generation
- `makeSPITSformat()`: Creates main SPITS output file
- `prepareDatabaseDataframe()`: Prepares data for database storage
- `createProjectSummaryCSV()`: Creates summary CSV file
- `createSQLdb()`: Creates SQLite database

## Version History

### Current Version (SPS_process_WGA_results_and_make_SPITS.py)
- Renamed from `enhanced_generate_SPITS_input.py` to follow SPS_ prefix convention
- CLI updated: 1 argument (`summary_MDA_results.csv`) instead of 2
- `lookupEchoIdFromDatabase()` replaces `addEchoId()` — Echo IDs now from `project_summary.db`
- `checkSourcePlateDistribution()` removed — Script 2 controls Dest_plate assignment
- Input CSV (`summary_MDA_results.csv`) now produced by Script 2 (`SPS_process_WGA_results.py`)

### Enhanced Version (enhanced_generate_SPITS_input.py — previous name)
- Database integration with SQLAlchemy
- Extended metadata columns (12 new fields)
- Individual Illumina index generation
- Command line argument support
- Improved error handling and code quality
- Constants for better maintainability

### Original Version
- Basic SPITS format generation
- Illumina index assignment
- Plate format conversion
- Echo barcode mapping (from separate CSV file)

## Notes

- The script requires exactly 1 command-line argument: the path to `summary_MDA_results.csv`
- `project_summary.db` must exist in the current working directory (project root)
- Negative controls are automatically populated with current date and location data
- The script uses a random starting point for Illumina index set assignment to distribute usage
- All output files are created in the current working directory
