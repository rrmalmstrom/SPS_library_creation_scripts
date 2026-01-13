#!/usr/bin/env python3

# USAGE: python SPS_make_illumina_index_and_FA_files_NEW.py

"""
SPS Library Creation Script - Enhanced Multi-Grid Table Version

This script automatically detects ALL valid grid table CSV files in the current
working directory and merges them with an existing project_summary.db database
to generate all necessary files for library preparation:
- Echo transfer files
- Illumina index transfer files
- Fragment Analyzer (FA) input files
- Dilution transfer files
- Bartender barcode label files

ENHANCED FEATURES:
- Multi-grid table processing: Processes ALL valid grid table files in directory
- Comprehensive duplicate detection: Validates samples across all files
- Missing sample identification: Ensures all database samples are present
- Enhanced safety validation: Prevents laboratory automation errors
- Backward compatibility: Single-file workflows still supported

The script archives existing database files before creating updated versions.

Grid Table Requirements:
Each grid table CSV file must contain these required columns:
- Well: Well position (e.g., A1, B2, C3)
- Library Plate Label: Destination plate name/identifier
- Illumina Library: Library identifier
- Library Plate Container Barcode: Destination plate barcode
- Nucleic Acid ID: Sample identifier (REQUIRED - cannot be empty)

Safety Features:
- FATAL ERROR on duplicate samples across files
- FATAL ERROR on missing Nucleic Acid IDs
- FATAL ERROR on missing database samples in grid tables
- Comprehensive validation with detailed error reporting
"""

import pandas as pd
import numpy as np
import sys
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    script_name = Path(__file__).stem
    status_dir = Path(".workflow_status")
    status_dir.mkdir(exist_ok=True)
    success_file = status_dir / f"{script_name}.success"
    
    try:
        with open(success_file, "w") as f:
            f.write(f"SUCCESS: {script_name} completed at {datetime.now()}\n")
        print(f"✅ Success marker created: {success_file}")
    except Exception as e:
        print(f"❌ ERROR: Could not create success marker: {e}")
        print("Script failed - workflow manager integration requires success marker")
        sys.exit()


# Global well lists for plate formats
WELL_LIST_96W = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']

WELL_LIST_384W = ['A1', 'C1', 'E1', 'G1', 'I1', 'K1', 'M1', 'O1', 'A3', 'C3', 'E3', 'G3', 'I3', 'K3', 'M3', 'O3', 'A5', 'C5', 'E5', 'G5',
                  'I5', 'K5', 'M5', 'O5', 'A7', 'C7', 'E7', 'G7', 'I7', 'K7', 'M7', 'O7', 'A9', 'C9', 'E9', 'G9', 'I9', 'K9', 'M9', 'O9',
                  'A11', 'C11', 'E11', 'G11', 'I11', 'K11', 'M11', 'O11', 'A13', 'C13', 'E13', 'G13', 'I13', 'K13', 'M13', 'O13', 'A15',
                  'C15', 'E15', 'G15', 'I15', 'K15', 'M15', 'O15', 'A17', 'C17', 'E17', 'G17', 'I17', 'K17', 'M17', 'O17', 'A19', 'C19',
                  'E19', 'G19', 'I19', 'K19', 'M19', 'O19', 'A21', 'C21', 'E21', 'G21', 'I21', 'K21', 'M21', 'O21', 'A23', 'C23', 'E23',
                  'G23', 'I23', 'K23', 'M23', 'O23']


def create_directories():
    """Create the complete directory structure for the SPS workflow (adapted from original)."""
    BASE_DIR = Path.cwd()
    
    # Main project directory
    PROJECT_DIR = BASE_DIR / "1_make_library_analyze_fa"
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    
    # First attempt library creation
    LIB_DIR = PROJECT_DIR / "A_first_attempt_make_lib"
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    
    ECHO_DIR = LIB_DIR / "echo_transfer_files"
    ECHO_DIR.mkdir(parents=True, exist_ok=True)
    
    INDEX_DIR = LIB_DIR / "illumina_index_transfer_files"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    FTRAN_DIR = LIB_DIR / "fa_transfer_files"
    FTRAN_DIR.mkdir(parents=True, exist_ok=True)
    
    FA_DIR = LIB_DIR / "FA_input_files"
    FA_DIR.mkdir(parents=True, exist_ok=True)
    
    # First attempt FA results
    ANALYZE_DIR = PROJECT_DIR / "B_first_attempt_fa_result"
    ANALYZE_DIR.mkdir(parents=True, exist_ok=True)
    
    # # Second attempt directories (for future use)
    # SECOND_DIR = PROJECT_DIR / "C_second_attempt_make_lib"
    # SECOND_DIR.mkdir(parents=True, exist_ok=True)
    
    # SECFA_DIR = PROJECT_DIR / "D_second_attempt_fa_result"
    # SECFA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Pooling workflow directories
    POOL_DIR = BASE_DIR / "2_pooling"
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    
    LIMS_DIR = POOL_DIR / "A_smear_file_for_ESP_upload"
    LIMS_DIR.mkdir(parents=True, exist_ok=True)
    
    ASGNPOOL_DIR = POOL_DIR / "B_assign_libs_to_pools"
    ASGNPOOL_DIR.mkdir(parents=True, exist_ok=True)
    
    FINISH_DIR = POOL_DIR / "C_finish_pooling"
    FINISH_DIR.mkdir(parents=True, exist_ok=True)
    
    REWORK_DIR = POOL_DIR / "D_pooling_and_rework"
    REWORK_DIR.mkdir(parents=True, exist_ok=True)
    
    # Archive directory
    ARCHIVE_DIR = BASE_DIR / "archived_files"
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    return BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR


def get_plate_type():
    """Get plate configuration and well mappings (adapted from original)."""
    # Create conversion dictionaries
    convert_96_to_384_plate = dict(zip(WELL_LIST_96W, WELL_LIST_384W))
    convert_384_to_96_plate = dict(zip(WELL_LIST_384W, WELL_LIST_96W))
    
    # Use 95-well format (standard for CE and SPS)
    well_list_95w_1_empty = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                             'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                             'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                             'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                             'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']
    
    return well_list_95w_1_empty, convert_96_to_384_plate, convert_384_to_96_plate


def read_project_database(base_dir):
    """Read the existing project_summary.db into a pandas DataFrame."""
    db_path = base_dir / 'project_summary.db'
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        query = "SELECT * FROM project_summary"
        db_df = pd.read_sql(query, engine)
        engine.dispose()
        
        print(f"Successfully read {len(db_df)} rows from project_summary.db")
        return db_df
        
    except Exception as e:
        raise RuntimeError(f"Error reading database: {e}")


def read_multiple_grid_tables(grid_table_files):
    """Read and concatenate multiple grid table files with comprehensive validation.
    
    This function processes multiple grid table CSV files, validates their structure
    and content, detects duplicate samples across files, and combines them into a
    single DataFrame for downstream processing. All validation errors are FATAL.
    
    Args:
        grid_table_files (list): List of grid table file paths as strings
        
    Returns:
        pd.DataFrame: Concatenated and validated grid table data with all samples
        
    Raises:
        ValueError: If no files provided or duplicate samples found (FATAL)
        FileNotFoundError: If any grid table file not found (FATAL)
        RuntimeError: If file reading fails (FATAL)
        
    Validation Process:
        1. Validates each file exists and is readable
        2. Checks required column headers in each file
        3. Detects duplicate samples across ALL files (FATAL if found)
        4. Validates Nucleic Acid IDs are not empty (FATAL if empty)
        5. Combines all valid data into single DataFrame
        
    Required Columns (validated for each file):
        - Well: Well position (e.g., A1, B2, C3)
        - Library Plate Label: Destination plate name
        - Illumina Library: Library identifier
        - Library Plate Container Barcode: Destination plate barcode
        - Nucleic Acid ID: Sample identifier (cannot be empty)
        
    Duplicate Detection:
        - Well + Library Plate Label combinations
        - Nucleic Acid ID duplicates
        - Container Barcode + Well combinations
        
    Example:
        >>> files = ['grid1.csv', 'grid2.csv', 'grid3.csv']
        >>> combined_df = read_multiple_grid_tables(files)
        Successfully read 32 rows from grid1.csv
        Successfully read 28 rows from grid2.csv
        Successfully read 35 rows from grid3.csv
        ✅ No duplicate samples detected across grid tables
        Successfully combined 3 grid table file(s) with 95 total samples
    """
    if not grid_table_files:
        raise ValueError("No grid table files provided")
    
    grid_dataframes = []
    
    # Read each grid table file
    for filename in grid_table_files:
        grid_path = Path(filename)
        
        if not grid_path.exists():
            raise FileNotFoundError(f"Grid table file not found: {filename}")
        
        try:
            grid_df = pd.read_csv(grid_path)
            
            # Validate required columns
            required_cols = ['Well', 'Library Plate Label', 'Illumina Library', 'Library Plate Container Barcode', 'Nucleic Acid ID']
            missing_cols = [col for col in required_cols if col not in grid_df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
            
            # Store dataframe with source file info
            grid_dataframes.append((filename, grid_df))
            
            print(f"Successfully read {len(grid_df)} rows from {Path(filename).name}")
            
        except Exception as e:
            raise RuntimeError(f"Error reading grid table {filename}: {e}")
    
    # Detect duplicate samples across files (FATAL if found)
    duplicate_report = detect_duplicate_samples(grid_dataframes)
    print("✅ No duplicate samples detected across grid tables")
    
    # Concatenate all dataframes
    combined_df = pd.concat([df for _, df in grid_dataframes], ignore_index=True)
    
    print(f"Successfully combined {len(grid_dataframes)} grid table file(s) with {len(combined_df)} total samples")
    
    return combined_df


def detect_duplicate_samples(grid_dataframes):
    """Detect duplicate samples across multiple grid tables with comprehensive validation.
    
    This function performs critical safety validation by detecting duplicate samples
    across multiple grid table files using multiple criteria. Any duplicates found
    result in FATAL ERROR termination to prevent laboratory automation errors.
    
    Args:
        grid_dataframes (list): List of (filename, dataframe) tuples
        
    Returns:
        dict: Empty dict if no duplicates found (function exits on duplicates)
        
    Raises:
        ValueError: If duplicates found or empty Nucleic Acid IDs detected (FATAL ERROR)
        
    Validation Criteria:
        1. Well + Library Plate Label combinations (must be unique across files)
        2. Nucleic Acid ID duplicates (must be unique across files)
        3. Container Barcode + Well combinations (must be unique across files)
        4. Empty/missing Nucleic Acid IDs (FATAL - laboratory safety requirement)
        
    Error Reporting:
        - Detailed location information (filename, row, well, plate)
        - Multiple duplicate types reported simultaneously
        - Clear error messages for laboratory technicians
        - Specific guidance for resolution
        
    Laboratory Safety:
        - Prevents duplicate sample processing
        - Ensures sample traceability
        - Validates data integrity before automation
        - Protects against cross-contamination
        
    Example Error Output:
        FATAL ERROR: Duplicate samples detected across grid tables!
        
        Nucleic Acid ID Duplicates:
        - Sample ID 'SAMPLE123' found in both:
          * grid_table_1.csv (well A1)
          * grid_table_2.csv (well B2)
          
        Laboratory safety requires unique samples across all grid tables.
        Please resolve duplicates before proceeding.
    """
    all_samples = []
    duplicate_report = {}
    
    # Collect all samples with their source file information
    for filename, df in grid_dataframes:
        for idx, row in df.iterrows():
            # Check for empty/NaN Nucleic Acid ID - this is a fatal error
            nucleic_acid_id = row['Nucleic Acid ID']
            if pd.isna(nucleic_acid_id) or str(nucleic_acid_id).strip() == '':
                error_msg = f"FATAL ERROR: Empty or missing Nucleic Acid ID found!\n\n"
                error_msg += f"File: {filename}\n"
                error_msg += f"Row: {idx + 2}\n"  # +2 because pandas is 0-indexed and CSV has header
                error_msg += f"Well: {row['Well']}\n"
                error_msg += f"Plate: {row['Library Plate Label']}\n\n"
                error_msg += "All samples must have valid Nucleic Acid IDs for laboratory safety.\n"
                error_msg += "Please verify data integrity before proceeding."
                raise ValueError(error_msg)
            
            sample_info = {
                'filename': filename,
                'well': row['Well'],
                'plate_label': row['Library Plate Label'],
                'nucleic_acid_id': nucleic_acid_id,
                'container_barcode': row['Library Plate Container Barcode'],
                'well_plate_key': f"{row['Well']}_{row['Library Plate Label']}",
                'container_well_key': f"{row['Library Plate Container Barcode']}_{row['Well']}"
            }
            all_samples.append(sample_info)
    
    # Check for duplicates using multiple criteria
    duplicates_found = False
    
    # Check 1: (Well, Library Plate Label) combination duplicates
    well_plate_seen = {}
    for sample in all_samples:
        key = sample['well_plate_key']
        if key in well_plate_seen:
            duplicates_found = True
            if 'well_plate_duplicates' not in duplicate_report:
                duplicate_report['well_plate_duplicates'] = []
            duplicate_report['well_plate_duplicates'].append({
                'key': key,
                'first_file': well_plate_seen[key]['filename'],
                'second_file': sample['filename'],
                'well': sample['well'],
                'plate_label': sample['plate_label']
            })
        else:
            well_plate_seen[key] = sample
    
    # Check 2: Nucleic Acid ID duplicates
    nucleic_acid_seen = {}
    for sample in all_samples:
        key = sample['nucleic_acid_id']
        if key in nucleic_acid_seen:
            duplicates_found = True
            if 'nucleic_acid_duplicates' not in duplicate_report:
                duplicate_report['nucleic_acid_duplicates'] = []
            duplicate_report['nucleic_acid_duplicates'].append({
                'nucleic_acid_id': key,
                'first_file': nucleic_acid_seen[key]['filename'],
                'second_file': sample['filename'],
                'first_well': nucleic_acid_seen[key]['well'],
                'second_well': sample['well']
            })
        else:
            nucleic_acid_seen[key] = sample
    
    # Check 3: (Container Barcode, Well) combination duplicates
    container_well_seen = {}
    for sample in all_samples:
        key = sample['container_well_key']
        if key in container_well_seen:
            duplicates_found = True
            if 'container_well_duplicates' not in duplicate_report:
                duplicate_report['container_well_duplicates'] = []
            duplicate_report['container_well_duplicates'].append({
                'key': key,
                'first_file': container_well_seen[key]['filename'],
                'second_file': sample['filename'],
                'container_barcode': sample['container_barcode'],
                'well': sample['well']
            })
        else:
            container_well_seen[key] = sample
    
    # If duplicates found, raise fatal error
    if duplicates_found:
        error_msg = "FATAL ERROR: Duplicate samples detected across grid tables!\n\n"
        
        if 'well_plate_duplicates' in duplicate_report:
            error_msg += "Well + Plate Label Duplicates:\n"
            for dup in duplicate_report['well_plate_duplicates']:
                error_msg += f"- Well {dup['well']} on plate '{dup['plate_label']}' found in both:\n"
                error_msg += f"  * {dup['first_file']}\n"
                error_msg += f"  * {dup['second_file']}\n"
            error_msg += "\n"
        
        if 'nucleic_acid_duplicates' in duplicate_report:
            error_msg += "Nucleic Acid ID Duplicates:\n"
            for dup in duplicate_report['nucleic_acid_duplicates']:
                error_msg += f"- Sample ID '{dup['nucleic_acid_id']}' found in both:\n"
                error_msg += f"  * {dup['first_file']} (well {dup['first_well']})\n"
                error_msg += f"  * {dup['second_file']} (well {dup['second_well']})\n"
            error_msg += "\n"
        
        if 'container_well_duplicates' in duplicate_report:
            error_msg += "Container Barcode + Well Duplicates:\n"
            for dup in duplicate_report['container_well_duplicates']:
                error_msg += f"- Container '{dup['container_barcode']}' well {dup['well']} found in both:\n"
                error_msg += f"  * {dup['first_file']}\n"
                error_msg += f"  * {dup['second_file']}\n"
            error_msg += "\n"
        
        error_msg += "Laboratory safety requires unique samples across all grid tables.\n"
        error_msg += "Please resolve duplicates before proceeding."
        
        raise ValueError(error_msg)
    
    return duplicate_report


def convert_well_to_row_col(well_position):
    """Convert well position string (e.g., 'C2') to numeric row and column."""
    if pd.isna(well_position) or not isinstance(well_position, str):
        raise ValueError(f"Invalid well position: {well_position}")
    
    well_str = str(well_position).strip().upper()
    
    if len(well_str) < 2:
        raise ValueError(f"Invalid well position format: {well_position}")
    
    # Extract row letter and column number
    row_letter = well_str[0]
    col_str = well_str[1:]
    
    # Validate row letter is A-Z
    if not row_letter.isalpha() or len(row_letter) != 1:
        raise ValueError(f"Invalid well position format: {well_position}")
    
    # Validate row letter is within reasonable range (A-P for 384-well)
    if ord(row_letter) < ord('A') or ord(row_letter) > ord('P'):
        raise ValueError(f"Invalid well position format: {well_position}")
    
    try:
        # Convert row letter to number (A=1, B=2, etc.)
        row_num = ord(row_letter) - ord('A') + 1
        col_num = int(col_str)
        
        # Validate column number is reasonable (1-24 for 384-well)
        if col_num < 1 or col_num > 24:
            raise ValueError(f"Invalid well position format: {well_position}")
        
        return row_num, col_num
        
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid well position format: {well_position}")


def identify_missing_samples(db_df, combined_grid_df):
    """Identify samples present in database but missing from grid tables.
    
    This function performs critical validation to ensure ALL database samples
    are present in the combined grid table data. Missing samples result in
    FATAL ERROR termination to prevent incomplete laboratory automation.
    
    Args:
        db_df (pd.DataFrame): Database samples from project_summary.db
        combined_grid_df (pd.DataFrame): Combined grid table data from all files
        
    Returns:
        pd.DataFrame: Empty DataFrame if no missing samples (function exits on missing)
        
    Raises:
        ValueError: If missing samples found (FATAL ERROR)
        
    Validation Process:
        1. Creates merge keys from Well + Plate combinations
        2. Compares database keys against grid table keys
        3. Identifies any database samples not in grid tables
        4. Generates detailed missing sample report with location info
        5. Raises FATAL ERROR if any samples missing
        
    Laboratory Safety:
        - Ensures complete sample coverage for automation
        - Prevents partial processing of sample sets
        - Validates data integrity before liquid handling
        - Protects against missing sample errors in downstream analysis
        
    Error Reporting:
        - Detailed table showing missing samples
        - Source plate and well information
        - Internal sample names and identifiers
        - Clear guidance for resolution
        
    Example Error Output:
        FATAL ERROR: 3 samples from database not found in grid tables!
        
        Missing Samples:
        Destination_Well | Destination_Plate | Internal_Name | Source_Plate | Source_Well
        -------------------------------------------------------------------------------
        A1              | 27-810155        | Sample001     | Prtist.13    | B2
        B3              | 27-810156        | Sample045     | Prtist.14    | C5
        
        All database samples must be present in grid tables for laboratory safety.
        Please verify grid table completeness before proceeding.
    """
    # Create merge keys for comparison
    db_keys = db_df[['Destination_Well', 'Destination_plate_name']].copy()
    db_keys['db_key'] = db_keys['Destination_Well'] + '_' + db_keys['Destination_plate_name']
    
    grid_keys = combined_grid_df[['Well', 'Library Plate Label']].copy()
    grid_keys['grid_key'] = grid_keys['Well'] + '_' + grid_keys['Library Plate Label']
    
    # Find database samples not present in grid tables
    db_key_set = set(db_keys['db_key'])
    grid_key_set = set(grid_keys['grid_key'])
    
    missing_keys = db_key_set - grid_key_set
    
    if missing_keys:
        # Create detailed missing samples report
        missing_samples = []
        for missing_key in missing_keys:
            well, plate = missing_key.split('_', 1)
            db_sample = db_df[(db_df['Destination_Well'] == well) &
                             (db_df['Destination_plate_name'] == plate)]
            if not db_sample.empty:
                sample_info = db_sample.iloc[0]
                missing_samples.append({
                    'Destination_Well': well,
                    'Destination_plate_name': plate,
                    'internal_name': sample_info.get('internal_name', 'N/A'),
                    'plate_id': sample_info.get('plate_id', 'N/A'),
                    'source_well': sample_info.get('source_well', 'N/A')
                })
        
        missing_df = pd.DataFrame(missing_samples)
        
        # Create detailed error message
        error_msg = f"FATAL ERROR: {len(missing_samples)} samples from database not found in grid tables!\n\n"
        error_msg += "Missing Samples:\n"
        error_msg += "Destination_Well | Destination_Plate | Internal_Name | Source_Plate | Source_Well\n"
        error_msg += "-" * 80 + "\n"
        
        for _, sample in missing_df.iterrows():
            error_msg += f"{sample['Destination_Well']:15} | {sample['Destination_plate_name']:16} | "
            error_msg += f"{sample['internal_name']:13} | {sample['plate_id']:12} | {sample['source_well']}\n"
        
        error_msg += "\nAll database samples must be present in grid tables for laboratory safety.\n"
        error_msg += "Please verify grid table completeness before proceeding."
        
        raise ValueError(error_msg)
    
    print(f"✅ All {len(db_df)} database samples found in grid tables")
    return pd.DataFrame()  # Return empty DataFrame if no missing samples


def validate_and_merge_data(db_df, grid_df):
    """Merge database and grid table data with validation."""
    print("Validating and merging data...")
    
    # Select only the 5 columns we need from grid table
    grid_subset = grid_df[['Well', 'Library Plate Label', 'Illumina Library', 'Library Plate Container Barcode', 'Nucleic Acid ID']].copy()
    
    # Rename columns for final output
    grid_subset = grid_subset.rename(columns={
        'Library Plate Container Barcode': 'Destination_Plate_Barcode',
        'Nucleic Acid ID': 'sample_id'
    })
    
    # Perform merge
    merged_df = pd.merge(
        db_df,
        grid_subset,
        left_on=['Destination_Well', 'Destination_plate_name'],
        right_on=['Well', 'Library Plate Label'],
        how='inner'
    )
    
    # Validate perfect merge
    if len(merged_df) != len(db_df):
        missing_db = len(db_df) - len(merged_df)
        raise ValueError(f"Merge validation failed: {missing_db} rows from database not matched")
    
    if len(merged_df) != len(grid_df):
        missing_grid = len(grid_df) - len(merged_df)
        raise ValueError(f"Merge validation failed: {missing_grid} rows from grid table not matched")
    
    # Drop the merge key columns from grid table (we keep the database versions)
    merged_df = merged_df.drop(columns=['Well', 'Library Plate Label'])
    
    print(f"Successfully merged {len(merged_df)} rows with perfect 1:1 match")
    return merged_df


def archive_existing_files(base_dir, archive_dir):
    """Archive existing project_summary.db and .csv files with timestamp."""
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    
    # Archive database file
    db_file = base_dir / "project_summary.db"
    if db_file.exists():
        archive_db = archive_dir / f"archive_project_summary_{timestamp}.db"
        db_file.rename(archive_db)
        # print(f"Archived database to: {archive_db}")
    
    # Archive CSV file
    csv_file = base_dir / "project_summary.csv"
    if csv_file.exists():
        archive_csv = archive_dir / f"archive_project_summary_{timestamp}.csv"
        csv_file.rename(archive_csv)
        # print(f"Archived CSV to: {archive_csv}")


def update_database(merged_df, base_dir):
    """Create new database and CSV files from merged data."""
    # Reorder columns as requested
    column_order = [
        'sample_id',
        'internal_name',
        'plate_id',
        'echo_id',
        'source_well',
        'type',
        'Destination_plate_name',
        'Destination_Plate_Barcode',
        'Destination_Well',
        'Illumina_index_set',
        'Illumina_index',
        'Illumina Library'
    ]
    
    # Reorder the dataframe columns
    merged_df_ordered = merged_df[column_order]
    
    # Create new SQLite database
    db_path = base_dir / 'project_summary.db'
    engine = create_engine(f'sqlite:///{db_path}')
    merged_df_ordered.to_sql('project_summary', engine, if_exists='replace', index=False)
    engine.dispose()
    
    # Create new CSV file
    csv_path = base_dir / 'project_summary.csv'
    merged_df_ordered.to_csv(csv_path, index=False)
    
    # print(f"Created new database and CSV with {len(merged_df_ordered)} rows")


def prepare_echo_data(merged_df):
    """Prepare data for Echo transfer files."""
    echo_df = merged_df.copy()
    
    # Convert well positions to numeric row/column with final column names
    # Use 'source_well' column from database for source positions (where samples come from)
    echo_df['Source Row'], echo_df['Source Column'] = zip(*echo_df['source_well'].apply(convert_well_to_row_col))
    # Use 'Destination_Well' for destination positions (where samples go to)
    echo_df['Destination Row'], echo_df['Destination Column'] = zip(*echo_df['Destination_Well'].apply(convert_well_to_row_col))
    
    # Create Echo file format
    echo_df = echo_df.rename(columns={
        'plate_id': 'Source Plate Name',
        'echo_id': 'Source Plate Barcode',
        'Destination_plate_name': 'Destination Plate Name',
        'Destination_Plate_Barcode': 'Destination Plate Barcode'
    })
    
    echo_df['Transfer Volume'] = 1000
    
    # Select final columns
    echo_final = echo_df[['Source Plate Name', 'Source Plate Barcode', 'Source Row', 'Source Column',
                         'Destination Plate Name', 'Destination Plate Barcode', 'Destination Row', 'Destination Column', 'Transfer Volume']]
    
    return echo_final


def make_echo_files(echo_df, directories):
    """Generate Echo transfer files grouped by destination plate."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    # Group by destination plate
    dest_plates = echo_df['Destination Plate Barcode'].unique()
    
    for dest_plate in dest_plates:
        plate_data = echo_df[echo_df['Destination Plate Barcode'] == dest_plate].copy()
        
        # Get unique source plates for this destination and sort them numerically
        source_plates = plate_data['Source Plate Barcode'].unique()
        # Sort numerically by extracting the number from plate names like "Prtist.13"
        def extract_plate_number(plate_name):
            try:
                # Extract number after the last dot
                return int(plate_name.split('.')[-1])
            except (ValueError, IndexError):
                # If no number found, return the original string for alphabetical sort
                return plate_name
        
        source_plates_sorted = sorted(source_plates, key=extract_plate_number)
        source_names = '_'.join(source_plates_sorted)
        
        # Create filename: destination_source1_source2_etc.csv
        filename = f"{dest_plate}_{source_names}.csv"
        
        # Sort by destination column and row
        plate_data = plate_data.sort_values(['Destination Column', 'Destination Row'])
        
        # Save file
        plate_data.to_csv(ECHO_DIR / filename, index=False)
        # print(f"Created Echo file: {filename}")


def create_illum_dataframe(merged_df, convert_384_to_96):
    """Prepare Illumina index data (adapted from original)."""
    illum_df = merged_df[['Destination_Plate_Barcode', 'Destination_Well', 'Illumina_index_set']].copy()
    
    # Convert 384-well to 96-well positions
    illum_df['Destination_Well_96'] = illum_df['Destination_Well'].replace(convert_384_to_96)
    
    # Set primer volume
    illum_df['Primer_volume_(uL)'] = 2
    
    # Rename columns
    illum_df = illum_df.rename(columns={
        'Destination_Well': 'Lib_plate_well',
        'Destination_Plate_Barcode': 'Lib_plate_ID',
        'Destination_Well_96': 'Illumina_source_well'
    })
    
    # Reorder columns
    illum_df = illum_df[['Illumina_index_set', 'Illumina_source_well', 'Lib_plate_ID', 'Lib_plate_well', 'Primer_volume_(uL)']]
    
    return illum_df


def make_illumina_files(illum_df, directories):
    """Generate Illumina index transfer files."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    dest_plates = illum_df['Lib_plate_ID'].unique()
    
    for dest_plate in dest_plates:
        plate_data = illum_df[illum_df['Lib_plate_ID'] == dest_plate].copy()
        
        # Add "h" prefix for Hamilton scanner
        plate_data['Lib_plate_ID'] = "h" + plate_data['Lib_plate_ID'].astype(str)
        
        # Save file
        filename = f"Illumina_index_transfer_{dest_plate}.csv"
        plate_data.to_csv(INDEX_DIR / filename, index=False)
        # print(f"Created Illumina file: {filename}")


def create_fa_dataframe(merged_df, convert_384_to_96):
    """Prepare FA data (adapted from original)."""
    FA_df = merged_df[['Destination_Plate_Barcode', 'sample_id']].copy()
    
    # Convert 384-well to 96-well positions
    FA_df['Destination_Well_96'] = merged_df['Destination_Well'].replace(convert_384_to_96)
    
    # Convert sample_id to string
    FA_df['sample_id'] = FA_df['sample_id'].astype(str)
    
    # Create sample names
    FA_df['name'] = FA_df[['Destination_Plate_Barcode', 'sample_id', 'Destination_Well_96']].agg('_'.join, axis=1)
    
    # Keep only needed columns
    FA_df = FA_df[['Destination_Plate_Barcode', 'Destination_Well_96', 'name']]
    
    return FA_df


def make_fa_files(FA_df, directories):
    """Generate FA upload files."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    dest_plates = FA_df['Destination_Plate_Barcode'].unique()
    
    for dest_plate in dest_plates:
        # Create dataframe with all 96 wells
        tmp_fa_df = pd.DataFrame(WELL_LIST_96W, columns=["Well"])
        
        # Merge with plate data
        plate_data = FA_df[FA_df['Destination_Plate_Barcode'] == dest_plate]
        tmp_fa_df = tmp_fa_df.merge(plate_data, how='outer', left_on=['Well'], right_on=['Destination_Well_96'])
        
        # Sort by column first (1-12), then by row (A-H) within each column
        # Extract row letter and column number for sorting
        tmp_fa_df['Row_Letter'] = tmp_fa_df['Well'].str[0]
        tmp_fa_df['Column_Number'] = tmp_fa_df['Well'].str[1:].astype(int)
        
        # Sort by column number first, then by row letter
        tmp_fa_df = tmp_fa_df.sort_values(['Column_Number', 'Row_Letter'])
        
        # Drop the temporary sorting columns
        tmp_fa_df = tmp_fa_df.drop(columns=['Row_Letter', 'Column_Number'])
        
        # Reset and set index starting from 1
        tmp_fa_df = tmp_fa_df.reset_index(drop=True)
        tmp_fa_df.index = range(1, len(tmp_fa_df) + 1)
        
        # Fill empty wells
        tmp_fa_df['name'] = tmp_fa_df['name'].fillna('empty_well')
        
        # Set ladder in H12
        tmp_fa_df.loc[tmp_fa_df['Well'] == 'H12', 'name'] = "ladder_1"
        
        # Clean up columns
        tmp_fa_df = tmp_fa_df[['Well', 'name']]
        
        # Save file
        filename = f"FA_upload_{dest_plate}.csv"
        tmp_fa_df.to_csv(FA_DIR / filename, index=True, header=False)
        # print(f"Created FA file: {filename}")


def make_dilution_dataframe(merged_df):
    """Create dilution transfer dataframe."""
    # Ask user for dilution factor
    dilution_factor = float(input("What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): ") or 5)
    
    dilution_df = merged_df[['Destination_Plate_Barcode', 'Destination_Well']].copy()
    
    # Convert 384-well to 96-well positions for FA
    convert_384_to_96 = dict(zip(WELL_LIST_384W, WELL_LIST_96W))
    
    dilution_df['FA_Well'] = dilution_df['Destination_Well'].replace(convert_384_to_96)
    dilution_df['dilution_factor'] = dilution_factor
    
    # Rename columns
    dilution_df = dilution_df.rename(columns={
        'Destination_Plate_Barcode': 'Library_Plate_Barcode',
        'Destination_Well': 'Library_Well'
    })
    
    # Create plate barcodes
    dilution_df['FA_Plate_Barcode'] = dilution_df['Library_Plate_Barcode'] + "F"
    dilution_df['Dilution_Plate_Barcode'] = dilution_df['Library_Plate_Barcode'] + "D"
    
    # Set volumes
    dilution_df['Nextera_Vol_Add'] = 30
    dilution_df['FA_Vol_Add'] = 2.4
    dilution_df['Dilution_Vol'] = 2.4
    dilution_df['Dilution_Plate_Preload'] = np.ceil((dilution_factor - 1) * dilution_df['FA_Vol_Add'])
    dilution_df['Total_buffer_aspiration'] = dilution_df['Nextera_Vol_Add'] + dilution_df['Dilution_Plate_Preload']
    
    # Reorder columns
    column_order = ['Library_Plate_Barcode', 'Dilution_Plate_Barcode', 'FA_Plate_Barcode', 'Library_Well', 'FA_Well',
                   'Nextera_Vol_Add', 'Dilution_Vol', 'FA_Vol_Add', 'Dilution_Plate_Preload', 'Total_buffer_aspiration']
    dilution_df = dilution_df[column_order]
    
    return dilution_df


def make_dilution_files(dilution_df, directories):
    """Generate dilution transfer files."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    dest_plates = dilution_df['Library_Plate_Barcode'].unique()
    
    for dest_plate in dest_plates:
        plate_data = dilution_df[dilution_df['Library_Plate_Barcode'] == dest_plate].copy()
        
        # Add "h" prefix for Hamilton scanner
        plate_data['Library_Plate_Barcode'] = 'h' + plate_data['Library_Plate_Barcode']
        
        # Save file
        filename = f"FA_plate_transfer_{dest_plate}.csv"
        plate_data.to_csv(FTRAN_DIR / filename, index=False)
        # print(f"Created dilution file: {filename}")


def make_threshold_file(merged_df, directories):
    """Generate threshold file for FA analysis."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    # Get unique destination plates and their dilution factors
    dest_plates = merged_df['Destination_Plate_Barcode'].unique()
    
    # Create threshold dataframe
    thresh_df = pd.DataFrame({
        'Destination_plate': dest_plates,
        'DNA_conc_threshold_(nmol/L)': "",
        'Size_theshold_(bp)': 530,
        'dilution_factor': 5  # Default value, could be made configurable
    })
    
    # Save file
    thresh_df.to_csv(ANALYZE_DIR / 'thresholds.txt', index=False, sep='\t')
    # print("Created threshold file: thresholds.txt")


def make_bartender_labels(merged_df, directories):
    """Generate Bartender barcode label file."""
    BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
    
    dest_list = sorted(merged_df['Destination_Plate_Barcode'].unique().tolist())
    
    # Bartender header
    header = '%BTW% /AF="\\\\BARTENDER\\shared\\templates\\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'
    
    filename = "BARTENDER_Library_IlluminaIndex_FA_plate_labels.txt"
    
    with open(filename, "w") as bc_file:
        bc_file.write(header)
        
        # Reverse sort for printing order
        dest_list.reverse()
        
        # FA run plates
        for plate in dest_list:
            bc_file.write(f'{plate}F,"FA.run {plate}F"\r\n')
        bc_file.write(',\r\n')
        
        # FA dilution plates
        for plate in dest_list:
            bc_file.write(f'{plate}D,"FA.dilute {plate}D"\r\n')
        bc_file.write(',\r\n')
        
        # Library plates
        for plate in dest_list:
            bc_file.write(f'h{plate},"     h{plate}"\r\n')
            bc_file.write(f'{plate},"SPS.lib.plate {plate}"\r\n')
    
    # Move to library directory
    Path(filename).rename(LIB_DIR / filename)
    # print(f"Created Bartender file: {filename}")


def find_csv_files(base_dir):
    """Find all CSV files in the base directory."""
    csv_files = []
    try:
        for file_path in base_dir.glob("*.csv"):
            if file_path.is_file():
                csv_files.append(file_path)
    except Exception as e:
        print(f"Error scanning directory for CSV files: {e}")
    
    return csv_files


def validate_grid_table_columns(csv_file):
    """Check if CSV file has required grid table columns without full validation."""
    required_cols = ['Well', 'Library Plate Label', 'Illumina Library', 'Library Plate Container Barcode', 'Nucleic Acid ID']
    
    try:
        # Read only the header row to check columns
        df_header = pd.read_csv(csv_file, nrows=0)
        missing_cols = [col for col in required_cols if col not in df_header.columns]
        
        if not missing_cols:
            return True, None
        else:
            return False, f"Missing columns: {missing_cols}"
            
    except Exception as e:
        return False, f"Error reading file: {e}"


def find_all_grid_tables(base_dir):
    """Find and validate ALL grid table files in directory.
    
    This function scans the current working directory for CSV files and validates
    each one to determine if it contains the required grid table columns. It
    supports multi-file processing by finding ALL valid grid table files rather
    than just one.
    
    Args:
        base_dir (Path): Base directory to scan for CSV files
        
    Returns:
        list: List of valid grid table file paths as strings
        
    Raises:
        SystemExit: If no valid grid tables found with detailed error message
        
    Validation Process:
        1. Scans directory for all CSV files
        2. Checks each CSV for required column headers
        3. Reports invalid files with specific error messages
        4. Returns all valid files for multi-grid processing
        
    Required Columns:
        - Well: Well position (e.g., A1, B2, C3)
        - Library Plate Label: Destination plate name
        - Illumina Library: Library identifier
        - Library Plate Container Barcode: Destination plate barcode
        - Nucleic Acid ID: Sample identifier
        
    Example:
        >>> grid_files = find_all_grid_tables(Path.cwd())
        Found 3 valid grid table file(s):
        - grid_table_OSJKAI.1.csv
        - grid_table_OSJKAI.2.csv
        - grid_table_OSJKAI.3.csv
    """
    print("Scanning current directory for grid table CSV files...")
    
    # Find all CSV files
    csv_files = find_csv_files(base_dir)
    
    if not csv_files:
        print("\nERROR: No CSV files found in current directory.")
        print("\nA grid table CSV file must contain these required columns:")
        print("- Well")
        print("- Library Plate Label")
        print("- Illumina Library")
        print("- Library Plate Container Barcode")
        print("- Nucleic Acid ID")
        print("\nPlease ensure your grid table file is in the current directory.")
        sys.exit()
    
    # Validate each CSV file
    valid_files = []
    invalid_files = []
    
    for csv_file in csv_files:
        is_valid, error_msg = validate_grid_table_columns(csv_file)
        if is_valid:
            valid_files.append(csv_file)
        else:
            invalid_files.append((csv_file, error_msg))
    
    # Handle results
    if len(valid_files) == 0:
        print(f"\nERROR: No valid grid table found in current directory.")
        print(f"\nFound {len(csv_files)} CSV file(s), but none contain the required columns:")
        for csv_file, error_msg in invalid_files:
            print(f"- {csv_file.name}: {error_msg}")
        print("\nA grid table CSV file must contain these required columns:")
        print("- Well")
        print("- Library Plate Label")
        print("- Illumina Library")
        print("- Library Plate Container Barcode")
        print("- Nucleic Acid ID")
        print("\nPlease ensure your grid table file contains all required columns.")
        sys.exit()
    
    # Return all valid files
    print(f"Found {len(valid_files)} valid grid table file(s):")
    for valid_file in valid_files:
        print(f"- {valid_file.name}")
    
    return [str(f) for f in valid_files]


def auto_detect_grid_table(base_dir):
    """Automatically detect grid table files in working directory with multi-file support.
    
    This function has been enhanced to support processing multiple grid table files
    simultaneously, replacing the original single-file detection. It maintains
    backward compatibility while enabling multi-grid table workflows.
    
    Args:
        base_dir (Path): Base directory to scan for grid table files
        
    Returns:
        list: List of valid grid table file paths as strings
        
    Raises:
        SystemExit: If no valid grid tables found
        
    Enhanced Features:
        - Multi-file detection: Finds ALL valid grid table files
        - Backward compatibility: Single-file workflows still supported
        - Comprehensive validation: Each file validated for required columns
        - Detailed reporting: Lists all found files with validation status
        
    Example Output:
        Scanning current directory for grid table CSV files...
        Found 3 valid grid table file(s):
        - grid_table_OSJKAI.1.csv
        - grid_table_OSJKAI.2.csv
        - grid_table_OSJKAI.3.csv
    """
    # Use the new find_all_grid_tables function for multi-file support
    return find_all_grid_tables(base_dir)


def main():
    """Main execution function with enhanced multi-grid table processing.
    
    This function orchestrates the complete SPS library creation workflow with
    enhanced multi-grid table support, comprehensive validation, and safety features.
    
    Workflow Steps:
        1. Create directory structure for output files
        2. Auto-detect ALL valid grid table files in current directory
        3. Read project database and combine multiple grid tables
        4. Perform comprehensive duplicate and missing sample validation
        5. Merge and validate data with perfect 1:1 correspondence
        6. Archive existing database files with timestamps
        7. Generate all required output files for laboratory automation
        8. Create success marker for workflow manager integration
        
    Enhanced Features:
        - Multi-grid table processing with automatic file detection
        - Comprehensive duplicate sample detection across all files
        - Missing sample identification and validation
        - Enhanced safety validation with detailed error reporting
        - Backward compatibility with single-file workflows
        
    Output Files Generated:
        - Echo transfer files (grouped by destination plate)
        - Illumina index transfer files
        - Fragment Analyzer input files
        - Dilution transfer files
        - Bartender barcode label files
        - Threshold files for FA analysis
        - Updated project database and CSV files
        
    Error Handling:
        All validation errors are FATAL and terminate execution with
        detailed error messages and resolution guidance.
    """
    try:
        # Create directory structure
        print("Creating directory structure...")
        directories = create_directories()
        BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
        
        # Auto-detect grid table files (supports multiple files)
        grid_table_files = auto_detect_grid_table(BASE_DIR)
        
        # Get plate configuration
        well_list, convert_96_to_384, convert_384_to_96 = get_plate_type()
        
        # Read input data
        print("Reading input data...")
        db_df = read_project_database(BASE_DIR)
        grid_df = read_multiple_grid_tables(grid_table_files)
        
        # Check for missing samples before merge
        identify_missing_samples(db_df, grid_df)
        
        # Merge and validate data
        merged_df = validate_and_merge_data(db_df, grid_df)
        
        # Archive existing files
        print("Archiving existing files...")
        archive_existing_files(BASE_DIR, ARCHIVE_DIR)
        
        # Update database with merged data
        print("Updating database...")
        update_database(merged_df, BASE_DIR)
        
        # Generate all output files
        print("\nGenerating output files...")
        
        # Generate Echo transfer files
        print("Creating Echo transfer files...")
        echo_df = prepare_echo_data(merged_df)
        make_echo_files(echo_df, directories)
        
        # Generate Illumina index files
        print("Creating Illumina index files...")
        illum_df = create_illum_dataframe(merged_df, convert_384_to_96)
        make_illumina_files(illum_df, directories)
        
        # Generate FA files
        print("Creating FA files...")
        fa_df = create_fa_dataframe(merged_df, convert_384_to_96)
        make_fa_files(fa_df, directories)
        
        # Generate dilution files
        print("Creating dilution files...")
        dilution_df = make_dilution_dataframe(merged_df)
        make_dilution_files(dilution_df, directories)
        
        # Generate threshold file
        print("Creating threshold file...")
        make_threshold_file(merged_df, directories)
        
        # Generate Bartender labels
        print("Creating Bartender label file...")
        make_bartender_labels(merged_df, directories)
        
        # Move grid table files to library directory
        for grid_file in grid_table_files:
            grid_path = Path(grid_file)
            if grid_path.exists():
                grid_path.rename(LIB_DIR / grid_path.name)
                # print(f"Moved {grid_path.name} to library directory")
        
        print("\n" + "="*50)
        print("SCRIPT COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Processed {len(merged_df)} samples")
        print("\nAll output files have been created and are ready for use.")
        
        # Create success marker for workflow manager integration
        create_success_marker()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit()


if __name__ == "__main__":
    main()