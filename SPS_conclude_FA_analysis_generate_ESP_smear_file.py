#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
import numpy as np


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



##########################
##########################
def findUpdateFAFile():
    # Check for missing critical files when directories exist
    if SECOND_FA_DIR.exists():
        second_fa_file = SECOND_FA_DIR / "updated_2nd_fa_analysis_summary.txt"
        if not second_fa_file.exists():
            print('\nERROR: Second attempt directory exists but critical file is missing!')
            print('Please generate the updated_2nd_fa_analysis_summary.txt file before running this script.\n')
            sys.exit()
        updated_file_name = second_fa_file

    elif FIRST_FA_DIR.exists():
        first_fa_file = FIRST_FA_DIR / "updated_fa_analysis_summary.txt"
        if not first_fa_file.exists():
            print('\nERROR: First attempt directory exists but critical file is missing!')
            print('Please generate the updated_fa_analysis_summary.txt file before running this script.\n')
            sys.exit(0)
        updated_file_name = first_fa_file

    else:
        print('\nERROR: No FA analysis directories found!')
        print('Expected one of the following directories to exist:')
        print('Please ensure at least one FA analysis has been completed.\n')
        sys.exit(1)

    return updated_file_name
##########################
##########################



##########################
##########################
def readSQLdb():
    
    # path to sqlite db project_summary.db
    sql_db_path = PROJECT_DIR /'project_summary.db'

    # create sqlalchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # define sql query
    query = "SELECT * FROM project_summary"
    
    # import sql db into pandas df
    sql_df = pd.read_sql(query, engine)
    
    engine.dispose()

    return sql_df
##########################
##########################


##########################
##########################
def handleFirstAttemptOnly(lib_df):
    """
    Create missing Redo columns when processing first-attempt-only data.
    This simulates what the noRework() function would have created.
    
    Args:
        lib_df: DataFrame with first attempt data only
        
    Returns:
        DataFrame with all required Redo columns added
        
    Raises:
        KeyError: If required first attempt columns are missing
        ValueError: If data validation fails
    """
    # Validate required columns exist
    required_columns = ['Passed_library', 'FA_Well']
    missing_columns = [col for col in required_columns if col not in lib_df.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns for first attempt processing: {missing_columns}")
    
    # Create Total_passed_attempts (core column for all logic)
    lib_df['Total_passed_attempts'] = lib_df['Passed_library'].fillna(0)
    
    # Create Redo columns with appropriate values for "no second attempt"
    lib_df['Redo_Passed_library'] = 0  # No second attempt happened
    
    # Create empty/placeholder Redo columns (will be empty since no second attempt)
    lib_df['Redo_dilution_factor'] = ""
    lib_df['Redo_FA_Well'] = lib_df['FA_Well']  # Copy from first attempt (gets dropped later)
    lib_df['Redo_Destination_Plate_Barcode'] = ""
    lib_df['Redo_Destination_Well'] = ""
    lib_df['Redo_Illumina_index_set'] = ""
    lib_df['Redo_Illumina_index'] = ""
    lib_df['Redo_ng/uL'] = ""
    lib_df['Redo_nmole/L'] = ""
    lib_df['Redo_Avg. Size'] = ""
    
    # Validate that Total_passed_attempts was created successfully
    if lib_df['Total_passed_attempts'].isnull().any():
        raise ValueError("Failed to create Total_passed_attempts column properly")
    
    print("✓ Created missing Redo columns for first-attempt-only workflow")
    
    return lib_df
##########################
##########################


##########################
##########################
def updateLibInfo(updated_file_name):

    # create df from fa_analysis_summary.txt file
    reduced_df = pd.read_csv(updated_file_name, sep='\t', header=0)
    
    # create df from project_summary.db sqliute file
    lib_df = readSQLdb()
    
    if 'Total_passed_attempts' in lib_df.columns:
    
        # remove older version to Total_attempts_passed so it can be replaced  during merge step below
        lib_df.drop(['Total_passed_attempts'], inplace=True, axis=1)


    lib_df = lib_df.merge(reduced_df, how='outer', left_on=['sample_id'], 
                          right_on=['sample_id'], suffixes=('', '_y'))
    
    # update dilution factors and previous lib pass/fail decisions
    # this logic also distinguished between instances when a 2nd attempt was made or not
    if 'Redo_dilution_factor_y' in lib_df.columns:
        # update the fa dilution factor using value from threshold.txt (second attempt scenario)
        lib_df['Redo_dilution_factor'] = lib_df['Redo_dilution_factor_y']
        
        # update Passed_Library and Redo_Passed_library with manually modified results from updated_*_fa_analysis_summary.txt
        if 'Passed_library_y' in lib_df.columns:
            lib_df['Passed_library'] = lib_df['Passed_library_y']
        
    else:
        # update the fa dilution factor using value from threshold.txt (first attempt only scenario)
        if 'dilution_factor_y' in lib_df.columns:
            lib_df['dilution_factor'] = lib_df['dilution_factor_y']
        

    
    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)
    
    # Handle first-attempt-only scenario by creating missing columns
    if updated_file_name == FIRST_FA_DIR / 'updated_fa_analysis_summary.txt':
        try:
            lib_df = handleFirstAttemptOnly(lib_df)
        except (KeyError, ValueError) as e:
            print(f'\nERROR: Failed to create missing columns for first-attempt-only workflow: {e}')
            print('This may indicate corrupted data or missing required columns.')
            print('Aborting script.\n')
            sys.exit()
    
    # remove redundante columns
    if 'Redo_FA_Well' in lib_df.columns:
        # remove unnecessary columne 'FA_Well'
        lib_df.drop(['Redo_FA_Well'], inplace=True, axis=1)

    # sort df based on sample_id in case user manually
    # changed sorting when generated updated_fa_analysis_summary.txt
    lib_df.sort_values(by=['sample_id'], inplace=True)

    # confirm all samples and fraction numbers in reduced_df
    # matched up with all samples and fraction numbrs in lib_df
    if lib_df['Total_passed_attempts'].isnull().values.any():

        print(f'\nProblem updating project_summary.csv with pass/fail results from {updated_file_name}. Aborting script\n\n')
        sys.exit()
        
        
    if updated_file_name == SECOND_FA_DIR / 'updated_2nd_fa_analysis_summary.txt':
        
        lib_df['check_total_pass'] =  lib_df['Total_passed_attempts'] - lib_df['Passed_library'].fillna(0) - lib_df['Redo_Passed_library'].fillna(0)
        
        # abort script if the total passed attempts count does not match  the  sum of individual pass/fail results for each fraction
        if (lib_df['check_total_pass'] != 0).any():
            
            print('\nTotal_passed_attempts does not equal sum of pass/fail results') 
            print(f'Check {updated_file_name} for pass/fail results that may not have been properly updated. Aborting script.\n\n')
            sys.exit()

        # drop column 'check_total_pass' since it's no longer needed
        lib_df.drop(['check_total_pass'], inplace=True, axis=1)        

    return lib_df
##########################
##########################

##########################
##########################
def selectPlateForPooling(lib_df):

    # Create Pool columns for ALL samples (both passed and failed)
    # Start with a copy of the entire dataframe
    final_df = lib_df.copy()

    # Initialize Pool columns for ALL samples
    final_df['Pool_source_plate'] = ""
    final_df['Pool_source_well'] = ""
    final_df['Pool_Illumina_index_set'] = ""
    final_df['Pool_Illumina_index'] = ""
    final_df['Pool_dilution_factor'] = ""
    final_df['Pool_DNA_conc_ng/uL'] = 0
    final_df['Pool_nmole/L'] = 0
    final_df['Pool_Avg. Size'] = 0

    # For ALL samples, populate Pool source plate/well/index/dilution based on which attempt was made
    # Preserve original logic: Total_passed_attempts == 2 gets priority, then Redo_Passed_library == 1, then first attempt
    final_df['Pool_source_plate'] = np.where(
        final_df['Total_passed_attempts'] == 2,
        final_df['Redo_Destination_Plate_Barcode'],
        (np.where(final_df['Redo_Passed_library'] == 1,
                  final_df['Redo_Destination_Plate_Barcode'],
                  final_df['Destination_Plate_Barcode']))
    )

    final_df['Pool_source_well'] = np.where(
        final_df['Total_passed_attempts'] == 2,
        final_df['Redo_Destination_Well'],
        (np.where(final_df['Redo_Passed_library'] == 1,
                  final_df['Redo_Destination_Well'],
                  final_df['Destination_Well']))
    )

    final_df['Pool_Illumina_index_set'] = np.where(
        final_df['Total_passed_attempts'] == 2,
        final_df['Redo_Illumina_index_set'],
        (np.where(final_df['Redo_Passed_library'] == 1,
                  final_df['Redo_Illumina_index_set'],
                  final_df['Illumina_index_set']))
    )

    final_df['Pool_Illumina_index'] = np.where(
        final_df['Total_passed_attempts'] == 2,
        final_df['Redo_Illumina_index'],
        (np.where(final_df['Redo_Passed_library'] == 1,
                  final_df['Redo_Illumina_index'],
                  final_df['Illumina_index']))
    )

    final_df['Pool_dilution_factor'] = np.where(
        final_df['Total_passed_attempts'] == 2,
        final_df['Redo_dilution_factor'],
        (np.where(final_df['Redo_Passed_library'] == 1,
                  final_df['Redo_dilution_factor'],
                  final_df['dilution_factor']))
    )
    
    # For concentration and size values: Only populate for PASSED libraries (Total_passed_attempts >= 1)
    # Failed libraries (Total_passed_attempts == 0) keep the default values of 0
    # Preserve original logic for passed libraries: Total_passed_attempts == 2 gets priority, then Redo_Passed_library == 1, then first attempt
    final_df['Pool_DNA_conc_ng/uL'] = np.where(
        final_df['Total_passed_attempts'] >= 1,
        np.where(
            final_df['Total_passed_attempts'] == 2,
            final_df['Redo_ng/uL'],
            (np.where(final_df['Redo_Passed_library'] == 1,
                      final_df['Redo_ng/uL'],
                      final_df['ng/uL']))
        ),
        0  # Failed libraries get 0
    )

    final_df['Pool_nmole/L'] = np.where(
        final_df['Total_passed_attempts'] >= 1,
        np.where(
            final_df['Total_passed_attempts'] == 2,
            final_df['Redo_nmole/L'],
            (np.where(final_df['Redo_Passed_library'] == 1,
                      final_df['Redo_nmole/L'],
                      final_df['nmole/L']))
        ),
        0  # Failed libraries get 0
    )

    final_df['Pool_Avg. Size'] = np.where(
        final_df['Total_passed_attempts'] >= 1,
        np.where(
            final_df['Total_passed_attempts'] == 2,
            final_df['Redo_Avg. Size'],
            (np.where(final_df['Redo_Passed_library'] == 1,
                      final_df['Redo_Avg. Size'],
                      final_df['Avg. Size']))
        ),
        0  # Failed libraries get 0
    )

    return final_df

##########################
##########################

##########################
##########################
def generateSmearFile(final_df):
    # ESP smear file columns: Well, Sample ID, Range, ng/uL, %Total, nmole/L, Avg. Size,
    # %CV, Volume uL, QC Result, Failure Mode, Index Name, PCR Cycles

    # create smear_df with relevant columns from final_df, including Destination_Plate_Barcode for grouping
    smear_df = final_df[['Destination_Well','Illumina Library','Pool_DNA_conc_ng/uL','Pool_nmole/L','Pool_Avg. Size','Pool_Illumina_index','Total_passed_attempts','Destination_Plate_Barcode']].copy()
    
    # rename columns to match ESP smear file format (except Destination_Plate_Barcode which we'll use for grouping)
    smear_df.rename(columns={
        'Destination_Well': 'Well',
        'Illumina Library': 'Sample ID',
        'Pool_DNA_conc_ng/uL': 'ng/uL',
        'Pool_nmole/L': 'nmole/L',
        'Pool_Avg. Size': 'Avg. Size',
        'Pool_Illumina_index': 'Index Name',
        'Total_passed_attempts': 'QC Result'
    }, inplace=True)

    # add constant columns with default values
    smear_df['Range'] = '400 bp to 800 bp'
    smear_df['%Total'] = 15
    smear_df['%CV'] = 20
    smear_df['Volume uL'] = 20
    smear_df['PCR Cycles'] = 12

    # if smear_df['QC Result'] >=1, set to 'Pass', else 'Fail'
    smear_df['QC Result'] = smear_df['QC Result'].apply(lambda x: 'Pass' if x >= 1 else 'Fail')

    # if smear_df['QC Result'] == 'Fail', set 'Failure Mode' to 'Sample Problem', else ''
    smear_df['Failure Mode'] = smear_df['QC Result'].apply(lambda x: 'Sample Problem' if x == 'Fail' else '')

    # Get unique destination plate barcodes
    unique_plates = smear_df['Destination_Plate_Barcode'].unique()
    
    print(f"Found {len(unique_plates)} unique destination plate barcodes: {list(unique_plates)}")
    
    # Create separate files for each unique destination plate barcode
    for plate_barcode in unique_plates:
        # Filter data for current plate barcode
        plate_df = smear_df[smear_df['Destination_Plate_Barcode'] == plate_barcode].copy()
        
        # Remove the Destination_Plate_Barcode column from the export (as requested)
        plate_df = plate_df.drop('Destination_Plate_Barcode', axis=1)
        
        # Reorder columns for final export
        plate_df = plate_df[['Well', 'Sample ID', 'Range', 'ng/uL', '%Total', 'nmole/L', 'Avg. Size',
                             '%CV', 'Volume uL', 'QC Result', 'Failure Mode', 'Index Name', 'PCR Cycles']]
        
        # Create filename with plate barcode included
        smear_file_path = SMEAR_DIR / f'ESP_smear_file_for_upload_{plate_barcode}.txt'
        
        # Export plate-specific data to tab delimited file
        plate_df.to_csv(smear_file_path, sep='\t', index=False)
        
        print(f"✓ Created ESP smear file: {smear_file_path} ({len(plate_df)} rows)")

    return
##########################
##########################


#########################
#########################
def createSQLdb(lib_df):
    
    # # make copy of current version so project_summary.db to be archived
    # # the copy will be moved to archive folder at a later step
    # shutil.copy(PROJECT_DIR /'project_summary.db', PROJECT_DIR / 'archive_project_summary.db')
    
    # archive the older version of sql project_summary.db
    Path(PROJECT_DIR /
        "project_summary.db").rename(ARCHIV_DIR / f"archive_project_summary_{date}.db")
    Path(ARCHIV_DIR / f"archive_project_summary_{date}.db").touch()

    sql_db_path = PROJECT_DIR /'project_summary.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'project_summary'
    
    # Export the DataFrame to the SQLite database
    lib_df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

    # archive the current project_summary.csv
    Path(PROJECT_DIR /
        "project_summary.csv").rename(ARCHIV_DIR / f"archive_project_summary_{date}.csv")
    Path(ARCHIV_DIR / f"archive_project_summary_{date}.csv").touch()

    # create updated library info file
    lib_df.to_csv(PROJECT_DIR / 'project_summary.csv', index=False)

    return 
#########################
#########################


def main():
    """
    Main function to conclude the FA analysis and generate an ESP smear file.
    1. Sets up folder organization and global variables.
    2. Determines which FA analysis results to use (1st or 2nd attempt
    """
    # #########################
    # set up folder organiztion
    # #########################

    # current_dir = os.path.basename(os.getcwd())

    global PROJECT_DIR, LIB_DIR, FIRST_FA_DIR, SECOND_FA_DIR
    global ARCHIV_DIR, POOL_DIR, SMEAR_DIR, date

    PROJECT_DIR = Path.cwd()

    LIB_DIR = PROJECT_DIR / "1_make_library_analyze_fa"

    FIRST_FA_DIR = LIB_DIR / "B_first_attempt_fa_result"

    SECOND_FA_DIR = LIB_DIR / "D_second_attempt_fa_result"

    ARCHIV_DIR = PROJECT_DIR / "archived_files"

    POOL_DIR = PROJECT_DIR / "2_pooling"

    SMEAR_DIR = POOL_DIR / "A_smear_file_for_ESP_upload"


    # get current date and time, will add to archive database file name
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


    # determine if we should use 1st or 2nd attempt fa results
    # based on which folder exists and contains the appropriate
    # updated_fa_analysis_summary.txt file
    updated_file_name = findUpdateFAFile()

    # add library pass/fail results from updated_X_fa_analysis.txt
    # to the project_summary.csv file
    # pass/fail results may have been manually modified
    lib_df = updateLibInfo(updated_file_name)

    # select plates and wells to use for pooling based on
    # pass/fail results and add 'Pool' columns to project_summary_df
    final_df = selectPlateForPooling(lib_df)

    # generate ESP smear file for clarity upload using 'Pool' columns
    # in final_df
    generateSmearFile(final_df)

    # create sqlite database file
    createSQLdb(final_df)

    print("\n✓ FA analysis concluded successfully!")
    print("✓ ESP smear file generated for upload")
    
    # Create success marker for workflow manager integration
    create_success_marker()


if __name__ == "__main__":
    main()
