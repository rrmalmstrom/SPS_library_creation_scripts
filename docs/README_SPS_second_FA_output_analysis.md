# SPS Second FA Output Analysis Script

## Overview

The **SPS Second FA Output Analysis Script** (`SPS_second_FA_output_analysis_NEW.py`) is a critical component of the Single-cell Sequencing (SPS) laboratory workflow. This script processes Fragment Analyzer (FA) output files from second attempt library creation, merges them with existing project data, applies quality control thresholds, and generates comprehensive summary reports.

## Laboratory Workflow Context

### SPS Workflow Position
This script operates at step 6 of the SPS workflow:

1. **Sample Processing** → DNA samples arranged in 96/384-well plates
2. **First Library Creation** → Initial attempt at creating sequencing libraries
3. **First QC Analysis** → Fragment Analyzer measures DNA concentration and size
4. **First Analysis** → `SPS_first_FA_output_analysis_NEW.py` processes results
5. **Rework Decision** → Samples failing QC get second attempt at library creation
6. **🔹 Second Analysis** → **THIS SCRIPT** processes second attempt FA results
7. **Final Decision** → `SPS_conclude_FA_analysis_generate_ESP_smear_file.py` identifies final failures

### Purpose
- **Quality Control**: Validates second attempt library creation success
- **Data Integration**: Merges new FA results with existing project database
- **Failure Identification**: Identifies samples that failed both QC rounds
- **Report Generation**: Creates summary files for laboratory review

## Features

### ✅ **Core Functionality**
- **Automated File Discovery**: Scans nested directory structures for FA output files
- **Plate Name Validation**: Ensures FA plate IDs match sample naming conventions
- **Database Integration**: Merges FA results with SQLite project summary database
- **Quality Threshold Application**: Uses configurable criteria for pass/fail decisions
- **Dilution Factor Correction**: Applies dilution factors to calculate original concentrations
- **Double Failure Detection**: Identifies samples failing both first and second attempts
- **Comprehensive Reporting**: Generates detailed summary and failure reports

### ✅ **Robust Error Handling**
- **Missing File Detection**: Validates all required files and directories exist
- **Data Integrity Checks**: Ensures merge operations preserve data consistency
- **Plate Name Validation**: Prevents processing mismatched plate data
- **User Interaction**: Prompts for dilution factor discrepancy resolution
- **Graceful Failure**: Provides clear error messages and exits cleanly

### ✅ **Modern Implementation**
- **Pathlib Usage**: Consistent cross-platform path handling
- **Enhanced Logging**: Detailed progress reporting and validation messages
- **Type Safety**: Proper data type conversion and validation
- **Memory Efficient**: Processes large datasets without memory issues

## Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, or Linux

### Python Dependencies
```bash
pip install pandas sqlalchemy numpy pathlib
```

### Required Libraries
- `pandas` - Data manipulation and analysis
- `sqlalchemy` - Database connectivity
- `numpy` - Numerical operations
- `pathlib` - Modern path handling
- `shutil` - File operations

## Directory Structure

The script expects the following directory structure from the **project root**:

```
PROJECT_ROOT/                          # Script execution location
├── project_summary.db                 # Main sample database (SQLite)
├── SPS_second_FA_output_analysis_NEW.py # This script
├── 1_make_library_analyze_fa/
│   ├── B_first_attempt_fa_result/     # First attempt results
│   └── D_second_attempt_fa_result/    # Second attempt target directory
│       ├── thresholds.txt             # Quality criteria configuration
│       ├── YYYY MM DD/               # Date-based folders (auto-created by FA)
│       │   ├── 27-XXXXXX.2F HH-MM-SS/ # Plate-specific folders
│       │   │   └── *Smear Analysis Result.csv # FA output files
│       │   └── 27-YYYYYY.2F HH-MM-SS/
│       ├── reduced_2nd_fa_analysis_summary.txt # Output (generated)
│       └── double_failed_libraries.txt         # Output (generated)
└── archived_files/                    # Archive location (auto-created)
```

## Input Files

### 1. Fragment Analyzer Output Files
**Location**: `D_second_attempt_fa_result/YYYY MM DD/PLATE_NAME HH-MM-SS/`
**Format**: `*Smear Analysis Result.csv`

**Required Columns**:
- `Sample ID` - Sample identifier (format: `PLATE.2_SAMPLE_WELL`)
- `Well` - Well position (e.g., `A:01`)
- `ng/uL` - DNA concentration in ng/μL
- `nmole/L` - DNA concentration in nmol/L
- `Avg. Size` - Average fragment size in base pairs

**Example**:
```csv
Sample ID,Well,ng/uL,nmole/L,Avg. Size
27-710888.2_365659_A1,A:01,2.5,12.3,650
27-710888.2_365660_A2,A:02,1.8,8.9,580
```

### 2. Quality Thresholds File
**Location**: `D_second_attempt_fa_result/thresholds.txt`
**Format**: Tab-delimited

**Required Columns**:
- `Destination_plate` - Plate identifier
- `DNA_conc_threshold_(nmol/L)` - Minimum concentration threshold
- `Size_theshold_(bp)` - Minimum size threshold
- `dilution_factor` - Dilution factor for concentration correction

**Example**:
```
Destination_plate	DNA_conc_threshold_(nmol/L)	Size_theshold_(bp)	dilution_factor
27-710888.2	5	530	40
27-710894.2	5	530	40
```

### 3. Project Summary Database
**Location**: `project_summary.db`
**Format**: SQLite database with `project_summary` table

**Key Columns**:
- `sample_id` - Sample identifier
- `Redo_Destination_Plate_Barcode` - Second attempt plate ID
- `Passed_library` - First attempt pass/fail status
- Additional sample metadata and first attempt results

## Usage

### Basic Execution
```bash
# Navigate to project root directory
cd /path/to/project/root

# Run the script
python SPS_second_FA_output_analysis_NEW.py
```

### Expected Output
```
Starting SPS Second FA Output Analysis...
Working directory: /path/to/project/root
Second attempt directory: /path/to/project/root/1_make_library_analyze_fa/D_second_attempt_fa_result
Scanning for FA files in: /path/to/project/root/1_make_library_analyze_fa/D_second_attempt_fa_result
Processing date directory: 2024 06 14
  Found FA plate directory: 27-710888.2F 13-23-17
  Parsed plate name: 27-710888.2F
    Found smear analysis file: 2024 06 14 13H 23M Smear Analysis Result.csv
Validating plate names for 27-710888.2F...
  Sample IDs found: 82 samples
  Parsed plate names: {'27-710888.2F', 'emptyF', 'ladderF'}
  Folder name: 27-710888.2F
  ✓ Validation passed for 27-710888.2F
    Copying [source] -> [destination]
    ✓ Copy successful: [file] (6716 bytes)

Successfully processed 2 FA files:
  - 27-710888.2F.csv
  - 27-710894.2F.csv

Processing 2 FA files...
Processing file: 27-710888.2F.csv
  Read 96 rows from 27-710888.2F.csv
  Filtered out 16 control rows, 80 samples remaining
  Destination plates: ['27-710888.2']
  ✓ Successfully processed 27-710888.2F.csv

Combined FA data: 175 samples
Merging FA results with project summary...
Reading project summary database...
  Read 406 rows from database
  FA data has 175 rows
  After merge: 406 rows
  Successfully merged FA data for 175 samples
Applying quality thresholds...
  Read thresholds for 2 plates
  Samples in rework plates: 175
  Samples that failed both attempts: 0

Analysis complete.
```

## Output Files

### 1. Reduced Second FA Analysis Summary
**File**: `D_second_attempt_fa_result/reduced_2nd_fa_analysis_summary.txt`
**Format**: Tab-delimited

**Columns**:
- `sample_id` - Sample identifier
- `Redo_Destination_Plate_Barcode` - Second attempt plate ID
- `Redo_FA_Well` - Well position
- `Redo_dilution_factor` - Applied dilution factor
- `Redo_ng/uL` - Corrected DNA concentration (ng/μL)
- `Redo_nmole/L` - Corrected DNA concentration (nmol/L)
- `Redo_Avg. Size` - Average fragment size (bp)
- `Redo_Passed_library` - Second attempt pass/fail (1/0)
- `Total_passed_attempts` - Combined first + second attempt passes

### 2. Double Failed Libraries
**File**: `D_second_attempt_fa_result/double_failed_libraries.txt`
**Format**: Tab-delimited

Contains all samples that failed both first and second QC attempts. Same column structure as the main summary but filtered to `Total_passed_attempts = 0`.

## Data Processing Details

### Sample ID Format
- **First Attempt**: `27-710888_365659_A1` (plate_sample_well)
- **Second Attempt**: `27-710888.2_365659_A1` (plate.2_sample_well)
- **Plate Naming**: `.2F` suffix indicates second attempt (e.g., `27-710888.2F`)

### Column Naming Strategy
- **First Attempt**: `FA_` prefix (`FA_Sample_ID`, `FA_Well`, `ng/uL`, etc.)
- **Second Attempt**: `Redo_` prefix (`Redo_FA_Sample_ID`, `Redo_ng/uL`, etc.)
- **Combined Analysis**: `Total_passed_attempts` (sum of both rounds)

### Quality Control Logic
1. **Threshold Application**: Sample passes if BOTH conditions met:
   - `Redo_nmole/L > DNA_conc_threshold_(nmol/L)`
   - `Redo_Avg. Size > Size_theshold_(bp)`

2. **Dilution Correction**: Raw FA concentrations multiplied by dilution factor:
   - `Corrected_ng/uL = Raw_ng/uL × dilution_factor`
   - `Corrected_nmole/L = Raw_nmole/L × dilution_factor`

3. **Total Attempts Calculation**:
   - `Total_passed_attempts = Passed_library + Redo_Passed_library`
   - NaN values treated as 0 for summation

### Control Sample Filtering
Automatically removes control samples containing (case-insensitive):
- `empty` - Empty wells
- `ladder` - Size ladder standards
- `LibStd` - Library standards

## Error Handling

### Common Error Scenarios

#### 1. Missing Database
```
ERROR: Database file not found: /path/to/project_summary.db
```
**Solution**: Ensure `project_summary.db` exists in project root

#### 2. Missing Second Attempt Directory
```
ERROR: Second attempt directory does not exist: /path/to/D_second_attempt_fa_result
```
**Solution**: Create directory structure or verify correct working directory

#### 3. No FA Files Found
```
Did not find any FA output files. Aborting program
```
**Solution**: Verify FA files exist in date-based subdirectories with correct naming

#### 4. Missing Thresholds File
```
ERROR: Thresholds file not found: /path/to/thresholds.txt
```
**Solution**: Create `thresholds.txt` in `D_second_attempt_fa_result/` directory

#### 5. Plate Name Mismatch
```
Mismatch between FA plate ID and sample names for plate 27-710888.2F. Aborting script
```
**Solution**: Verify folder names match sample IDs in FA files

#### 6. Dilution Factor Discrepancy
```
The dilution factor in the thresholds file does not match value in project_summary.csv. 
Is the thresholds.txt file correct? (Y/N):
```
**User Action Required**: 
- `Y` - Use thresholds.txt value (recommended)
- `N` - Abort and fix thresholds.txt file

## Troubleshooting

### Performance Issues
- **Large datasets**: Script handles 1000+ samples efficiently
- **Memory usage**: Minimal memory footprint with pandas optimization
- **Processing time**: Typically 30-60 seconds for standard datasets

### Data Validation
- **Row count preservation**: Merge operations maintain original sample count
- **Type conversion**: Automatic handling of numeric data types
- **Missing data**: NaN values properly handled in calculations

### File System Issues
- **Path handling**: Cross-platform compatibility with pathlib
- **File permissions**: Requires read access to input files, write access to output directory
- **Disk space**: Minimal additional storage required for output files

## Integration with SPS Workflow

### Upstream Dependencies
- **First FA Analysis**: Must be completed before running this script
- **Project Database**: Must contain first attempt results and sample metadata
- **Second Attempt FA**: Fragment Analyzer must have processed second attempt plates

### Downstream Processing
- **Conclude Script**: `SPS_conclude_FA_analysis_generate_ESP_smear_file.py` uses this script's output
- **Database Updates**: Conclude script automatically fixes dilution factor discrepancies
- **Final Reports**: ESP smear files generated for sequencing platform upload

### Workflow Manager Integration
- **Exit Codes**: Always exits with code 0 (workflow manager handles error reporting)
- **Error Messages**: Clear, descriptive messages printed to stdout/stderr
- **Status Reporting**: Detailed progress information for workflow monitoring

## Version History

### Version 2.0 (Current)
- **Refactored**: Complete pathlib implementation for cross-platform compatibility
- **Enhanced Error Handling**: Comprehensive validation and user-friendly error messages
- **Improved Logging**: Detailed progress reporting and debugging information
- **Database Schema**: Updated for `Redo_Destination_Plate_Barcode` column compatibility
- **File Operations**: Enhanced file copying with validation and error recovery
- **Testing**: Comprehensive validation against real laboratory data

### Version 1.0 (Legacy)
- Original implementation with mixed os.path/pathlib usage
- Basic error handling
- Subdirectory execution assumption

## Support and Maintenance

### Laboratory Contact
- **Primary Contact**: Laboratory Automation Team
- **Documentation**: This README and inline code comments
- **Testing Data**: Available in `test_folders/` directory

### Development Notes
- **Code Style**: PEP 8 compliant with comprehensive docstrings
- **Testing**: Validated against real laboratory data from Schultz protist project
- **Error Scenarios**: Tested with missing files, corrupted data, and edge cases
- **Performance**: Optimized for typical laboratory dataset sizes (100-1000 samples)

---

**Last Updated**: January 2026  
**Script Version**: 2.0  
**Python Compatibility**: 3.7+  
**Platform Compatibility**: Windows, macOS, Linux