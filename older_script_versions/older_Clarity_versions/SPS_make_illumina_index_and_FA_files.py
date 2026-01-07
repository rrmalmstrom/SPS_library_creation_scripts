#!/usr/bin/env python3

# USAGE:   python sps_make_illumina_index_and_FA_files.py <less_inclusive.csv> <SPITS.csv>

# sys.argv[1] = .csv summary file from 'less inclusive' report downloaded from the data warehouse.


# import datetime as dt
import pandas as pd
import numpy as np
import sys
import string
from datetime import datetime
from pathlib import Path
import os
from stat import S_IREAD, S_IRGRP, S_IROTH
import random
from sqlalchemy import create_engine


# define list of destination well positions for a 96-well and 384-well plates
well_list_96w = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                  'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                  'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                  'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                  'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']






#########################
#########################
def createDirectories():
    # BASE_DIR = Path(__file__).parent
    BASE_DIR = Path.cwd()
    
    PROJECT_DIR = BASE_DIR / "1_make_library_analyze_fa"
    
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    
    LIB_DIR = PROJECT_DIR / "A_first_attempt_make_lib"

    LIB_DIR.mkdir(parents=True, exist_ok=True)

    ECHO_DIR = LIB_DIR / "echo_transfer_files"

    ECHO_DIR.mkdir(parents=True, exist_ok=True)
    
    
    INDEX_DIR = LIB_DIR / "illumina_index_transfer_files"

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    FTRAN_DIR = LIB_DIR / "fa_transfer_files"

    FTRAN_DIR.mkdir(parents=True, exist_ok=True)
    
    ANALYZE_DIR = PROJECT_DIR / "B_first_attempt_fa_result"
    
    ANALYZE_DIR.mkdir(parents=True, exist_ok=True)
    
    FA_DIR = LIB_DIR / "FA_input_files"

    FA_DIR.mkdir(parents=True, exist_ok=True)
    
    
    SECOND_DIR = PROJECT_DIR / "C_second_attempt_make_lib"
    
    SECOND_DIR.mkdir(parents=True, exist_ok=True)
    
    SECFA_DIR = PROJECT_DIR / "D_second_attempt_fa_result"
    
    SECFA_DIR.mkdir(parents=True, exist_ok=True)
    
    
    POOL_DIR = BASE_DIR / "2_pooling"
    
    POOL_DIR.mkdir(parents=True, exist_ok=True)
    
    LIMS_DIR = POOL_DIR / "A_fill_clarity_lib_creation_file"
    
    LIMS_DIR.mkdir(parents=True, exist_ok=True)
    
    ASGNPOOL_DIR = POOL_DIR / "B_assign_libs_to_pools"
    
    ASGNPOOL_DIR.mkdir(parents=True, exist_ok=True)
    
    FINISH_DIR = POOL_DIR / "C_finish_pooling"
    
    FINISH_DIR.mkdir(parents=True, exist_ok=True)
    
    REWORK_DIR = POOL_DIR / "D_pooling_and_rework"
    
    REWORK_DIR.mkdir(parents=True, exist_ok=True)

    return BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR

#########################
#########################


#########################
#########################
def getPlateType():
    # define list of destination well positions for a 96-well and 384-well plates
    well_list_96w = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                     'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                     'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                     'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                     'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12']

    well_list_384w = ['A1', 'C1', 'E1', 'G1', 'I1', 'K1', 'M1', 'O1', 'A3', 'C3', 'E3', 'G3', 'I3', 'K3', 'M3', 'O3', 'A5', 'C5', 'E5', 'G5',
                      'I5', 'K5', 'M5', 'O5', 'A7', 'C7', 'E7', 'G7', 'I7', 'K7', 'M7', 'O7', 'A9', 'C9', 'E9', 'G9', 'I9', 'K9', 'M9', 'O9',
                      'A11', 'C11', 'E11', 'G11', 'I11', 'K11', 'M11', 'O11', 'A13', 'C13', 'E13', 'G13', 'I13', 'K13', 'M13', 'O13', 'A15',
                      'C15', 'E15', 'G15', 'I15', 'K15', 'M15', 'O15', 'A17', 'C17', 'E17', 'G17', 'I17', 'K17', 'M17', 'O17', 'A19', 'C19',
                      'E19', 'G19', 'I19', 'K19', 'M19', 'O19', 'A21', 'C21', 'E21', 'G21', 'I21', 'K21', 'M21', 'O21', 'A23', 'C23', 'E23',
                      'G23', 'I23', 'K23', 'M23', 'O23']

    # define lists of destination well positions for 96-well and 384-well platse assuming empty corners
    well_list_96w_emptycorners = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                                 'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                                 'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                                 'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                                 'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']

    well_list_384w_emptycorners = ['C1', 'E1', 'G1', 'I1', 'K1', 'M1', 'A3', 'C3', 'E3', 'G3', 'I3', 'K3', 'M3', 'O3', 'A5', 'C5', 'E5', 'G5',
                                  'I5', 'K5', 'M5', 'O5', 'A7', 'C7', 'E7', 'G7', 'I7', 'K7', 'M7', 'O7', 'A9', 'C9', 'E9', 'G9', 'I9', 'K9', 'M9', 'O9',
                                  'A11', 'C11', 'E11', 'G11', 'I11', 'K11', 'M11', 'O11', 'A13', 'C13', 'E13', 'G13', 'I13', 'K13', 'M13', 'O13', 'A15',
                                  'C15', 'E15', 'G15', 'I15', 'K15', 'M15', 'O15', 'A17', 'C17', 'E17', 'G17', 'I17', 'K17', 'M17', 'O17', 'A19', 'C19',
                                  'E19', 'G19', 'I19', 'K19', 'M19', 'O19', 'A21', 'C21', 'E21', 'G21', 'I21', 'K21', 'M21', 'O21', 'C23', 'E23',
                                  'G23', 'I23', 'K23', 'M23']
    
    well_list_95w_1_empty = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'A3', 'B3', 'C3',
                     'D3', 'E3', 'F3', 'G3', 'H3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5',
                     'H5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'A8', 'B8', 'C8',
                     'D8', 'E8', 'F8', 'G8', 'H8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10',
                     'H10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12']

    # make dict with key = 96well position and value = equivalent 384well position
    # assuming 96-well plates stamped into upper left corner of 384well plate (A1 = A1)
    convert_96_to_384_plate = dict(zip(well_list_96w, well_list_384w))

    convert_384_to_96_plate = dict(zip(well_list_384w, well_list_96w))


    # set well list to 95wells with one empty corner. Standard formate for CE and SPS
    well_list = well_list_95w_1_empty

    return well_list, convert_96_to_384_plate, convert_384_to_96_plate
#########################
#########################



#########################
#########################
def extractLessInclusiv(less_inclusive):
    
    # make df from less inclusive file
    meta_df = pd.read_csv(less_inclusive,usecols=['proposal_id','sequencing_project_id','sequencing_project_name','sequencing_project_status','sample_id','sample_tube_plate_label','plate_location'])
    
    # remove rows when sequencing project status == "Abandoned"
    meta_df = meta_df.drop(meta_df[meta_df.sequencing_project_status == 'Abandoned'].index)
    
    # created sorted set of all source plates names in proposal. It's possible there are more
    # source plates in less inclusive than in current batch of echo files if not all SPS were created
    # at the same time
    all_proposal_source_plates = set(meta_df['sample_tube_plate_label'].unique().tolist())
    
    return meta_df, all_proposal_source_plates
#########################
#########################





##########################
##########################
def getEchoFiles(my_dirname):
    # create empty list to hold FA output files
    echo_files = []

# loop through all files in directory, find files end with .csv and add them to a list
# not all .csv are echo tranasfer files, so later step will verify the file has correct column headers
    for file in os.listdir(my_dirname):
        # if ((file.startswith('echo')) or (file.startswith('Echo'))) and (file.endswith('.csv')):
            # echo_files.append(file)
        
        if (file.endswith('.csv')):
            
            # read csv into pandas df
            loadcsv = pd.read_csv(file, header=0)
            
            # list of expected column headers in a proper echo transfer file
            expect_cols = set(['Source Plate Name','Source Plate Barcode','Source Row','Source Column','Destination Plate Name','Destination Plate Barcode','Destination Row','Destination Column','Transfer Volume'])
    
            # list of column headers found in df created from current .csv file
            found_cols = set(loadcsv.columns)
            
            
            # if found column headers matche expected column headers of an echo transfer file,
            # the add the .csv file name to a list of echo filees
            if len(expect_cols.difference(found_cols)) == 0:
            
                echo_files.append(file)

        else:
            continue

    # quit script if directory doesn't contain FA .csv files
    if len(echo_files) == 0:
        print(
            "\n\n Did not find any .csv echo transfer files.  Aborting program\n\n")
        sys.exit()

    else:

        # sort list of echo files and return        
        echo_files.sort()
        
        return echo_files
##########################
##########################



#########################
#########################
def parseEchoFiles(echo_files):
    # create dict where key is echo file name and value will be a df of the echo file
    echo_df_dict = {}

    # create dict where key is echo file name and value is a list of the destination barcode, destination plate name, and source plate name
    echo_info_dict = {}

    # create empty list to hold all destination plate barcodes
    dest_list = []
    
    # create empty list to hold all source plate barcodes
    source_list = []
    
    source_bc = []

    # loop through all echo files 
    for e in echo_files:
        
        # create a df in dict where key is echo  file name and value is df of the echo file
        echo_df_dict[e] = pd.read_csv(e)
        
        # # sort df by destination row and column
        # echo_df_dict[e] = echo_df_dict[e].sort_values(['Destination Row','Destination Column'])
        
        # extrat destination plate barcode, destination plate name, and source plate barcode
        dest_bc = echo_df_dict[e]['Destination Plate Barcode'].iloc[0]
        
        dest_name = echo_df_dict[e]['Destination Plate Name'].iloc[0]
        
        # source_bc = echo_df_dict[e]['Source Plate Barcode'].iloc[0]
        
        
        # add to dict where key is echo file name and value is destination barcode
        echo_info_dict[e] = [dest_bc,echo_df_dict[e]['Source Plate Barcode'].unique().tolist()]
        
        # add new destination bc to list
        dest_list.append(dest_bc)
        
        # source_list.append(source_bc)
        
        # append list of source plates in echo file to master source_list
        source_list = source_list + echo_df_dict[e]['Source Plate Barcode'].unique().tolist()


    # sort the list of destination barcodes    
    dest_list.sort()
    
    source_list.sort()
    
    source_set = set(source_list)
    
    # for k in echo_df_dict.keys():
    #     # sort df by destination row and column
    #     echo_df_dict[k] = echo_df_dict[k].sort_values(['Destination Row','Destination Column'])
    
    
    return echo_df_dict, echo_info_dict, dest_list, source_set
#########################
######################### 



#########################
######################### 
def compareSourcePlates(source_set, all_proposal_source_plates):
    
    # abort program if echo files contain source plates that were not in the less inclusive.csv summary file
    if len(source_set.difference(all_proposal_source_plates)) >0:
        print ('\n\n Some echo source plates were not found in the less_inclusive.csv summary.  Aborting script \n\n')
        sys.exit()
    
    # ask user if they want to continue if echo files do not include all source plates
    # associated with the entire proposal
    elif len(all_proposal_source_plates.difference(source_set))>=1:
        # make set of source plates in less inclusive file that weren't in the echo files
        extra_source = all_proposal_source_plates.difference(source_set)
        
        print (f"""
               The echo files did not include all source plates in the proposal.\n
               
               These source plates were NOT found in the echo files:\n
               {extra_source}\n
               Do you wish to continue withe just the echo files?  (y/n): \n""")

        val = input()

        if (val == 'Y' or val == 'y'):
            print("Ok, we'll keep going\n\n")

        elif (val == 'N' or val == 'n'):
            print('Ok, aborting script\n\n')
            sys.exit()
        else:
            print("Sorry, you must choose 'Y' or 'N' next time. \n\nAborting\n\n")
            sys.exit()                                           
        
    return
#########################
######################### 




#########################
#########################
def addDestandSourceWells(merged_df_df):
    
    # dict where key is number and value is upper case letter in alphabet
    alphabet_dict = dict(enumerate(string.ascii_uppercase, 1))
    
    # new column with desination well in 384-well plate    
    merged_df['Destination_Well'] = merged_df['Destination Row'].replace(alphabet_dict) + merged_df['Destination Column'].astype(str)

    # make new column where convert 384 well position to 96 well position
    merged_df['Destination_Well_96'] = merged_df['Destination_Well'].replace(convert_384_to_96_plate)
    
    # new column with desination well in 384-well plate    
    merged_df['Source_Well'] = merged_df['Source Row'].replace(alphabet_dict) + merged_df['Source Column'].astype(str)

    return merged_df

#########################
#########################



#########################
#########################
def combineMetaAndMergeDfs(meta_df, merged_df):
    
    # join meta_df and merged_df based on source plate id and source well position
    result_df = pd.merge(meta_df, merged_df, left_on=['sample_tube_plate_label','plate_location'], right_on=['Source Plate Barcode','Source_Well'], how='inner')

    # confirm that there were no missing values or  mismatches between meta_df angd merged_df
    # if merged_df.shape[0] != meta_df.shape[0]:
    #     print("\nThere was a mismatch between _info_submitted df and pool creation .xls sheets.  Aborting process\n")
    #     sys.exit()
        
    
    # update result_df with only a subset of columns
    result_df = result_df[['proposal_id',	'sequencing_project_name'	,'sequencing_project_id'	,'sample_id'	,'Source Plate Name'	,'Source Plate Barcode'	,'Source Row'	,'Source Column'	,'Source_Well'	,'Destination Plate Name'	,'Destination Plate Barcode','Destination Row'	,'Destination Column',	'Transfer Volume',	'Destination_Well'	,'Destination_Well_96']]


    return result_df
#########################
#########################




#########################
#########################
def addIlluminaIndex(my_import_df, spits):



    adapt_set_PE17 = ['PE17_A01','PE17_B01','PE17_C01','PE17_D01','PE17_E01','PE17_F01','PE17_G01','PE17_H01','PE17_A02','PE17_B02','PE17_C02','PE17_D02','PE17_E02','PE17_F02','PE17_G02','PE17_H02','PE17_A03','PE17_B03','PE17_C03','PE17_D03','PE17_E03','PE17_F03','PE17_G03','PE17_H03','PE17_A04','PE17_B04','PE17_C04','PE17_D04','PE17_E04','PE17_F04','PE17_G04','PE17_H04','PE17_A05','PE17_B05','PE17_C05','PE17_D05','PE17_E05','PE17_F05','PE17_G05','PE17_H05','PE17_A06','PE17_B06','PE17_C06','PE17_D06','PE17_E06','PE17_F06','PE17_G06','PE17_H06','PE17_A07','PE17_B07','PE17_C07','PE17_D07','PE17_E07','PE17_F07','PE17_G07','PE17_H07','PE17_A08','PE17_B08','PE17_C08','PE17_D08','PE17_E08','PE17_F08','PE17_G08','PE17_H08','PE17_A09','PE17_B09','PE17_C09','PE17_D09','PE17_E09','PE17_F09','PE17_G09','PE17_H09','PE17_A10','PE17_B10','PE17_C10','PE17_D10','PE17_E10','PE17_F10','PE17_G10','PE17_H10','PE17_A11','PE17_B11','PE17_C11','PE17_D11','PE17_E11','PE17_F11','PE17_G11','PE17_H11','PE17_A12','PE17_B12','PE17_C12','PE17_D12','PE17_E12','PE17_F12','PE17_G12','PE17_H12']

    adapt_set_PE18 = ['PE18_A01','PE18_B01','PE18_C01','PE18_D01','PE18_E01','PE18_F01','PE18_G01','PE18_H01','PE18_A02','PE18_B02','PE18_C02','PE18_D02','PE18_E02','PE18_F02','PE18_G02','PE18_H02','PE18_A03','PE18_B03','PE18_C03','PE18_D03','PE18_E03','PE18_F03','PE18_G03','PE18_H03','PE18_A04','PE18_B04','PE18_C04','PE18_D04','PE18_E04','PE18_F04','PE18_G04','PE18_H04','PE18_A05','PE18_B05','PE18_C05','PE18_D05','PE18_E05','PE18_F05','PE18_G05','PE18_H05','PE18_A06','PE18_B06','PE18_C06','PE18_D06','PE18_E06','PE18_F06','PE18_G06','PE18_H06','PE18_A07','PE18_B07','PE18_C07','PE18_D07','PE18_E07','PE18_F07','PE18_G07','PE18_H07','PE18_A08','PE18_B08','PE18_C08','PE18_D08','PE18_E08','PE18_F08','PE18_G08','PE18_H08','PE18_A09','PE18_B09','PE18_C09','PE18_D09','PE18_E09','PE18_F09','PE18_G09','PE18_H09','PE18_A10','PE18_B10','PE18_C10','PE18_D10','PE18_E10','PE18_F10','PE18_G10','PE18_H10','PE18_A11','PE18_B11','PE18_C11','PE18_D11','PE18_E11','PE18_F11','PE18_G11','PE18_H11','PE18_A12','PE18_B12','PE18_C12','PE18_D12','PE18_E12','PE18_F12','PE18_G12','PE18_H12']
    
    adapt_set_PE19 = ['PE19_A01','PE19_B01','PE19_C01','PE19_D01','PE19_E01','PE19_F01','PE19_G01','PE19_H01','PE19_A02','PE19_B02','PE19_C02','PE19_D02','PE19_E02','PE19_F02','PE19_G02','PE19_H02','PE19_A03','PE19_B03','PE19_C03','PE19_D03','PE19_E03','PE19_F03','PE19_G03','PE19_H03','PE19_A04','PE19_B04','PE19_C04','PE19_D04','PE19_E04','PE19_F04','PE19_G04','PE19_H04','PE19_A05','PE19_B05','PE19_C05','PE19_D05','PE19_E05','PE19_F05','PE19_G05','PE19_H05','PE19_A06','PE19_B06','PE19_C06','PE19_D06','PE19_E06','PE19_F06','PE19_G06','PE19_H06','PE19_A07','PE19_B07','PE19_C07','PE19_D07','PE19_E07','PE19_F07','PE19_G07','PE19_H07','PE19_A08','PE19_B08','PE19_C08','PE19_D08','PE19_E08','PE19_F08','PE19_G08','PE19_H08','PE19_A09','PE19_B09','PE19_C09','PE19_D09','PE19_E09','PE19_F09','PE19_G09','PE19_H09','PE19_A10','PE19_B10','PE19_C10','PE19_D10','PE19_E10','PE19_F10','PE19_G10','PE19_H10','PE19_A11','PE19_B11','PE19_C11','PE19_D11','PE19_E11','PE19_F11','PE19_G11','PE19_H11','PE19_A12','PE19_B12','PE19_C12','PE19_D12','PE19_E12','PE19_F12','PE19_G12','PE19_H12']
    
    adapt_set_PE20 = ['PE20_A01','PE20_B01','PE20_C01','PE20_D01','PE20_E01','PE20_F01','PE20_G01','PE20_H01','PE20_A02','PE20_B02','PE20_C02','PE20_D02','PE20_E02','PE20_F02','PE20_G02','PE20_H02','PE20_A03','PE20_B03','PE20_C03','PE20_D03','PE20_E03','PE20_F03','PE20_G03','PE20_H03','PE20_A04','PE20_B04','PE20_C04','PE20_D04','PE20_E04','PE20_F04','PE20_G04','PE20_H04','PE20_A05','PE20_B05','PE20_C05','PE20_D05','PE20_E05','PE20_F05','PE20_G05','PE20_H05','PE20_A06','PE20_B06','PE20_C06','PE20_D06','PE20_E06','PE20_F06','PE20_G06','PE20_H06','PE20_A07','PE20_B07','PE20_C07','PE20_D07','PE20_E07','PE20_F07','PE20_G07','PE20_H07','PE20_A08','PE20_B08','PE20_C08','PE20_D08','PE20_E08','PE20_F08','PE20_G08','PE20_H08','PE20_A09','PE20_B09','PE20_C09','PE20_D09','PE20_E09','PE20_F09','PE20_G09','PE20_H09','PE20_A10','PE20_B10','PE20_C10','PE20_D10','PE20_E10','PE20_F10','PE20_G10','PE20_H10','PE20_A11','PE20_B11','PE20_C11','PE20_D11','PE20_E11','PE20_F11','PE20_G11','PE20_H11','PE20_A12','PE20_B12','PE20_C12','PE20_D12','PE20_E12','PE20_F12','PE20_G12','PE20_H12']
    
    
  
    # creat dict where key is index set# + well postion, and values is illumin index ID
    dict_index = dict(zip(['PE17' + w for w in well_list_96w], adapt_set_PE17)
                        ) | dict(zip(['PE18' + w for w in well_list_96w], adapt_set_PE18)) | dict(zip(['PE19' + w for w in well_list_96w], adapt_set_PE19)) | dict(zip(['PE20' + w for w in well_list_96w], adapt_set_PE20))


    # create list of illumin index set numbers
    ill_sets = ['PE17', 'PE18', 'PE19','PE20']
    
    
    
    spits_df = pd.read_excel(spits, usecols=['Destination Container Name','Destination Container Location','Internal Collaborator Sample Name'])
    
    spits_df['Illumina_index_set'] = spits_df['Internal Collaborator Sample Name'].str.split('_').str[-1]
    
    spits_df.drop(['Internal Collaborator Sample Name'], inplace=True, axis=1)
    
    spits_df = spits_df.rename(columns={'Destination Container Name':'Destination Plate Name','Destination Container Location':'Destination_Well'})
    
    # merge df's to add illumina index set to my_import_df
    my_import_df = pd.merge(my_import_df, spits_df, left_on=['Destination Plate Name','Destination_Well'], right_on=['Destination Plate Name','Destination_Well'], how = 'inner')
    

    # add new row that's a concat of the illumina index set and well postion
    my_import_df['Illumina_index'] = my_import_df['Illumina_index_set'] + \
        my_import_df['Destination_Well_96']

    # replace index set and well poistion wiht JGI illumina index ID using dict
    my_import_df['Illumina_index'] = my_import_df['Illumina_index'].replace(
        dict_index)

    if (my_import_df['Illumina_index'].isnull().any()) or (my_import_df['Illumina_index_set'].isnull().any()):
        
        print('\n\nProblem adding illumina index. terminating script\n\n')
        sys.exit()

    return my_import_df

#########################
#########################



#########################
#########################
def createIllumDataframe(result_df):

    illum_df = result_df[['Destination Plate Barcode','Destination_Well',
                          'Destination_Well_96', 'Illumina_index_set']].copy()

    # adjuste volume of primer addition based on tagementation reactions size
    illum_df['Primer_volume_(uL)'] = 2

    # illum_df['Illumina_source_well'] = illum_df['Destination_Well_96']
    
    # illum_df.drop(['Destination_Well_96'], inplace=True, axis=1)

    illum_df = illum_df.rename(
        columns={'Destination_Well': 'Lib_plate_well', 'Destination Plate Barcode': 'Lib_plate_ID','Destination_Well_96':'Illumina_source_well'})

    # rearrange column order
    illum_column_list = ['Illumina_index_set',
                         'Illumina_source_well', 'Lib_plate_ID', 'Lib_plate_well', 'Primer_volume_(uL)']

    illum_df = illum_df.reindex(columns=illum_column_list)

    return illum_df
#########################
#########################



#########################
#########################
def createFAdataframe(result_df):

    FA_df = result_df[['Destination_Well_96',
                        'Destination Plate Barcode', 'sample_id']].copy()
    
    FA_df['sample_id'] = FA_df['sample_id'].astype(str)


    FA_df['name'] = FA_df[['Destination Plate Barcode', 'sample_id', 'Destination_Well_96']].agg(
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

        tmp_fa_df = tmp_fa_df.merge(FA_df.loc[FA_df['Destination Plate Barcode'] == d], how='outer', left_on=['Well'],
                                    right_on=['Destination_Well_96'])

        # updated index so begins at 1 instead of 0.  Index column will be added to FA input file
        tmp_fa_df.index = range(1, tmp_fa_df.shape[0]+1)

        tmp_fa_df.drop(['Destination Plate Barcode', 'Destination_Well_96'],
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
        tmp_illum_df = illum_df.loc[illum_df['Lib_plate_ID'] == d].copy()

        # add "h" prefix to lib plate ID because barcode label on plate side read by
        # hamilton scanner has "h" prefix
        tmp_illum_df['Lib_plate_ID'] = "h" + \
            tmp_illum_df['Lib_plate_ID'].astype(str)

        # create echo transfer file
        tmp_illum_df.to_csv(INDEX_DIR / f'Illumina_index_transfer_{d}.csv', index=False)
        
        
#########################
#########################


#########################
#########################
def makeBarcodeLabels(result_df, dest_list):

    # # creates lists of source and destination plate barcodes
    # source_list = result_df['Source Plate Barcode'].unique().tolist()

    # this was older format for bartender templates.  The newer version below changes "/" to "\"
    # in the path to the template files  AF="*"
    # x = '%BTW% /AF="//BARTENDER/shared/templates/ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'

    # add info to start of barcode print file indicating the template and printer to use
    x = '%BTW% /AF="\\\BARTENDER\shared\\templates\ECHO_BCode8.btw" /D="%Trigger File Name%" /PRN="bcode8" /R=3 /P /DD\r\n\r\n%END%\r\n\r\n\r\n'


    bc_file = open("BARTENDER_IlluminaIndex_FA_plates.txt", "w")

    bc_file.writelines(x)
    
    # revoerse sort the destination plate list
    dest_list.reverse()

    

    for p in dest_list:
        bc_file.writelines(f'{p}F,"FA.run {p}F"\r\n')
        
    bc_file.writelines(',\r\n')
    

    for p in dest_list:
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
        
        
    bc_file.writelines(',\r\n')   
    
    
    # add barcodes of library destination plates, dna source plates, and buffer plate
    for p in dest_list:
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
        
        bc_file.writelines(f'h{p},"     h{p}"\r\n')
        
        bc_file.writelines(f'{p},"SPS.lib.plate {p}"\r\n')
        
        




    bc_file.close()
    
    # move each echo file to new sub directory
    Path(BASE_DIR / "BARTENDER_IlluminaIndex_FA_plates.txt").rename(LIB_DIR / "BARTENDER_IlluminaIndex_FA_plates.txt")
   
    
    
#########################
#########################



#########################
#########################
def makeThreshold(final_df, dest_list):

    # thresh_df = pd.DataFrame(dest_list)
    
    plate_dict = dict(zip(final_df['Destination Plate Barcode'],final_df['dilution_factor']))
    
    
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
    thresh_df.to_csv(ANALYZE_DIR / 'thresholds.txt', index=False, sep='\t')

    return
#########################
#########################




#########################
#########################
def createProjectFile(result_df):
    
    # ask user the fold dilution used to set up FA plate
    dilution_factor = float(input(
        "What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): ") or 5)
    
    
    # update result_df with only a subset of columns
    final_df = result_df[['proposal_id',	'sequencing_project_name'	,'sequencing_project_id','sample_id','Source Plate Name','Source_Well','Destination Plate Barcode','Destination_Well','Destination_Well_96','Illumina_index_set','Illumina_index']]

    # add dilutioon factor column to data frame.
    final_df['dilution_factor'] = dilution_factor
    
    final_df = final_df.rename(columns={'Destination_Well_96':'FA_Well'})

    final_df.to_csv("project_summary.csv",index=False)

    # # make the project_summary.csv read only
    # os.chmod("project_summary.csv", S_IREAD|S_IRGRP|S_IROTH)    

    return final_df

#########################
#########################



#########################
#########################
def createSQLdb(final_df):
    

    sql_db_path = BASE_DIR /'project_summary.db'

    engine = create_engine(f'sqlite:///{sql_db_path}') 


    # Specify the table name and database engine
    table_name = 'project_summary'
    
    # Export the DataFrame to the SQLite database
    final_df.to_sql(table_name, engine, if_exists='replace', index=False) 

    engine.dispose()

    return
#########################
#########################



#########################
#########################
def makeDilution(final_df):
    
    
    # # ask user if using 96-well or 384-well plate for library construction
    # dilution_factor = float(input(
    #     "What is the desired fold-dilution for libraries loaded into the FA plate? (default 5): ") or 5)
    
    

    
    
    dilution_df = final_df[['Destination Plate Barcode','Destination_Well','FA_Well','dilution_factor']].copy()
    
    # rename columns to match dilution transfer file format
    dilution_df = dilution_df.rename(columns={'Destination Plate Barcode' : 'Library_Plate_Barcode', 'Destination_Well' : 'Library_Well'})

    # make column for FA barcode by appending "F" to libary barcode
    dilution_df['FA_Plate_Barcode'] = dilution_df['Library_Plate_Barcode']+"F"
    
    # make column for dilution plate barcode by appending "D" to libary barcode
    dilution_df['Dilution_Plate_Barcode'] = dilution_df['Library_Plate_Barcode']+"D"
    

    dilution_df['Nextera_Vol_Add'] = 30
    
    
    dilution_df['FA_Vol_Add'] = 2.4
    
    dilution_df['Dilution_Vol'] = 2.4
    
    # # calculate the volume of  buffer that should be added to the dilution plate
    # dilution_df['Dilution_Plate_Preload'] = np.ceil((dilution_factor-1) * dilution_df['FA_Vol_Add'])
    
    # calculate the volume of  buffer that should be added to the dilution plate
    dilution_df['Dilution_Plate_Preload'] = np.ceil((dilution_df['dilution_factor']-1) * dilution_df['FA_Vol_Add'])
    
    
    
    
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

        # had "h" prefix to library plate for reading barcode on Hamilton Star
        tmp_df['Library_Plate_Barcode'] = 'h'+tmp_df['Library_Plate_Barcode']

        # create echo transfer file
        tmp_df.to_csv(FTRAN_DIR / f'FA_plate_transfer_{d}.csv', index=False)

    return
#########################
#########################



#########################
#########################
### MAIN PROGRAM  #######
#########################
#########################


# create all sub folders for project folder
BASE_DIR, PROJECT_DIR, LIB_DIR, ECHO_DIR, FA_DIR, INDEX_DIR, ANALYZE_DIR, FTRAN_DIR = createDirectories()


# get current working directory and its parent directory
crnt_dir = os.getcwd()
prnt_dir = os.path.dirname(crnt_dir)
prjct_dir = os.path.dirname(prnt_dir)

# get name of less inclusive.csv summary file downloaded from data warehouse
less_inclusive = sys.argv[1]

spits = sys.argv[2]

# create df of info from the less inclusive file
meta_df, all_proposal_source_plates = extractLessInclusiv(less_inclusive)

# determine type of plate format (96 or 384) for library creation
well_list, convert_96_to_384_plate, convert_384_to_96_plate = getPlateType()


# get list of .xls clarity lib creation files
echo_files = getEchoFiles(crnt_dir)

# parse echo files, make df's of each file, and get lists of destination and source plate barcodes
echo_df_dict, echo_info_dict, dest_list, source_set = parseEchoFiles(echo_files)

# compare source plates found in echo files vs those in the less inclusive.csv summary file
compareSourcePlates(source_set, all_proposal_source_plates)

    
# sort each echo_df by row and column
for k in echo_df_dict.keys():
    
    dest_id = echo_info_dict[k][0]
    
    source_id = '_'.join(map(str,echo_info_dict[k][1]))
    
    # sort df by destination row and column
    echo_df_dict[k] = echo_df_dict[k].sort_values(['Destination Row','Destination Column'])
    
    # # move each echo file to new sub directory
    # Path(BASE_DIR /
    #       f"{k}").rename(ECHO_DIR / f"{echo_info_dict[k][0]}_{echo_info_dict[k][1]}.csv")
    # Path(ECHO_DIR / f"{k}").touch()
    
    # move each echo file to new sub directory
    Path(BASE_DIR /
          f"{k}").rename(ECHO_DIR / f"{dest_id}_{source_id}.csv")

# merge all echo plates df's into one big df
merged_df = pd.concat(echo_df_dict.values(), ignore_index=True)


# add new columns with well position in source and destination plates (384well format),
# and an additional column of destination well position in in 96 well format
merged_df = addDestandSourceWells(merged_df)


# genearte new df after joining meta_df and merged_df
result_df = combineMetaAndMergeDfs(meta_df, merged_df)


# add column with Illumina index used in each well
result_df = addIlluminaIndex(result_df, spits)

# make df for later determining which index set to use
illum_df = createIllumDataframe(result_df)



# make FA_df for generating FA files
FA_df = createFAdataframe(result_df)

# make upload files for FA runs
makeFAfiles(FA_df, dest_list, well_list_96w)

# make transfer files for adding Illumina indexes
makeIlluminaFiles(illum_df, dest_list)


# make .txt for printing barcodes of echo, library, FA, and dilution plates
makeBarcodeLabels(result_df, dest_list)

# make .csv project summary file
final_df = createProjectFile(result_df)

# create sql .db file 
createSQLdb(final_df)



# make threshold.txt file for FA output analysis in next step of SIP wetlab process
makeThreshold(final_df, dest_list)

# create df with info necessary for makign the FA plates
dilution_df = makeDilution(final_df)

# make hamilton transfer files for setting up FA plate
makeDilutionFile(dilution_df, dest_list)


# move less inclusive .csv file to subdirectory 1)
Path(BASE_DIR /
      f"{less_inclusive}").rename(LIB_DIR / f"{less_inclusive}")


