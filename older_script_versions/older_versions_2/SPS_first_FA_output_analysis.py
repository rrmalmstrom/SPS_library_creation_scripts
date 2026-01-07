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
    #     input("Enter the FA plate dilution factor (default 1): ") or 1)

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
            columns={"Sample ID": "FA_Sample_ID", "Well": "FA_Well"})

        fa_dict[f]['FA_Well'] = fa_dict[f]['FA_Well'].str.replace(
            ':', '')

        # remove rows with "empty" or "ladder" in sample ID. search is case insensitive
        fa_dict[f] = fa_dict[f][fa_dict[f]["FA_Sample_ID"].str.contains(
            'empty', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["FA_Sample_ID"].str.contains(
            'ladder', case=False) == False]

        fa_dict[f] = fa_dict[f][fa_dict[f]["FA_Sample_ID"].str.contains(
            'LibStd', case=False) == False]

        # create three new columns by parsing Sample_ID string using "_" as delimiter
        fa_dict[f][['FA_Destination_plate', 'FA_Sample', 'FA_well_2']
                   ] = fa_dict[f].FA_Sample_ID.str.split("_", expand=True)
        
     

        fa_dict[f]['ng/uL'] = fa_dict[f]['ng/uL'].fillna(0)

        fa_dict[f]['nmole/L'] = fa_dict[f]['nmole/L'].fillna(0)

        fa_dict[f]['Avg. Size'] = fa_dict[f]['Avg. Size'].fillna(0)

        # fa_dict[f]['FA_Fraction'] = fa_dict[f]['FA_Fraction'].astype(int)

        fa_dict[f]['FA_Sample'] = fa_dict[f]['FA_Sample'].astype(str)

        fa_dict[f]['ng/uL'] = fa_dict[f]['ng/uL'].astype(float)

        fa_dict[f]['nmole/L'] = fa_dict[f]['nmole/L'].astype(float)

        fa_dict[f]['Avg. Size'] = fa_dict[f]['Avg. Size'].astype(float)

        # fa_dict[f]['ng/uL'] = fa_dict[f]['ng/uL'] * dilute_factor

        # fa_dict[f]['nmole/L'] = fa_dict[f]['nmole/L'] * dilute_factor

        # fa_dict[f]['dilution_factor'] = dilute_factor

        # add destination plates in fa file to list fa_dest_plates
        fa_dest_plates = fa_dest_plates + \
            fa_dict[f]['FA_Destination_plate'].unique().tolist()       
    
        # get rid of unnecessary columsn
        fa_dict[f].drop(['FA_Destination_plate','FA_well_2','FA_Sample_ID','FA_Well'], inplace=True, axis=1)

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
    my_lib_df = my_lib_df.merge(my_fa_df, how='outer', left_on=['sample_id'], right_on=['FA_Sample'])
    
    
    
    
    # # confirm that merging did not change the row number
    if my_lib_df.shape[0] != num_rows:
        print(
            '\n problem merging lib_info.csv with FA files. Check out error.txt file just generated. Aborting.\n\n')
        print(my_lib_df.loc[my_lib_df['Destination_ID'].isnull()])

        my_lib_df.to_csv('error.txt', sep='\t', index=False)
        sys.exit()


    # get rid of unnecessary columns
    my_lib_df.drop(['FA_Sample'], inplace=True, axis=1)

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

    # add thresholds of my_lib_df
    my_lib_df = my_lib_df.merge(thresh_df, how='outer', left_on=[
        'Destination Plate Barcode'], right_on=['Destination_plate'], suffixes=('', '_y'))
    
    # make column that compares dilution factor in project_summary.csv with value in threholds.txt
    my_lib_df['compare_dilution_factors'] = my_lib_df['dilution_factor'].equals(my_lib_df['dilution_factor_y'])
    
    # determine what to do if dilution factors differ
    if my_lib_df['compare_dilution_factors'].any() == False:
        
        val  = input('\n\n the dilution factor in the thresholds file does not match value in project_summary.csv.  Is the thresholds.txt file correct?:  ')
    
    
        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")
            
            my_lib_df['dilution_factor'] = my_lib_df['dilution_factor_y']
            
            

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script. Please resolve issue with dilution factor in thresholds file \n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()  
    
    
    # remove column with dilution_factor read from thresholds file and column comparing dilution factors
    my_lib_df.drop(columns=['dilution_factor_y','compare_dilution_factors'], inplace=True)

    # get max number of failed libs per plate before triggering whole plate rework
    min_failed_libs = float(
        input("""How many failed libs per plate to trigger whole plate rework?\n 
              Default threshold is 20: """) or 20)

    # assign pass or fail to each lib based on dna conc and size thresholds
    my_lib_df['Passed_library'] = np.where(((my_lib_df['nmole/L'] > my_lib_df['DNA_conc_threshold_(nmol/L)']) & (
        my_lib_df['Avg. Size'] > my_lib_df['Size_theshold_(bp)'])), 1, 0)

    # update lib conc info based on the dilution factor.  This is conc in original library plate
    my_lib_df['ng/uL'] = my_lib_df['ng/uL'] * my_lib_df['dilution_factor']

    my_lib_df = my_lib_df.round({'ng/uL': 3})

    my_lib_df['nmole/L'] = my_lib_df['nmole/L'] * my_lib_df['dilution_factor']

    my_lib_df = my_lib_df.round({'nmole/L': 3})

    # remove columns no longer needed
    my_lib_df.drop(['Destination_plate', 'DNA_conc_threshold_(nmol/L)',
                   'Size_theshold_(bp)'], inplace=True, axis=1)

    # create empty list for whole plates that need rework
    whole_plate_redo = []

    # # identify whole plates that need rework
    # for val, cnt in my_lib_df[(my_lib_df['Passed_library'] == 0)]['Destination Plate Barcode'].value_counts().iteritems():
    #     # for val, cnt in redo_df.Destination_ID.value_counts().iteritems():
    #     if cnt >= min_failed_libs:
    #         whole_plate_redo.append(val)
    
    # identify whole plates that need rework
    for val, cnt in my_lib_df[(my_lib_df['Passed_library'] == 0)]['Destination Plate Barcode'].value_counts().items():
    
        if cnt >= min_failed_libs:
            whole_plate_redo.append(val)
        

    # sort the list of whole plates that neede to be reworked
    whole_plate_redo = sorted(whole_plate_redo)

    my_lib_df['Redo_whole_plate'] = ""

    # identify libs that are part of a whole plate rework
    my_lib_df['Redo_whole_plate'].loc[my_lib_df['Destination Plate Barcode'].isin(
        whole_plate_redo)] = True

    # # make new column indicating if a library creation should be re-attempted
    # # rex, there mighte be a problem with "or" so try "|" if you have a problem
    # my_lib_df['Make_new_library'] = np.where(((my_lib_df['Passed_library'] == 0) | (
    #     my_lib_df['Redo_whole_plate'] == True)), 1, 0)

    return my_lib_df

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
# fa_files = ['27-685346F.csv','27-685345F.csv','27-685347F.csv','27-685497F.csv','27-686572F.csv']

# get dictionary where keys are FA file names and values are df's created from FA files
# and get a list of destination/lib plate IDs processed
fa_lib_dict, fa_dest_plates = processFAfiles(fa_files)

# create new dataframe combining all entries in dictionary fa_lib_dict
fa_df = pd.concat(fa_lib_dict.values(), ignore_index=True)


# add FA results to df from lib_info.csv
lib_df = addFAresults(prjct_dir, fa_df)

# print(list(lib_df.columns))

# identify libs that passed/failed based on user provided thresholds
fa_summary_df = findPassFailLibs(lib_df, fa_dest_plates)


# df.sort_values(by = ['Name', 'Rank'], axis=0, ascending=[False, True], inplace=False,
#                kind='quicksort', na_position='first', ignore_index=True, key=None)

# make smaller version of FA summary with only a subset of columns
reduced_fa_df = fa_summary_df[['sample_id', 'Destination Plate Barcode', 'FA_Well', 'dilution_factor','ng/uL', 'nmole/L', 'Avg. Size', 'Passed_library', 'Redo_whole_plate']].copy()

reduced_fa_df.sort_values(
    by=['Destination Plate Barcode', 'sample_id'], inplace=True)




# create updated library info file
reduced_fa_df.to_csv('reduced_fa_analysis_summary.txt',
                     sep='\t', index=False)
