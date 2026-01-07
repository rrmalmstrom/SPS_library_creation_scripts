# Enhanced Generate SPITS Input Script

## Overview

The `enhanced_generate_SPITS_input.py` script is an enhanced version of the original SPITS input generator that processes single cell MDA (Multiple Displacement Amplification) results and generates formatted output files for laboratory information management systems. This enhanced version includes database functionality, improved metadata handling, and better code quality.

## Features

### Core Functionality
- **Single Cell Data Processing**: Imports and processes manually modified summary_MDA_results.csv files
- **Illumina Index Assignment**: Automatically assigns PE17-PE20 Illumina index sets with sequential numbering
- **Plate Format Conversion**: Handles both 96-well and 384-well plate formats with automatic conversion
- **SPITS Format Generation**: Creates properly formatted CSV files for laboratory workflows

### Enhanced Features (New)
- **Database Integration**: Creates SQLite database with processed data using SQLAlchemy
- **Project Summary Files**: Generates CSV and database files following SPS workflow patterns
- **Extended Metadata**: Adds 12 new metadata columns with automatic population for negative controls
- **Multi-plate Validation**: Immediate exit when source plates are split across destinations
- **Individual Illumina Indexes**: Creates properly formatted individual index names (e.g., PE17_E01)

### Code Quality Improvements
- **Constants Documentation**: Magic numbers replaced with documented constants
- **Improved Error Messages**: Consistent, informative error formatting
- **Better Function Names**: Descriptive function names (e.g., `assignPlatePositions`)
- **Organized Code Structure**: Hardcoded lists moved to constants section
- **Command Line Arguments**: Flexible file input via command line parameters

## Usage

```bash
python enhanced_generate_SPITS_input.py <input_csv_file> <echo_barcodes_csv_file>
```

### Example
```bash
python enhanced_generate_SPITS_input.py input.csv "SingleCell Query - Echo Barcodes.csv"
```

## Input Files

### 1. Input CSV File (manually modified summary_MDA_results.csv)
Required columns:
- `Plate_id`: Source plate identifier
- `Well`: Well position (e.g., A1, B2)
- `Type`: Sample type ('sample' or 'negative')
- `Dest_plate`: Destination plate number
- `Row`: Row letter (A-H)
- `Col`: Column number (1-24)

### 2. Echo Barcodes CSV File
Required columns (header on line 2):
- `Project Name`: Project identifier
- `Echo Barcode`: Echo plate barcode
- `Sample Name`: Sample identifier
- `Window Name`: Window identifier
- `Plate Index`: Plate index number

## Output Files

### 1. output.csv (SPITS Format)
Main output file with 25 columns including:
- Sample information and metadata
- Illumina index assignments
- Plate and well positions
- 12 new metadata columns for sample tracking

### 2. project_summary.csv
Database-compatible summary with 9 columns:
- `internal_name`: Plate_id + Well
- `plate_id`: Source plate identifier
- `echo_id`: Echo barcode
- `well`: Well position
- `type`: Sample type
- `dest_plate`: Destination plate
- `dest_well_384`: 384-well format position
- `illumina_index_set`: Index set (PE17-PE20)
- `illumina_index`: Individual index (e.g., PE17_E01)

### 3. project_summary.db
SQLite database containing the same data as project_summary.csv in a `project_summary` table.

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
2. **Source Plate Distribution**: No source plate can be split across multiple destination plates
3. **Index Assignment**: Validates proper Illumina index assignment
4. **Echo ID Mapping**: Ensures all source plates have corresponding echo IDs

### Error Messages
All error messages follow a consistent format:
- Start with "ERROR:" prefix
- Provide clear description of the problem
- Include troubleshooting guidance
- End with "Aborting script."

## Metadata Columns

### Standard Columns
- `Sample_name`: Auto-generated based on sample type
- `DNA_conc`: Default value (10)
- `Sample_vol`: Default value (25)
- `Sample_container`: 'plate'
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
- `countLibsPerPlate()`: Validates sample count per plate
- `checkSourcePlateDistribution()`: Ensures no source plate splitting

### Plate and Index Management
- `assignLibPlateID()`: Generates unique destination plate IDs
- `assignPlatePositions()`: Assigns sequential positions within plates
- `makeConversionKey()`: Creates 96-well to 384-well conversion mappings
- `makeIlluminaIndexSetToUse()`: Sets up Illumina index assignments
- `assignIlluminaIndex()`: Assigns specific indexes to samples

### Data Enhancement
- `addEchoId()`: Maps echo barcodes to source plates
- `addSPITScolumns()`: Adds required SPITS columns and metadata
- `createIndividualIlluminaIndex()`: Creates formatted individual index names

### Output Generation
- `makeSPITSformat()`: Creates main SPITS output file
- `prepareDatabaseDataframe()`: Prepares data for database storage
- `createProjectSummaryCSV()`: Creates summary CSV file
- `createSQLdb()`: Creates SQLite database

## Version History

### Enhanced Version Features
- Database integration with SQLAlchemy
- Extended metadata columns (12 new fields)
- Multi-plate validation with immediate exit
- Individual Illumina index generation
- Command line argument support
- Improved error handling and code quality
- Constants for better maintainability

### Original Version
- Basic SPITS format generation
- Illumina index assignment
- Plate format conversion
- Echo barcode mapping

## Notes

- The script requires exactly 2 command line arguments
- Source plates cannot be split across multiple destination plates
- Negative controls are automatically populated with current date and location data
- The script uses a random starting point for Illumina index set assignment to distribute usage
- All output files are created in the current working directory