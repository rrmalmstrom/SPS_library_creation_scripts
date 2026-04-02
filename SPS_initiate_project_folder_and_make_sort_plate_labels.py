#!/usr/bin/env python3

"""
Laboratory Barcode Label Generation Script

This script generates BarTender-compatible barcode labels for microwell plates
following laboratory safety standards with automated file detection and
simplified barcode generation system.

USAGE: python generate_barcode_labels.py

CRITICAL REQUIREMENTS:
- MUST use sip-lims conda environment
- Follows existing SPS script patterns
- Implements comprehensive error handling with "FATAL ERROR" messaging
- Creates success markers for workflow manager integration

Features:
- Automatic detection of sample metadata CSV files (sample_metadtata.csv)
- File-based input for custom plates (custom_plate_names.txt)
- File-based input for additional standard plates (additional_standard_plates.txt)
- Simplified incremental barcode generation (e.g., ABC12-1, ABC12-2, ABC12-3)
- Two-table database architecture for better data organization
- Consolidated folder management with automatic creation of workflow structure
- Timestamped file movement to prevent overwrites on subsequent runs
- Smart file location detection (working directory for first runs, organized folders for subsequent runs)
- CSV file archiving and regeneration
- BarTender file generation with reverse order and interleaved format

Database Schema (Two-Table Architecture):
- sample_metadata table: Project and sample information
- individual_plates table: Individual plate data with barcodes
- Database file: project_summary.db

File Organization:
- Main workflow folders: 1_make_barcode_labels/, 2_sort_plates_and_amplify_genomes/, 3_make_library_analyze_fa/, 4_pooling/
- BarTender files → 1_make_barcode_labels/bartender_barcode_labels/
- Processed input files → 1_make_barcode_labels/previously_process_label_input_files/custom_plates/ and /standard_plates/
- Sort plate layouts → 2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/
- WGA results → 2_sort_plates_and_amplify_genomes/B_WGA_results/
- Archived files → archived_files/ (with timestamp suffixes)
- Updated CSV files: sample_metadata.csv and individual_plates.csv

Barcode System:
- Single base barcode per project (5-character alphanumeric)
- Incremental numbering: BASE-1, BASE-2, BASE-3, etc.
- No collision avoidance needed - simple sequential numbering

Safety Features:
- Comprehensive barcode uniqueness validation
- Laboratory-grade error messaging with "FATAL ERROR" prefix
- Automatic file archiving before updates
- Success marker creation for workflow integration
- Consistent error handling with sys.exit() (no exit codes)
"""

import argparse
import pandas as pd
import random
import sys
import shutil
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

# Constants following implementation guide
CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
LETTERS_ONLY = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BARTENDER_HEADER = '%BTW% /AF="\\\\BARTENDER\\shared\\templates\\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'

# Database and file names
DATABASE_NAME = "project_summary.db"
BARTENDER_FILE = "BARTENDER_sort_plate_labels.txt"


def validate_custom_base_barcode(base_barcode):
    """
    Validate that a custom base barcode follows the expected format.
    
    Args:
        base_barcode (str): The custom base barcode to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Validation rules:
    - Must be exactly 5 characters long
    - First character must be a letter (A-Z)
    - All characters must be uppercase letters or digits
    - All characters must be from the allowed CHARSET
    """
    if not base_barcode:
        return False
    
    # Check length
    if len(base_barcode) != 5:
        return False
    
    # Check first character is a letter
    if not base_barcode[0].isalpha():
        return False
    
    # Check all characters are uppercase and from allowed charset
    if base_barcode != base_barcode.upper():
        return False
    
    # Check all characters are in the allowed charset
    for char in base_barcode:
        if char not in CHARSET:
            return False
    
    return True


# ---------------------------------------------------------------------------
# Experiment type selection
# ---------------------------------------------------------------------------

# Valid experiment type constants
EXPERIMENT_TYPE_SPS_CE = "sps_ce"
EXPERIMENT_TYPE_BONCAT = "boncat"
EXPERIMENT_TYPE_OTHER  = "other"


def get_experiment_type():
    """
    Interactively ask the user to select the experiment / input-file type.

    Accepts exactly '1', '2', or '3'.  Any other input terminates the script
    immediately with a FATAL ERROR message (consistent with the rest of the
    script's error-handling convention).

    Returns:
        str: One of EXPERIMENT_TYPE_SPS_CE, EXPERIMENT_TYPE_BONCAT,
             or EXPERIMENT_TYPE_OTHER.

    Raises:
        SystemExit: If the user enters anything other than 1, 2, or 3.
    """
    print("\nSelect input file type:")
    print("  1) Standard SPS-CE")
    print("  2) Standard BONCAT")
    print("  3) Other")
    print("")

    response = input("Enter 1, 2, or 3: ").strip()

    if response == '1':
        print("✅ Experiment type set to: Standard SPS-CE")
        return EXPERIMENT_TYPE_SPS_CE
    elif response == '2':
        print("✅ Experiment type set to: Standard BONCAT")
        return EXPERIMENT_TYPE_BONCAT
    elif response == '3':
        print("✅ Experiment type set to: Other")
        return EXPERIMENT_TYPE_OTHER
    else:
        print(f"FATAL ERROR: Invalid selection '{response}'. Please enter 1, 2, or 3.")
        print("Laboratory automation requires a valid experiment type selection for safety.")
        sys.exit()


# ---------------------------------------------------------------------------
# Sample metadata CSV validation helpers
# ---------------------------------------------------------------------------

def _validate_shared_columns(df, csv_path):
    """
    Apply column-level validation rules that are identical across all three
    experiment types.  Terminates with FATAL ERROR on any violation.

    Shared rules:
    - Required columns present: Proposal, Group_or_abrvSample, Sample_full,
      Number_of_sorted_plates
    - Number_of_sorted_plates must be a positive integer
    - Proposal < 9 characters
    - Group_or_abrvSample < 9 characters, alphanumeric only

    Args:
        df (pd.DataFrame): DataFrame read from the CSV.
        csv_path (Path): Path used only for error messages.
    """
    required_cols = ['Proposal', 'Group_or_abrvSample', 'Sample_full', 'Number_of_sorted_plates']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"FATAL ERROR: Missing required columns in CSV file: {missing}")
        print(f"Required columns: {required_cols}")
        print(f"Found columns: {list(df.columns)}")
        print("Laboratory automation requires exact column names for safety.")
        sys.exit()

    # Number_of_sorted_plates must be a valid integer
    try:
        df['Number_of_sorted_plates'] = df['Number_of_sorted_plates'].astype(int)
    except ValueError as e:
        print(f"FATAL ERROR: Invalid data in 'Number_of_sorted_plates' column: {e}")
        print("All values must be integers for laboratory automation safety.")
        sys.exit()

    # Proposal < 9 characters
    invalid_proposals = df[df['Proposal'].astype(str).str.len() >= 9]['Proposal'].tolist()
    if invalid_proposals:
        print(f"FATAL ERROR: 'Proposal' values must be less than 9 characters.")
        print(f"Invalid values: {invalid_proposals}")
        print("Laboratory automation requires valid proposal identifiers for safety.")
        sys.exit()

    # Group_or_abrvSample < 9 characters
    invalid_groups_len = df[df['Group_or_abrvSample'].astype(str).str.len() >= 9]['Group_or_abrvSample'].tolist()
    if invalid_groups_len:
        print(f"FATAL ERROR: 'Group_or_abrvSample' values must be less than 9 characters.")
        print(f"Invalid values: {invalid_groups_len}")
        print("Laboratory automation requires valid group/sample abbreviations for safety.")
        sys.exit()

    # Group_or_abrvSample alphanumeric only
    invalid_groups_chars = df[~df['Group_or_abrvSample'].astype(str).str.match(r'^[A-Za-z0-9]+$')]['Group_or_abrvSample'].tolist()
    if invalid_groups_chars:
        print(f"FATAL ERROR: 'Group_or_abrvSample' values must contain only letters and numbers (no symbols or spaces).")
        print(f"Invalid values: {invalid_groups_chars}")
        print("Laboratory automation requires alphanumeric-only group identifiers for safety.")
        sys.exit()


def _validate_sps_ce_or_other(df):
    """
    Additional validation for Standard SPS-CE and Other experiment types.

    Rule: every Group_or_abrvSample value must be unique across all rows.
    Duplicate group names would produce colliding plate names and are not
    permitted.

    Args:
        df (pd.DataFrame): DataFrame that has already passed shared validation.

    Raises:
        SystemExit: If any Group_or_abrvSample value appears more than once.
    """
    duplicates = df[df.duplicated(subset=['Group_or_abrvSample'], keep=False)]['Group_or_abrvSample'].unique().tolist()
    if duplicates:
        print(f"FATAL ERROR: Duplicate 'Group_or_abrvSample' values found: {duplicates}")
        print("For Standard SPS-CE and Other experiment types each row must have a")
        print("unique 'Group_or_abrvSample' value to avoid plate name collisions.")
        print("Laboratory automation requires unique sample identifiers for safety.")
        sys.exit()


def _validate_boncat(df):
    """
    Additional validation for Standard BONCAT experiment type.

    Rules:
    1. Every Group_or_abrvSample value must appear in at least 2 rows
       (i.e. at least 2 distinct Sample_full values per group).
    2. All rows sharing the same (Proposal, Group_or_abrvSample) must have
       the same Number_of_sorted_plates value.

    Args:
        df (pd.DataFrame): DataFrame that has already passed shared validation.

    Raises:
        SystemExit: On any BONCAT-specific violation.
    """
    # Rule 1: each group must have ≥ 2 rows
    group_counts = df.groupby('Group_or_abrvSample').size()
    singleton_groups = group_counts[group_counts < 2].index.tolist()
    if singleton_groups:
        print(f"FATAL ERROR: The following 'Group_or_abrvSample' groups have fewer than 2 samples: {singleton_groups}")
        print("For Standard BONCAT each group must contain at least 2 individual samples")
        print("(e.g. BONCAT+ and SYTO+ replicates sorted onto the same plate).")
        print("Laboratory automation requires valid BONCAT group structure for safety.")
        sys.exit()

    # Rule 2: Number_of_sorted_plates must be consistent within each (Proposal, Group) pair
    inconsistent_groups = []
    for (proposal, group), sub_df in df.groupby(['Proposal', 'Group_or_abrvSample']):
        unique_plate_counts = sub_df['Number_of_sorted_plates'].unique()
        if len(unique_plate_counts) > 1:
            inconsistent_groups.append(f"{proposal}_{group} (values: {list(unique_plate_counts)})")
    if inconsistent_groups:
        print(f"FATAL ERROR: Inconsistent 'Number_of_sorted_plates' values within BONCAT groups:")
        for g in inconsistent_groups:
            print(f"  - {g}")
        print("All rows in the same BONCAT group must share the same Number_of_sorted_plates value.")
        print("Laboratory automation requires consistent plate counts per group for safety.")
        sys.exit()


def read_sample_csv(csv_path, experiment_type=EXPERIMENT_TYPE_SPS_CE):
    """
    Read sample metadata CSV and return DataFrame with validation.

    Applies shared column/character validation first, then experiment-type-
    specific structural validation:
      - SPS-CE / Other : Group_or_abrvSample must be unique per row
      - BONCAT         : each group must have ≥2 rows; Number_of_sorted_plates
                         must be consistent within each group

    Args:
        csv_path (Path): Path to the CSV file.
        experiment_type (str): One of EXPERIMENT_TYPE_SPS_CE,
                               EXPERIMENT_TYPE_BONCAT, or EXPERIMENT_TYPE_OTHER.

    Returns:
        pd.DataFrame: Validated sample metadata.

    Raises:
        SystemExit: If required columns are missing, validation fails, or the
                    file cannot be read.
        FileNotFoundError: If the CSV file does not exist.
    """
    try:
        # Read CSV with proper encoding handling (including BOM)
        df = pd.read_csv(csv_path, encoding='utf-8-sig')

        # --- Shared validation (identical for all experiment types) ---
        _validate_shared_columns(df, csv_path)

        # --- Experiment-type-specific validation ---
        if experiment_type == EXPERIMENT_TYPE_BONCAT:
            _validate_boncat(df)
        else:
            # SPS-CE and Other both require unique Group_or_abrvSample per row
            _validate_sps_ce_or_other(df)

        print(f"✅ Read {len(df)} rows from CSV file")
        return df

    except FileNotFoundError:
        print(f"FATAL ERROR: CSV file not found: {csv_path}")
        print("Laboratory automation requires valid input files for safety.")
        raise
    except SystemExit:
        raise
    except Exception as e:
        print(f"FATAL ERROR: Could not read CSV file {csv_path}: {e}")
        print("Laboratory automation requires valid CSV format for safety.")
        sys.exit()


def make_plate_names(sample_df, experiment_type=EXPERIMENT_TYPE_SPS_CE):
    """
    Generate standard plate names from sample data.

    Dispatches to the appropriate generator based on experiment_type:
      - SPS-CE / Other : one set of plates per row (current behaviour)
      - BONCAT         : one set of plates per unique (Proposal, Group) pair

    Args:
        sample_df (pd.DataFrame): Sample metadata DataFrame.
        experiment_type (str): One of the EXPERIMENT_TYPE_* constants.

    Returns:
        pd.DataFrame: DataFrame with plate names and metadata.
    """
    if experiment_type == EXPERIMENT_TYPE_BONCAT:
        return _make_plate_names_boncat(sample_df)
    else:
        return _make_plate_names_standard(sample_df)


def _make_plate_names_standard(sample_df):
    """
    Generate plate names for Standard SPS-CE and Other experiment types.

    One row in the metadata CSV = one sample = N individual plates.

    Args:
        sample_df (pd.DataFrame): Sample metadata DataFrame.

    Returns:
        pd.DataFrame: DataFrame with plate names and metadata.
    """
    plates = []

    for _, row in sample_df.iterrows():
        proposal = row['Proposal']
        sample = row['Group_or_abrvSample']
        num_plates = int(row['Number_of_sorted_plates'])

        for i in range(1, num_plates + 1):
            plates.append({
                'plate_name': f"{proposal}_{sample}.{i}",
                'project': proposal,
                'sample': sample,
                'plate_number': i,
                'is_custom': False
            })

    result_df = pd.DataFrame(plates)
    print(f"✅ Generated {len(result_df)} standard plates")
    return result_df


def _make_plate_names_boncat(sample_df):
    """
    Generate plate names for Standard BONCAT experiment type.

    In BONCAT mode, Group_or_abrvSample represents a *group* of individual
    samples that are all sorted onto the same physical plate.  Plate labels
    are therefore generated once per unique (Proposal, Group_or_abrvSample)
    combination, using the Number_of_sorted_plates value shared by that group.

    Example: if three rows share Group_or_abrvSample='WCBP1PR' and each has
    Number_of_sorted_plates=2, this produces two plate labels:
        509735_WCBP1PR.1  and  509735_WCBP1PR.2

    Args:
        sample_df (pd.DataFrame): Sample metadata DataFrame (already validated).

    Returns:
        pd.DataFrame: DataFrame with plate names and metadata.
    """
    plates = []

    # Deduplicate: take the first row for each (Proposal, Group) pair to get
    # the plate count (validation already confirmed consistency within groups).
    group_df = sample_df.drop_duplicates(subset=['Proposal', 'Group_or_abrvSample'])

    for _, row in group_df.iterrows():
        proposal = row['Proposal']
        group = row['Group_or_abrvSample']
        num_plates = int(row['Number_of_sorted_plates'])

        for i in range(1, num_plates + 1):
            plates.append({
                'plate_name': f"{proposal}_{group}.{i}",
                'project': proposal,
                'sample': group,
                'plate_number': i,
                'is_custom': False
            })

    result_df = pd.DataFrame(plates)
    print(f"✅ Generated {len(result_df)} BONCAT group plates "
          f"(from {len(sample_df)} individual sample rows across "
          f"{len(group_df)} groups)")
    return result_df


def generate_simple_barcodes(plates_df, existing_individual_plates_df=None, custom_base_barcode=None):
    """
    Generate simplified incremental barcodes for all plates.
    
    Args:
        plates_df (pd.DataFrame): DataFrame of plates needing barcodes
        existing_individual_plates_df (pd.DataFrame, optional): Existing individual plates to continue numbering
        custom_base_barcode (str, optional): Custom base barcode to use instead of generating random one
        
    Returns:
        pd.DataFrame: DataFrame with generated barcodes
        
    Raises:
        SystemExit: If barcode generation fails
    """
    try:
        # Determine base barcode and starting number
        start_number = 1
        base_barcode = None
        
        if existing_individual_plates_df is not None and len(existing_individual_plates_df) > 0:
            # Extract existing base barcode from first existing barcode
            first_barcode = existing_individual_plates_df['barcode'].iloc[0]
            if '-' in str(first_barcode):
                base_barcode = str(first_barcode).split('-')[0]
                # Reuse existing base barcode
            
            # Find the highest existing barcode number to continue from
            existing_numbers = []
            for barcode in existing_individual_plates_df['barcode']:
                if '-' in str(barcode):
                    try:
                        number = int(str(barcode).split('-')[-1])
                        existing_numbers.append(number)
                    except ValueError:
                        continue
            
            if existing_numbers:
                start_number = max(existing_numbers) + 1
                # Continue numbering from existing plates
        
        # Generate new base barcode only if no existing plates
        if base_barcode is None:
            if custom_base_barcode:
                # Use provided custom base barcode
                if not validate_custom_base_barcode(custom_base_barcode):
                    print(f"FATAL ERROR: Invalid custom base barcode '{custom_base_barcode}'")
                    print("Custom base barcode must be exactly 5 characters:")
                    print("- First character must be a letter (A-Z)")
                    print("- All characters must be uppercase letters or digits")
                    print("- Example: REX12, ABCD1, TEST9")
                    print("Laboratory automation requires valid barcode format for safety.")
                    sys.exit()
                base_barcode = custom_base_barcode.upper()
                print(f"Using custom base barcode: '{base_barcode}'")
            else:
                # Generate random base barcode
                # First character must be a letter, remaining 4 can be letters or numbers
                first_char = random.choice(LETTERS_ONLY)
                remaining_chars = ''.join(random.choices(CHARSET, k=4))
                base_barcode = first_char + remaining_chars
                print(f"Generated base barcode: '{base_barcode}'")
        
        # Assign incremental barcodes to all plates
        for i, idx in enumerate(plates_df.index):
            barcode_number = start_number + i
            full_barcode = f"{base_barcode}-{barcode_number}"
            
            plates_df.at[idx, 'barcode'] = full_barcode
            plates_df.at[idx, 'created_timestamp'] = datetime.now().isoformat()
        
        print(f"✅ Generated {len(plates_df)} barcodes: {base_barcode}-{start_number} to {base_barcode}-{start_number + len(plates_df) - 1}")
        
        return plates_df
        
    except Exception as e:
        print(f"FATAL ERROR: Could not generate barcodes: {e}")
        print("Laboratory automation requires reliable barcode generation for safety.")
        sys.exit()


def generate_barcodes(plates_df, existing_df=None, custom_base_barcode=None):
    """
    Wrapper function for backward compatibility.
    Calls the new simplified barcode generation system.
    """
    return generate_simple_barcodes(plates_df, existing_df, custom_base_barcode)


def validate_barcode_uniqueness(df):
    """
    Validate that all barcodes in DataFrame are unique.
    
    Args:
        df (pd.DataFrame): DataFrame with barcode column
        
    Returns:
        bool: True if all barcodes are unique, False otherwise
    """
    if 'barcode' not in df.columns:
        print("WARNING: No 'barcode' column found for validation")
        return True
    
    barcodes = df['barcode'].tolist()
    unique_barcodes = set(barcodes)
    
    is_unique = len(barcodes) == len(unique_barcodes)
    
    if not is_unique:
        duplicates = [barcode for barcode in unique_barcodes if barcodes.count(barcode) > 1]
        print(f"Duplicate barcodes found: {duplicates}")
    
    return is_unique


def save_to_two_table_database(sample_metadata_df, individual_plates_df, db_path):
    """
    Save DataFrames to two-table SQLite database using SQLAlchemy.
    
    Args:
        sample_metadata_df (pd.DataFrame): Sample metadata DataFrame
        individual_plates_df (pd.DataFrame): Individual plates DataFrame
        db_path (Path): Path to database file
        
    Raises:
        SystemExit: If database operation fails
    """
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Save both tables with replace to handle updates
        sample_metadata_df.to_sql('sample_metadata', engine, if_exists='replace', index=False)
        individual_plates_df.to_sql('individual_plates', engine, if_exists='replace', index=False)
        
        # Properly dispose of engine
        engine.dispose()
        
        print(f"✅ Saved to database: {len(sample_metadata_df)} samples, {len(individual_plates_df)} plates")
        
    except Exception as e:
        print(f"FATAL ERROR: Could not save to database {db_path}: {e}")
        print("Laboratory automation requires reliable data storage for safety.")
        sys.exit()


def save_to_database_smart(sample_metadata_df, new_plates_df, db_path, is_first_run, existing_sample_df=None):
    """
    Smart database save that only updates tables that actually need updating.
    Preserves all unknown tables by only touching specific tables.
    
    Args:
        sample_metadata_df (pd.DataFrame): Sample metadata DataFrame
        new_plates_df (pd.DataFrame): NEW plates DataFrame (not all plates)
        db_path (Path): Path to database file
        is_first_run (bool): True for first runs, False for subsequent runs
        existing_sample_df (pd.DataFrame, optional): Existing sample metadata for comparison
        
    Raises:
        SystemExit: If database operation fails
    """
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        
        if is_first_run:
            # First run: create both tables fresh
            sample_metadata_df.to_sql('sample_metadata', engine, if_exists='replace', index=False)
            new_plates_df.to_sql('individual_plates', engine, if_exists='replace', index=False)
            print(f"✅ Created database: {len(sample_metadata_df)} samples, {len(new_plates_df)} plates")
        else:
            # Subsequent run: only update what actually changes
            sample_updated = False
            
            # Check if sample metadata actually changed
            if existing_sample_df is not None and sample_metadata_df.equals(existing_sample_df):
                # Sample metadata unchanged - skip update
                pass
            else:
                # Sample metadata changed - update it
                sample_metadata_df.to_sql('sample_metadata', engine, if_exists='replace', index=False)
                sample_updated = True
            
            # Always append new plates (this is the main purpose of subsequent runs)
            if not new_plates_df.empty:
                new_plates_df.to_sql('individual_plates', engine, if_exists='append', index=False)
            
            # Summary
            print(f"\n✅ Database updated successfully")
        
        # Properly dispose of engine
        engine.dispose()
        
    except Exception as e:
        print(f"FATAL ERROR: Could not save to database {db_path}: {e}")
        print("Laboratory automation requires reliable data storage for safety.")
        sys.exit()


def save_to_database(sample_metadata_df, individual_plates_df, db_path):
    """
    Save DataFrames to two-table SQLite database using SQLAlchemy.
    
    Args:
        sample_metadata_df (pd.DataFrame): Sample metadata DataFrame
        individual_plates_df (pd.DataFrame): Individual plates DataFrame
        db_path (Path): Path to database file
        
    Raises:
        SystemExit: If database operation fails
    """
    return save_to_two_table_database(sample_metadata_df, individual_plates_df, db_path)


def read_from_two_table_database(db_path):
    """
    Read DataFrames from two-table SQLite database using SQLAlchemy.
    
    Args:
        db_path (Path): Path to database file
        
    Returns:
        tuple: (sample_metadata_df, individual_plates_df) or (None, None) if file doesn't exist
        
    Raises:
        SystemExit: If database read fails unexpectedly
    """
    if not Path(db_path).exists():
        return None, None
    
    try:
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Check if tables exist
        with engine.connect() as conn:
            # Check for new two-table format
            try:
                sample_metadata_df = pd.read_sql('SELECT * FROM sample_metadata', conn)
                individual_plates_df = pd.read_sql('SELECT * FROM individual_plates', conn)
                engine.dispose()
                
                # Database read successfully
                return sample_metadata_df, individual_plates_df
                
            except Exception:
                # Tables don't exist - might be old single-table format
                engine.dispose()
                return None, None
        
    except Exception as e:
        print(f"FATAL ERROR: Could not read from database {db_path}: {e}")
        print("Laboratory automation requires reliable data access for safety.")
        sys.exit()


def read_from_database(db_path):
    """
    Read DataFrames from two-table SQLite database using SQLAlchemy.
    
    Args:
        db_path (Path): Path to database file
        
    Returns:
        tuple: (sample_metadata_df, individual_plates_df) or (None, None) if file doesn't exist
        
    Raises:
        SystemExit: If database read fails unexpectedly
    """
    return read_from_two_table_database(db_path)


def make_bartender_file(df, output_path):
    """
    Generate BarTender label file with simplified barcode system.
    
    Args:
        df (pd.DataFrame): DataFrame with barcode data (must have 'barcode' and 'plate_name' columns)
        output_path (Path): Path for output file
        
    Raises:
        SystemExit: If file creation fails
    """
    try:
        with open(output_path, 'w', newline='') as f:
            # Write header
            f.write(BARTENDER_HEADER)
            
            # Sort by barcode number in reverse order (highest first)
            # Extract number from barcode (e.g., "W91ZL-15" -> 15)
            df_sorted = df.copy()
            df_sorted['barcode_num'] = df_sorted['barcode'].str.split('-').str[1].astype(int)
            df_sorted = df_sorted.sort_values('barcode_num', ascending=False)
            
            # Sort plate labels in reverse order with separators
            for i, (_, row) in enumerate(df_sorted.iterrows()):
                plate_name = row['plate_name']

                # Standard label (barcode with quoted plate name as label
                f.write(f'{plate_name},"{plate_name}"\r\n')
                
                # # Add blank separator line between plate sets (except after last plate)
                # if i < len(df_sorted) - 1:
                #     f.write(',\r\n')
            
            # Add proper trailing empty lines for BarTender compatibility
            f.write('\r\n')
        
        # BarTender file created silently
        
    except Exception as e:
        print(f"FATAL ERROR: Could not create BarTender file {output_path}: {e}")
        print("Laboratory automation requires valid label files for safety.")
        sys.exit()


def detect_sample_metadata_csv():
    """
    Detect and validate sample metadata CSV file in working directory.
    
    Returns:
        Path: Valid sample metadata CSV file path
        
    Raises:
        SystemExit: If no valid sample metadata CSV found
    """
    # Complete list of expected headers from sample_metadtata.csv format
    expected_headers = [
        'Proposal', 'Group_or_abrvSample', 'Sample_full', 'Collection Year',
        'Collection Month', 'Collection Day', 'Sample Isolated From', 'Latitude', 'Longitude',
        'Depth (m)', 'Elevation (m)', 'Country', 'Number_of_sorted_plates'
    ]
    
    # Required subset for processing
    required_headers = ['Proposal', 'Group_or_abrvSample', 'Sample_full', 'Number_of_sorted_plates']
    
    # Look for sample_metadtata.csv specifically first
    sample_metadata_file = Path('sample_metadtata.csv')
    if sample_metadata_file.exists():
        try:
            df = pd.read_csv(sample_metadata_file, encoding='utf-8-sig')
            
            # Check for all expected headers
            missing_expected = [col for col in expected_headers if col not in df.columns]
            if missing_expected:
                print(f"⚠️  Sample metadata CSV missing some expected columns: {missing_expected}")
            
            # Check for required headers
            missing_required = [col for col in required_headers if col not in df.columns]
            if missing_required:
                print(f"FATAL ERROR: Sample metadata CSV missing required columns: {missing_required}")
                print(f"Required columns: {required_headers}")
                print("Laboratory automation requires exact column names for safety.")
                sys.exit()
            
            print(f"✅ Found valid sample metadata CSV: {sample_metadata_file}")
            return sample_metadata_file
            
        except Exception as e:
            print(f"FATAL ERROR: Could not read sample metadata CSV {sample_metadata_file}: {e}")
            print("Laboratory automation requires valid CSV format for safety.")
            sys.exit()
    
    # If sample_metadtata.csv doesn't exist, search for other CSV files
    csv_files = [f for f in Path('.').glob('*.csv') if f.name != 'sample_metadtata.csv']
    
    if not csv_files:
        print("FATAL ERROR: No sample metadata CSV file found in working directory")
        print("Expected: 'sample_metadtata.csv' or other CSV with required headers")
        print(f"Required columns: {required_headers}")
        print("Laboratory automation requires valid input files for safety.")
        sys.exit()
    
    # Check all CSV files for validity first
    valid_csv_files = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            # Check for required headers
            missing_required = [col for col in required_headers if col not in df.columns]
            if not missing_required:
                valid_csv_files.append(csv_file)
                
        except Exception as e:
            print(f"⚠️  Skipping invalid CSV file {csv_file}: {e}")
            continue
    
    # Check if we found multiple valid CSV files
    if len(valid_csv_files) > 1:
        print("FATAL ERROR: Multiple valid sample metadata CSV files found in working directory")
        print("Found valid CSV files:")
        for csv_file in valid_csv_files:
            print(f"  - {csv_file}")
        print("Laboratory automation requires exactly one sample metadata CSV file for safety.")
        print("Please ensure only one valid CSV file exists in the working directory.")
        sys.exit()
    
    # Check if we found exactly one valid CSV file
    if len(valid_csv_files) == 1:
        print(f"✅ Found valid sample metadata CSV: {valid_csv_files[0]}")
        return valid_csv_files[0]
    
    # No valid CSV found
    print("FATAL ERROR: No valid sample metadata CSV file found in working directory")
    print(f"Required columns: {required_headers}")
    print("Laboratory automation requires valid input files for safety.")
    sys.exit()


def get_csv_file():
    """
    Get CSV file path using automatic detection.
    """
    return detect_sample_metadata_csv()


def read_custom_plates_file(is_first_run=True):
    """
    Read custom plate names from 'custom_plate_names.txt' file.
    Location depends on whether this is a first run or subsequent run.
    
    Args:
        is_first_run (bool): True for first runs (look in working directory),
                            False for subsequent runs (look in 1_make_barcode_labels folder)
    
    Returns:
        list: List of validated custom plate names
        
    Raises:
        SystemExit: If file format is invalid or multiple custom plate files found
    """
    # Determine where to look for input files based on run type
    if is_first_run:
        # First run: look in working directory
        search_dir = Path('.')
        custom_file = Path('custom_plate_names.txt')
        location_desc = "working directory"
    else:
        # Subsequent run: look in 1_make_barcode_labels folder
        search_dir = Path('1_make_barcode_labels')
        custom_file = Path('1_make_barcode_labels/custom_plate_names.txt')
        location_desc = "1_make_barcode_labels folder"
    
    # Check for multiple custom plate files in search directory
    custom_files = list(search_dir.glob('*custom*plate*names*.txt'))
    custom_files.extend(search_dir.glob('custom_plate_names.txt'))
    custom_files.extend(search_dir.glob('*custom*plates*.txt'))
    
    # Remove duplicates and filter to actual files
    custom_files = list(set([f for f in custom_files if f.is_file()]))
    
    if len(custom_files) > 1:
        print(f"FATAL ERROR: Multiple custom plate files found in {location_desc}")
        print("Found custom plate files:")
        for custom_file_found in custom_files:
            print(f"  - {custom_file_found}")
        print("Laboratory automation requires exactly one custom plate file for safety.")
        print(f"Please ensure only 'custom_plate_names.txt' exists in the {location_desc}.")
        sys.exit()
    
    if not custom_file.exists():
        print(f"FATAL ERROR: Custom plates requested but 'custom_plate_names.txt' file not found in {location_desc}")
        print("")
        print("To fix this error:")
        if is_first_run:
            print("1. Create a file named 'custom_plate_names.txt' in the working directory")
        else:
            print("1. Create a file named 'custom_plate_names.txt' in the 1_make_barcode_labels folder")
        print("2. Add one plate name per line (each name must be < 20 characters)")
        print("3. Example file content:")
        print("   Rex_badass_custom.1")
        print("   MA_test_44.1")
        print("   Custom_Plate_Name")
        print("")
        print("Laboratory automation requires valid input files for safety.")
        sys.exit()
    
    try:
        with open(custom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        plates = []
        for line_num, line in enumerate(lines, 1):
            name = line.strip()
            if not name:  # Skip empty lines
                continue
                
            # Validate plate name length
            if len(name) >= 20:
                print(f"FATAL ERROR: Custom plate name too long (>= 20 chars) on line {line_num}: {name}")
                print("Laboratory automation requires valid plate names for safety.")
                sys.exit()
            
            plates.append(name)
        
        if plates:
            print(f"✅ Read {len(plates)} custom plate names from {custom_file}")
        
        return plates
        
    except Exception as e:
        print(f"FATAL ERROR: Could not read custom plates file {custom_file}: {e}")
        print("Laboratory automation requires valid input files for safety.")
        sys.exit()


def read_additional_standard_plates_file(is_first_run=True):
    """
    Read additional standard plates from 'additional_standard_plates.txt'.
    Location depends on whether this is a first run or subsequent run.
    
    Args:
        is_first_run (bool): True for first runs (look in working directory),
                            False for subsequent runs (look in 1_make_barcode_labels folder)
    
    Returns:
        dict: Mapping of sample_id to additional plate count
        
    Raises:
        SystemExit: If file format is invalid or multiple additional plate files found
    """
    # Determine where to look for input files based on run type
    if is_first_run:
        # First run: look in working directory
        search_dir = Path('.')
        additional_file = Path('additional_standard_plates.txt')
        location_desc = "working directory"
    else:
        # Subsequent run: look in 1_make_barcode_labels folder
        search_dir = Path('1_make_barcode_labels')
        additional_file = Path('1_make_barcode_labels/additional_standard_plates.txt')
        location_desc = "1_make_barcode_labels folder"
    
    # Check for multiple additional plate files in search directory
    additional_files = list(search_dir.glob('*additional*standard*plates*.txt'))
    additional_files.extend(search_dir.glob('additional_standard_plates.txt'))
    additional_files.extend(search_dir.glob('*additional*plates*.txt'))
    
    # Remove duplicates and filter to actual files
    additional_files = list(set([f for f in additional_files if f.is_file()]))
    
    if len(additional_files) > 1:
        print(f"FATAL ERROR: Multiple additional standard plate files found in {location_desc}")
        print("Found additional plate files:")
        for additional_file_found in additional_files:
            print(f"  - {additional_file_found}")
        print("Laboratory automation requires exactly one additional plate file for safety.")
        print(f"Please ensure only 'additional_standard_plates.txt' exists in the {location_desc}.")
        sys.exit()
    
    if not additional_file.exists():
        print(f"FATAL ERROR: Additional standard plates requested but 'additional_standard_plates.txt' file not found in {location_desc}")
        print("")
        print("To fix this error:")
        if is_first_run:
            print("1. Create a file named 'additional_standard_plates.txt' in the working directory")
        else:
            print("1. Create a file named 'additional_standard_plates.txt' in the 1_make_barcode_labels folder")
        print("2. Add one entry per line in format: PROJECT_SAMPLE:COUNT")
        print("3. Example file content:")
        print("   BP9735_SitukAM:2")
        print("   BP9735_WCBP1PR:1")
        print("4. This means add 2 more plates to BP9735_SitukAM and 1 more to BP9735_WCBP1PR")
        print("")
        print("Laboratory automation requires valid input files for safety.")
        sys.exit()
    
    try:
        with open(additional_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        additional_plates = {}
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            # Parse format: "BP9735_SitukAM:2"
            if ':' not in line:
                print(f"FATAL ERROR: Invalid format on line {line_num}: {line}")
                print("Expected format: 'PROJECT_SAMPLE:COUNT' (e.g., 'BP9735_SitukAM:2')")
                print("Laboratory automation requires valid file formats for safety.")
                sys.exit()
            
            try:
                sample_id, count_str = line.split(':', 1)
                count = int(count_str)
                
                if count <= 0:
                    print(f"FATAL ERROR: Invalid plate count on line {line_num}: {count}")
                    print("Plate count must be positive integer.")
                    print("Laboratory automation requires valid data for safety.")
                    sys.exit()
                
                additional_plates[sample_id.strip()] = count
                
            except ValueError as e:
                print(f"FATAL ERROR: Invalid format on line {line_num}: {line}")
                print(f"Error: {e}")
                print("Laboratory automation requires valid file formats for safety.")
                sys.exit()
        
        if additional_plates:
            print(f"✅ Read additional plates for {len(additional_plates)} samples from {additional_file}")
        
        return additional_plates
        
    except Exception as e:
        print(f"FATAL ERROR: Could not read additional plates file {additional_file}: {e}")
        print("Laboratory automation requires valid input files for safety.")
        sys.exit()


def get_additional_standard_plates(is_first_run=True):
    """
    Interactive function to ask user if they want additional standard plates and read from file.
    
    Additional standard plates file format (additional_standard_plates.txt):
    - One entry per line
    - Format: PROJECT_SAMPLE:COUNT
    - Example format:
        BP9735_SitukAM:2
        BP9735_WCBP1PR:1
    - This means add 2 more plates to BP9735_SitukAM and 1 more plate to BP9735_WCBP1PR
    
    Args:
        is_first_run (bool): True for first runs, False for subsequent runs
    
    Returns:
        dict: Mapping of sample_id to additional plate count, or empty dict if user declines
    """
    # Ask user interactively
    while True:
        response = input("Add additional standard plates to existing samples? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            # User wants additional standard plates - look for file
            print("Looking for 'additional_standard_plates.txt' file...")
            return read_additional_standard_plates_file(is_first_run)
        elif response in ['n', 'no']:
            # User doesn't want additional standard plates
            return {}
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def get_custom_plates(is_first_run=True):
    """
    Interactive function to ask user if they want custom plates and read from file.
    
    Custom plate names file format (custom_plate_names.txt):
    - One plate name per line
    - Each name must be < 20 characters
    - Empty lines are ignored
    - Example format:
        Rex_badass_custom.1
        MA_test_44.1
        Custom_Plate_Name
    
    Args:
        is_first_run (bool): True for first runs, False for subsequent runs
    
    Returns:
        list: List of custom plate names, or empty list if user declines
    """
    # Ask user interactively
    while True:
        response = input("Add custom plates? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            # User wants custom plates - look for file
            print("Looking for 'custom_plate_names.txt' file...")
            return read_custom_plates_file(is_first_run)
        elif response in ['n', 'no']:
            # User doesn't want custom plates
            return []
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def create_project_folder_structure():
    """
    Create the standardized project folder structure.
    
    Creates the following folders if they don't exist:
    - 1_make_barcode_labels/
    - 2_sort_plates_and_amplify_genomes/
    - 3_make_library_analyze_fa/
    - 4_pooling/
    - archived_files/
    - 1_make_barcode_labels/bartender_barcode_labels/
    - 1_make_barcode_labels/previously_process_label_input_files/
    - 1_make_barcode_labels/previously_process_label_input_files/custom_plates/
    - 1_make_barcode_labels/previously_process_label_input_files/standard_plates/
    - 2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/
    - 2_sort_plates_and_amplify_genomes/B_WGA_results/
    
    Returns:
        dict: Dictionary with folder paths for easy access
        
    Raises:
        SystemExit: If folder creation fails
    """
    try:
        # Main workflow folders
        folders = {
            'make_barcode_labels': Path("1_make_barcode_labels"),
            'sort_plates_and_amplify': Path("2_sort_plates_and_amplify_genomes"),
            'make_library_analyze_fa': Path("3_make_library_analyze_fa"),
            'pooling': Path("4_pooling"),
            'archived_files': Path("archived_files"),
        }
        
        # Track which folders were actually created
        created_folders = []
        
        # Create main folders
        for folder_name, folder_path in folders.items():
            if not folder_path.exists():
                created_folders.append(str(folder_path))
            folder_path.mkdir(exist_ok=True)
        
        # Create subfolder structure for barcode labels
        bartender_dir = folders['make_barcode_labels'] / "bartender_barcode_labels"
        if not bartender_dir.exists():
            created_folders.append(str(bartender_dir))
        bartender_dir.mkdir(exist_ok=True)
        
        label_input_dir = folders['make_barcode_labels'] / "previously_process_label_input_files"
        if not label_input_dir.exists():
            created_folders.append(str(label_input_dir))
        label_input_dir.mkdir(exist_ok=True)
        
        custom_plates_dir = label_input_dir / "custom_plates"
        standard_plates_dir = label_input_dir / "standard_plates"
        if not custom_plates_dir.exists():
            created_folders.append(str(custom_plates_dir))
        if not standard_plates_dir.exists():
            created_folders.append(str(standard_plates_dir))
        custom_plates_dir.mkdir(exist_ok=True)
        standard_plates_dir.mkdir(exist_ok=True)
        
        # Create subfolder structure for sort plates and amplify genomes
        sort_plate_layouts_dir = folders['sort_plates_and_amplify'] / "A_sort_plate_layouts"
        wga_results_dir = folders['sort_plates_and_amplify'] / "B_WGA_results"
        if not sort_plate_layouts_dir.exists():
            created_folders.append(str(sort_plate_layouts_dir))
        if not wga_results_dir.exists():
            created_folders.append(str(wga_results_dir))
        sort_plate_layouts_dir.mkdir(exist_ok=True)
        wga_results_dir.mkdir(exist_ok=True)

        # Add subfolder paths to the dictionary
        folders['bartender_labels'] = bartender_dir
        folders['label_input_files'] = label_input_dir
        folders['custom_plates'] = custom_plates_dir
        folders['standard_plates'] = standard_plates_dir
        folders['sort_plate_layouts'] = sort_plate_layouts_dir
        folders['wga_results'] = wga_results_dir
        
        # Only print if folders were actually created
        if created_folders:
            print(f"✅ Created {len(created_folders)} new project folders")
        
        return folders
        
    except Exception as e:
        print(f"FATAL ERROR: Could not create project folder structure: {e}")
        print("Laboratory automation requires proper folder organization for safety.")
        sys.exit()


def create_success_marker():
    """
    Create success marker file for workflow manager integration.
    
    Raises:
        SystemExit: If marker creation fails
    """
    try:
        script_name = Path(__file__).stem
        status_dir = Path(".workflow_status")
        status_dir.mkdir(exist_ok=True)
        success_file = status_dir / f"{script_name}.success"
        
        with open(success_file, "w") as f:
            f.write(f"SUCCESS: {script_name} completed at {datetime.now()}\n")
        
        print(f"✅ Success marker created: {success_file}")
        
    except Exception as e:
        print(f"FATAL ERROR: Could not create success marker: {e}")
        print("Laboratory automation requires workflow integration for safety.")
        sys.exit()


def archive_database_file(db_path, folders):
    """
    Archive database file with timestamp as suffix by copying (not moving).
    This preserves the original database for in-place updates.
    
    Args:
        db_path (Path): Path to database file to archive
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
    """
    if not Path(db_path).exists():
        return
    
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    archive_dir = folders['archived_files']
    
    # Create archive name with timestamp as suffix
    # sample_metadtata.db → sample_metadtata_2026_02_24-Time14-30-25.db
    db_path = Path(db_path)
    stem = db_path.stem  # "sample_metadtata"
    suffix = db_path.suffix  # ".db"
    archive_name = f"{stem}_{timestamp}{suffix}"
    archive_path = archive_dir / archive_name
    
    # Copy instead of move to preserve original for in-place updates
    shutil.copy2(str(db_path), str(archive_path))
    # Database archived silently


def manage_bartender_file(bartender_file_path, folders):
    """
    Move BarTender file to organized folder structure.
    
    Args:
        bartender_file_path (Path): Path to BarTender file to organize
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
    """
    bartender_file_path = Path(bartender_file_path)
    if not bartender_file_path.exists():
        return
    
    # Use the dedicated bartender labels folder
    bartender_dir = folders['bartender_labels']
    
    # Move file to bartender folder
    destination = bartender_dir / bartender_file_path.name
    shutil.move(str(bartender_file_path), str(destination))
    # BarTender file organized


def manage_input_files(folders, is_first_run=True, custom_plates_processed=False, additional_plates_processed=False):
    """
    Move processed input files to organized folder structure with timestamps.
    Uses the new consolidated folder structure and adds timestamps to prevent overwrites.
    Only moves files that were actually processed during this run.
    
    Args:
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
        is_first_run (bool): True for first runs (look in working directory),
                            False for subsequent runs (look in 1_make_barcode_labels folder)
        custom_plates_processed (bool): True if custom plates were processed this run
        additional_plates_processed (bool): True if additional standard plates were processed this run
    """
    moved_files = []
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    
    # Determine where to look for input files based on run type
    if is_first_run:
        # First run: look in working directory
        search_dir = Path('.')
    else:
        # Subsequent run: look in 1_make_barcode_labels folder
        search_dir = Path('1_make_barcode_labels')
    
    # Move custom plate files with timestamp (only if they were processed)
    if custom_plates_processed:
        custom_files = list(search_dir.glob('custom_plate_names.txt')) + list(search_dir.glob('custom_sort_plate_names.txt'))
        for custom_file in custom_files:
            if custom_file.exists():
                # Add timestamp to filename: custom_plate_names.txt -> custom_plate_names_2026_02_26-Time14-30-25.txt
                stem = custom_file.stem
                suffix = custom_file.suffix
                timestamped_name = f"{stem}_{timestamp}{suffix}"
                destination = folders['custom_plates'] / timestamped_name
                shutil.move(str(custom_file), str(destination))
                moved_files.append(str(destination))
                # File moved silently
    
    # Move additional standard plate files with timestamp (only if they were processed)
    if additional_plates_processed:
        standard_files = list(search_dir.glob('additional_standard_plates.txt')) + list(search_dir.glob('additional_sort_plates.txt'))
        for standard_file in standard_files:
            if standard_file.exists():
                # Add timestamp to filename: additional_standard_plates.txt -> additional_standard_plates_2026_02_26-Time14-30-25.txt
                stem = standard_file.stem
                suffix = standard_file.suffix
                timestamped_name = f"{stem}_{timestamp}{suffix}"
                destination = folders['standard_plates'] / timestamped_name
                shutil.move(str(standard_file), str(destination))
                moved_files.append(str(destination))
                # File moved silently
    
    # Input files organized silently
    
    return moved_files


def archive_csv_file(csv_file_path, folders):
    """
    Archive CSV file with timestamp as suffix.
    
    Args:
        csv_file_path (Path): Path to CSV file to archive
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
    """
    csv_file_path = Path(csv_file_path)
    if not csv_file_path.exists():
        return
    
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    archive_dir = folders['archived_files']
    
    # Create archive name with timestamp as suffix
    # sample_metadtata.csv → sample_metadtata_2026_02_24-Time14-30-25.csv
    stem = csv_file_path.stem  # "sample_metadtata"
    suffix = csv_file_path.suffix  # ".csv"
    archive_name = f"{stem}_{timestamp}{suffix}"
    archive_path = archive_dir / archive_name
    
    shutil.move(str(csv_file_path), str(archive_path))
    # Archived CSV file


def create_updated_csv_files(sample_metadata_df, individual_plates_df):
    """
    Create updated CSV files from current DataFrames.
    Uses ALL available columns from the DataFrames.
    
    Args:
        sample_metadata_df (pd.DataFrame): Sample metadata DataFrame
        individual_plates_df (pd.DataFrame): Individual plates DataFrame
    """
    # Create new sample_metadata.csv with all columns
    sample_metadata_df.to_csv('sample_metadata.csv', index=False)
    # Create new individual_plates.csv with ALL columns to ensure any new columns added over time are included
    individual_plates_df.to_csv('individual_plates.csv', index=False)
    # CSV files updated with all available columns


def manage_csv_files(sample_metadata_df, individual_plates_df, folders):
    """
    Archive existing CSV files and create new updated versions.
    
    Args:
        sample_metadata_df (pd.DataFrame): Sample metadata DataFrame
        individual_plates_df (pd.DataFrame): Individual plates DataFrame
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
    """
    # Archive existing CSV files if they exist
    if Path('sample_metadata.csv').exists():
        archive_csv_file('sample_metadata.csv', folders)
    
    if Path('individual_plates.csv').exists():
        archive_csv_file('individual_plates.csv', folders)
    
    # Create new updated CSV files
    create_updated_csv_files(sample_metadata_df, individual_plates_df)


def archive_existing_files(file_list, folders):
    """
    Archive existing files with timestamp.
    
    Args:
        file_list (list): List of Path objects to archive
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
    """
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    archive_dir = folders['archived_files']
    
    archived_count = 0
    for file_path in file_list:
        if file_path.exists():
            archive_name = f"{timestamp}_{file_path.name}"
            archive_path = archive_dir / archive_name
            shutil.move(str(file_path), str(archive_path))
            print(f"📁 Archived: {file_path} → {archive_path}")
            archived_count += 1
    
    if archived_count > 0:
        print(f"✅ Archived {archived_count} existing files")


def print_header():
    """Print the script header."""
    print("=" * 60)
    print("Laboratory Barcode Label Generation")
    # print("Following SPS Laboratory Safety Standards")
    # print("=" * 60)


def process_first_run(experiment_type, pre_validated_sample_df=None, pre_validated_csv_file=None):
    """
    Handle first run: plate generation and custom plates.

    CSV detection and validation are performed in main() *before* folder
    creation so that invalid input fails fast without leaving empty project
    folders on disk.  When main() passes the already-validated DataFrame via
    pre_validated_sample_df, this function skips re-detection and
    re-validation entirely.

    Args:
        experiment_type (str): One of the EXPERIMENT_TYPE_* constants selected
                               by the user at the start of the session.
        pre_validated_sample_df (pd.DataFrame, optional): Already-validated
            sample metadata DataFrame from main().  When provided, CSV
            detection and read_sample_csv() are skipped.
        pre_validated_csv_file (Path, optional): Path used only for logging
            when pre_validated_sample_df is supplied.

    Returns:
        tuple: (sample_df, plates_df, custom_plates_processed,
                additional_plates_processed) — sample metadata DataFrame,
                plates DataFrame, and processing flags.
    """
    # Use pre-validated data from main() if available; otherwise fall back to
    # detecting and reading the CSV here (e.g. if called standalone in tests).
    if pre_validated_sample_df is not None:
        sample_df = pre_validated_sample_df
    else:
        print("\n🔬 FIRST RUN DETECTED")
        print("Processing sample metadata CSV file...")
        csv_file = detect_sample_metadata_csv()
        sample_df = read_sample_csv(csv_file, experiment_type)

    # Stamp the experiment type onto the metadata DataFrame so it is
    # persisted in the database and available to downstream scripts.
    sample_df['experiment_type'] = experiment_type

    plates_df = make_plate_names(sample_df, experiment_type)

    # Track what was processed
    custom_plates_processed = False
    additional_plates_processed = False  # Never processed on first run

    # Add custom plates if requested (first run)
    custom_plates = get_custom_plates(is_first_run=True)
    if custom_plates:
        custom_df = pd.DataFrame([
            {'plate_name': name, 'project': 'CUSTOM', 'sample': 'CUSTOM',
             'plate_number': 1, 'is_custom': True}
            for name in custom_plates
        ])
        plates_df = pd.concat([plates_df, custom_df], ignore_index=True)
        print(f"✅ Added {len(custom_plates)} custom plates")
        custom_plates_processed = True

    return sample_df, plates_df, custom_plates_processed, additional_plates_processed


def process_additional_standard_plates(existing_sample_df, additional_plates, existing_plates_df):
    """
    Process additional standard plates for existing samples.
    
    Args:
        existing_sample_df (pd.DataFrame): Existing sample metadata
        additional_plates (dict): Mapping of sample_id to additional plate count
        existing_plates_df (pd.DataFrame): Existing plates data to determine next plate numbers
        
    Returns:
        pd.DataFrame: DataFrame of additional plates
    """
    print(f"✅ Found {len(additional_plates)} samples needing additional plates")
    additional_plates_list = []
    
    for sample_id, count in additional_plates.items():
        print(f"  - {sample_id}: {count} additional plates")
        
        # Parse PROPOSAL_GROUP format (e.g., "509735_WCBP1PR" -> proposal="509735", sample="WCBP1PR")
        if '_' not in sample_id:
            print(f"⚠️  WARNING: Invalid format for {sample_id}. Expected PROPOSAL_GROUP format (e.g., '509735_WCBP1PR')")
            continue
            
        proposal, sample = sample_id.split('_', 1)
        
        # Find the sample with matching Proposal and Group_or_abrvSample combination
        sample_row = existing_sample_df[
            (existing_sample_df['Proposal'].astype(str) == str(proposal)) &
            (existing_sample_df['Group_or_abrvSample'] == sample)
        ]
        
        if sample_row.empty:
            print(f"⚠️  WARNING: Proposal-Group combination '{proposal}' + '{sample}' not found in existing metadata")
            continue
        
        # Find existing plates for this proposal-sample combination
        existing_sample_plates = existing_plates_df[
            (existing_plates_df['project'].astype(str) == str(proposal)) &
            (existing_plates_df['sample'] == sample) &
            (existing_plates_df['is_custom'] == False)
        ]
        
        # Find the highest existing plate number for this sample
        if not existing_sample_plates.empty:
            max_plate_number = existing_sample_plates['plate_number'].max()
        else:
            max_plate_number = 0
        
        # Create additional plates for this sample, continuing from the highest existing number
        for i in range(count):
            next_plate_number = max_plate_number + i + 1
            plate_name = f"{proposal}_{sample}.{next_plate_number}"
            
            additional_plates_list.append({
                'plate_name': plate_name,
                'project': proposal,
                'sample': sample,
                'plate_number': next_plate_number,
                'is_custom': False
            })
    
    return pd.DataFrame(additional_plates_list) if additional_plates_list else pd.DataFrame()


def process_subsequent_run(existing_sample_df, existing_plates_df, experiment_type=EXPERIMENT_TYPE_SPS_CE):
    """
    Handle subsequent run: additional plates, custom plates.

    Args:
        existing_sample_df (pd.DataFrame): Existing sample metadata.
        existing_plates_df (pd.DataFrame): Existing plates data.
        experiment_type (str): One of the EXPERIMENT_TYPE_* constants, loaded
            from the database by main() and passed here so that future
            type-specific logic can branch on it without requiring a database
            re-read inside this function.  Currently unused beyond being
            available for future extension.

    Returns:
        tuple: (sample_df, plates_df, custom_plates_processed,
                additional_plates_processed) — sample metadata, new plates
                DataFrames, and processing flags.
    """
    print(f"\n🔄 SUBSEQUENT RUN DETECTED\n")
    
    # Track what was processed
    custom_plates_processed = False
    additional_plates_processed = False
    
    # Ask for additional standard plates (only on subsequent runs)
    additional_plates = get_additional_standard_plates(is_first_run=False)
    
    # Ask for custom plates (available on all runs, subsequent run)
    custom_plates = get_custom_plates(is_first_run=False)
    
    # Check if user wants to add any plates
    if not additional_plates and not custom_plates:
        return existing_sample_df, pd.DataFrame(), custom_plates_processed, additional_plates_processed
    
    # Process additional standard plates
    plates_df = pd.DataFrame()
    sample_df = existing_sample_df  # Use existing sample metadata
    
    if additional_plates:
        additional_df = process_additional_standard_plates(existing_sample_df, additional_plates, existing_plates_df)
        plates_df = additional_df
        additional_plates_processed = True
    
    # Process custom plates
    if custom_plates:
        custom_df = pd.DataFrame([
            {'plate_name': name, 'project': 'CUSTOM', 'sample': 'CUSTOM',
             'plate_number': 1, 'is_custom': True}
            for name in custom_plates
        ])
        if plates_df.empty:
            plates_df = custom_df
        else:
            plates_df = pd.concat([plates_df, custom_df], ignore_index=True)
        print(f"✅ Added {len(custom_plates)} custom plates")
        custom_plates_processed = True
    
    # Plates prepared for processing
    
    return sample_df, plates_df, custom_plates_processed, additional_plates_processed


def process_barcodes(plates_df, existing_plates_df, custom_base_barcode=None):
    """
    Generate and validate barcodes for new plates.
    
    Args:
        plates_df (pd.DataFrame): New plates needing barcodes
        existing_plates_df (pd.DataFrame): Existing plates data
        custom_base_barcode (str, optional): Custom base barcode to use instead of generating random one
        
    Returns:
        tuple: (plates_df, final_plates_df) - Updated plates and combined final data
    """
    # Generate barcodes
    
    # Generate simplified barcodes for new plates
    plates_df = generate_simple_barcodes(plates_df, existing_plates_df, custom_base_barcode)
    
    # Validate barcode uniqueness
    if not validate_barcode_uniqueness(plates_df):
        print("FATAL ERROR: Generated barcodes are not unique!")
        print("Laboratory automation requires unique identifiers for safety.")
        sys.exit()
    
    # Combine with existing data for final validation
    if existing_plates_df is not None:
        final_plates_df = pd.concat([existing_plates_df, plates_df], ignore_index=True)
    else:
        final_plates_df = plates_df
    
    # Final validation
    if not validate_barcode_uniqueness(final_plates_df):
        print("FATAL ERROR: Final barcode set contains duplicates!")
        print("Laboratory automation requires unique identifiers for safety.")
        sys.exit()
    
    return plates_df, final_plates_df


def finalize_files_and_database(sample_df, final_plates_df, new_plates_df, folders, is_first_run=True, custom_plates_processed=False, additional_plates_processed=False, existing_sample_df=None):
    """
    Handle all file operations: archiving, saving, organizing.
    
    Args:
        sample_df (pd.DataFrame): Sample metadata
        final_plates_df (pd.DataFrame): Final plates data (all plates combined)
        new_plates_df (pd.DataFrame): New plates added this run
        folders (dict): Dictionary with folder paths from create_project_folder_structure()
        is_first_run (bool): True for first runs, False for subsequent runs
        custom_plates_processed (bool): True if custom plates were processed this run
        additional_plates_processed (bool): True if additional standard plates were processed this run
        existing_sample_df (pd.DataFrame, optional): Existing sample metadata for comparison
    """
    # Archive existing database file (copy, not move)
    archive_database_file(DATABASE_NAME, folders)
    
    # Smart database save - only update what actually changes
    save_to_database_smart(sample_df, new_plates_df, DATABASE_NAME, is_first_run, existing_sample_df)
    
    # Generate BarTender file with timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")
    bartender_filename = f"BARTENDER_sort_plate_labels_{timestamp}.txt"
    
    # Use only new plates for BarTender file generation
    if not new_plates_df.empty:
        plates_for_bartender = new_plates_df
    else:
        plates_for_bartender = final_plates_df
    
    make_bartender_file(plates_for_bartender, bartender_filename)
    
    # File Management - Organize output and input files
    manage_bartender_file(bartender_filename, folders)
    manage_input_files(folders, is_first_run, custom_plates_processed, additional_plates_processed)
    
    # CSV Management - Archive and create updated CSV files
    manage_csv_files(sample_df, final_plates_df, folders)


def print_completion_summary(sample_df, final_plates_df, new_plates_df):
    """
    Print final success summary.
    
    Args:
        sample_df (pd.DataFrame): Sample metadata
        final_plates_df (pd.DataFrame): Final plates data
        new_plates_df (pd.DataFrame): New plates added this run
    """
    # Completion summary suppressed for minimal output
    pass


def parse_command_line_arguments():
    """
    Parse command line arguments for the script.
    
    Returns:
        argparse.Namespace: Parsed arguments containing custom_base_barcode
    """
    parser = argparse.ArgumentParser(
        description="Laboratory Barcode Label Generation Script",
        epilog="Example: python generate_barcode_labels.py REX12"
    )
    
    parser.add_argument(
        'custom_base_barcode',
        nargs='?',  # Optional positional argument
        help='Custom 5-character base barcode (e.g., REX12). Must start with a letter and contain only uppercase letters and digits.'
    )
    
    return parser.parse_args()


def main():
    """
    Main script execution following laboratory safety standards.
    Uses two-table database architecture and simplified barcode system.

    Execution order is deliberately structured so that all interactive prompts
    and input validation run BEFORE any folders or files are created on disk.
    This prevents leaving behind empty project folder trees when the user
    enters invalid data or selects the wrong experiment type.

    Order of operations:
      1. Parse CLI arguments
      2. Print header
      3. Read database (determines first vs subsequent run)
      4. Experiment type: prompt user (first run) or load from database (subsequent)
      5. First run only: detect and fully validate the sample metadata CSV
      6. Create project folder structure (only after all validation passes)
      7. Generate plate names, barcodes, save to database, write output files
    """
    # Parse command line arguments
    args = parse_command_line_arguments()
    custom_base_barcode = args.custom_base_barcode

    print_header()

    # Determine run type and get existing data
    existing_sample_df, existing_plates_df = read_from_two_table_database(DATABASE_NAME)
    is_first_run = existing_sample_df is None

    # --- Step 1: Experiment type selection (interactive or from database) ---
    # Done before folder creation so a wrong-mode entry fails fast with no
    # side-effects on the filesystem.
    if is_first_run:
        experiment_type = get_experiment_type()
    else:
        if 'experiment_type' in existing_sample_df.columns:
            experiment_type = existing_sample_df['experiment_type'].iloc[0]
            type_labels = {
                EXPERIMENT_TYPE_SPS_CE: "Standard SPS-CE",
                EXPERIMENT_TYPE_BONCAT: "Standard BONCAT",
                EXPERIMENT_TYPE_OTHER:  "Other",
            }
            label = type_labels.get(experiment_type, experiment_type)
            print(f"Experiment type: {label} (loaded from project database)")
        else:
            # Legacy database without experiment_type column — default to SPS-CE
            experiment_type = EXPERIMENT_TYPE_SPS_CE
            print("Experiment type: Standard SPS-CE (default — no type stored in database)")

    # --- Step 2: First-run CSV detection and validation ---
    # Runs before folder creation so that a bad CSV or wrong experiment type
    # terminates the script without creating any project folders.
    if is_first_run:
        print("\n🔬 FIRST RUN DETECTED")
        print("Processing sample metadata CSV file...")
        csv_file = detect_sample_metadata_csv()
        # read_sample_csv applies both shared and experiment-type-specific
        # validation; it calls sys.exit() on any failure.
        _pre_validated_sample_df = read_sample_csv(csv_file, experiment_type)
    else:
        _pre_validated_sample_df = None
        csv_file = None

    # --- Step 3: Create project folder structure ---
    # Only reached if experiment type selection and CSV validation both passed.
    folders = create_project_folder_structure()

    # --- Step 4: Process plates ---
    if is_first_run:
        sample_df, plates_df, custom_plates_processed, additional_plates_processed = process_first_run(
            experiment_type,
            pre_validated_sample_df=_pre_validated_sample_df,
            pre_validated_csv_file=csv_file,
        )
    else:
        sample_df, plates_df, custom_plates_processed, additional_plates_processed = process_subsequent_run(existing_sample_df, existing_plates_df, experiment_type)
        if plates_df.empty:
            print("No new plates to add. Exiting.")
            return

    # Generate and validate barcodes
    plates_df, final_plates_df = process_barcodes(plates_df, existing_plates_df, custom_base_barcode)

    # Handle all file operations
    finalize_files_and_database(sample_df, final_plates_df, plates_df, folders, is_first_run, custom_plates_processed, additional_plates_processed, existing_sample_df)

    # Print completion summary
    print_completion_summary(sample_df, final_plates_df, plates_df)

    # Create success marker for workflow manager
    create_success_marker()


if __name__ == "__main__":
    main()