#!/usr/bin/env python3

# USAGE: python SPS_make_illumina_index_and_FA_files_NEW.py <grid_table.csv>

"""
SPS Library Creation Script - Revised Version

This script reads an existing project_summary.db database and merges it with 
grid table data to generate all necessary files for library preparation:
- Echo transfer files
- Illumina index transfer files  
- Fragment Analyzer (FA) input files
- Dilution transfer files
- Bartender barcode label files

The script archives existing database files before creating updated versions.
"""

import pandas as pd
import numpy as np
import sys
import string
from datetime import datetime
from pathlib import Path
import os
from sqlalchemy import create_engine


# Global well list for 96-well plates
WELL_LIST_96W = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']


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
    
    # Second attempt directories (for future use)
    SECOND_DIR = PROJECT_DIR / "C_second_attempt_make_lib"
    SECOND_DIR.mkdir(parents=True, exist_ok=True)
    
    SECFA_DIR = PROJECT_DIR / "D_second_attempt_fa_result"
    SECFA_DIR.mkdir(parents=True, exist_ok=True)
    
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
    well_list_96w = WELL_LIST_96W
    
    well_list_384w = ['A1', 'C1', 'E1', 'G1', 'I1', 'K1', 'M1', 'O1', 'A3', 'C3', 'E3', 'G3', 'I3', 'K3', 'M3', 'O3', 'A5', 'C5', 'E5', 'G5',
                      'I5', 'K5', 'M5', 'O5', 'A7', 'C7', 'E7', 'G7', 'I7', 'K7', 'M7', 'O7', 'A9', 'C9', 'E9', 'G9', 'I9', 'K9', 'M9', 'O9',
                      'A11', 'C11', 'E11', 'G11', 'I11', 'K11', 'M11', 'O11', 'A13', 'C13', 'E13', 'G13', 'I13', 'K13', 'M13', 'O13', 'A15',
                      'C15', 'E15', 'G15', 'I15', 'K15', 'M15', 'O15', 'A17', 'C17', 'E17', 'G17', 'I17', 'K17', 'M17', 'O17', 'A19', 'C19',
                      'E19', 'G19', 'I19', 'K19', 'M19', 'O19', 'A21', 'C21', 'E21', 'G21', 'I21', 'K21', 'M21', 'O21', 'A23', 'C23', 'E23',
                      'G23', 'I23', 'K23', 'M23', 'O23']
    
    # Create conversion dictionaries
    convert_96_to_384_plate = dict(zip(well_list_96w, well_list_384w))
    convert_384_to_96_plate = dict(zip(well_list_384w, well_list_96w))
    
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


def read_grid_table(filename):
    """Read and validate the grid table CSV file."""
    grid_path = Path(filename)
    
    if not grid_path.exists():
        raise FileNotFoundError(f"Grid table file not found: {filename}")
    
    try:
        grid_df = pd.read_csv(grid_path)
        
        # Validate required columns
        required_cols = ['Well', 'Aliquot Plate Label', 'Illumina Library', 'Container Barcode', 'Nucleic Acid ID']
        missing_cols = [col for col in required_cols if col not in grid_df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns in grid table: {missing_cols}")
        
        print(f"Successfully read {len(grid_df)} rows from grid table")
        return grid_df
        
    except Exception as e:
        raise RuntimeError(f"Error reading grid table: {e}")


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


def validate_and_merge_data(db_df, grid_df):
    """Merge database and grid table data with validation."""
    print("Validating and merging data...")
    
    # Select only the 5 columns we need from grid table
    grid_subset = grid_df[['Well', 'Aliquot Plate Label', 'Illumina Library', 'Container Barcode', 'Nucleic Acid ID']].copy()
    
    # Rename columns for final output
    grid_subset = grid_subset.rename(columns={
        'Container Barcode': 'Destination_Plate_Barcode',
        'Nucleic Acid ID': 'sample_id'
    })
    
    # Perform merge
    merged_df = pd.merge(
        db_df,
        grid_subset,
        left_on=['Destination_Well', 'Destination_plate_name'],
        right_on=['Well', 'Aliquot Plate Label'],
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
    merged_df = merged_df.drop(columns=['Well', 'Aliquot Plate Label'])
    
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
        print(f"Archived database to: {archive_db}")
    
    # Archive CSV file
    csv_file = base_dir / "project_summary.csv"
    if csv_file.exists():
        archive_csv = archive_dir / f"archive_project_summary_{timestamp}.csv"
        csv_file.rename(archive_csv)
        print(f"Archived CSV to: {archive_csv}")


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
    
    print(f"Created new database and CSV with {len(merged_df_ordered)} rows")


def prepare_echo_data(merged_df):
    """Prepare data for Echo transfer files."""
    echo_df = merged_df.copy()
    
    # Convert well positions to numeric row/column
    # Use 'source_well' column from database for source positions (where samples come from)
    echo_df['Source_Row'], echo_df['Source_Column'] = zip(*echo_df['source_well'].apply(convert_well_to_row_col))
    # Use 'Destination_Well' for destination positions (where samples go to)
    echo_df['Dest_Row'], echo_df['Dest_Column'] = zip(*echo_df['Destination_Well'].apply(convert_well_to_row_col))
    
    # Create Echo file format
    echo_df = echo_df.rename(columns={
        'plate_id': 'Source Plate Name',
        'echo_id': 'Source Plate Barcode',
        'Destination_plate_name': 'Destination Plate Name'
    })
    
    echo_df['Source Row'] = echo_df['Source_Row']
    echo_df['Source Column'] = echo_df['Source_Column']
    echo_df['Destination Row'] = echo_df['Dest_Row']
    echo_df['Destination Column'] = echo_df['Dest_Column']
    echo_df['Transfer Volume'] = 500
    echo_df['Destination Plate Barcode'] = echo_df['Destination_Plate_Barcode']
    
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
        
        # Get unique source plates for this destination
        source_plates = plate_data['Source Plate Barcode'].unique()
        source_names = '_'.join(source_plates)
        
        # Create filename: destination_source1_source2_etc.csv
        filename = f"{dest_plate}_{source_names}.csv"
        
        # Sort by destination column and row
        plate_data = plate_data.sort_values(['Destination Column', 'Destination Row'])
        
        # Save file
        plate_data.to_csv(ECHO_DIR / filename, index=False)
        print(f"Created Echo file: {filename}")


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
        print(f"Created Illumina file: {filename}")


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
        print(f"Created FA file: {filename}")


def make_dilution_dataframe(merged_df):
    """Create dilution transfer dataframe."""
    # Ask user for dilution factor
    dilution_factor = float(input("What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): ") or 5)
    
    dilution_df = merged_df[['Destination_Plate_Barcode', 'Destination_Well']].copy()
    
    # Convert 384-well to 96-well positions for FA
    well_list_384w = ['A1', 'C1', 'E1', 'G1', 'I1', 'K1', 'M1', 'O1', 'A3', 'C3', 'E3', 'G3', 'I3', 'K3', 'M3', 'O3', 'A5', 'C5', 'E5', 'G5',
                      'I5', 'K5', 'M5', 'O5', 'A7', 'C7', 'E7', 'G7', 'I7', 'K7', 'M7', 'O7', 'A9', 'C9', 'E9', 'G9', 'I9', 'K9', 'M9', 'O9',
                      'A11', 'C11', 'E11', 'G11', 'I11', 'K11', 'M11', 'O11', 'A13', 'C13', 'E13', 'G13', 'I13', 'K13', 'M13', 'O13', 'A15',
                      'C15', 'E15', 'G15', 'I15', 'K15', 'M15', 'O15', 'A17', 'C17', 'E17', 'G17', 'I17', 'K17', 'M17', 'O17', 'A19', 'C19',
                      'E19', 'G19', 'I19', 'K19', 'M19', 'O19', 'A21', 'C21', 'E21', 'G21', 'I21', 'K21', 'M21', 'O21', 'A23', 'C23', 'E23',
                      'G23', 'I23', 'K23', 'M23', 'O23']
    convert_384_to_96 = dict(zip(well_list_384w, WELL_LIST_96W))
    
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
        print(f"Created dilution file: {filename}")


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
    print("Created threshold file: thresholds.txt")


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
    print(f"Created Bartender file: {filename}")


def main():
    """Main execution function."""
    if len(sys.argv) != 2:
        print("Usage: python SPS_make_illumina_index_and_FA_files_NEW.py <grid_table.csv>")
        sys.exit()
    
    grid_table_file = sys.argv[1]
    
    try:
        # Create directory structure
        print("Creating directory structure...")
        directories = create_directories()
        BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR, ARCHIVE_DIR = directories
        
        # Get plate configuration
        well_list, convert_96_to_384, convert_384_to_96 = get_plate_type()
        
        # Read input data
        print("Reading input data...")
        db_df = read_project_database(BASE_DIR)
        grid_df = read_grid_table(grid_table_file)
        
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
        
        # Move grid table file to library directory
        grid_path = Path(grid_table_file)
        if grid_path.exists():
            grid_path.rename(LIB_DIR / grid_table_file)
            print(f"Moved {grid_table_file} to library directory")
        
        print("\n" + "="*50)
        print("SCRIPT COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Processed {len(merged_df)} samples")
        print(f"Generated files in: {PROJECT_DIR}")
        print("All output files have been created and are ready for use.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit()


if __name__ == "__main__":
    main()