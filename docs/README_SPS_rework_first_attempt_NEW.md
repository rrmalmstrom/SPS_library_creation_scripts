# SPS Rework First Attempt Script

## Overview

The [`SPS_rework_first_attempt_NEW.py`](SPS_rework_first_attempt_NEW.py) script is a critical component of the Single-cell Sequencing (SPS) library creation workflow. This script processes Fragment Analyzer (FA) results to identify plates that need rework due to failed library preparation and generates all necessary transfer files for the second attempt at library creation.

## Purpose

After the first attempt at library creation and Fragment Analyzer quality control analysis, some library plates may fail to meet quality standards. This script automates the process of:

1. Identifying which plates need complete rework
2. Generating new plate IDs for rework attempts
3. Creating all necessary liquid handling transfer files
4. Updating the project database with rework information
5. Preparing files for the second round of Fragment Analyzer analysis

## Workflow Position

This script is part of a larger SPS workflow:

```
Initial Library Creation → FA Analysis → [THIS SCRIPT] → Rework Library Creation → Second FA Analysis
```

## Prerequisites

### Environment Requirements
- **Python Environment**: `sipsps_env` conda environment
- **Working Directory**: Script must be run from the project root directory (where `project_summary.db` is located)
- **Python Version**: Python 3.x with required packages (pandas, numpy, sqlalchemy, pathlib)

### Required Input Files
1. **`project_summary.db`**: SQLite database containing project information
2. **`1_make_library_analyze_fa/B_first_attempt_fa_result/updated_fa_analysis_summary.txt`**: FA analysis results with rework decisions

### Directory Structure Expected
```
project_root/
├── project_summary.db
├── project_summary.csv
├── 1_make_library_analyze_fa/
│   ├── B_first_attempt_fa_result/
│   │   └── updated_fa_analysis_summary.txt
│   ├── C_second_attempt_make_lib/          # Created by script
│   └── D_second_attempt_fa_result/         # Created by script
└── archived_files/                         # Created by script
```

## Input File Format

### updated_fa_analysis_summary.txt
This tab-delimited file must contain the following columns:
- `sample_id`: Unique sample identifier
- `Destination_Plate_Barcode`: Original library plate barcode
- `Redo_whole_plate`: Boolean flag (TRUE/FALSE) indicating if entire plate needs rework
- Additional columns from FA analysis (concentrations, sizes, pass/fail status)

## Script Functionality

### Core Functions

#### 1. Data Processing Functions
- **[`readSQLdb()`](SPS_rework_first_attempt_NEW.py:62)**: Reads project summary database
- **[`updateLibInfo()`](SPS_rework_first_attempt_NEW.py:96)**: Merges FA results with project database
- **[`getReworkFiles()`](SPS_rework_first_attempt_NEW.py:227)**: Identifies plates needing rework

#### 2. File Generation Functions
- **[`makeEchoFiles()`](SPS_rework_first_attempt_NEW.py:297)**: Creates Echo liquid handler transfer files
- **[`createIllumDataframe()`](SPS_rework_first_attempt_NEW.py:368)**: Prepares Illumina index transfer data
- **[`makeIlluminaFiles()`](SPS_rework_first_attempt_NEW.py:452)**: Generates Illumina index transfer files
- **[`createFAdataframe()`](SPS_rework_first_attempt_NEW.py:396)**: Prepares FA upload data
- **[`makeFAfiles()`](SPS_rework_first_attempt_NEW.py:417)**: Creates FA upload files
- **[`makeBarcodeLabels()`](SPS_rework_first_attempt_NEW.py:476)**: Generates barcode label files
- **[`makeThreshold()`](SPS_rework_first_attempt_NEW.py:530)**: Creates FA analysis threshold files
- **[`makeDilution()`](SPS_rework_first_attempt_NEW.py:567)**: Prepares dilution transfer data
- **[`makeDilutionFile()`](SPS_rework_first_attempt_NEW.py:611)**: Creates Hamilton liquid handler files

#### 3. Database Functions
- **[`createSQLdb()`](SPS_rework_first_attempt_NEW.py:119)**: Archives old database and creates new one
- **[`updateProjectDatabase()`](SPS_rework_first_attempt_NEW.py:146)**: Updates project database with rework info

#### 4. Special Case Handling
- **[`noRework()`](SPS_rework_first_attempt_NEW.py:173)**: Handles cases where no rework is needed

## Output Files

The script creates multiple output directories and files:

### C_second_attempt_make_lib/
- **echo_transfer_files/**: Echo liquid handler transfer files
  - `REDO_echo_transfer_{plate_id}.csv`: DNA transfer instructions
- **illumina_index_transfer_files/**: Illumina index addition files
  - `Illumina_index_transfer_{plate_id}.csv`: Index primer transfer instructions
- **FA_input_files/**: Fragment Analyzer upload files
  - `FA_upload_{plate_id}.csv`: Sample information for FA analysis
- **fa_transfer_files/**: Hamilton liquid handler files
  - `FA_plate_transfer_{plate_id}.csv`: Dilution and FA plate setup instructions
- **BARTENDER_Redo_Library_FA_plates.txt**: Barcode label printing file

### D_second_attempt_fa_result/
- **thresholds.txt**: FA analysis parameters for quality control

### Database Updates
- **project_summary.db**: Updated with rework information
- **project_summary.csv**: CSV backup of updated database
- **archived_files/**: Timestamped backups of previous database versions

## File Format Details

### Echo Transfer Files
```csv
Source Plate Name,Source Plate Barcode,Source Row,Source Column,Destination Plate Name,Destination_Plate_Barcode,Destination Row,Destination Column,Transfer Volume
Prtist.Plumas.1A.1,Prtist.13,12,21,27-710888.2,27-710888.2,1,1,500
```

### Illumina Index Transfer Files
```csv
Illumina_index_set,Illumina_source_well,Lib_plate_ID,Lib_plate_well,Primer_volume_(uL)
TM326,A1,h27-710888.2,A1,2
```

### FA Upload Files
```csv
1,A1,27-710888.2_12345_A1
2,B1,27-710888.2_12346_B1
```

### Dilution Transfer Files
```csv
Library_Plate_Barcode,Dilution_Plate_Barcode,FA_Plate_Barcode,Library_Well,FA_Well,Nextera_Vol_Add,Dilution_Vol,FA_Vol_Add,Dilution_Plate_Preload,Total_buffer_aspiration
h27-710888.2,27-710888.2D,27-710888.2F,A1,A1,30,2.4,2.4,10,40
```

## Usage

### Command Line Execution
```bash
# Activate conda environment
conda activate sipsps_env

# Navigate to project directory
cd /path/to/project/directory

# Run script
python SPS_rework_first_attempt_NEW.py
```

### Interactive Prompts
The script will prompt for:
- **Dilution factor**: Fold-dilution for libraries loaded into FA plate (default: 5)

### Example Session
```
Starting SPS library rework process...
Reading library information and FA analysis results...
Identifying plates that need rework...


 What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): 5

Creating Echo transfer files...
Creating Illumina index transfer files...
Creating FA upload files...
Creating barcode label files...
Creating threshold files...
Creating dilution transfer files...
Updating project database...

✓ Script completed successfully!
✓ Processed 2 plates for rework
✓ Files created in: 1_make_library_analyze_fa/C_second_attempt_make_lib
```

## Plate Naming Convention

The script follows a specific naming convention for rework plates:

- **Original plate**: `27-710888.1`
- **Rework plate**: `27-710888.2`
- **FA plate**: `27-710888.2F`
- **Dilution plate**: `27-710888.2D`
- **Hamilton barcode**: `h27-710888.2`

## Error Handling

The script includes comprehensive error handling for:

- **Missing input files**: Checks for required files before processing
- **Empty data**: Handles cases where no rework is needed
- **Database errors**: Manages SQLite connection issues
- **Column mismatches**: Validates required columns in input files
- **File I/O errors**: Handles file creation and writing issues

### Common Error Messages
- `Could not find file updated_fa_analysis_summary.txt`: Input file missing
- `No library rework is needed`: No plates marked for rework
- `Missing required column in data`: Input file format issue

## Dependencies

### Python Packages
```python
import sys
import string
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
```

### External Tools
- **Echo Liquid Handler**: Uses generated CSV files for DNA transfers
- **Hamilton STAR**: Uses generated CSV files for dilution and FA plate setup
- **Fragment Analyzer**: Uses generated upload files for quality control
- **Bartender**: Uses generated text files for barcode label printing

## Troubleshooting

### Common Issues

1. **Script fails to find input file**
   - Ensure `updated_fa_analysis_summary.txt` exists in `B_first_attempt_fa_result/`
   - Check file permissions

2. **Database connection errors**
   - Verify `project_summary.db` exists in project root
   - Check file is not locked by another process

3. **No rework needed message**
   - Check that `Redo_whole_plate` column contains `TRUE` values
   - Verify input file format matches expected structure

4. **Permission errors**
   - Ensure write permissions for output directories
   - Check disk space availability

### Debug Mode
For debugging, examine the intermediate DataFrames by adding print statements:
```python
print(f"Plates needing rework: {whole_plate_redo}")
print(f"Rework DataFrame shape: {wp_redo_df.shape}")
```

## Version History

### Recent Fixes (2026-01-06)
- Fixed Pandas SettingWithCopyWarning by using `.copy()` method
- Corrected column case sensitivity issue (`Source_Well` vs `source_well`)
- Fixed echo file source plate barcode to use `echo_id` instead of `plate_id`
- Added default transfer volume of 500 to echo files

### Key Improvements
- Enhanced error handling and user feedback
- Comprehensive logging of processing steps
- Automatic directory creation
- Database backup and archiving

## Related Scripts

This script is part of a larger SPS workflow:

- **Predecessor**: `SPS_first_FA_output_analysis_NEW.py` (analyzes first FA results)
- **Successor**: `SPS_second_FA_output_analysis.py` (analyzes second FA results)
- **Related**: `SPS_make_illumina_index_and_FA_files_NEW.py` (initial library creation)

## Support

For issues or questions:
1. Check the error message and troubleshooting section
2. Verify input file formats match expected structure
3. Ensure all prerequisites are met
4. Contact the SPS workflow maintainer

## License

This script is part of the SPS (Single-cell Protist Sequencing) workflow developed for laboratory automation in genomics research.