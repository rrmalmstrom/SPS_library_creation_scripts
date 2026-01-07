#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 13:53:21 2024

@author: RRMalmstrom
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python rework_first_attempt.py <updated_fa_analysis_summary.txt>

# sys.argv[1] = manually updated version of fa_analysis_summary.txt generated from first_FA.output.analysis.py

import pandas as pd
import numpy as np
import sys
import os
import math
import string
from datetime import datetime
from pathlib import Path
from os.path import exists as file_exists
from stat import S_IREAD, S_IRGRP, S_IROTH
from sqlalchemy import create_engine


# define list of destination well positions for a 96-well
well_list_96w = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']

# define list of destination well positions for a 96-well plate with empty corners
well_list_96w_emptycorner = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                             'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                             'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                             'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                             'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']




##########################
##########################
def readSQLdb():

    # # path to sqlite db lib_info.db
    # sql_db_path = f'{my_prjct_dir}/lib_info.db'
    
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
    reduced_df = pd.read_csv(sys.argv[1], sep='\t', header=0)

    reduced_df['Redo_whole_plate'] = reduced_df['Redo_whole_plate'].fillna('')

    # lib_df = pd.read_csv(PROJECT_DIR / "project_summary.csv", header=0)
    
    # read projet_summary.db sql db
    lib_df = readSQLdb()

    lib_df = lib_df.merge(reduced_df, how='outer', left_on=[
                          'sample_id','Destination Plate Barcode'], right_on=['sample_id','Destination Plate Barcode'], suffixes=('', '_y'))
    
    # # updated the pass/fail results in Passed_library using values from updated_fa_analysis_summary.txt
    # lib_df['Passed_library'] = lib_df['Passed_library_y']

    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)

    # # remove unnecessary columne 'FA_Well'
    # lib_df.drop(['FA_Well'], inplace=True, axis=1)

    # # sort df based on sample and fraction number in case user manually
    # # changed sorting when generated updated_fa_analysis_summary.txt
    # lib_df.sort_values(by=['Sample Barcode', 'Fraction #'], inplace=True)

    return lib_df
##########################
##########################



#########################
#########################
def createSQLdb(project_df, date):
    
    # # make copy of current version so lib_info.db to be archived
    # # the copy will be moved to archive folder at a later step
    # shutil.copy(PROJECT_DIR /'lib_info.db', PROJECT_DIR / 'archive_lib_info.db')
    
    Path(PROJECT_DIR /
         "project_summary.db").rename(ARCHIV_DIR / f"archive_project_summary_{date}.db")
    Path(ARCHIV_DIR / f"archive_project_summary_{date}.db").touch()


    sql_db_path = PROJECT_DIR /'project_summary.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'project_summary'
    
    # Export the DataFrame to the SQLite database
    project_df.to_sql(table_name, engine, if_exists='replace', index=False) 


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
    
    # # make the project_summary.csv read only
    # os.chmod(PROJECT_DIR / 'project_summary.csv', S_IREAD|S_IRGRP|S_IROTH)  

    
##########################
##########################





##########################
##########################
def noRework(lib_df, wp_redo_df):
    # bypass rework steps and secound round of FA analysis
    
    # add empyt columns that would have been generated by rework and are expected for later scripts
    lib_df[['Redo_whole_plate',	'Redo_Destination_ID','Redo_Destination_Well',	'Redo_FA_Well',	'Redo_Illumina_index_set',	'Redo_Illumina_index','Redo_dilution_factor','Redo_ng/uL','Redo_nmole/L','	Redo_Avg. Size']] = ''
    
    lib_df['Redo_Passed_library'] = 0
    
    
    # find samples that failed both attempts at library creation
    # by adding Passed and Redo_Passed columns.  Treat NaN as 0 for summing
    lib_df['Total_passed_attempts'] = lib_df['Passed_library'].fillna(0) + \
        lib_df['Redo_Passed_library'].fillna(0)
        
    
    # 'pool' columns identify the specific libs that will move forward with pooling at a later step
    # setting 'pool' columns to values from first round fa analysis
    lib_df['Pool_source_plate'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['Destination Plate Barcode'],"")

    lib_df['Pool_source_well'] = np.where(lib_df['Total_passed_attempts'] > 0,lib_df['Destination_Well'],"")

    lib_df['Pool_Illumina_index_set'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['Illumina_index_set'],"")

    lib_df['Pool_Illumina_index'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['Illumina_index'], "")

    lib_df['Pool_DNA_conc_ng/uL'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['ng/uL'],"")

    lib_df['Pool_nmole/L'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['nmole/L'], "")

    lib_df['Pool_Avg. Size'] = np.where(lib_df['Total_passed_attempts'] > 0, lib_df['Avg. Size'],"")
    
    lib_df['Pool_dilution_factor'] = np.where(lib_df['Total_passed_attempts'] >0, lib_df['dilution_factor'], "")
    

    

    # the clarity lib creation file requires an index even if library failed
    lib_df['Pool_Illumina_index'] = np.where(lib_df['Total_passed_attempts'] == 0, lib_df['Illumina_index'], lib_df['Pool_Illumina_index'])
    
    # # make copy of updated_fa_analysis_summary.txt in directory
    # # where the fa analysis of reworked libs would go
    # lib_df.to_csv(SECOND_FA_DIR / 'updated_2nd_fa_analysis_summary.txt', sep='\t', index=False)
    
    updateProjectDatabase(lib_df, wp_redo_df)
    
    print("\n No library rework is needeed. Go to folder 2_pooling/A_fill_clarity_lib_creation_file  and run script 'SPS_fill_clarity_lib_creation_sheet' after downloading the library creation .xlsx files from Clarity\n\n")
    
    
    sys.exit()


##########################
##########################



##########################
##########################
def getReworkFiles(lib_df):

    # get list of library plates that need whole palte redo
    whole_plate_redo = lib_df[lib_df['Redo_whole_plate'] == True]['Destination Plate Barcode'].unique().tolist()
    
    wp_redo_df = lib_df[lib_df['Destination Plate Barcode'].isin(
        whole_plate_redo)].copy()
    
        
    # empty_list= []    


    # wp_redo_df = lib_df[lib_df['Destination Plate Barcode'].isin(empty_list)].copy()
    
    # terminate script if no rework necessary
    if wp_redo_df.shape[0] == 0:
        noRework(lib_df,wp_redo_df)


    # create empty column
    wp_redo_df['Redo_Destination_ID'] = ""

    # add new destination plate ID for reworked plates
    for wp in whole_plate_redo:
        
        # # parse first row entry for "Destination_ID" to get base ID without "-#"
        # # this get based destination barcode ID
        # my_destbc = my_lib_df['Destination Plate Barcode'].iloc[0].split(".")
        
        my_destbc = wp.split(".")
        
        if len(my_destbc) == 2:
            my_next_plate_num = my_destbc[1] + 1
        else:
            my_next_plate_num = 2
        
        
        wp_redo_df['Redo_Destination_ID'].loc[wp_redo_df['Destination Plate Barcode']
                                              == wp] = my_destbc[0] + "." + str(my_next_plate_num)


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


# ##########################
# ##########################
# def addIlluminaIndex(lib_df, wp_redo_df):

#     adapt_set_5 = ['5A01i7-7A01i5',	'5B01i7-7B01i5',	'5C01i7-7C01i5',	'5D01i7-7D01i5',	'5E01i7-7E01i5',	'5F01i7-7F01i5',	'5G01i7-7G01i5',	'5H01i7-7H01i5',	'5A02i7-7A02i5',	'5B02i7-7B02i5',	'5C02i7-7C02i5',	'5D02i7-7D02i5',	'5E02i7-7E02i5',	'5F02i7-7F02i5',	'5G02i7-7G02i5',	'5H02i7-7H02i5',	'5A03i7-7A03i5',	'5B03i7-7B03i5',	'5C03i7-7C03i5',	'5D03i7-7D03i5',	'5E03i7-7E03i5',	'5F03i7-7F03i5',	'5G03i7-7G03i5',	'5H03i7-7H03i5',	'5A04i7-7A04i5',	'5B04i7-7B04i5',	'5C04i7-7C04i5',	'5D04i7-7D04i5',	'5E04i7-7E04i5',	'5F04i7-7F04i5',	'5G04i7-7G04i5',	'5H04i7-7H04i5',	'5A05i7-7A05i5',	'5B05i7-7B05i5',	'5C05i7-7C05i5',	'5D05i7-7D05i5',	'5E05i7-7E05i5',	'5F05i7-7F05i5',	'5G05i7-7G05i5',	'5H05i7-7H05i5',	'5A06i7-7A06i5',	'5B06i7-7B06i5',	'5C06i7-7C06i5',	'5D06i7-7D06i5',	'5E06i7-7E06i5',	'5F06i7-7F06i5',	'5G06i7-7G06i5',	'5H06i7-7H06i5',
#                    '5A07i7-7A07i5',	'5B07i7-7B07i5',	'5C07i7-7C07i5',	'5D07i7-7D07i5',	'5E07i7-7E07i5',	'5F07i7-7F07i5',	'5G07i7-7G07i5',	'5H07i7-7H07i5',	'5A08i7-7A08i5',	'5B08i7-7B08i5',	'5C08i7-7C08i5',	'5D08i7-7D08i5',	'5E08i7-7E08i5',	'5F08i7-7F08i5',	'5G08i7-7G08i5',	'5H08i7-7H08i5',	'5A09i7-7A09i5',	'5B09i7-7B09i5',	'5C09i7-7C09i5',	'5D09i7-7D09i5',	'5E09i7-7E09i5',	'5F09i7-7F09i5',	'5G09i7-7G09i5',	'5H09i7-7H09i5',	'5A10i7-7A10i5',	'5B10i7-7B10i5',	'5C10i7-7C10i5',	'5D10i7-7D10i5',	'5E10i7-7E10i5',	'5F10i7-7F10i5',	'5G10i7-7G10i5',	'5H10i7-7H10i5',	'5A11i7-7A11i5',	'5B11i7-7B11i5',	'5C11i7-7C11i5',	'5D11i7-7D11i5',	'5E11i7-7E11i5',	'5F11i7-7F11i5',	'5G11i7-7G11i5',	'5H11i7-7H11i5',	'5A12i7-7A12i5',	'5B12i7-7B12i5',	'5C12i7-7C12i5',	'5D12i7-7D12i5',	'5E12i7-7E12i5',	'5F12i7-7F12i5',	'5G12i7-7G12i5',	'5H12i7-7H12i5']

#     adapt_set_6 = ['6A01i7-8A01i5',	'6B01i7-8B01i5',	'6C01i7-8C01i5',	'6D01i7-8D01i5',	'6E01i7-8E01i5',	'6F01i7-8F01i5',	'6G01i7-8G01i5',	'6H01i7-8H01i5',	'6A02i7-8A02i5',	'6B02i7-8B02i5',	'6C02i7-8C02i5',	'6D02i7-8D02i5',	'6E02i7-8E02i5',	'6F02i7-8F02i5',	'6G02i7-8G02i5',	'6H02i7-8H02i5',	'6A03i7-8A03i5',	'6B03i7-8B03i5',	'6C03i7-8C03i5',	'6D03i7-8D03i5',	'6E03i7-8E03i5',	'6F03i7-8F03i5',	'6G03i7-8G03i5',	'6H03i7-8H03i5',	'6A04i7-8A04i5',	'6B04i7-8B04i5',	'6C04i7-8C04i5',	'6D04i7-8D04i5',	'6E04i7-8E04i5',	'6F04i7-8F04i5',	'6G04i7-8G04i5',	'6H04i7-8H04i5',	'6A05i7-8A05i5',	'6B05i7-8B05i5',	'6C05i7-8C05i5',	'6D05i7-8D05i5',	'6E05i7-8E05i5',	'6F05i7-8F05i5',	'6G05i7-8G05i5',	'6H05i7-8H05i5',	'6A06i7-8A06i5',	'6B06i7-8B06i5',	'6C06i7-8C06i5',	'6D06i7-8D06i5',	'6E06i7-8E06i5',	'6F06i7-8F06i5',	'6G06i7-8G06i5',	'6H06i7-8H06i5',
#                    '6A07i7-8A07i5',	'6B07i7-8B07i5',	'6C07i7-8C07i5',	'6D07i7-8D07i5',	'6E07i7-8E07i5',	'6F07i7-8F07i5',	'6G07i7-8G07i5',	'6H07i7-8H07i5',	'6A08i7-8A08i5',	'6B08i7-8B08i5',	'6C08i7-8C08i5',	'6D08i7-8D08i5',	'6E08i7-8E08i5',	'6F08i7-8F08i5',	'6G08i7-8G08i5',	'6H08i7-8H08i5',	'6A09i7-8A09i5',	'6B09i7-8B09i5',	'6C09i7-8C09i5',	'6D09i7-8D09i5',	'6E09i7-8E09i5',	'6F09i7-8F09i5',	'6G09i7-8G09i5',	'6H09i7-8H09i5',	'6A10i7-8A10i5',	'6B10i7-8B10i5',	'6C10i7-8C10i5',	'6D10i7-8D10i5',	'6E10i7-8E10i5',	'6F10i7-8F10i5',	'6G10i7-8G10i5',	'6H10i7-8H10i5',	'6A11i7-8A11i5',	'6B11i7-8B11i5',	'6C11i7-8C11i5',	'6D11i7-8D11i5',	'6E11i7-8E11i5',	'6F11i7-8F11i5',	'6G11i7-8G11i5',	'6H11i7-8H11i5',	'6A12i7-8A12i5',	'6B12i7-8B12i5',	'6C12i7-8C12i5',	'6D12i7-8D12i5',	'6E12i7-8E12i5',	'6F12i7-8F12i5',	'6G12i7-8G12i5',	'6H12i7-8H12i5']

#     adapt_set_7 = ['7A01i7-5A01i5',	'7B01i7-5B01i5',	'7C01i7-5C01i5',	'7D01i7-5D01i5',	'7E01i7-5E01i5',	'7F01i7-5F01i5',	'7G01i7-5G01i5',	'7H01i7-5H01i5',	'7A02i7-5A02i5',	'7B02i7-5B02i5',	'7C02i7-5C02i5',	'7D02i7-5D02i5',	'7E02i7-5E02i5',	'7F02i7-5F02i5',	'7G02i7-5G02i5',	'7H02i7-5H02i5',	'7A03i7-5A03i5',	'7B03i7-5B03i5',	'7C03i7-5C03i5',	'7D03i7-5D03i5',	'7E03i7-5E03i5',	'7F03i7-5F03i5',	'7G03i7-5G03i5',	'7H03i7-5H03i5',	'7A04i7-5A04i5',	'7B04i7-5B04i5',	'7C04i7-5C04i5',	'7D04i7-5D04i5',	'7E04i7-5E04i5',	'7F04i7-5F04i5',	'7G04i7-5G04i5',	'7H04i7-5H04i5',	'7A05i7-5A05i5',	'7B05i7-5B05i5',	'7C05i7-5C05i5',	'7D05i7-5D05i5',	'7E05i7-5E05i5',	'7F05i7-5F05i5',	'7G05i7-5G05i5',	'7H05i7-5H05i5',	'7A06i7-5A06i5',	'7B06i7-5B06i5',	'7C06i7-5C06i5',	'7D06i7-5D06i5',	'7E06i7-5E06i5',	'7F06i7-5F06i5',	'7G06i7-5G06i5',	'7H06i7-5H06i5',
#                    '7A07i7-5A07i5',	'7B07i7-5B07i5',	'7C07i7-5C07i5',	'7D07i7-5D07i5',	'7E07i7-5E07i5',	'7F07i7-5F07i5',	'7G07i7-5G07i5',	'7H07i7-5H07i5',	'7A08i7-5A08i5',	'7B08i7-5B08i5',	'7C08i7-5C08i5',	'7D08i7-5D08i5',	'7E08i7-5E08i5',	'7F08i7-5F08i5',	'7G08i7-5G08i5',	'7H08i7-5H08i5',	'7A09i7-5A09i5',	'7B09i7-5B09i5',	'7C09i7-5C09i5',	'7D09i7-5D09i5',	'7E09i7-5E09i5',	'7F09i7-5F09i5',	'7G09i7-5G09i5',	'7H09i7-5H09i5',	'7A10i7-5A10i5',	'7B10i7-5B10i5',	'7C10i7-5C10i5',	'7D10i7-5D10i5',	'7E10i7-5E10i5',	'7F10i7-5F10i5',	'7G10i7-5G10i5',	'7H10i7-5H10i5',	'7A11i7-5A11i5',	'7B11i7-5B11i5',	'7C11i7-5C11i5',	'7D11i7-5D11i5',	'7E11i7-5E11i5',	'7F11i7-5F11i5',	'7G11i7-5G11i5',	'7H11i7-5H11i5',	'7A12i7-5A12i5',	'7B12i7-5B12i5',	'7C12i7-5C12i5',	'7D12i7-5D12i5',	'7E12i7-5E12i5',	'7F12i7-5F12i5',	'7G12i7-5G12i5',	'7H12i7-5H12i5']

#     adapt_set_8 = ['8A01i7-6A01i5',	'8B01i7-6B01i5',	'8C01i7-6C01i5',	'8D01i7-6D01i5',	'8E01i7-6E01i5',	'8F01i7-6F01i5',	'8G01i7-6G01i5',	'8H01i7-6H01i5',	'8A02i7-6A02i5',	'8B02i7-6B02i5',	'8C02i7-6C02i5',	'8D02i7-6D02i5',	'8E02i7-6E02i5',	'8F02i7-6F02i5',	'8G02i7-6G02i5',	'8H02i7-6H02i5',	'8A03i7-6A03i5',	'8B03i7-6B03i5',	'8C03i7-6C03i5',	'8D03i7-6D03i5',	'8E03i7-6E03i5',	'8F03i7-6F03i5',	'8G03i7-6G03i5',	'8H03i7-6H03i5',	'8A04i7-6A04i5',	'8B04i7-6B04i5',	'8C04i7-6C04i5',	'8D04i7-6D04i5',	'8E04i7-6E04i5',	'8F04i7-6F04i5',	'8G04i7-6G04i5',	'8H04i7-6H04i5',	'8A05i7-6A05i5',	'8B05i7-6B05i5',	'8C05i7-6C05i5',	'8D05i7-6D05i5',	'8E05i7-6E05i5',	'8F05i7-6F05i5',	'8G05i7-6G05i5',	'8H05i7-6H05i5',	'8A06i7-6A06i5',	'8B06i7-6B06i5',	'8C06i7-6C06i5',	'8D06i7-6D06i5',	'8E06i7-6E06i5',	'8F06i7-6F06i5',	'8G06i7-6G06i5',	'8H06i7-6H06i5',
#                    '8A07i7-6A07i5',	'8B07i7-6B07i5',	'8C07i7-6C07i5',	'8D07i7-6D07i5',	'8E07i7-6E07i5',	'8F07i7-6F07i5',	'8G07i7-6G07i5',	'8H07i7-6H07i5',	'8A08i7-6A08i5',	'8B08i7-6B08i5',	'8C08i7-6C08i5',	'8D08i7-6D08i5',	'8E08i7-6E08i5',	'8F08i7-6F08i5',	'8G08i7-6G08i5',	'8H08i7-6H08i5',	'8A09i7-6A09i5',	'8B09i7-6B09i5',	'8C09i7-6C09i5',	'8D09i7-6D09i5',	'8E09i7-6E09i5',	'8F09i7-6F09i5',	'8G09i7-6G09i5',	'8H09i7-6H09i5',	'8A10i7-6A10i5',	'8B10i7-6B10i5',	'8C10i7-6C10i5',	'8D10i7-6D10i5',	'8E10i7-6E10i5',	'8F10i7-6F10i5',	'8G10i7-6G10i5',	'8H10i7-6H10i5',	'8A11i7-6A11i5',	'8B11i7-6B11i5',	'8C11i7-6C11i5',	'8D11i7-6D11i5',	'8E11i7-6E11i5',	'8F11i7-6F11i5',	'8G11i7-6G11i5',	'8H11i7-6H11i5',	'8A12i7-6A12i5',	'8B12i7-6B12i5',	'8C12i7-6C12i5',	'8D12i7-6D12i5',	'8E12i7-6E12i5',	'8F12i7-6F12i5',	'8G12i7-6G12i5',	'8H12i7-6H12i5']

#     # creat dict where key is index set# + well postion, and values is illumin index ID
#     dict_index = dict(zip(['5' + w for w in well_list_96w], adapt_set_5)
#                       ) | dict(zip(['6' + w for w in well_list_96w], adapt_set_6)) | dict(zip(['7' + w for w in well_list_96w], adapt_set_7)) | dict(zip(['8' + w for w in well_list_96w], adapt_set_8))

#     # create list of illumin index set numbers
#     ill_sets = ['5', '6', '7', '8']

#     dest_id_dict = {}
    
#     last_illum_set_num = len(lib_df['Destination Plate Barcode'].unique().tolist()) % len(ill_sets)

#     # get list of uniqued destination plate IDs
#     tmp_list = sorted(wp_redo_df['Redo_Destination_ID'].unique().tolist())

#     ## create dict were keys are destination plate IDs and values are illumin index set#
#     # the modulo is used because the number of destination plates might exceed the number
#     # of index sets, so the module wraps around ill_set list
#     # also use cnt+next_plate_num-1 so that the first illumina index used fo rework
#     # is the next in the list after last index used in first attempt at lib creation
#     for cnt, dp in enumerate(tmp_list):
#         id_set = str(ill_sets[(cnt+last_illum_set_num) % len(ill_sets)])
#         dest_id_dict[dp] = id_set

#     # add new column with illumina set # based on Destination ID by looking up in dict
#     wp_redo_df['Redo_Illumina_index_set'] = wp_redo_df['Redo_Destination_ID'].replace(
#         dest_id_dict)

#     # add new row that's a concat of the illumina index set and well postion
#     wp_redo_df['Redo_Illumina_index'] = wp_redo_df['Redo_Illumina_index_set'] + \
#         wp_redo_df['Redo_FA_Well']

#     # replace index set and well poistion wiht JGI illumina index ID using dict
#     wp_redo_df['Redo_Illumina_index'] = wp_redo_df['Redo_Illumina_index'].replace(
#         dict_index)

#     # add new row that's a concat of the illumina index set and well postion
#     wp_redo_df['Redo_Illumina_index_set'] = 'Nextera_Index-' + \
#         wp_redo_df['Redo_Illumina_index_set']

#     return wp_redo_df

# ##########################
# ##########################






##########################
##########################


def makeEchoFiles(wp_redo_df):

    # # create two copies of subsets of import_df
    # echo_df = wp_redo_df[['Plate Barcode', 'Source_row', 'Source_col',
    #                        'Destination_ID', 'Destination_row', 'Destination_col', 'DNA_transfer_vol_(nl)']].copy()
    
    echo_df = wp_redo_df.copy()
    
    # create two copies of subsets of import_df
    echo_df = echo_df[['Source Plate Name', 'Source_Well',
                           'Redo_Destination_ID', 'Redo_Destination_Well']]
    
    # # rename transfer volume headers
    # echo_df = echo_df.rename(columns={"Source Plate Name": "Source_ID"})
    
    echo_df['Source Plate Barcode'] = echo_df['Source Plate Name']
    
    echo_df['Destination Plate Name'] = echo_df['Redo_Destination_ID']
    
    echo_df['Destination Plate Barcode'] = echo_df['Redo_Destination_ID']
    

    echo_df['Source Row'] = echo_df['Source_Well'].astype(
        str).str[0]
    echo_df['Source Column'] = echo_df['Source_Well'].astype(
        str).str[1:]

    echo_df['Source Row'] = echo_df['Source Row'].apply(
        lambda x: 1 + string.ascii_uppercase.index(x))


    echo_df['Destination Row'] = echo_df['Redo_Destination_Well'].astype(
        str).str[0]
    echo_df['Destination Column'] = echo_df['Redo_Destination_Well'].astype(
        str).str[1:]

    echo_df['Destination Row'] = echo_df['Destination Row'].apply(
        lambda x: 1 + string.ascii_uppercase.index(x))

    echo_df['Transfer Volume'] = ''

    # convert row and column values to integers to aid in df sorting
    echo_df['Destination Column'] = echo_df['Destination Column'].astype(int)
    echo_df['Destination Row'] = echo_df['Destination Row'].astype(int)

    # # sort dataframe
    # echo_df.sort_values(by=['Destination_ID', 'sorter', 'Source_ID',
    #                           'Destination_col', 'Destination_row'], inplace=True)

    # sort dataframe
    echo_df.sort_values(by=['Destination Plate Barcode', 'Destination Column', 'Destination Row'], inplace=True)


    # rearrange columns into final order
    echo_df = echo_df[['Source Plate Name',	'Source Plate Barcode',	'Source Row',	'Source Column',
                       'Destination Plate Name',	'Destination Plate Barcode',	'Destination Row',	'Destination Column',	'Transfer Volume']]

    dest_list = echo_df['Destination Plate Barcode'].unique().tolist()

    # create echo transfer files
    for d in dest_list:
        tmp_df = echo_df.loc[echo_df['Destination Plate Barcode'] == d].copy()

        # create echo transfer file
        tmp_df.to_csv(ECHO_DIR /
                      f'REDO_echo_transfer_{d}.csv', index=False)
        


    return echo_df, dest_list
##########################
##########################



#########################
#########################
def createIllumDataframe(wo_redo_df):

    illum_df = wp_redo_df[['Redo_Destination_ID',
                          'Redo_Destination_Well', 'Redo_FA_Well','Redo_Illumina_index_set']].copy()

    # adjuste volume of primer addition based on tagementation reactions size
    illum_df['Primer_volume_(uL)'] = 2

    illum_df['Illumina_source_well'] = illum_df['Redo_FA_Well']

    illum_df = illum_df.rename(
        columns={'Redo_Destination_Well': 'Lib_plate_well', 'Redo_Destination_ID': 'Lib_plate_ID', 'Redo_Illumina_index_set':'Illumina_index_set'})

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
                        'Redo_Destination_ID', 'sample_id']].copy()
    
    FA_df['sample_id'] = FA_df['sample_id'].astype(str)


    FA_df['name'] = FA_df[['Redo_Destination_ID', 'sample_id', 'Redo_FA_Well']].agg(
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

        tmp_fa_df = tmp_fa_df.merge(FA_df.loc[FA_df['Redo_Destination_ID'] == d], how='outer', left_on=['Well'],
                                    right_on=['Redo_FA_Well'])

        # updated index so begins at 1 instead of 0.  Index column will be added to FA input file
        tmp_fa_df.index = range(1, tmp_fa_df.shape[0]+1)

        tmp_fa_df.drop(['Redo_Destination_ID', 'Redo_FA_Well'],
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


    bc_file = open("BARTENDER_Redo_Library_FA_plates.txt", "w")

    bc_file.writelines(x)

    # reversse sort the dest_list
    dest_list.reverse()
    
    
    for p in dest_list:
        bc_file.writelines(f'{p}F,"FA.run {p}F"\r\n')  
    
    bc_file.writelines(',\r\n')
    
    for p in dest_list:
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
  
    
    bc_file.writelines(',\r\n')

    # add barcodes of library destination plates, dna source plates
    for p in dest_list:
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
        
        bc_file.writelines(f'h{p},"     h{p}"\r\n')
        
        bc_file.writelines(f'{p},"SPS.lib.plate {p}"\r\n')
      
        



    bc_file.close()
    
    # move label files to new directory
    Path(FIRST_DIR / "BARTENDER_Redo_Library_FA_plates.txt").rename(SECOND_ATMPT_DIR / "BARTENDER_Redo_Library_FA_plates.txt")
   
    
    
#########################
#########################



#########################
#########################
def makeThreshold(wp_redo_df, dest_list):

    
    plate_dict = dict(zip(wp_redo_df['Redo_Destination_ID'],wp_redo_df['Redo_dilution_factor']))
    
    
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
    
    
    
    dilution_df = wp_redo_df[['Redo_Destination_ID','Redo_Destination_Well','Redo_FA_Well','Redo_dilution_factor']].copy()
    
    # rename columns to match dilution transfer file format
    dilution_df = dilution_df.rename(columns={'Redo_Destination_ID' : 'Library_Plate_Barcode', 'Redo_Destination_Well' : 'Library_Well','Redo_FA_Well':'FA_Well'})

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









##########################
# MAIN PROGRAM
##########################
# check if all required input files were provided and exist
if len(sys.argv) < 2:
    print('\n\nDid not provide all required input files. Aborting. \n\n')
    sys.exit()
elif (file_exists(sys.argv[1]) == 0):
    print(f'\n\nCould not find file {sys.argv[1]} \nAborting\n\n')
    sys.exit()

elif (sys.argv[1] != 'updated_fa_analysis_summary.txt'):
    print('Aborting.  Please provide file named updated_fa_anaylsis_summary.txt \n\n')
    sys.exit()


# get current working directory and its parent directory
crnt_dir = os.getcwd()
prnt_dir = os.path.dirname(crnt_dir)
prjct_dir = os.path.dirname(prnt_dir)


###########################
# set up folder organiztion
###########################

FIRST_DIR = Path.cwd()

MAKE_DIR = FIRST_DIR.parent

SECOND_ATMPT_DIR = MAKE_DIR / "C_second_attempt_make_lib"




ECHO_DIR = SECOND_ATMPT_DIR / "echo_transfer_files"

ECHO_DIR.mkdir(parents=True, exist_ok=True)

INDEX_DIR = SECOND_ATMPT_DIR / "illumina_index_transfer_files"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

FTRAN_DIR = SECOND_ATMPT_DIR / "fa_transfer_files"

FTRAN_DIR.mkdir(parents=True, exist_ok=True)



PROJECT_DIR = MAKE_DIR.parent

ARCHIV_DIR = PROJECT_DIR / "archived_files"

ARCHIV_DIR.mkdir(parents=True, exist_ok=True)

SECOND_FA_DIR = MAKE_DIR / "D_second_attempt_fa_result"

FA_DIR = SECOND_ATMPT_DIR / "FA_input_files"

FA_DIR.mkdir(parents=True, exist_ok=True)




# # create df from fa_analysis_summary.txt file
# lib_df = pd.read_csv("updated_fa_analysis_summary.txt", sep='\t',
#                      header=0, converters={'Sample Barcode': str, 'Fraction #': int})

# add library pass/fail results from reduced_fa_analysis file
# to the lib_info file
lib_df = updateLibInfo()


# # find the number of original FA plates and increment by 1
# next_plate_num = len(lib_df.Destination_ID.value_counts().index) + 1


# generate df with just plates needing whole plate rework
wp_redo_df = getReworkFiles(lib_df)


## no longer using this module for determining  the indexes used for rework
## Since only whole plate rework is allowed, the rework plates use the same
## indexes as the original plate

# # add Illumina indexes to rework df
# wp_redo_df = addIlluminaIndex(lib_df, wp_redo_df)


# make df that will be used ot create echo transfer files, then creat echo transfer files
echo_df, dest_list = makeEchoFiles(wp_redo_df)


# create df just for making Illumin index transfer files for loading indexes after tagmentation reaction
illum_df = createIllumDataframe(wp_redo_df)


# make FA_df for generating FA files
FA_df = createFAdataframe(wp_redo_df)

# make upload files for FA runs
makeFAfiles(FA_df, dest_list, well_list_96w)

# make transfer files for adding Illumina indexes
makeIlluminaFiles(illum_df, dest_list)


# make .txt for printing barcodes of echo, library, FA, and dilution plates
makeBarcodeLabels(wp_redo_df, dest_list)


# make threshold.txt file for FA output analysis in next step of SIP wetlab process
makeThreshold(wp_redo_df,dest_list)

# create df with info necessary for makign the FA plates
dilution_df = makeDilution(wp_redo_df)

# make hamilton transfer files for setting up FA plate
makeDilutionFile(dilution_df, dest_list)


# updated the project_summary.csv file with info about plates needing rework
updateProjectDatabase(lib_df, wp_redo_df)



