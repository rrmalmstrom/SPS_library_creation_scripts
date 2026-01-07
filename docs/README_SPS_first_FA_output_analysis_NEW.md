# SPS First FA Output Analysis Script

## Overview

The `SPS_first_FA_output_analysis_NEW.py` script processes Fragment Analyzer (FA) output files to analyze DNA library quality for Single-cell Proteomics by Sequencing (SPS) workflows. This script reads FA smear analysis results, merges them with project summary data, applies quality thresholds, and generates comprehensive summary reports for library pass/fail analysis.

## Features

- **Automated FA File Discovery**: Scans directory structure to find and process FA output CSV files
- **Data Validation**: Validates plate names match between folder structure and sample IDs
- **Quality Assessment**: Applies user-defined thresholds for DNA concentration and fragment size
- **Dilution Factor Correction**: Automatically applies dilution factors to concentration measurements
- **Whole Plate Analysis**: Identifies plates requiring complete rework based on failure rates
- **Comprehensive Reporting**: Generates detailed summary files with pass/fail status

## Requirements

### Environment
- **Python Environment**: `sipsps_env` conda environment
- **Python Version**: 3.11+
- **Required Packages**:
  - `pandas` - Data manipulation and analysis
  - `numpy` - Numerical computing
  - `sqlalchemy` - Database connectivity
  - `pathlib` - Modern path handling

### Directory Structure
The script expects to be run from a project directory with the following structure:
```
project_root/
├── project_summary.db          # SQLite database with sample information
├── 1_make_library_analyze_fa/
│   └── B_first_attempt_fa_result/
│       ├── thresholds.txt      # Quality thresholds configuration
│       └── [date folders]/     # FA output directories
│           └── [plate_folders]/
│               └── *Smear Analysis Result.csv
└── archived_files/             # Auto-created for backups
```

## Input Files

### 1. Project Summary Database (`project_summary.db`)
SQLite database containing sample metadata with required columns:
- `sample_id`: Unique sample identifier
- `Destination_Plate_Barcode`: Target plate barcode
- Additional sample metadata fields

### 2. Thresholds Configuration (`thresholds.txt`)
Tab-separated file defining quality criteria per plate:
```
Destination_plate	DNA_conc_threshold_(nmol/L)	Size_theshold_(bp)	dilution_factor
27-710888	0.3	500	10
27-710889	0.9	500	10
```

### 3. FA Output Files
Fragment Analyzer "Smear Analysis Result.csv" files containing:
- `Well`: Well position
- `Sample ID`: Sample identifier (format: `plate_sample_well`)
- `ng/uL`: DNA concentration
- `nmole/L`: Molar concentration  
- `Avg. Size`: Average fragment size

## Usage

### Basic Execution
```bash
# Activate the conda environment
conda activate sipsps_env

# Navigate to project directory
cd /path/to/project

# Run the script with threshold input
echo "20" | python SPS_first_FA_output_analysis_NEW.py
```

### Interactive Execution
```bash
conda activate sipsps_env
cd /path/to/project
python SPS_first_FA_output_analysis_NEW.py
# When prompted, enter the number of failed libraries per plate to trigger whole plate rework
```

## Output

### Primary Output File
**`reduced_fa_analysis_summary.txt`** - Tab-separated summary containing:
- `sample_id`: Sample identifier
- `Destination_Plate_Barcode`: Plate barcode
- `dilution_factor`: Applied dilution factor
- `ng/uL`: Corrected DNA concentration (ng/μL)
- `nmole/L`: Corrected molar concentration (nmol/L)
- `Avg. Size`: Average fragment size (bp)
- `Passed_library`: Pass/fail status (1/0)
- `Redo_whole_plate`: Whole plate rework flag (True/False)

### Processing Summary
The script provides real-time feedback including:
- List of processed FA output files
- User input prompts
- Completion confirmation with output file location

## Algorithm Details

### 1. File Discovery and Validation
- Scans subdirectories for FA output files
- Validates plate names match between folder structure and sample IDs
- Copies and renames files to working directory

### 2. Data Processing
- Reads FA CSV files with required columns
- Removes control samples (empty, ladder, LibStd)
- Parses sample IDs to extract plate and sample information
- Handles missing values and ensures proper data types

### 3. Data Integration
- Merges FA results with project summary database
- Validates row counts remain consistent after merging
- Integrates quality thresholds from configuration file

### 4. Quality Assessment
- Applies concentration and size thresholds per plate
- Corrects concentrations using dilution factors
- Identifies individual library failures
- Determines whole plate rework requirements based on failure rates

### 5. Output Generation
- Creates comprehensive summary with all relevant metrics
- Sorts results by plate and sample ID
- Saves tab-separated file for downstream analysis

## Error Handling

The script includes robust error handling for common issues:
- **Missing FA files**: Exits with clear error message
- **Plate name mismatches**: Validates consistency between folders and sample IDs
- **Missing thresholds**: Checks for complete threshold data
- **Merge failures**: Validates data integrity during database joins
- **File I/O errors**: Handles missing files and directories gracefully

## Code Quality Features

This script follows Python best practices:
- **PEP 8 Compliance**: Consistent code style and formatting
- **Comprehensive Documentation**: Module and function docstrings
- **Modern Path Handling**: Uses `pathlib` for cross-platform compatibility
- **Proper Error Handling**: Informative error messages and graceful exits
- **Modular Design**: Well-organized functions with clear responsibilities
- **Type Safety**: Explicit data type handling and validation

## Version History

### Current Version (NEW)
- **Improved Code Quality**: PEP 8 compliance, comprehensive docstrings
- **Modern Path Handling**: Consistent use of `pathlib.Path`
- **Enhanced Error Handling**: Better error messages and validation
- **Cleaned Dependencies**: Removed unused imports
- **Professional Structure**: Proper main() function and modular design

### Previous Version
- Legacy implementation with mixed path handling strategies
- Less comprehensive error handling and documentation

## Troubleshooting

### Common Issues

1. **"Did not find any FA output files"**
   - Verify directory structure matches expected format
   - Check that FA output directories contain "Smear Analysis Result.csv" files

2. **"Mismatch between FA plate ID and sample names"**
   - Ensure plate names in folder structure match sample ID prefixes
   - Verify sample ID format follows `plate_sample_well` convention

3. **"Missing needed values in thresholds.txt"**
   - Check that thresholds file contains all required columns
   - Verify no empty cells in the thresholds configuration

4. **Environment Issues**
   - Ensure `sipsps_env` conda environment is activated
   - Verify all required Python packages are installed

### Performance Notes
- Script processes hundreds of samples efficiently
- Runtime typically under 30 seconds for standard datasets
- Memory usage scales linearly with number of samples

## Support

For issues or questions regarding this script:
1. Check the troubleshooting section above
2. Verify input file formats match specifications
3. Ensure proper conda environment activation
4. Review error messages for specific guidance

---

**Author**: SPS Lab  
**Last Updated**: January 2026  
**Script Version**: NEW (Refactored)