# SPS Library Creation Script - NEW Version

## Overview

This script is a completely rewritten version of the original `SPS_make_illumina_index_and_FA_files.py` that processes existing project databases and grid table data to generate all necessary files for Illumina sequencing library preparation and Fragment Analyzer quality control.

## Key Changes from Original Version

### Fundamental Workflow Change
- **Original**: Processed Echo transfer files and data warehouse exports to create a new database
- **NEW**: Reads existing `project_summary.db` database and merges with grid table CSV data

### New Features
- **Database archiving**: Automatically archives existing database/CSV files with timestamps
- **Perfect merge validation**: Ensures 1:1 correspondence between database and grid table data
- **Enhanced error handling**: All errors are fatal and cause program termination
- **Improved file organization**: Better sorting and column ordering

## Requirements

### Python Dependencies
```bash
pip install pandas numpy sqlalchemy pathlib
```

### Input Files Required
1. **Existing project_summary.db**: SQLite database from previous workflow
2. **Grid table CSV file**: Contains well mapping and sample information

### Grid Table CSV Format
The grid table CSV must contain these exact column headers:
- `Well`: Well position (e.g., A1, B2, C3)
- `Aliquot Plate Label`: Plate name/identifier
- `Illumina Library`: Library identifier
- `Container Barcode`: Destination plate barcode
- `Nucleic Acid ID`: Sample identifier

## Usage

### Basic Command
```bash
python SPS_make_illumina_index_and_FA_files_NEW.py <grid_table.csv>
```

### Example
```bash
python SPS_make_illumina_index_and_FA_files_NEW.py my_grid_table.csv
```

### Interactive Input
The script will prompt you for:
- **Dilution factor**: Fold-dilution for libraries loaded into FA plate (default: 5)

## Output Files Generated

### Directory Structure
```
1_make_library_analyze_fa/
├── A_first_attempt_make_lib/
│   ├── echo_transfer_files/
│   │   └── {destination_plate}_{source_plates}.csv
│   ├── illumina_index_transfer_files/
│   │   └── Illumina_index_transfer_{plate}.csv
│   ├── fa_transfer_files/
│   │   └── FA_plate_transfer_{plate}.csv
│   ├── FA_input_files/
│   │   └── FA_upload_{plate}.csv
│   └── BARTENDER_Library_IlluminaIndex_FA_plate_labels.txt
├── B_first_attempt_fa_result/
│   └── thresholds.txt
├── C_second_attempt_make_lib/
└── D_second_attempt_fa_result/

2_pooling/
├── A_fill_clarity_lib_creation_file/
├── B_assign_libs_to_pools/
├── C_finish_pooling/
└── D_pooling_and_rework/

archived_files/
├── archive_project_summary_{timestamp}.db
└── archive_project_summary_{timestamp}.csv
```

### File Descriptions

#### Echo Transfer Files
- **Location**: `1_make_library_analyze_fa/A_first_attempt_make_lib/echo_transfer_files/`
- **Format**: `{destination_plate}_{source_plates}.csv`
- **Purpose**: Instructions for Echo liquid handler to transfer samples
- **Columns**: Source Plate Name, Source Plate Barcode, Source Row, Source Column, Destination Plate Name, Destination Plate Barcode, Destination Row, Destination Column, Transfer Volume

#### Illumina Index Transfer Files
- **Location**: `1_make_library_analyze_fa/A_first_attempt_make_lib/illumina_index_transfer_files/`
- **Format**: `Illumina_index_transfer_{plate}.csv`
- **Purpose**: Instructions for adding Illumina sequencing indexes
- **Columns**: Illumina_index_set, Illumina_source_well, Lib_plate_ID, Lib_plate_well, Primer_volume_(uL)

#### Fragment Analyzer Input Files
- **Location**: `1_make_library_analyze_fa/A_first_attempt_make_lib/FA_input_files/`
- **Format**: `FA_upload_{plate}.csv`
- **Purpose**: Sample layout for Fragment Analyzer quality control
- **Features**: 
  - Complete 96-well plate layout
  - Sorted by column first (1-12), then row (A-H)
  - Empty wells marked as 'empty_well'
  - H12 reserved for 'ladder_1'

#### Dilution Transfer Files
- **Location**: `1_make_library_analyze_fa/A_first_attempt_make_lib/fa_transfer_files/`
- **Format**: `FA_plate_transfer_{plate}.csv`
- **Purpose**: Instructions for Hamilton liquid handler dilution setup
- **Columns**: Library_Plate_Barcode, Dilution_Plate_Barcode, FA_Plate_Barcode, Library_Well, FA_Well, Nextera_Vol_Add, Dilution_Vol, FA_Vol_Add, Dilution_Plate_Preload, Total_buffer_aspiration

#### Bartender Barcode Labels
- **Location**: `1_make_library_analyze_fa/A_first_attempt_make_lib/BARTENDER_Library_IlluminaIndex_FA_plate_labels.txt`
- **Purpose**: Barcode labels for all plates used in the workflow
- **Includes**: FA run plates, FA dilution plates, Hamilton scanner plates, library plates

#### Threshold File
- **Location**: `1_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt`
- **Purpose**: Analysis parameters for Fragment Analyzer results
- **Columns**: Destination_plate, DNA_conc_threshold_(nmol/L), Size_theshold_(bp), dilution_factor

#### Updated Database Files
- **project_summary.db**: Updated SQLite database with merged data
- **project_summary.csv**: Updated CSV file with merged data
- **Column Order**: sample_id, internal_name, plate_id, echo_id, well, type, Destination_plate_name, Destination_Plate_Barcode, Destination_Well, Illumina_index_set, Illumina_index, Illumina Library

## Data Validation

### Merge Validation
The script performs strict validation to ensure perfect 1:1 correspondence between:
- Database records and grid table entries
- Well positions and plate names
- Sample identifiers

### Error Handling
All errors are **fatal** and will cause the script to terminate with descriptive error messages:
- Missing input files
- Invalid file formats
- Data mismatches
- Invalid well positions
- Missing required columns

## Workflow Integration

### Prerequisites
1. Existing `project_summary.db` database from previous SPS workflow
2. Grid table CSV file with correct format and column headers
3. Proper directory permissions for file creation

### Post-Processing
After running this script, you can proceed with:
1. Fragment Analyzer quality control using generated FA files
2. Library pooling using generated transfer files
3. Sequencing preparation using Illumina index files

## Troubleshooting

### Common Issues

#### "Database file not found"
- Ensure `project_summary.db` exists in the current directory
- Check file permissions

#### "Missing required columns in grid table"
- Verify grid table CSV has exact column headers: Well, Aliquot Plate Label, Illumina Library, Container Barcode, Nucleic Acid ID
- Check for typos in column names

#### "Merge validation failed"
- Ensure well positions in database match those in grid table
- Verify plate names are consistent between files
- Check for missing or extra samples

#### "Invalid well position format"
- Well positions must be in format: Letter + Number (e.g., A1, B2, H12)
- Valid rows: A-P, Valid columns: 1-24

### Testing
Run the comprehensive test suite to verify functionality:
```bash
python test_SPS_make_illumina_index_and_FA_files_NEW.py
```

## Technical Details

### Plate Formats
- **384-well plates**: Used for library construction
- **96-well plates**: Used for Fragment Analyzer and some transfers
- **Automatic conversion**: Script handles 384→96 well position mapping

### Well Position Sorting
- **FA files**: Sorted by column first (1-12), then row (A-H)
- **Echo files**: Sorted by destination column and row
- **Result**: Consistent, predictable well ordering

### Database Archiving
- **Automatic**: Existing files archived before creating new ones
- **Timestamp format**: YYYY_MM_DD-TimeHH-MM-SS
- **Location**: `archived_files/` directory

## Version History

### NEW Version (Current)
- Complete rewrite with new workflow
- Database merging instead of creation
- Enhanced validation and error handling
- Improved file organization and sorting
- Comprehensive automated testing

### Original Version
- Processed Echo files and data warehouse exports
- Created new databases from scratch
- Basic error handling
- Manual file organization

## Support

For issues or questions:
1. Check error messages for specific guidance
2. Verify input file formats and column headers
3. Run automated tests to check system compatibility
4. Review this documentation for workflow requirements

## Files in This Package

- `SPS_make_illumina_index_and_FA_files_NEW.py`: Main script
- `test_SPS_make_illumina_index_and_FA_files_NEW.py`: Comprehensive test suite
- `README_SPS_make_illumina_index_and_FA_files_NEW.md`: This documentation