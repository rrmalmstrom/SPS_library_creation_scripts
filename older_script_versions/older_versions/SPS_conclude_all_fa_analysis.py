#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# USAGE:   python conclude.all.fa.analysis.py <updated_2nd_fa_analysis_summary.txt>

# sys.argv[1] = manually updated version of fa_analysis_summary.txt generated from first_FA.output.analysis.py


import pandas as pd
import numpy as np
import sys
from pathlib import Path
from os.path import exists as file_exists
from datetime import datetime


##########################
##########################
def updateLibInfo():
    # create df from fa_analysis_summary.txt file
    reduced_df = pd.read_csv(sys.argv[1], sep='\t', header=0)

    # create df of project_summary.csv
    lib_df = pd.read_csv(PROJECT_DIR / "project_summary.csv", header=0)

    # add info from 2nd fa analysis and pass/fail results to project_summary.csv
    lib_df = lib_df.merge(reduced_df, how='outer', left_on=[
                          'sample_id'], right_on=['sample_id'], suffixes=('', '_y'))

    # remove redundant columns after merging
    lib_df.drop(lib_df.filter(regex='_y$').columns, axis=1, inplace=True)

    # # remove unnecessary columne 'FA_Well'
    # lib_df.drop(['Redo_FA_Well'], inplace=True, axis=1)

    # sort df based on sample id
    lib_df.sort_values(by=['sample_id'], inplace=True)

    # confirm all samples and fraction numbers in reduced_df
    # matched up with all samples and fraction numbrs in lib_df
    if lib_df['Total_passed_attempts'].isnull().values.any():

        print("""\nProblem updating lib_info.csv with pass/fail results from updated_2nd_fa_analysis_summary.txt.\nTotal passed attempts has some null entries\n\nAborting script\n\n""")
        sys.exit()

    else:

        return lib_df
##########################
##########################



##########################
##########################
def selectPlateForPooling(lib_df):

    # select samples that passed >=1 attempt at lib cration
    passed_df = lib_df[lib_df['Total_passed_attempts'] >= 1].copy()

    # create empty columns for pooling source plate and wells
    passed_df['Pool_source_plate'] = ""

    passed_df['Pool_source_well'] = ""




    # select redo plate over intial plate if lib passed in both attempts
    passed_df['Pool_source_plate'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_Destination_ID'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_Destination_ID'], passed_df['Destination Plate Barcode'])))

    passed_df['Pool_source_well'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_Destination_Well'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_Destination_Well'], passed_df['Destination_Well'])))

    passed_df['Pool_Illumina_index_set'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_Illumina_index_set'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_Illumina_index_set'], passed_df['Illumina_index_set'])))

    passed_df['Pool_Illumina_index'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_Illumina_index'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_Illumina_index'], passed_df['Illumina_index'])))

    passed_df['Pool_dilution_factor'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_dilution_factor'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_dilution_factor'], passed_df['dilution_factor'])))
    
    
    passed_df['Pool_DNA_conc_ng/uL'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_ng/uL'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_ng/uL'], passed_df['ng/uL'])))

    passed_df['Pool_nmole/L'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_nmole/L'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_nmole/L'], passed_df['nmole/L'])))

    passed_df['Pool_Avg. Size'] = np.where(
        passed_df['Total_passed_attempts'] == 2, passed_df['Redo_Avg. Size'], (np.where(passed_df['Redo_Passed_library'] == 1, passed_df['Redo_Avg. Size'], passed_df['Avg. Size'])))

    # add "pool" columns from passed_df to lib_df. The pool column contain info on specific
    # plates and libs that will go into pooling at a later step.
    final_df = pd.merge(lib_df,passed_df, how = 'outer', left_on=['sample_id'], right_on=['sample_id'], suffixes=('', '_y'))

    # remove redundant columns after merging
    final_df.drop(final_df.filter(regex='_y$').columns, axis=1, inplace=True)

    return final_df, passed_df

##########################
##########################





##########################
##########################
# MAIN PROGRAM
##########################
##########################




###########################
# set up folder organiztion
###########################

SECOND_FA_DIR = Path.cwd()

LIB_DIR = SECOND_FA_DIR.parent

PROJECT_DIR = LIB_DIR.parent

ARCHIV_DIR = PROJECT_DIR / "archived_files"

POOL_DIR = PROJECT_DIR / "2_pooling"

# CLARITY_DIR = POOL_DIR / "A_make_clarity_aliquot_upload_file"


# check if all required input files were provided and exist
if len(sys.argv) < 2:
    print('\n\nDid not provide all required input files. Aborting. \n\n')
    sys.exit()
elif (file_exists(sys.argv[1]) == 0):
    print(f'\n\nCould not find file {sys.argv[1]} \nAborting\n\n')
    sys.exit()

elif (sys.argv[1] != 'updated_2nd_fa_analysis_summary.txt'):
    print('Aborting.  Please provide file named updated_2nd_fa_anaylsis_summary.txt \n\n')
    sys.exit()


# add library pass/fail results from updated_2nd_fa_analysis.txt
# to the project_summary.csv file
# pass/fail results may have been manually modified from
# automatic outpt generated by script second.FA.output.analysis.py
lib_df = updateLibInfo()


# select specific plates that will go into pooling at a later step
# and add this info into a new set of df's
# final_df has info on all plates and samples
# passed_df only has info on samples with successful lib creation
final_df, passed_df = selectPlateForPooling(lib_df)




# get current date and time, will add to archive database file name
date = datetime.now().strftime("%Y_%m_%d-Time%H-%M-%S")


# archive the current lib_info.csv
Path(PROJECT_DIR /
     "project_summary.csv").rename(ARCHIV_DIR / f"archive_project_summary_{date}.csv")
Path(ARCHIV_DIR / f"archive_project_summary_{date}.csv").touch()

# create updated project_summary.csv file
final_df.to_csv(PROJECT_DIR / 'project_summary.csv', index=False)

# # create updated project_summary.csv file
# passed_df.to_csv(PROJECT_DIR / 'passed_library_summary.csv', index=False)


