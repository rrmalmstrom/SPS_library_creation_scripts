#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python SPS_rework_first_attempt_NEW.py

# Script automatically looks for updated_fa_analysis_summary.txt in the B_first_attempt_fa_result directory


import sys
import string
from datetime import datetime
from pathlib import Path
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


# define list of destination well positions for a 96-well
well_list_96w = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']


PROJECT_DIR = Path.cwd()

MAKE_DIR = PROJECT_DIR / "1_make_library_analyze_fa"

FIRST_DIR = MAKE_DIR / "B_first_attempt_fa_result"

ARCHIV_DIR = PROJECT_DIR / "archived_files"


SECOND_ATMPT_DIR = MAKE_DIR / "C_second_attempt_make_lib"

SECOND_ATMPT_DIR.mkdir(parents=True, exist_ok=True)

ECHO_DIR = SECOND_ATMPT_DIR / "echo_transfer_files"

ECHO_DIR.mkdir(parents=True, exist_ok=True)

INDEX_DIR = SECOND_ATMPT_DIR / "illumina_index_transfer_files"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

FTRAN_DIR = SECOND_ATMPT_DIR / "fa_transfer_files"

FTRAN_DIR.mkdir(parents=True, exist_ok=True)

FA_DIR = SECOND_ATMPT_DIR / "FA_input_files"

FA_DIR.mkdir(parents=True, exist_ok=True)

SECOND_FA_DIR = MAKE_DIR / "D_second_attempt_fa_result"

SECOND_FA_DIR.mkdir(parents=True, exist_ok=True)


##########################
##########################
def readSQLdb():
    """
    Read the project summary database and return as pandas DataFrame.
    
    Returns:
        pd.DataFrame: Complete project summary data from the SQLite database
        
    Raises:
        FileNotFoundError: If project_summary.db doesn't exist
        sqlalchemy.exc.DatabaseError: If database connection fails
    """
    # path to sqlite db lib_info.db
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
def updateLibInfo():
    # create df from fa_analysis_summary.txt file
    reduced_df = pd.read_csv(FIRST_DIR / "updated_fa_analysis_summary.txt", sep='\t', header=0)

    reduced_df['Redo_whole_plate'] = reduced_df['Redo_whole_plate'].fillna('')

    # read projet_summary.db sql db
    sql_df = readSQLdb()

    sql_df = sql_df.merge(reduced_df, how='outer', left_on=[
                          'sample_id','Destination_Plate_Barcode'], right_on=['sample_id','Destination_Plate_Barcode'], suffixes=('', '_y'))

    # remove redundant columns after merging
    sql_df.drop(sql_df.filter(regex='_y$').columns, axis=1, inplace=True)

    return sql_df
##########################
##########################



#########################
#########################
def createSQLdb(project_df, date):
    
    Path(PROJECT_DIR /
         "project_summary.db").rename(ARCHIV_DIR / f"archive_project_summary_{date}.db")
    Path(ARCHIV_DIR / f"archive_project_summary_{date}.db").touch()

    sql_db_path = PROJECT_DIR /'project_summary.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 

    # Specify the table name and database engine
    table_name = 'project_summary'
    
    # Export the DataFrame to the SQLite database
    project_df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

    return
#########################
#########################



##########################
##########################
# update project database with samples the went into Library creation
def updateProjectDatabase(lib_df, wp_redo_df):

    # get current date and time, will add to archive database file name
    date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

    project_df = pd.merge(lib_df, wp_redo_df, left_on=['sample_id'],right_on=['sample_id'], how='outer', suffixes=('', '_y'))

    # remove redundant columns after merging
    project_df.drop(project_df.filter(regex='_y$').columns, axis=1, inplace=True)

    # call function to archive old project_summary.db and generate new one
    createSQLdb(project_df, date)

    # archive .csv veresion of project_summary
    Path(PROJECT_DIR /
         "project_summary.csv").rename(ARCHIV_DIR / f"archive_project_summary_{date}.csv")
    Path(ARCHIV_DIR / f"archive_project_summary_{date}.csv").touch()

    # create updated project database file
    project_df.to_csv(PROJECT_DIR / 'project_summary.csv', index=False)
    
##########################
##########################


##########################
##########################
def noRework(lib_df, wp_redo_df):
    """
    Handle case where no rework is needed.
    Inform user to use workflow manager to skip rework step.
    """
    print("\n" + "="*60)
    print("NO REWORK DETECTED")
    print("="*60)
    print("All libraries passed on the first attempt.")
    print("No plates need to be reworked.")
    print("\nNEXT STEPS:")
    print("1. Go to your workflow manager")
    print("2. Undo the rework decision step")
    print("3. Select 'No Rework Needed' option")
    print("4. Proceed directly to conclude FA analysis")
    print("="*60)
    
    # # Create success marker for workflow manager integration
    # create_success_marker()
    
    sys.exit()

##########################
##########################



##########################
##########################
def getReworkFiles(lib_df):
    """
    Identify plates that need rework and prepare rework DataFrame.
    
    Args:
        lib_df (pd.DataFrame): Library DataFrame with FA analysis results
        
    Returns:
        pd.DataFrame: DataFrame containing only samples from plates needing rework,
                     with additional columns for rework plate IDs and parameters
                     
    Side Effects:
        - Calls noRework() and exits if no plates need rework
        - Prompts user for dilution factor input
    """
    # get list of library plates that need whole palte redo
    whole_plate_redo = lib_df[lib_df['Redo_whole_plate'] == True]['Destination_Plate_Barcode'].unique().tolist()
    
    wp_redo_df = lib_df[lib_df['Destination_Plate_Barcode'].isin(
        whole_plate_redo)].copy()
    
    # terminate script if no rework necessary
    if wp_redo_df.shape[0] == 0:
        noRework(lib_df,wp_redo_df)


    # create empty column
    wp_redo_df['Redo_Destination_Plate_Barcode'] = ""

    # add new destination plate ID for reworked plates
    for wp in whole_plate_redo:
        
        # # parse first row entry for "Destination_ID" to get base ID without "-#"
        # # this get based destination barcode ID
        # my_destbc = my_lib_df['Destination_Plate_Barcode'].iloc[0].split(".")      
        my_destbc = wp.split(".")
        
        if len(my_destbc) == 2:
            my_next_plate_num = int(my_destbc[1]) + 1
        else:
            my_next_plate_num = 2
        
        wp_redo_df.loc[wp_redo_df['Destination_Plate_Barcode'] == wp, 'Redo_Destination_Plate_Barcode'] = my_destbc[0] + "." + str(my_next_plate_num)

    # add new well positions for rework plates.  These are 384well format
    wp_redo_df['Redo_Destination_Well'] = wp_redo_df['Destination_Well']
    
    # add new well positions for FA plates in 96well format
    wp_redo_df['Redo_FA_Well'] = wp_redo_df['FA_Well']
    
    # use same index set from original plate for rework plate
    wp_redo_df['Redo_Illumina_index_set'] = wp_redo_df['Illumina_index_set']
    
    wp_redo_df['Redo_Illumina_index'] = wp_redo_df['Illumina_index']
    
    # ask user the fold dilution used to set up FA plate
    dilution_factor = float(input(
        "\n\n What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): ") or 5)
    
    wp_redo_df['Redo_dilution_factor'] = dilution_factor
    
    return wp_redo_df
##########################
##########################



##########################
##########################
def makeEchoFiles(wp_redo_df):

    echo_df = wp_redo_df.copy()
    
    # create two copies of subsets of import_df
    echo_df = echo_df[['plate_id', 'echo_id', 'source_well',
                           'Redo_Destination_Plate_Barcode', 'Redo_Destination_Well']]
    
    echo_df['Source Plate Name'] = echo_df['plate_id']
    echo_df['Source Plate Barcode'] = echo_df['echo_id']
    
    echo_df['Destination Plate Name'] = echo_df['Redo_Destination_Plate_Barcode']
    
    echo_df['Destination_Plate_Barcode'] = echo_df['Redo_Destination_Plate_Barcode']
    

    echo_df['Source Row'] = echo_df['source_well'].astype(
        str).str[0]
    echo_df['Source Column'] = echo_df['source_well'].astype(
        str).str[1:]

    echo_df['Source Row'] = echo_df['Source Row'].apply(
        lambda x: 1 + string.ascii_uppercase.index(x))


    echo_df['Destination Row'] = echo_df['Redo_Destination_Well'].astype(
        str).str[0]
    echo_df['Destination Column'] = echo_df['Redo_Destination_Well'].astype(
        str).str[1:]

    echo_df['Destination Row'] = echo_df['Destination Row'].apply(
        lambda x: 1 + string.ascii_uppercase.index(x))

    echo_df['Transfer Volume'] = 500

    # convert row and column values to integers to aid in df sorting
    echo_df['Destination Column'] = echo_df['Destination Column'].astype(int)
    echo_df['Destination Row'] = echo_df['Destination Row'].astype(int)

    # # sort dataframe
    # echo_df.sort_values(by=['Destination_ID', 'sorter', 'Source_ID',
    #                           'Destination_col', 'Destination_row'], inplace=True)

    # sort dataframe
    echo_df.sort_values(by=['Destination_Plate_Barcode', 'Destination Column', 'Destination Row'], inplace=True)


    # rearrange columns into final order
    echo_df = echo_df[['Source Plate Name',	'Source Plate Barcode',	'Source Row',	'Source Column',
                       'Destination Plate Name',	'Destination_Plate_Barcode',	'Destination Row',	'Destination Column',	'Transfer Volume']]

    dest_list = echo_df['Destination_Plate_Barcode'].unique().tolist()

    # create echo transfer files
    for d in dest_list:
        tmp_df = echo_df.loc[echo_df['Destination_Plate_Barcode'] == d].copy()

        # create echo transfer file
        tmp_df.to_csv(ECHO_DIR /
                      f'REDO_echo_transfer_{d}.csv', index=False)
        


    return echo_df, dest_list
##########################
##########################



#########################
#########################
def createIllumDataframe(wp_redo_df):

    illum_df = wp_redo_df[['Redo_Destination_Plate_Barcode',
                          'Redo_Destination_Well', 'Redo_FA_Well','Redo_Illumina_index_set']].copy()

    # adjuste volume of primer addition based on tagementation reactions size
    illum_df['Primer_volume_(uL)'] = 2

    illum_df['Illumina_source_well'] = illum_df['Redo_FA_Well']

    illum_df = illum_df.rename(
        columns={'Redo_Destination_Well': 'Lib_plate_well', 'Redo_Destination_Plate_Barcode': 'Lib_plate_ID', 'Redo_Illumina_index_set':'Illumina_index_set'})

    # rearrange column order
    illum_column_list = ['Illumina_index_set',
                         'Illumina_source_well', 'Lib_plate_ID', 'Lib_plate_well', 'Primer_volume_(uL)']

    illum_df = illum_df.reindex(columns=illum_column_list)

    return illum_df
#########################
#########################




#########################
#########################
def createFAdataframe(wp_redo_df):

    FA_df = wp_redo_df[['Redo_FA_Well',
                        'Redo_Destination_Plate_Barcode', 'sample_id']].copy()
    
    FA_df['sample_id'] = FA_df['sample_id'].astype(str)


    FA_df['name'] = FA_df[['Redo_Destination_Plate_Barcode', 'sample_id', 'Redo_FA_Well']].agg(
        '_'.join, axis=1)

    # drop unecessary columns so only have df with 'Destination_Well', 'Destination_ID', and 'name'
    FA_df.drop(['sample_id'], inplace=True, axis=1)

    return FA_df
#########################
#########################


#########################
#########################
def makeFAfiles(FA_df, dest_list, well_list_96w):

    for d in dest_list:
        # make df with single column of data.  Column contains all wells in 96-well plate
        tmp_fa_df = pd.DataFrame(well_list_96w)

        tmp_fa_df.columns = ["Well"]

        tmp_fa_df = tmp_fa_df.merge(FA_df.loc[FA_df['Redo_Destination_Plate_Barcode'] == d], how='outer', left_on=['Well'],
                                    right_on=['Redo_FA_Well'])

        # updated index so begins at 1 instead of 0.  Index column will be added to FA input file
        tmp_fa_df.index = range(1, tmp_fa_df.shape[0]+1)

        tmp_fa_df.drop(['Redo_Destination_Plate_Barcode', 'Redo_FA_Well'],
                       inplace=True, axis=1)

        tmp_fa_df['name'] = tmp_fa_df['name'].fillna('empty_well')

        tmp_fa_df.loc[tmp_fa_df.Well == 'H12', 'name'] = "ladder_1"

        # tmp_fa_df.loc[tmp_fa_df.Well == 'A1', 'name'] = "LibStd_A1"

        # tmp_fa_df.loc[tmp_fa_df.Well == 'A12', 'name'] = "LibStd_A12"

        # tmp_fa_df.loc[tmp_fa_df.Well == 'H1', 'name'] = "LibStd_H1"

        tmp_fa_df.to_csv(FA_DIR / f'FA_upload_{d}.csv', index=True, header=False)

#########################
#########################


#########################
#########################
def makeIlluminaFiles(illum_df, dest_list):
    # create illumin index transfer files
    for d in dest_list:
        
        tmp_name = d.replace(".","-")
        
        
        tmp_illum_df = illum_df.loc[illum_df['Lib_plate_ID'] == d].copy()

        # add "h" prefix to lib plate ID because barcode label on plate side read by
        # hamilton scanner has "h" prefix
        tmp_illum_df['Lib_plate_ID'] = "h" + \
            tmp_illum_df['Lib_plate_ID'].astype(str)

        # create illumina index transfer file
        tmp_illum_df.to_csv(INDEX_DIR / f'Illumina_index_transfer_{tmp_name}.csv', index=False)
        
        
#########################
#########################


#########################
#########################
def makeBarcodeLabels(wp_redo_df, dest_list):


    # this was older format for bartender templates.  The newer version below changes "/" to "\"
    # in the path to the template files  AF="*"
    # x = '%BTW% /AF="//BARTENDER/shared/templates/ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'

    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\BARTENDER\shared\\templates\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    bc_file = open(SECOND_ATMPT_DIR / "BARTENDER_Redo_Library_FA_plates.txt", "w")

    bc_file.writelines(x)

    # reversse sort the dest_list
    dest_list.reverse()
    
    
    # for p in dest_list:
    #     bc_file.writelines(f'{p}F,"FA.run {p}F"\r\n')  
    
    # bc_file.writelines(',\r\n')
    
    # for p in dest_list:
    #     bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
  
    
    # bc_file.writelines(',\r\n')

    # add barcodes of library destination plates, dna source plates
    for p in dest_list:

        bc_file.writelines(f'{p}F,"FA.run {p}F"\r\n')

        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
        
        bc_file.writelines(f'h{p},"     h{p}"\r\n')
        
        bc_file.writelines(f'{p},"SPS.lib.plate {p}"\r\n')

        bc_file.writelines(',\r\n')
      
        



    bc_file.close()
    
   
    
    
#########################
#########################



#########################
#########################
def makeThreshold(wp_redo_df, dest_list):

    
    plate_dict = dict(zip(wp_redo_df['Redo_Destination_Plate_Barcode'],wp_redo_df['Redo_dilution_factor']))
    
    
    thresh_df = pd.DataFrame(list(plate_dict.items()))
    
    
    thresh_df.columns=['Destination_plate','dilution_factor']
  
    # add blan column
    thresh_df['DNA_conc_threshold_(nmol/L)'] = ""
  
    # add minimum library size to be used in FA analysis thresholds later
    thresh_df['Size_theshold_(bp)'] = 530
    
    # thresh_df['dilution_factor'] = ""
  
    # make list of column  headers to rearrange by column
    thresh_col_list = ['Destination_plate',
                        'DNA_conc_threshold_(nmol/L)', 'Size_theshold_(bp)', 'dilution_factor']

    thresh_df = thresh_df.reindex(columns=thresh_col_list)

    # create thresholds.txt file for use in later FA analysis
    thresh_df.to_csv(SECOND_FA_DIR / 'thresholds.txt', index=False, sep='\t')

    return
#########################
#########################




#########################
#########################
def makeDilution(wp_redo_df):
    
    
    
    dilution_df = wp_redo_df[['Redo_Destination_Plate_Barcode','Redo_Destination_Well','Redo_FA_Well','Redo_dilution_factor']].copy()
    
    # rename columns to match dilution transfer file format
    dilution_df = dilution_df.rename(columns={'Redo_Destination_Plate_Barcode' : 'Library_Plate_Barcode', 'Redo_Destination_Well' : 'Library_Well','Redo_FA_Well':'FA_Well'})

    # make column with FA barcode by appending "F" to libary barcode
    dilution_df['FA_Plate_Barcode'] = dilution_df['Library_Plate_Barcode']+"F"
    
    # make column for dilution plate barcode by appending "D" to libary barcode
    dilution_df['Dilution_Plate_Barcode'] = dilution_df['Library_Plate_Barcode']+"D"
    

    dilution_df['Nextera_Vol_Add'] = 30
    
    
    dilution_df['FA_Vol_Add'] = 2.4
    
    dilution_df['Dilution_Vol'] = 2.4
    
    
    # calculate the volume of  buffer that should be added to the dilution plate
    dilution_df['Dilution_Plate_Preload'] = np.ceil((dilution_df['Redo_dilution_factor']-1) * dilution_df['FA_Vol_Add'])
    
    # calculated the total amount of buffer to be aspirated before pre-loading
    # the dilution plate and topping up the Nextera plate
    dilution_df['Total_buffer_aspiration'] = dilution_df['Nextera_Vol_Add'] + dilution_df['Dilution_Plate_Preload']
    
    # rearrange column order
    dilution_column_list = ['Library_Plate_Barcode','Dilution_Plate_Barcode','FA_Plate_Barcode','Library_Well','FA_Well',	'Nextera_Vol_Add',	'Dilution_Vol','FA_Vol_Add','Dilution_Plate_Preload','Total_buffer_aspiration']

    dilution_df = dilution_df.reindex(columns=dilution_column_list)
   

    return dilution_df
#########################
#########################


#########################
#########################
def makeDilutionFile(dilution_df, dest_list):
    # create echo transfer files
    for d in dest_list:
        tmp_df = dilution_df.loc[dilution_df['Library_Plate_Barcode'] == d].copy(
        )
        
        adj_plate_name = d.replace(".","-")

        # had "h" prefix to library plate for reading barcode on Hamilton Star
        tmp_df['Library_Plate_Barcode'] = 'h'+tmp_df['Library_Plate_Barcode']

        # # create echo transfer file
        # tmp_df.to_csv(FTRAN_DIR / f'FA_plate_transfer_{d}.csv', index=False)
        
        # create echo transfer file
        tmp_df.to_csv(FTRAN_DIR / f'FA_plate_transfer_{adj_plate_name}.csv', index=False)

    return
#########################
#########################


#########################
# MAIN PROGRAM
##########################

def main():
    """
    Main function to process library rework for failed plates in the SPS workflow.
    
    This script processes Fragment Analyzer (FA) results to identify plates that need
    to be reworked due to failed library preparation. It generates all necessary
    transfer files and updates the project database.
    
    Workflow:
    1. Reads FA analysis results from updated_fa_analysis_summary.txt
    2. Identifies plates marked for whole plate rework (Redo_whole_plate == 'TRUE')
    3. Generates Echo transfer files for DNA transfers
    4. Creates Illumina index transfer files for post-tagmentation indexing
    5. Generates FA upload files for quality control analysis
    6. Creates barcode label files for plate identification
    7. Generates threshold files for FA analysis parameters
    8. Creates dilution transfer files for Hamilton liquid handler
    9. Updates project database with rework information
    
    Input Files:
    - {PROJECT_DIR}/1_make_library_analyze_fa/B_first_attempt_fa_result/updated_fa_analysis_summary.txt
    - {PROJECT_DIR}/project_summary.db
    
    Output Files:
    - Echo transfer files in C_second_attempt_make_lib/echo_transfer_files/
    - Illumina index files in C_second_attempt_make_lib/illumina_index_transfer_files/
    - FA upload files in C_second_attempt_make_lib/FA_input_files/
    - Barcode labels in C_second_attempt_make_lib/BARTENDER_Redo_Library_FA_plates.txt
    - Threshold file in D_second_attempt_fa_result/thresholds.txt
    - Dilution files in C_second_attempt_make_lib/fa_transfer_files/
    - Updated project_summary.db and project_summary.csv
    
    Exits:
    - If no input file found: sys.exit()
    - If no rework needed: calls noRework() which does sys.exit()
    """
    # path to updated_fa_analysis_summary.txt file from first FA analysis
    # this file may have been manually updated from the original reduced_fa_analysis_summary.txt
    updated_file_name = FIRST_DIR / "updated_fa_analysis_summary.txt"

    # check if the required input file exists
    if not updated_file_name.exists():
        print(f'\n\nCould not find file {updated_file_name} \nAborting\n\n')
        sys.exit()

    try:
        print("Starting SPS library rework process...")
        
        # add library pass/fail results from reduced_fa_analysis file
        # to the df created from project_summary.db
        print("Reading library information and FA analysis results...")
        lib_df = updateLibInfo()

        # generate df with just plates needing whole plate rework
        print("Identifying plates that need rework...")
        wp_redo_df = getReworkFiles(lib_df)

        # make df that will be used ot create echo transfer files, then creat echo transfer files
        print("Creating Echo transfer files...")
        echo_df, dest_list = makeEchoFiles(wp_redo_df)

        # create df just for making Illumin index transfer files for loading indexes after tagmentation reaction
        print("Creating Illumina index transfer files...")
        illum_df = createIllumDataframe(wp_redo_df)

        # make FA_df for generating FA files
        print("Creating FA upload files...")
        FA_df = createFAdataframe(wp_redo_df)

        # make upload files for FA runs
        makeFAfiles(FA_df, dest_list, well_list_96w)

        # make transfer files for adding Illumina indexes
        makeIlluminaFiles(illum_df, dest_list)

        # make .txt for printing barcodes of echo, library, FA, and dilution plates
        print("Creating barcode label files...")
        makeBarcodeLabels(wp_redo_df, dest_list)

        # make threshold.txt file for FA output analysis in next step of SIP wetlab process
        print("Creating threshold files...")
        makeThreshold(wp_redo_df,dest_list)

        # create df with info necessary for makign the FA plates
        print("Creating dilution transfer files...")
        dilution_df = makeDilution(wp_redo_df)

        # make hamilton transfer files for setting up FA plate
        makeDilutionFile(dilution_df, dest_list)

        # updated the project_summary.csv file with info about plates needing rework
        print("Updating project database...")
        updateProjectDatabase(lib_df, wp_redo_df)
        
        print(f"\n✓ Script completed successfully!")
        print(f"✓ Processed {len(dest_list)} plates for rework")
        # print(f"✓ Files created in: \n{SECOND_ATMPT_DIR}")
        
        # Create success marker for workflow manager integration
        create_success_marker()
        
    except FileNotFoundError as e:
        print(f"\n✗ File not found error: {e}")
        print("Please check that all required input files exist.")
        sys.exit()
        
    except pd.errors.EmptyDataError as e:
        print(f"\n✗ Data file is empty or corrupted: {e}")
        print("Please check the FA analysis summary file.")
        sys.exit()
        
    except KeyError as e:
        print(f"\n✗ Missing required column in data: {e}")
        print("Please check that the FA analysis file has all required columns.")
        sys.exit()
        
    except Exception as e:
        print(f"\n✗ Unexpected error occurred: {e}")
        print("Please check the error message above and contact support if needed.")
        import traceback
        traceback.print_exc()
        sys.exit()


if __name__ == "__main__":
    main()


