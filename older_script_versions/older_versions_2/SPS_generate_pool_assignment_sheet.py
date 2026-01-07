#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:

import pandas as pd
import numpy as np
import sys
from datetime import datetime
from pathlib import Path
import openpyxl
import shutil
import os





##########################
##########################
def findPoolPrepFile(crnt_dir):
    
    clarity_pool_prep_files = []

    # search through current directory for Clarity Pool Prep file
    # format is PoolingPrep_XX-XXXXXXXX.xlsx
    for file in os.listdir(crnt_dir):
        if file.startswith('PoolingPrep_'):
            
            # add any files matching pattern to list
            clarity_pool_prep_files.append(file)
          
    # abort script if no pool creation files are found or 
    # if >1 pool creation file found        
    if len(clarity_pool_prep_files) == 0:
        print('\n\nCould not find Clarity pool prep file, e.g. PoolingPrep_XX-XXXXX.xslx   Aborting script\n\n')
        sys.exit()
    elif len(clarity_pool_prep_files) > 1:
        print(f'\n\nMultiple Clarity pool prep files found\n\n{clarity_pool_prep_files}\n\nAborting script\n\n')
        sys.exit()

    pool_file = clarity_pool_prep_files[0]

    # return Clarity pool creation file name
    return pool_file
##########################
##########################




##########################
##########################
def makePoolDict(pool_file):
    
    # read in pooling prep file into df
    clarity_df = pd.read_excel(pool_file, header=2, usecols="A:O")

    # make dict where key is library name and value is pool number assigned by clarity
    pool_dict = dict(zip(clarity_df['Library Name'],clarity_df['Pool Number']))    
    
    
    return pool_dict
##########################
##########################




##########################
##########################
def getConstants():
    print('\n\n')

    # user provides min conc threshold for successful lib creation.
    target_pool_mass = float(
        input("Enter the target pool MASS needed (default 2.75 pmol): ") or 2.75)

    print('\n\n')
    
    # dilut_factor = float(
    #     input("What was the dilution factor of the FA plates? (default = 1): ") or 1)

    # print('\n\n')

    max_conc_vol = float(
        input("Enter the max CONCENTRATED volume used for individual libraries.  Should be <= half lib volume (default = 15uL): ") or 15)

    print('\n\n')

    max_dilut_vol = float(
        input("Enter the max DILUTED volume used for individual libraries.  Should be <= half lib volume (default = 5uL): ") or 5)

    print('\n\n')

    min_tran_vol = float(
        input("Enter the MINIMUM accurate pipet volume of instrument (default = 2.4uL): ") or 2.4)

    print('\n\n')

    # return target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol, dilut_factor

    return target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol
##########################
##########################






##########################
##########################
# def fillPoolingSheet(passed_df, target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol, dilut_factor):
    
def fillPoolingSheet(passed_df, pool_dict, target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol):
    workbook = openpyxl.load_workbook(filename="tmp_BLANK.xlsx")
    #sheet = workbook.active

    poolsheet = workbook['Pooling_tool']
    
    
    # add pool number assigned by clarity to each library using the pool_dict
    # pool_dict key is library name and value is pool number assigned by clarity
    passed_df['Pool_Number'] = passed_df['Library Name'].map(pool_dict)

    # # make small df of plate id, illumina index set, and number of libs in plate
    # x_df = passed_df.groupby(['Pool_source_plate', 'Pool_Illumina_index_set'])[
    #     'Pool_Illumina_index'].agg('count').reset_index()
    
    # make small df of plate id, pool number ,illumina index set, and number of libs in plate
    x_df = passed_df.groupby(['Pool_source_plate', 'Pool_Number','Pool_Illumina_index_set'])[
        'Pool_Illumina_index'].agg('count').reset_index()

    x_df.rename(columns={'Pool_Illumina_index': '#_of_libs'}, inplace=True)
    
    
    

    # make each column of x_df into own df, then loop through
    # each row and write to corresponding column in .xslx file
    plate_df = x_df[['Pool_source_plate']].copy()

    for index, row in plate_df.iterrows():
        cell = 'A%d' % (index + 3)
        poolsheet[cell] = row[0]

    
    poolnum_df = x_df[['Pool_Number']].copy()
    
    for index, row in poolnum_df.iterrows():
        cell = 'B%d' % (index + 3)
        poolsheet[cell] = row[0]



    index_df = x_df[['Pool_Illumina_index_set']].copy()

    for index, row in index_df.iterrows():
        cell = 'C%d' % (index + 3)
        poolsheet[cell] = row[0]

    count_df = x_df[['#_of_libs']].copy()

    for index, row in count_df.iterrows():
        cell = 'D%d' % (index + 3)
        poolsheet[cell] = row[0]

    # add info about individuals to different tab in .xlsx file
    poolsheet['Q2'] = min_tran_vol

    poolsheet['Q4'] = max_conc_vol

    poolsheet['Q6'] = max_dilut_vol

    poolsheet['Q8'] = target_pool_mass
    
    
    ###########################################
    ##### THIS SECTION MUST BE USED ON HAMILTON PC BECAUSE IT RUNS AN OLDER VERSION
    ##### OF PYTHON OR PANDAS
    ###########################################
    
    # y_df = passed_df[['Pool_source_plate', 'Pool_source_well',
    #                      'Pool_Illumina_index_set', 'Pool_nmole/L', 'Pool_dilution_factor']].copy()

    # writer = pd.ExcelWriter('tmp_BLANK.xlsx', engine='openpyxl')

    # writer.book = workbook
    # writer.sheets = dict((ws.title, ws) for ws in workbook.worksheets)

    # y_df.to_excel(writer, sheet_name='individual_lib_info',
    #               header=True, index=False)

    # # save as new .xlsx file for users to manually assign pool numbers
    # workbook.save(filename="assign_pool_number_sheet.xlsx")
    
    ###########################################
    ###########################################
    
    ###########################################
    ##### THIS SECTION MUST BE USED ON REX'S MAC BECAUSE IT HAS A NEWER
    ##### VERSION OF SOME SOFTWARE
    ###########################################
    
    # save as new .xlsx file for users to manually assign pool numbers
    workbook.save(filename="assign_pool_number_sheet.xlsx")

    # libsheet = workbook['individual_lib_info']

    # writer = pd.ExcelWriter('tmp_BLANK.xlsx', engine='openpyxl')

    # writer.book = workbook
    # writer.sheets = dict((ws.title, ws) for ws in workbook.worksheets)
    
    
    
    writer = pd.ExcelWriter("assign_pool_number_sheet.xlsx",engine="openpyxl",mode="a",if_sheet_exists="overlay",)
    
    y_df = passed_df[['Pool_source_plate', 'Pool_source_well',
                          'Pool_Illumina_index_set', 'Pool_nmole/L', 'Pool_dilution_factor']].copy()
    
    # y_df = passed_df[['Pool_source_plate', 'Pool_source_well',
    #                      'Pool_Illumina_index_set', 'Pool_nmole/L']].copy()
    
    # y_df['Pool_dilution_factor'] = dilut_factor

    y_df.to_excel(writer, sheet_name='individual_lib_info',
                  header=True, index=False)

    writer.close()

    return
##########################
##########################


##########################
# MAIN PROGRAM
##########################
###########################
# set up folder organiztion
###########################
ASSIGN_DIR = Path.cwd()

POOLING_DIR = ASSIGN_DIR.parent

PROJECT_DIR = POOLING_DIR.parent

ARCHIV_DIR = PROJECT_DIR / "archived_files"


# get current working directory and its parent directory
crnt_dir = os.getcwd()
prnt_dir = os.path.dirname(crnt_dir)
prjct_dir = os.path.dirname(prnt_dir)

# make temporary copy of blank pooling tool, and use temp copy for modifications
# this script corrupts the blank .xlsx  file used in functions above
# so I make a copy of original, use temp copy for modification, then delete temp copy
shutil.copy('BLANK_POOLING_TOOL.xlsx', 'tmp_BLANK.xlsx')  # new metatags


# # create df from updated_redo_fa_analysis_summary.csv file
# lib_df = pd.read_csv(sys.argv[1],
#                      header=0, converters={'Sample Barcode': str, 'Fraction #': int})


# get name of Clarity pool prep file, and abort script
# if 0 or >1 pool prep files are found
pool_file = findPoolPrepFile(crnt_dir)

 # open poolingprep .xlsx file created by clarity and
 # make dict where key is library name and value is pool number assigned by clarity
pool_dict = makePoolDict(pool_file)


# make df with a subset of columns related to pools
passed_df = pd.read_csv(PROJECT_DIR / 'project_summary.csv', header=0,usecols=['Library Name','Pool_source_plate', 'Pool_source_well',
                     'Pool_Illumina_index_set', 'Pool_Illumina_index','Pool_dilution_factor','Pool_nmole/L'])

# remove any rows with with empty fields
passed_df.dropna(inplace=True)


# # get library and pipetting specs from user
# target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol, dilut_factor = getConstants()

# get library and pipetting specs from user
target_pool_mass, max_conc_vol, max_dilut_vol, min_tran_vol = getConstants()


# # fill a blank pooling tool .xlsx file with plate, illumina index, and # of libs in each plate
# fillPoolingSheet(passed_df, target_pool_mass,
#                  max_conc_vol, max_dilut_vol, min_tran_vol, dilut_factor)

# fill a blank pooling tool .xlsx file with plate, pool number, illumina index, and # of libs in each plate
fillPoolingSheet(passed_df, pool_dict, target_pool_mass,
                 max_conc_vol, max_dilut_vol, min_tran_vol)

# delete temporary copy of blank pooling tool .xlsx
os.remove('tmp_BLANK.xlsx')
