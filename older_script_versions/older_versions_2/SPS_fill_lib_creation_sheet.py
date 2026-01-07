#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os
import xlrd
from xlutils.copy import copy
import xlwt
from datetime import datetime
from pathlib import Path
from sklearn.impute import SimpleImputer


##########################
##########################
def getCalrityFiles(dirname, ext):
    # create empty list to hold FA output files
    list_matched_files = []

# loop through all files in directory, find files that end with .xls and adde them to a list
    for file in os.listdir(dirname):
        if file.startswith('autofilled'):
            continue

        elif file.endswith(ext):

            list_matched_files.append(file)

        else:
            continue

    # quit script if directory doesn't contain FA .csv files
    if len(list_matched_files) == 0:
        print(
            "\n\n Did not find any .xls clarity lib creation files.  Aborting program\n\n")
        sys.exit()

    else:

        return list_matched_files
##########################
##########################


#####################
#####################
def mergeLibDataFiles(lib_df, clarity_df, clarity_lib_plate_id):

    # make slice of lib_df with only data matching library plate on current worksheet
    tmp_lib_df = lib_df[lib_df['Destination Plate Barcode'] == clarity_lib_plate_id].copy()

    # add make new column with original index from lib_df
    # this can be used to update dataframe later
    tmp_lib_df['original_index'] = tmp_lib_df.index

    # tmp_lib_df['original_index'] = tmp_lib_df['original_index'].astype(str)

    # # add column wiht fake library volume
    # tmp_lib_df['Library Volume (ul)'] = 35
    
    tmp_lib_df['LC - Notes'] = ""
    
    
    # This sets all libs to pass, but this code must be removed once
    # clairty lims updated to allwo SPS/CE libs to fail
    tmp_lib_df['Library QC (Pass/Fail)'] = "Pass"
    
    # temporarily commenting out this code because Clarity requires all SPS/CE libs to "pass"
    # updated Clarity LIMS should allow pass/fail in future, but for now all must pass
    # tmp_lib_df['Library QC (Pass/Fail)'] = np.where(tmp_lib_df['Total_passed_attempts'] > 0, "Pass","Fail")
    
    
    
    # tmp_lib_df['Library Failure Mode'] = np.where(tmp_lib_df['Total_passed_attempts'] == 0, "insufficient quantity","")
    
    tmp_lib_df['LC - Notes'] = np.where(tmp_lib_df['Total_passed_attempts'] == 0, "failed library but clarity requires all SPS and CE libs to pass","")
    
    
    # tmp_lib_df['Library Volume (ul)'] = np.where(tmp_lib_df['Total_passed_attempts'] > 0, 30,"")
    
    tmp_lib_df['Library Volume (ul)'] = 30
    

    
    
    # replace missing values with median DNA concentration and size info that's missing from failed libraries
    # Clarity requires this info for failed libraires
    # imputed missing values are rounded to integers
    tmp_lib_df['Pool_DNA_conc_ng/uL'].fillna(tmp_lib_df['Pool_DNA_conc_ng/uL'].median(),inplace=True)
    
    tmp_lib_df['Pool_nmole/L'].fillna(tmp_lib_df['Pool_nmole/L'].median(),inplace=True)
    
    tmp_lib_df['Pool_Avg. Size'].fillna(int(tmp_lib_df['Pool_Avg. Size'].median()),inplace=True)
    
    # round decimals for median values used with failed libs
    tmp_lib_df = tmp_lib_df.round({"Pool_DNA_conc_ng/uL":2, "Pool_nmole/L":2}) 



    # make slice of clarity_df with well and lib name
    tmp_clarity_df = clarity_df[['Well', 'Library Name']].dropna().copy()
    
    # # make slice of clarity_df with well and lib name
    # tmp_clarity_df = clarity_df[['Well', 'Library Name']].copy()

    # abort script if current library plate id wasn't found in database
    if tmp_lib_df.shape[0] < 1:
        print(
            f"\n\n Could not find {clarity_lib_plate_id} in database file. Aborting process\n\n")
        sys.exit()

    # aborts script if there's a mismatch in number of libraries in clarity_df and lib_df
    elif tmp_lib_df.shape[0] != tmp_clarity_df.shape[0]:
        print(
            f"\n\n Mismatch in plate {clarity_lib_plate_id} between number of libs in creation sheet and database. Aborting processn\n")
        sys.exit()

    # confirm tmp_clarity_df and tmp_lib_df can be merged without any mismatches
    # if there's a mismatch, i.e. and extra row because of outer  join created row with Nan
    # then abort process
    else:
        tmp_merge_df = pd.merge(tmp_clarity_df, tmp_lib_df, how='outer', left_on=[
            'Well'], right_on=['Destination_Well'])

        if tmp_merge_df.shape[0] != tmp_clarity_df.shape[0]:
            print(
                f"\n\n Mismatch in plate {clarity_lib_plate_id} between number of libs in creation sheet and database. Aborting processn\n")
            sys.exit()

    # merge tmp_lib_df with info on libs with the clarity_df based on Well position
    clarity_info_df = pd.merge(clarity_df, tmp_lib_df,  how='outer', left_on=[
        'Well'], right_on=['Destination_Well'])

    merged_df = clarity_info_df.copy()

    merged_df.drop(['Pool_source_plate', 'Pool_source_well',
                       'Pool_Illumina_index_set', 'original_index'], inplace=True, axis=1)
    
    # # add illumina index used.  If lib failed, then use index that assigned  by clarity 
    # merged_df['final_index'] = np.where(merged_df['Pool_Illumina_index'].isna(), merged_df['clarity_index'], merged_df['Pool_Illumina_index'])

    # rearrange column order to match expect excel file format
    merged_df = merged_df.reindex(
        columns=['Well', 'Library LIMS ID', 'Library Name', 'Pool_Illumina_index','Pool_DNA_conc_ng/uL', 'Pool_nmole/L','Pool_Avg. Size', 'Library Volume (ul)', 'LC - Notes','Library QC (Pass/Fail)','Library Failure Mode'])


    merged_df.fillna('', inplace=True)
    
    
    # ## thsi step creates a problem for failed libraries, which clarity does not allow
    # ## will just remove empty rows instead
    
    #clarity_info_df = clarity_info_df[clarity_info_df['Total_passed_attempts'] >= 1]
    
    # remove rows / wells from dataframe that do not contain a lib in clarity lib creation sheet    
    clarity_info_df.dropna(subset=['Library Name'], inplace=True)

    
    # add the library plate id to empty column   
    clarity_info_df['Clarity_Lib_Plate_ID'] = clarity_lib_plate_id

    clarity_info_df.drop(['Well', 'Pool_Illumina_index_set', 'Pool_Illumina_index', 'Pool_DNA_conc_ng/uL',
                            'Pool_Avg. Size', 'Library Volume (ul)', 'Pool_nmole/L'], inplace=True, axis=1)

    clarity_info_df.rename(columns={'Pool_source_plate': 'tmp_pool_source_plate',
                              'Pool_source_well': 'tmp_pool_source_well'}, inplace=True)

    
    # use original index numbers on dataframe
    clarity_info_df = clarity_info_df.set_index('original_index')

    clarity_info_df.index = clarity_info_df.index.rename('Index')

    return merged_df, clarity_info_df


#####################
#####################


#####################
#####################
def updateLibCreationFile(sheet, merged_df, lib_plate):

    # define the index set to be entered in lib creation file
    illumina_index_set = 'Custom'

    # add fake values about DNA aliquots that are necessary for clarity upload
    target_aliquot_mass = 1

    target_aliquot_vol = 5

    pcr_cycle = int(input(
        f"\n\nEnter number of PCR cycles used in library creation for {lib_plate} (default = 13):\n\n") or 13)

    # overwrite all cell values from row 26-500 and col 1-21 to create blank slate in lib info area of .xls file
    for r in range(26, 500, 1):
        for c in range(0, 20, 1):
            sheet.write(r, c, '')

    # loop through merged df and write info into .xls file
    for row_num, row in merged_df.iterrows():
        for col_num, col in enumerate(row):
            sheet.write(26+row_num, col_num, col)

    # update necessary cells in .xls file
    sheet.write(14, 1, 'Pass')

    sheet.write(16, 1, pcr_cycle)

    sheet.write(17, 1, illumina_index_set)

    sheet.write(10, 1, target_aliquot_mass)

    sheet.write(11, 1, target_aliquot_vol)

    return sheet

#####################
#####################


##########################
##########################
def processXLSfiles(xls_files, lib_df):
    # make empty list to hold names of lib plates that successfully filled .xls lib creation file
    completed_plates = []
    
    # get list of library plate id's.  Do NOT include redo plates with names like 27-***.2 that include *.2
    lib_plate_list = lib_df['Destination Plate Barcode'].unique().tolist()

    # create empty df to eventually hold lib summary info plus clairty lib name, sample ID, and plate IDs
    lib_name_df = pd.DataFrame()

    for x in xls_files:

        lib_creation_file = x

        # # import library creation .xls file downloaded from clarity queue
        # clarity_df = pd.read_excel(
        #     lib_creation_file, header=25, engine=("xlrd"), usecols=['Well', 'Library LIMS ID', 'Library Name', 'Aliquot Mass (ng)'])

        
        # read in library creation file
        book = xlrd.open_workbook(lib_creation_file)

        # make copy of workbook with xlwt module so that it can be editted
        wb = copy(book)

        # loop through all sheets in workbook
        for sheet in book.sheets():

            # # skip over hidden sheets in library creation file
            # if (sheet.name == 'hidden') or (sheet.name == 'Excel Configuration'):
            #     continue

            # else:

            # # skip over hidden sheets in library creation file
            # if (sheet.name == 'Results'):
            # skip over hidden sheets in library creation file
            if sheet.name in lib_plate_list:
                
                test = sheet.name

                # # get the name of the source plate from lib creation file
                # source_plate = sheet.cell_value(rowx=2, colx=1)

                # get library plate barcode from clarity, e.g. 27_****
                clarity_lib_plate_id = sheet.cell_value(rowx=3, colx=1)
                
                # create df with info extracted from Clarity lib creation sheet
                clarity_df = pd.read_excel(
                    lib_creation_file, sheet_name = sheet.name, header=25, engine=("xlrd"), usecols=['Well', 'Library LIMS ID', 'Library Name'])

                
                clarity_df = clarity_df[clarity_df.index < 96]
                
                # clarity_df.rename(columns={'Index':'clarity_index'}, inplace=True)

                # call funtion to merge data from lib summary file and lib creation file
                merged_df, clarity_info_df = mergeLibDataFiles(
                    lib_df, clarity_df, clarity_lib_plate_id)

                # append clarity lib name, lib id, and plate id to
                if lib_name_df.empty:
                    lib_name_df = clarity_info_df.copy()

                else:
                    # lib_name_df = pd.concat(
                    #     [lib_name_df, clarity_info_df], axis=0, ignore_index=True)

                    lib_name_df = pd.concat(
                        [lib_name_df, clarity_info_df], axis=0)

                # select current worksheet in wlwt from wb copy of workbook
                s = wb.get_sheet(sheet.name)

                # update worksheet with library summary stats and metadata
                s = updateLibCreationFile(s, merged_df, clarity_lib_plate_id)

                completed_plates.append(clarity_lib_plate_id)

                # # make new lib_creation.xls filled out with library metadata
                # wb.save(f'autofilled_{sheet.name}')

                # # arive the current lib_info_submitted_to_clarity.csv
                # Path(PROJECT_DIR /
                #      f'autofilled_{sheet.name}').rename(AUTO_DIR / f"af'autofilled_{sheet.name}'")
    
        # make new lib_creation.xls filled out with library metadata
        wb.save(f'autofilled_{x}')
        
    lib_name_df = lib_name_df[['sample_id','Library Name']]
    
            
    return completed_plates, lib_name_df
##########################
##########################


##########################
##########################
def removefiles(dirname, ext):
    for file in os.listdir(dirname):
        if file.endswith(ext) and file.startswith('autofilled'):
            os.remove(file)

        else:
            continue

    return
##########################
##########################


##########################
##########################
def findMissingPlateFiles(lib_df, completed_plates):

    # total_lib_plates = sorted(lib_df['Pool_source_plate'].unique().tolist())
    
    total_lib_plates = lib_df['Destination Plate Barcode'].unique().tolist()

    # missing_plates = sorted(set(set(total_lib_plates)-set(completed_plates)))
    
    missing_plates = set(set(total_lib_plates)-set(completed_plates))

    if len(missing_plates) > 0:
        print(
            f'\n\nWARNING!!!   WARNING!!!   WARNING!!!\n\nThe library plates below were NOT processed in clarity lib creation files:\n\n{missing_plates}\n\n')

        keep_going = input(
            'Would you like to autofill clarity creation files for ONLY some the library plates? (Y/N)\n')

        if (keep_going == 'Y' or keep_going == 'y'):
            print(
                "Ok, we'll keep going, but do you have a plan for processing missing plates?\n\n")

        elif (keep_going == 'N' or keep_going == 'n'):
            print('Ok, aborting script\n\n')
            removefiles(crnt_dir, ext)
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            removefiles(crnt_dir, ext)
            sys.exit()

##########################
##########################


##########################
##########################
def addClarityInfoToLibInfo(summary_df, lib_name_df):

    # check if lib_info_submitted_to_clarity.csv already has column 'Library Name' indicating
    # it was already partially upated with a subset lib plates
    # in this case just fill in empty (Nan) cells with new data from lib_name_df
    if 'Library Name' in summary_df.columns:
        message = """
        The lib_info_submitted_to_clarity.csv database already has some
        info about clarity Library names, Library LIMS ID, and Library Plates.
        Existing data will NOT be overwritten by continuing this process.
        Only library currenlty missing these clarity id's will be updated.
        """
        print(f'\n\n{message}\n\n')

        keep_going = input(
            'Would you like to autofill clarity creation files for ONLY some the library plates? (Y/N)\n')

        if (keep_going == 'Y' or keep_going == 'y'):
            print(
                "Ok, we'll keep going, but do you have a plan for processing missing plates?\n\n")

        elif (keep_going == 'N' or keep_going == 'n'):
            print('Ok, aborting script\n\n')
            removefiles(crnt_dir, ext)
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            removefiles(crnt_dir, ext)
            sys.exit()

        # lib_name_df.drop(
        #     ['tmp_pool_source_plate', 'tmp_pool_source_well'], inplace=True, axis=1)
        updated_df = summary_df.copy()
        updated_df = updated_df.fillna(lib_name_df)

    # if lib_info_submitted_to_clarity.csv doesn't have columen 'Library Name'
    # then merge with lib_name_df to add clarity lib name, lims id, and lib plate id
    else:
        # updated_df = pd.merge(summary_df, lib_name_df, how='outer', left_on=[
        #                       'Pool_source_plate', 'Pool_source_well'], right_on=['tmp_pool_source_plate', 'tmp_pool_source_well'])
        
        updated_df = pd.merge(summary_df, lib_name_df, how='outer', left_on=[
                              'sample_id'], right_on=['sample_id'])

        # updated_df.drop(
        #     ['tmp_pool_source_plate', 'tmp_pool_source_well'], inplace=True, axis=1)

        # updated_df = pd.concat([summary_df, lib_name_df], axis=1)

    if updated_df.shape[0] != summary_df.shape[0]:
        print('\n\nError in adding Clarity LIMS ID, Library Name, and Library Plate ID to library database.  Aborting process:')
        removefiles(crnt_dir, ext)
        sys.exit()

    return updated_df
##########################
##########################


##########################
##########################
def moveBlankLibCreationFiles(xls_files):

    for x in xls_files:
        # arive the blank .xls file
        Path(CLARITY_DIR /
             f"{x}").rename(OLD_DIR / f"{x}")
        Path(OLD_DIR / f"{x}").touch()

##########################
##########################


##########################
# MAIN PROGRAM
##########################

# get current working directory and its parent directory
crnt_dir = os.getcwd()
prnt_dir = os.path.dirname(crnt_dir)
prjct_dir = os.path.dirname(prnt_dir)


###########################
# set up folder organiztion
###########################
CLARITY_DIR = Path.cwd()

OLD_DIR = CLARITY_DIR / "processed_blank_lib_creation_files"

OLD_DIR.mkdir(parents=True, exist_ok=True)

# AUTO_DIR = CLARITY_DIR / "autofilled_lib_creation_files"

# AUTO_DIR.mkdir(parents=True, exist_ok=True)

POOLING_DIR = CLARITY_DIR.parent

PROJECT_DIR = POOLING_DIR.parent

ARCHIV_DIR = PROJECT_DIR / "archived_files"


# file extension for FA output file
ext = ('.xls')


# get list of .xls clarity lib creation files
xls_files = getCalrityFiles(crnt_dir, ext)


# lib_summary_file = 'lib_info_submitted_to_clarity.csv'

# import csv indicating which fractions should be made into libs
lib_df = pd.read_csv(PROJECT_DIR / 'project_summary.csv', header=0, usecols=['sample_id','Destination Plate Barcode','Destination_Well','Total_passed_attempts','Pool_source_plate', 'Pool_source_well', 'Pool_Illumina_index_set', 'Pool_Illumina_index', 'Pool_DNA_conc_ng/uL', 'Pool_nmole/L', 'Pool_Avg. Size'])

# loop through all .xls files and fill in missing library metadata
# and return a df lib_name_df that can be used to update lib_info_submitted_to_clarity.csv
# with Clarity LIMS ID, library name, and lib plate ID
completed_plates, lib_name_df = processXLSfiles(xls_files, lib_df)

# make sure all library plates had a corresponding blank .xls file downloaded from clarity, and that
# all .xls file were filled out by python script
findMissingPlateFiles(lib_df, completed_plates)

# make new df from lib_info_submitted_to_clarity.csv  so that clarity lib name, lims id, and lib plate id can be added to df
summary_df = pd.read_csv(PROJECT_DIR / 'project_summary.csv', header=0)

# add clarity library lims id, library name, and library plate id to project+summary.csv database
updated_df = addClarityInfoToLibInfo(summary_df, lib_name_df)

# move blank .xls files that have been processed to subfolder for storage
moveBlankLibCreationFiles(xls_files)

# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")

# arive the current project_summary.csv
Path(PROJECT_DIR /
     "project_summary.csv").rename(ARCHIV_DIR / f"archive_project_summary_{date}.csv")
Path(ARCHIV_DIR / f"archive_project_summary_{date}.csv").touch()

# create updated project_summary.csv file
updated_df.to_csv(
    PROJECT_DIR / 'project_summary.csv', index=False)
