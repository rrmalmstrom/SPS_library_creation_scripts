#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPS Second FA Output Analysis Script

This script processes Fragment Analyzer (FA) output files for second attempt library analysis.
It reads FA smear analysis results from libraries that failed first QC, merges them with
project summary data, applies quality thresholds, and generates summary reports including
identification of samples that failed both attempts.

The script expects to be run from the project root directory and will:
1. Find and process second attempt FA output CSV files in D_second_attempt_fa_result
2. Merge with project summary database
3. Apply quality thresholds from thresholds.txt
4. Calculate total passed attempts across both rounds
5. Generate reduced summary and double-failed libraries output files

Author: Laboratory Automation Team
Version: 2.0 (Refactored for pathlib and improved error handling)
"""

import sys
from pathlib import Path
import shutil
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from datetime import datetime


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


# Define paths using pathlib strategy
PROJECT_DIR = Path.cwd()

MAKE_DIR = PROJECT_DIR / "1_make_library_analyze_fa"

FIRST_DIR = MAKE_DIR / "B_first_attempt_fa_result"

SECOND_DIR = MAKE_DIR / "D_second_attempt_fa_result"

ARCHIV_DIR = PROJECT_DIR / "archived_files"

ARCHIV_DIR.mkdir(parents=True, exist_ok=True)


##########################
##########################
def compareFolderFileNames(folder_path, file, folder_name):
    """
    Validate that FA plate names in folder match sample names in CSV file.
    
    Args:
        folder_path: Path to the folder containing the FA file
        file: Name of the FA CSV file
        folder_name: Name of the FA plate folder
        
    Raises:
        SystemExit: If plate names don't match
    """
    # print(f"Validating plate names for {folder_name}...")
    
    # Read FA smear analysis output CSV file
    fa_df = pd.read_csv(folder_path / file, usecols=['Sample ID'])
    
    # Extract unique sample names
    sample_list = fa_df['Sample ID'].unique().tolist()
    
    # Parse plate names from sample IDs and add 'F' suffix to match folder naming
    # For second attempt, expect .2F pattern
    plate_list = [s.split('_')[0] + 'F' for s in sample_list]
    
    # print(f"  Sample IDs found: {len(sample_list)} samples")
    # print(f"  Parsed plate names: {set(plate_list)}")
    # print(f"  Folder name: {folder_name}")
    
    # Validate folder name matches parsed plate names
    if folder_name not in set(plate_list):
        print(f'\n\nMismatch between FA plate ID and sample names for plate {folder_name}. Aborting script\n')
        sys.exit()
    
    # print(f"  ✓ Validation passed for {folder_name}")
##########################
##########################

##########################
##########################
def getFAfiles(second_dir):
    """
    Scan directories for second attempt FA output files and copy them to the working directory.
    
    Args:
        second_dir: Path to the second attempt FA result directory
        
    Returns:
        Tuple of (List of FA file names that were processed, List of FA result directories for archiving)
        
    Raises:
        SystemExit: If no FA files are found or copying fails
    """
    # print(f"Scanning for FA files in: {second_dir}")
    fa_files = []
    fa_result_dirs_to_archive = []  # NEW: Track directories for archiving
    
    if not second_dir.exists():
        print(f"ERROR: Second attempt directory does not exist: {second_dir}")
        sys.exit()
    
    for direct in second_dir.iterdir():
        if direct.is_dir():
            # print(f"Processing date directory: {direct.name}")
            nxt_dir = direct
            
            # scan current directory and find subdirectories
            for fa in nxt_dir.iterdir():
                if fa.is_dir():
                    # print(f"  Found FA plate directory: {fa.name}")
                    
                    # find full path to subdirectories
                    folder_path = fa
                    
                    # extract name of FA plate by parsing the subdirectory name
                    folder_name = fa.name
                    folder_name = folder_name.split(' ')[0]
                    # print(f"  Parsed plate name: {folder_name}")
                    
                    # search for smear analysis files in each subdirectory
                    smear_files = []
                    for file_path in fa.iterdir():
                        if file_path.name.endswith('Smear Analysis Result.csv'):
                            smear_files.append(file_path)
                            # print(f"    Found smear analysis file: {file_path.name}")
                    
                    if not smear_files:
                        print(f"    No smear analysis files found in {fa.name}")
                        continue
                    
                    # Process the first smear analysis file found
                    source_file = smear_files[0]
                    
                    # confirm folder name matches plate name parsed from
                    # smear analysis .csv sample names.  Error out if mismatch
                    compareFolderFileNames(folder_path, source_file.name, folder_name)
                    
                    # copy and rename smear analysis to main directory if good match
                    dest_file = second_dir / f'{folder_name}.csv'
                    # print(f"    Copying {source_file} -> {dest_file}")
                    
                    try:
                        shutil.copy(source_file, dest_file)
                        
                        # Verify the copy was successful
                        if dest_file.exists():
                            file_size = dest_file.stat().st_size
                            # print(f"    ✓ Copy successful: {dest_file} ({file_size} bytes)")
                            fa_files.append(f'{folder_name}.csv')
                            
                            # NEW: Track this directory for archiving
                            fa_result_dirs_to_archive.append(fa)
                        else:
                            print(f"    ERROR: Copy failed - destination file does not exist: {dest_file}")
                            sys.exit()
                            
                    except Exception as e:
                        print(f"    ERROR: Failed to copy file: {e}")
                        sys.exit()

    # quit script if directory doesn't contain FA .csv files
    if len(fa_files) == 0:
        print("\n\nDid not find any FA output files. Aborting program\n\n")
        sys.exit()
    
    print(f"\nSuccessfully processed {len(fa_files)} FA files:")
    for f in fa_files:
        print(f"  - {f}")
    
    # return both lists
    return fa_files, fa_result_dirs_to_archive
##########################
##########################

##########################
##########################
def processFAfiles(my_fa_files):
    """
    Process second attempt FA CSV files into DataFrames with cleaned and standardized data.
    
    Args:
        my_fa_files: List of FA file names to process
        
    Returns:
        Tuple of (dictionary mapping filenames to DataFrames, list of destination plates)
        
    Raises:
        SystemExit: If processing fails or file counts don't match
    """
    # print(f"\nProcessing {len(my_fa_files)} FA files...")
    
    # create dict where  keys are FA file names and value are df's from those files
    fa_dict = {}

    fa_dest_plates = []

    # loop through all FA files and create df's stored in dict
    for f in my_fa_files:
        # print(f"Processing file: {f}")
        
        file_path = SECOND_DIR / f
        if not file_path.exists():
            print(f"ERROR: FA file not found: {file_path}")
            sys.exit()
        
        try:
            fa_dict[f] = pd.read_csv(file_path, usecols=[
                'Well', 'Sample ID', 'ng/uL', 'nmole/L', 'Avg. Size'])
            
            # print(f"  Read {len(fa_dict[f])} rows from {f}")

            fa_dict[f] = fa_dict[f].rename(
                columns={"Sample ID": "Redo_FA_Sample_ID", "Well": "Redo_FA_Well", 
                        "ng/uL": "Redo_ng/uL", "nmole/L": "Redo_nmole/L", "Avg. Size": "Redo_Avg. Size"})

            fa_dict[f]['Redo_FA_Well'] = fa_dict[f]['Redo_FA_Well'].str.replace(
                ':', '')

            # remove rows with "empty" or "ladder" in sample ID. search is case insensitive
            initial_rows = len(fa_dict[f])
            
            fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
                'empty', case=False) == False]

            fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
                'ladder', case=False) == False]

            fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
                'LibStd', case=False) == False]
            
            filtered_rows = len(fa_dict[f])
            # print(f"  Filtered out {initial_rows - filtered_rows} control rows, {filtered_rows} samples remaining")

            # create three new columns by parsing Sample_ID string using "_" as delimiter
            fa_dict[f][['Redo_FA_Destination_plate', 'Redo_FA_Sample', 'Redo_FA_well_2']
                       ] = fa_dict[f].Redo_FA_Sample_ID.str.split("_", expand=True)
            

            fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].fillna(0)

            fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].fillna(0)

            fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].fillna(0)

            fa_dict[f]['Redo_FA_Sample'] = fa_dict[f]['Redo_FA_Sample'].astype(str)

            fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].astype(float)

            fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].astype(float)

            fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].astype(float)

            # add destination plates in fa file to list fa_dest_plates
            dest_plates = fa_dict[f]['Redo_FA_Destination_plate'].unique().tolist()
            fa_dest_plates.extend(dest_plates)
            # print(f"  Destination plates: {dest_plates}")
        
            # get rid of unnecessary columns
            fa_dict[f].drop(['Redo_FA_Destination_plate','Redo_FA_well_2','Redo_FA_Sample_ID','Redo_FA_Well'], inplace=True, axis=1)
            
            # print(f"  ✓ Successfully processed {f}")
            
        except Exception as e:
            print(f"ERROR processing {f}: {e}")
            sys.exit()

    # quit script if were not able to process FA input files
    if len(fa_dict.keys()) == 0:
        print("\n\nDid not successfully extract FA files\n\n")
        sys.exit()

    elif len(fa_dict.keys()) != len(set(fa_dest_plates)):
        print(f"\n\nMismatch in number of FA files ({len(fa_dict.keys())}) and destination plates ({len(set(fa_dest_plates))})\n\n")
        print(f"FA files: {list(fa_dict.keys())}")
        print(f"Destination plates: {set(fa_dest_plates)}")
        sys.exit()

    # # print out list of successfully processed FA files
    # print("\n\n\nList of processed FA output files:\n\n\n")

    # for k in fa_dict.keys():
    #     print(f'{k}\n')

    # # add some blank lines after displaying list of processed FA files
    # print('\n\n\n')

    return fa_dict, list(set(fa_dest_plates))
##########################
##########################



##########################
##########################
def readSQLdb():
    """
    Read project summary data from SQLite database.
    
    Returns:
        DataFrame containing project summary data
    """
    print("Reading project summary database...")
    
    # path to sqlite db project_summary.db
    sql_db_path = PROJECT_DIR / 'project_summary.db'
    
    if not sql_db_path.exists():
        print(f"ERROR: Database file not found: {sql_db_path}")
        sys.exit()

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM project_summary"
    
    try:
        # import sql db into pandas df
        sql_df = pd.read_sql(query, engine)
        # print(f"  Read {len(sql_df)} rows from database")
        
        engine.dispose()
        return sql_df
        
    except Exception as e:
        print(f"ERROR reading database: {e}")
        engine.dispose()
        sys.exit()
##########################
##########################



##########################
##########################
def addFAresults(my_prjct_dir, my_fa_df):
    """
    Merge second attempt FA results with project summary data.
    
    Args:
        my_prjct_dir: Project directory path (currently unused)
        my_fa_df: DataFrame containing second attempt FA analysis results
        
    Returns:
        Merged DataFrame with FA and project data
        
    Raises:
        SystemExit: If merge operation fails or changes row count
    """
    print("\nMerging FA results with project summary...")
    
    # create df from sqlite db
    my_lib_df = readSQLdb()
    
    # convert sample id to string
    my_lib_df['sample_id'] = my_lib_df['sample_id'].astype(str)

    # record number of rows in my_lib_df. want to make sure doesn't change when merged with fa_df
    num_rows = my_lib_df.shape[0]
    # print(f"  Project summary has {num_rows} rows")
    # print(f"  FA data has {len(my_fa_df)} rows")

    # merge lib df with fa_df
    my_lib_df = my_lib_df.merge(my_fa_df, how='left', left_on=['sample_id'], right_on=['Redo_FA_Sample'])
    
    # print(f"  After merge: {len(my_lib_df)} rows")
    
    # confirm that merging did not change the row number
    if my_lib_df.shape[0] != num_rows:
        print(
            '\nProblem merging project summary with FA files. Check out error.txt file just generated. Aborting.\n\n')
        print(my_lib_df.loc[my_lib_df['Destination_Plate_Barcode'].isnull()])

        my_lib_df.to_csv('error.txt', sep='\t', index=False)
        sys.exit()

    # get rid of unnecessary columns
    my_lib_df.drop(['Redo_FA_Sample'], inplace=True, axis=1)
    
    # Count how many samples got FA data
    fa_samples = my_lib_df['Redo_ng/uL'].notna().sum()
    # print(f"  Successfully merged FA data for {fa_samples} samples")

    return my_lib_df
##########################
##########################


##########################
##########################
def findPassFailLibs(my_lib_df, my_dest_plates):
    """
    Apply quality thresholds and identify pass/fail libraries for second attempt.
    
    Args:
        my_lib_df: DataFrame with merged library and FA data
        my_dest_plates: List of destination plate names
        
    Returns:
        Tuple of (DataFrame with pass/fail analysis, DataFrame with double-failed samples)
        
    Raises:
        SystemExit: If thresholds file is missing values or dilution factor issues
    """
    print("\nApplying quality thresholds...")
    
    # import df with dna conc and size thresholds for each FA plate
    thresh_file = SECOND_DIR / "thresholds.txt"
    if not thresh_file.exists():
        print(f"ERROR: Thresholds file not found: {thresh_file}")
        sys.exit()
        
    thresh_df = pd.read_csv(thresh_file, sep="\t", header=0)
    # print(f"  Read thresholds for {len(thresh_df)} plates")
    
    # make sure threshold file has values for all threshold parameters
    if thresh_df.isnull().values.any():
        print('\nThe thresholds.txt file is missing needed values. Aborting\n\n')
        sys.exit()
    
    thresh_df = thresh_df.rename(columns={"dilution_factor": "Redo_dilution_factor"})

    # add thresholds to my_lib_df
    my_lib_df = my_lib_df.merge(thresh_df, how='left', left_on=[
        'Redo_Destination_Plate_Barcode'], right_on=['Destination_plate'], suffixes=('', '_y'))
    
    # make column that compares dilution factor in project_summary.csv with value in thresholds.txt
    my_lib_df['compare_dilution_factors'] = my_lib_df['Redo_dilution_factor'].equals(my_lib_df['Redo_dilution_factor_y'])
    
    # determine what to do if dilution factors differ
    if my_lib_df['compare_dilution_factors'].any() == False:
        
        val = input('\n\nThe dilution factor in the thresholds file does not match value in project_summary.csv. Is the thresholds.txt file correct? (Y/N): ')
    
        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")
            
            my_lib_df['Redo_dilution_factor'] = my_lib_df['Redo_dilution_factor_y']

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script. Please resolve issue with dilution factor in thresholds file\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time.\n\nAborting\n\n")
            sys.exit()
    
    # remove column with dilution_factor read from thresholds file and column comparing dilution factors
    my_lib_df.drop(columns=['Redo_dilution_factor_y','compare_dilution_factors'], inplace=True)

    # assign pass or fail to each lib based on dna conc and size thresholds
    my_lib_df['Redo_Passed_library'] = np.where(((my_lib_df['Redo_nmole/L'] > my_lib_df['DNA_conc_threshold_(nmol/L)']) & (
        my_lib_df['Redo_Avg. Size'] > my_lib_df['Size_theshold_(bp)'])), 1, 0)

    # update lib conc info based on the dilution factor.  This is conc in original library plate
    my_lib_df['Redo_ng/uL'] = my_lib_df['Redo_ng/uL'] * my_lib_df['Redo_dilution_factor']

    my_lib_df = my_lib_df.round({'Redo_ng/uL': 3})

    my_lib_df['Redo_nmole/L'] = my_lib_df['Redo_nmole/L'] * my_lib_df['Redo_dilution_factor']

    my_lib_df = my_lib_df.round({'Redo_nmole/L': 3})

    # remove columns no longer needed
    my_lib_df.drop(['Destination_plate', 'DNA_conc_threshold_(nmol/L)',
                   'Size_theshold_(bp)'], inplace=True, axis=1)

    # find samples that failed both attempts at library creation
    # by adding Passed and Redo_Passed columns.  Treat NaN as 0 for summing
    my_lib_df['Total_passed_attempts'] = my_lib_df['Passed_library'].fillna(0) + \
        my_lib_df['Redo_Passed_library'].fillna(0)
        
    # select subset of lib_df containing info only on plates that went through rework
    redux_mask = my_lib_df['Redo_Destination_Plate_Barcode'].isin(my_dest_plates)
    
    redux_df = my_lib_df[redux_mask]
    
    # print(f"  Samples in rework plates: {len(redux_df)}")

    # make a summary file containing only libs that failed both attempts
    my_double_fail_df = redux_df.loc[redux_df['Total_passed_attempts'] == 0].copy()
    
    # print(f"  Samples that failed both attempts: {len(my_double_fail_df)}")

    return my_lib_df, my_double_fail_df
##########################
##########################

def archive_fa_results(fa_result_dirs, archive_subdir_name):
    """Archive FA result directories to permanent storage by copying them"""
    if not fa_result_dirs:
        return
    
    # Create archive directory
    archive_base = PROJECT_DIR / "archived_files"
    archive_dir = archive_base / archive_subdir_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for result_dir in fa_result_dirs:
        if result_dir.exists():
            dest_path = archive_dir / result_dir.name
            
            # Handle existing archives (prevent nesting)
            if dest_path.exists():
                shutil.rmtree(dest_path)
                # print(f"Removing existing archive: {result_dir.name}")
            
            # Copy directory to archive (preserves original)
            shutil.copytree(str(result_dir), str(dest_path))
            print(f"Archived (copied): {result_dir.name}")

def main():
    """
    Main function to orchestrate the second attempt FA analysis workflow.
    """
    print("Starting SPS Second FA Output Analysis...")
    # print(f"Working directory: {PROJECT_DIR}")
    # print(f"Second attempt directory: {SECOND_DIR}")
    
    # MODIFIED: Update function call to receive both returns
    fa_files, fa_result_dirs_to_archive = getFAfiles(SECOND_DIR)

    # get dictionary where keys are FA file names and values are df's created from FA files
    # and get a list of destination/lib plate IDs processed
    fa_lib_dict, fa_dest_plates = processFAfiles(fa_files)

    # create new dataframe combining all entries in dictionary fa_lib_dict
    fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)
    # print(f"Combined FA data: {len(fa_df)} samples")

    # add FA results to df from project summary database
    lib_df = addFAresults(PROJECT_DIR, fa_df)

    # identify libs that passed/failed based on user provided thresholds
    fa_summary_df, double_fail_df = findPassFailLibs(lib_df, fa_dest_plates)

    # make smaller version of FA summary with only a subset of columns
    reduced_fa_df = fa_summary_df[['sample_id', 'Redo_Destination_Plate_Barcode', 'Redo_FA_Well', 'Redo_dilution_factor',
                                  'Redo_ng/uL', 'Redo_nmole/L', 'Redo_Avg. Size', 'Redo_Passed_library',
                                  'Total_passed_attempts']].copy()

    reduced_fa_df.sort_values(
        by=['Redo_Destination_Plate_Barcode', 'sample_id'], inplace=True)

    # create updated library info file
    output_file = SECOND_DIR / 'reduced_2nd_fa_analysis_summary.txt'
    reduced_fa_df.to_csv(output_file, sep='\t', index=False)

    # create new df of samples that failed both attempts at library creation
    double_fail_output = SECOND_DIR / 'double_failed_libraries.txt'
    double_fail_df.to_csv(double_fail_output, sep='\t', index=False)
    
    print(f"\nAnalysis complete.")
    
    # NEW: Archive FA results before creating success marker
    if fa_result_dirs_to_archive:
        archive_fa_results(fa_result_dirs_to_archive, "second_lib_attempt_fa_results")
    
    # Create success marker for workflow manager integration
    create_success_marker()


if __name__ == "__main__":
    main()