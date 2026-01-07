#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
from PyPDF2 import PdfFileMerger
import seaborn as sns
from datetime import datetime
import shutil


# define list of destination well positions for a 96-well plate
well_list_96w_emptycorner = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                             'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                             'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                             'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                             'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']




##########################
##########################
def compareFolderFileNames(folder_path, file, folder_name):
    
    # make df from FA smear analysis output .csv file
    fa_df = pd.read_csv(folder_path +f'/{file}', usecols=['Sample ID'] )
    
    # make list of all sample names
    sample_list = fa_df['Sample ID'].unique().tolist()
    
    plate_list = []
    
    # make new plate list after spliting sample names at '_'
    # add 'F' to paresed plate name to matche expected plate barcode in
    # FA output folder name
    for s in sample_list:
        plate_list.append(s.split('_')[0]+'F')
    
    # abort program if the plate name in output folder does not
    # match plate name parsed from sample name in smear analysis .csv file
    if folder_name not in set(plate_list):
        print (f'\n\nThere is a mismatch between FA plate ID and sample names for plate {folder_name}.  Aborting script\n')
        sys.exit()
    
    
    return

##########################
##########################

##########################
##########################
def getFAfiles(crnt_dir):

    fa_files = []
  
    # # scan current directory and find subdirectories
    # for fa in os.scandir(crnt_dir): 
    #     if fa.is_dir():
            
    #         # find full path to subdirectories
    #         folder_path = os.path.abspath(fa)
            
    #         # extract name of FA plate by parsing the subdirectory name
    #         folder_name = os.path.basename(fa)
    #         folder_name = folder_name.split(' ')[0]
            
    #         # search for smear analysis files in each subdirectory
    #         for file in os.listdir(fa):
    #             if file.endswith('Smear Analysis Result.csv'):
    #                 # confirm folder name matches plate name parsed from
    #                 # smear analysis .csv sample names.  Error out if mismatch
    #                 compareFolderFileNames(folder_path, file, folder_name)
                    
    #                 # copy and rename smear analysis to main directory if good match
    #                 shutil.copy(folder_path +f'/{file}',crnt_dir)
    #                 os.rename(file,f'{folder_name}.csv')
                    
    #                 # add folder name (aka FA plate name) to list
    #                 fa_files.append(f'{folder_name}.csv')

    for direct in os.scandir(crnt_dir):
        if direct.is_dir():
            nxt_dir = os.path.abspath(direct)
            
            # scan current directory and find subdirectories
            for fa in os.scandir(nxt_dir): 
                if fa.is_dir():
                    
                    # find full path to subdirectories
                    folder_path = os.path.abspath(fa)
                    
                    # extract name of FA plate by parsing the subdirectory name
                    folder_name = os.path.basename(fa)
                    folder_name = folder_name.split(' ')[0]
                    
                    # search for smear analysis files in each subdirectory
                    for file in os.listdir(fa):
                        if file.endswith('Smear Analysis Result.csv'):
                            # confirm folder name matches plate name parsed from
                            # smear analysis .csv sample names.  Error out if mismatch
                            compareFolderFileNames(folder_path, file, folder_name)
                            
                            # copy and rename smear analysis to main directory if good match
                            shutil.copy(folder_path +f'/{file}',crnt_dir)
                            os.rename(file,f'{folder_name}.csv')
                            
                            # add folder name (aka FA plate name) to list
                            fa_files.append(f'{folder_name}.csv')
    
    

    # quit script if directory doesn't contain FA .csv files
    if len(fa_files) == 0:
        print("\n\n Did not find any FA output files.  Aborting program\n\n")
        sys.exit()

    else:

        # return a list of FA plate names
        return fa_files
##########################
##########################




##########################
##########################
def processFAfiles(my_fa_files):

    # # ask user input dilution factor used in setting  up FA plate
    # dilute_factor = float(
    #     input("Enter the FA plate dilution factor (default 40): ") or 40)

    # if dilute_factor <= 1:
    #     print('\n Dilution factor must be >=1.  Aborting script\n\n')
    #     sys.exit()

    # create dict where  keys are FA file names and value are df's from those files
    fa_dict = {}

    fa_dest_plates = []

    # loop through all FA files and create df's stored in dict
    for f in my_fa_files:
        # fa_dict[f] = pd.read_csv(f, usecols=[
        #     'Well', 'Sample ID', 'ng/uL', 'nmole/L', 'Avg. Size'], converters={'ng/uL': float, 'nmole/L': float, 'Avg. Size': float})

        fa_dict[f] = pd.read_csv(f, usecols=[
            'Well', 'Sample ID', 'ng/uL', 'nmole/L', 'Avg. Size'])

        fa_dict[f] = fa_dict[f].rename(
            columns={"Sample ID": "Redo_FA_Sample_ID", "Well": "Redo_FA_Well", "ng/uL": "Redo_ng/uL", "nmole/L": "Redo_nmole/L", "Avg. Size": "Redo_Avg. Size"})

        fa_dict[f]['Redo_FA_Well'] = fa_dict[f]['Redo_FA_Well'].str.replace(
            ':', '')

        # remove rows with "empty" or "ladder" in sample ID. search is case insensitive
        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'empty', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'ladder', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["Redo_FA_Sample_ID"].str.contains(
            'LibStd', case=False) == False]

        # create three new columns by parsing Sample_ID string using "_" as delimiter
        fa_dict[f][['Redo_FA_Destination_plate', 'Redo_FA_Sample', 'Redo_FA_well_2']
                   ] = fa_dict[f].Redo_FA_Sample_ID.str.split("_", expand=True)
        
     

        fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].fillna(0)

        fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].fillna(0)

        fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].fillna(0)

        # fa_dict[f]['FA_Fraction'] = fa_dict[f]['FA_Fraction'].astype(int)

        fa_dict[f]['Redo_FA_Sample'] = fa_dict[f]['Redo_FA_Sample'].astype(str)

        fa_dict[f]['Redo_ng/uL'] = fa_dict[f]['Redo_ng/uL'].astype(float)

        fa_dict[f]['Redo_nmole/L'] = fa_dict[f]['Redo_nmole/L'].astype(float)

        fa_dict[f]['Redo_Avg. Size'] = fa_dict[f]['Redo_Avg. Size'].astype(float)

        # fa_dict[f]['ng/uL'] = fa_dict[f]['ng/uL'] * dilute_factor

        # fa_dict[f]['nmole/L'] = fa_dict[f]['nmole/L'] * dilute_factor

        # fa_dict[f]['dilution_factor'] = dilute_factor

        # add destination plates in fa file to list fa_dest_plates
        fa_dest_plates = fa_dest_plates + \
            fa_dict[f]['Redo_FA_Destination_plate'].unique().tolist()       
    
        # get rid of unnecessary columsn
        fa_dict[f].drop(['Redo_FA_Destination_plate','Redo_FA_well_2','Redo_FA_Sample_ID','Redo_FA_Well'], inplace=True, axis=1)

    # quit script if were not able to process FA input files
    if len(fa_dict.keys()) == 0:
        print("\n\n Did not sucessfully extract FA files\n\n")
        sys.exit()

    elif len(fa_dict.keys()) != len(fa_dest_plates):
        print("\n\n mismatch in number of FA files and destination plates\n\n")
        sys.exit()

    # print out list of successfully processed FA files
    print("\n\n\nList of processed FA output files:\n\n\n")

    for k in fa_dict.keys():
        print(f'{k}\n')

    # add some blank lines after displaying list of processed FA files
    print('\n\n\n')

    return fa_dict, fa_dest_plates
##########################
##########################


##########################
##########################
def addFAresults(my_prjct_dir, my_fa_df):

    # merging df from lib_info.csv, which as all samples, with df's from FA output

    # create df from lib_info.csv file
    my_lib_df = pd.read_csv(my_prjct_dir + "/project_summary.csv",
                            header=0, converters={'sample_id': str})

    # record number of rows in my_lib_df. want to make sure doesn't change when merged with fa_df
    num_rows = my_lib_df.shape[0]

    
    # merge lib df with fa_df
    my_lib_df = my_lib_df.merge(my_fa_df, how='outer', left_on=['sample_id'], right_on=['Redo_FA_Sample'])
    
    
    
    
    # # confirm that merging did not change the row number
    if my_lib_df.shape[0] != num_rows:
        print(
            '\n problem merging lib_info.csv with FA files. Check out error.txt file just generated. Aborting.\n\n')
        print(my_lib_df.loc[my_lib_df['Destination_ID'].isnull()])

        my_lib_df.to_csv('error.txt', sep='\t', index=False)
        sys.exit()


    # get rid of unnecessary columns
    my_lib_df.drop(['Redo_FA_Sample'], inplace=True, axis=1)

    return my_lib_df

##########################
##########################


##########################
##########################
def findPassFailLibs(my_lib_df, my_dest_plates):

    # import df with dna conc and size thresholds for each FA plate
    thresh_df = pd.read_csv("thresholds.txt", sep="\t", header=0)
    
    # make sure threshold file has values for all threshodl parameters
    if (thresh_df.isnull().values.any()):
        print('\nThe thresholds.txt file is missing needed values.  Aborting\n\n')
        sys.exit()
    
    
    thresh_df = thresh_df.rename(columns={"dilution_factor": "Redo_dilution_factor"})

    # add thresholds of my_lib_df
    my_lib_df = my_lib_df.merge(thresh_df, how='outer', left_on=[
        'Redo_Destination_ID'], right_on=['Destination_plate'])


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
        
    # select subsete of lib_df containing info only on plates that went through rework
    redux_mask = my_lib_df['Redo_Destination_ID'].isin(my_dest_plates)
    
    redux_df= my_lib_df[redux_mask]    

    # make a summary file containing only libs  that failed both attempts
    my_double_fail_df = redux_df.loc[redux_df['Total_passed_attempts'] == 0].copy(
    )

 

    return my_lib_df, my_double_fail_df

##########################
##########################




##########################
# MAIN PROGRAM
##########################


# get current working directory and its parent directory
crnt_dir = os.getcwd()
prnt_dir = os.path.dirname(crnt_dir)
prjct_dir = os.path.dirname(prnt_dir)




####### MUST uncomment to work as designed
# get list of FA output files
fa_files = getFAfiles(crnt_dir)


# ######## must comment out to work as designed
# fa_files = ['27-685346.2F.csv','27-685345.2F.csv']

# get dictionary where keys are FA file names and values are df's created from FA files
# and get a list of destination/lib plate IDs processed
fa_lib_dict, fa_dest_plates = processFAfiles(fa_files)

# create new dataframe combining all entries in dictionary fa_lib_dict
fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)


# add FA results to df from lib_info.csv
lib_df = addFAresults(prjct_dir, fa_df)


# identify libs that passed/failed based on user provided thresholds
fa_summary_df, double_fail_df = findPassFailLibs(lib_df, fa_dest_plates)



# make smaller version of FA summary with only a subset of columns
reduced_fa_df = fa_summary_df[['sample_id', 'Redo_Destination_ID', 'Redo_FA_Well', 'Redo_dilution_factor','Redo_ng/uL', 'Redo_nmole/L', 'Redo_Avg. Size', 'Redo_Passed_library','Total_passed_attempts']].copy()

reduced_fa_df.sort_values(
    by=['Redo_Destination_ID', 'sample_id'], inplace=True)




# create updated library info file
reduced_fa_df.to_csv('reduced_2nd_fa_analysis_summary.txt',
                      sep='\t', index=False)

# create new df of samples that failed both attempts at library creation
double_fail_df.to_csv('double_failed_libraries.txt', sep='\t', index=False)