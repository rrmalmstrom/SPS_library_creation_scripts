#!/usr/bin/env python3

# USAGE:   python sps_make_illumina_index_and_FA_files.py <less_inclusive.csv>

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
def addIlluminaIndex(result_df):

    adapt_set_5 = ['5A01i7-7A01i5',	'5B01i7-7B01i5',	'5C01i7-7C01i5',	'5D01i7-7D01i5',	'5E01i7-7E01i5',	'5F01i7-7F01i5',	'5G01i7-7G01i5',	'5H01i7-7H01i5',	'5A02i7-7A02i5',	'5B02i7-7B02i5',	'5C02i7-7C02i5',	'5D02i7-7D02i5',	'5E02i7-7E02i5',	'5F02i7-7F02i5',	'5G02i7-7G02i5',	'5H02i7-7H02i5',	'5A03i7-7A03i5',	'5B03i7-7B03i5',	'5C03i7-7C03i5',	'5D03i7-7D03i5',	'5E03i7-7E03i5',	'5F03i7-7F03i5',	'5G03i7-7G03i5',	'5H03i7-7H03i5',	'5A04i7-7A04i5',	'5B04i7-7B04i5',	'5C04i7-7C04i5',	'5D04i7-7D04i5',	'5E04i7-7E04i5',	'5F04i7-7F04i5',	'5G04i7-7G04i5',	'5H04i7-7H04i5',	'5A05i7-7A05i5',	'5B05i7-7B05i5',	'5C05i7-7C05i5',	'5D05i7-7D05i5',	'5E05i7-7E05i5',	'5F05i7-7F05i5',	'5G05i7-7G05i5',	'5H05i7-7H05i5',	'5A06i7-7A06i5',	'5B06i7-7B06i5',	'5C06i7-7C06i5',	'5D06i7-7D06i5',	'5E06i7-7E06i5',	'5F06i7-7F06i5',	'5G06i7-7G06i5',	'5H06i7-7H06i5',
                   '5A07i7-7A07i5',	'5B07i7-7B07i5',	'5C07i7-7C07i5',	'5D07i7-7D07i5',	'5E07i7-7E07i5',	'5F07i7-7F07i5',	'5G07i7-7G07i5',	'5H07i7-7H07i5',	'5A08i7-7A08i5',	'5B08i7-7B08i5',	'5C08i7-7C08i5',	'5D08i7-7D08i5',	'5E08i7-7E08i5',	'5F08i7-7F08i5',	'5G08i7-7G08i5',	'5H08i7-7H08i5',	'5A09i7-7A09i5',	'5B09i7-7B09i5',	'5C09i7-7C09i5',	'5D09i7-7D09i5',	'5E09i7-7E09i5',	'5F09i7-7F09i5',	'5G09i7-7G09i5',	'5H09i7-7H09i5',	'5A10i7-7A10i5',	'5B10i7-7B10i5',	'5C10i7-7C10i5',	'5D10i7-7D10i5',	'5E10i7-7E10i5',	'5F10i7-7F10i5',	'5G10i7-7G10i5',	'5H10i7-7H10i5',	'5A11i7-7A11i5',	'5B11i7-7B11i5',	'5C11i7-7C11i5',	'5D11i7-7D11i5',	'5E11i7-7E11i5',	'5F11i7-7F11i5',	'5G11i7-7G11i5',	'5H11i7-7H11i5',	'5A12i7-7A12i5',	'5B12i7-7B12i5',	'5C12i7-7C12i5',	'5D12i7-7D12i5',	'5E12i7-7E12i5',	'5F12i7-7F12i5',	'5G12i7-7G12i5',	'5H12i7-7H12i5']

    adapt_set_6 = ['6A01i7-8A01i5',	'6B01i7-8B01i5',	'6C01i7-8C01i5',	'6D01i7-8D01i5',	'6E01i7-8E01i5',	'6F01i7-8F01i5',	'6G01i7-8G01i5',	'6H01i7-8H01i5',	'6A02i7-8A02i5',	'6B02i7-8B02i5',	'6C02i7-8C02i5',	'6D02i7-8D02i5',	'6E02i7-8E02i5',	'6F02i7-8F02i5',	'6G02i7-8G02i5',	'6H02i7-8H02i5',	'6A03i7-8A03i5',	'6B03i7-8B03i5',	'6C03i7-8C03i5',	'6D03i7-8D03i5',	'6E03i7-8E03i5',	'6F03i7-8F03i5',	'6G03i7-8G03i5',	'6H03i7-8H03i5',	'6A04i7-8A04i5',	'6B04i7-8B04i5',	'6C04i7-8C04i5',	'6D04i7-8D04i5',	'6E04i7-8E04i5',	'6F04i7-8F04i5',	'6G04i7-8G04i5',	'6H04i7-8H04i5',	'6A05i7-8A05i5',	'6B05i7-8B05i5',	'6C05i7-8C05i5',	'6D05i7-8D05i5',	'6E05i7-8E05i5',	'6F05i7-8F05i5',	'6G05i7-8G05i5',	'6H05i7-8H05i5',	'6A06i7-8A06i5',	'6B06i7-8B06i5',	'6C06i7-8C06i5',	'6D06i7-8D06i5',	'6E06i7-8E06i5',	'6F06i7-8F06i5',	'6G06i7-8G06i5',	'6H06i7-8H06i5',
                   '6A07i7-8A07i5',	'6B07i7-8B07i5',	'6C07i7-8C07i5',	'6D07i7-8D07i5',	'6E07i7-8E07i5',	'6F07i7-8F07i5',	'6G07i7-8G07i5',	'6H07i7-8H07i5',	'6A08i7-8A08i5',	'6B08i7-8B08i5',	'6C08i7-8C08i5',	'6D08i7-8D08i5',	'6E08i7-8E08i5',	'6F08i7-8F08i5',	'6G08i7-8G08i5',	'6H08i7-8H08i5',	'6A09i7-8A09i5',	'6B09i7-8B09i5',	'6C09i7-8C09i5',	'6D09i7-8D09i5',	'6E09i7-8E09i5',	'6F09i7-8F09i5',	'6G09i7-8G09i5',	'6H09i7-8H09i5',	'6A10i7-8A10i5',	'6B10i7-8B10i5',	'6C10i7-8C10i5',	'6D10i7-8D10i5',	'6E10i7-8E10i5',	'6F10i7-8F10i5',	'6G10i7-8G10i5',	'6H10i7-8H10i5',	'6A11i7-8A11i5',	'6B11i7-8B11i5',	'6C11i7-8C11i5',	'6D11i7-8D11i5',	'6E11i7-8E11i5',	'6F11i7-8F11i5',	'6G11i7-8G11i5',	'6H11i7-8H11i5',	'6A12i7-8A12i5',	'6B12i7-8B12i5',	'6C12i7-8C12i5',	'6D12i7-8D12i5',	'6E12i7-8E12i5',	'6F12i7-8F12i5',	'6G12i7-8G12i5',	'6H12i7-8H12i5']

    adapt_set_7 = ['7A01i7-5A01i5',	'7B01i7-5B01i5',	'7C01i7-5C01i5',	'7D01i7-5D01i5',	'7E01i7-5E01i5',	'7F01i7-5F01i5',	'7G01i7-5G01i5',	'7H01i7-5H01i5',	'7A02i7-5A02i5',	'7B02i7-5B02i5',	'7C02i7-5C02i5',	'7D02i7-5D02i5',	'7E02i7-5E02i5',	'7F02i7-5F02i5',	'7G02i7-5G02i5',	'7H02i7-5H02i5',	'7A03i7-5A03i5',	'7B03i7-5B03i5',	'7C03i7-5C03i5',	'7D03i7-5D03i5',	'7E03i7-5E03i5',	'7F03i7-5F03i5',	'7G03i7-5G03i5',	'7H03i7-5H03i5',	'7A04i7-5A04i5',	'7B04i7-5B04i5',	'7C04i7-5C04i5',	'7D04i7-5D04i5',	'7E04i7-5E04i5',	'7F04i7-5F04i5',	'7G04i7-5G04i5',	'7H04i7-5H04i5',	'7A05i7-5A05i5',	'7B05i7-5B05i5',	'7C05i7-5C05i5',	'7D05i7-5D05i5',	'7E05i7-5E05i5',	'7F05i7-5F05i5',	'7G05i7-5G05i5',	'7H05i7-5H05i5',	'7A06i7-5A06i5',	'7B06i7-5B06i5',	'7C06i7-5C06i5',	'7D06i7-5D06i5',	'7E06i7-5E06i5',	'7F06i7-5F06i5',	'7G06i7-5G06i5',	'7H06i7-5H06i5',
                   '7A07i7-5A07i5',	'7B07i7-5B07i5',	'7C07i7-5C07i5',	'7D07i7-5D07i5',	'7E07i7-5E07i5',	'7F07i7-5F07i5',	'7G07i7-5G07i5',	'7H07i7-5H07i5',	'7A08i7-5A08i5',	'7B08i7-5B08i5',	'7C08i7-5C08i5',	'7D08i7-5D08i5',	'7E08i7-5E08i5',	'7F08i7-5F08i5',	'7G08i7-5G08i5',	'7H08i7-5H08i5',	'7A09i7-5A09i5',	'7B09i7-5B09i5',	'7C09i7-5C09i5',	'7D09i7-5D09i5',	'7E09i7-5E09i5',	'7F09i7-5F09i5',	'7G09i7-5G09i5',	'7H09i7-5H09i5',	'7A10i7-5A10i5',	'7B10i7-5B10i5',	'7C10i7-5C10i5',	'7D10i7-5D10i5',	'7E10i7-5E10i5',	'7F10i7-5F10i5',	'7G10i7-5G10i5',	'7H10i7-5H10i5',	'7A11i7-5A11i5',	'7B11i7-5B11i5',	'7C11i7-5C11i5',	'7D11i7-5D11i5',	'7E11i7-5E11i5',	'7F11i7-5F11i5',	'7G11i7-5G11i5',	'7H11i7-5H11i5',	'7A12i7-5A12i5',	'7B12i7-5B12i5',	'7C12i7-5C12i5',	'7D12i7-5D12i5',	'7E12i7-5E12i5',	'7F12i7-5F12i5',	'7G12i7-5G12i5',	'7H12i7-5H12i5']

    adapt_set_8 = ['8A01i7-6A01i5',	'8B01i7-6B01i5',	'8C01i7-6C01i5',	'8D01i7-6D01i5',	'8E01i7-6E01i5',	'8F01i7-6F01i5',	'8G01i7-6G01i5',	'8H01i7-6H01i5',	'8A02i7-6A02i5',	'8B02i7-6B02i5',	'8C02i7-6C02i5',	'8D02i7-6D02i5',	'8E02i7-6E02i5',	'8F02i7-6F02i5',	'8G02i7-6G02i5',	'8H02i7-6H02i5',	'8A03i7-6A03i5',	'8B03i7-6B03i5',	'8C03i7-6C03i5',	'8D03i7-6D03i5',	'8E03i7-6E03i5',	'8F03i7-6F03i5',	'8G03i7-6G03i5',	'8H03i7-6H03i5',	'8A04i7-6A04i5',	'8B04i7-6B04i5',	'8C04i7-6C04i5',	'8D04i7-6D04i5',	'8E04i7-6E04i5',	'8F04i7-6F04i5',	'8G04i7-6G04i5',	'8H04i7-6H04i5',	'8A05i7-6A05i5',	'8B05i7-6B05i5',	'8C05i7-6C05i5',	'8D05i7-6D05i5',	'8E05i7-6E05i5',	'8F05i7-6F05i5',	'8G05i7-6G05i5',	'8H05i7-6H05i5',	'8A06i7-6A06i5',	'8B06i7-6B06i5',	'8C06i7-6C06i5',	'8D06i7-6D06i5',	'8E06i7-6E06i5',	'8F06i7-6F06i5',	'8G06i7-6G06i5',	'8H06i7-6H06i5',
                   '8A07i7-6A07i5',	'8B07i7-6B07i5',	'8C07i7-6C07i5',	'8D07i7-6D07i5',	'8E07i7-6E07i5',	'8F07i7-6F07i5',	'8G07i7-6G07i5',	'8H07i7-6H07i5',	'8A08i7-6A08i5',	'8B08i7-6B08i5',	'8C08i7-6C08i5',	'8D08i7-6D08i5',	'8E08i7-6E08i5',	'8F08i7-6F08i5',	'8G08i7-6G08i5',	'8H08i7-6H08i5',	'8A09i7-6A09i5',	'8B09i7-6B09i5',	'8C09i7-6C09i5',	'8D09i7-6D09i5',	'8E09i7-6E09i5',	'8F09i7-6F09i5',	'8G09i7-6G09i5',	'8H09i7-6H09i5',	'8A10i7-6A10i5',	'8B10i7-6B10i5',	'8C10i7-6C10i5',	'8D10i7-6D10i5',	'8E10i7-6E10i5',	'8F10i7-6F10i5',	'8G10i7-6G10i5',	'8H10i7-6H10i5',	'8A11i7-6A11i5',	'8B11i7-6B11i5',	'8C11i7-6C11i5',	'8D11i7-6D11i5',	'8E11i7-6E11i5',	'8F11i7-6F11i5',	'8G11i7-6G11i5',	'8H11i7-6H11i5',	'8A12i7-6A12i5',	'8B12i7-6B12i5',	'8C12i7-6C12i5',	'8D12i7-6D12i5',	'8E12i7-6E12i5',	'8F12i7-6F12i5',	'8G12i7-6G12i5',	'8H12i7-6H12i5']

    # creat dict where key is index set# + well postion(96), and values is illumin index ID
    dict_index = dict(zip(['5' + w for w in well_list_96w], adapt_set_5)
                      ) | dict(zip(['6' + w for w in well_list_96w], adapt_set_6)) | dict(zip(['7' + w for w in well_list_96w], adapt_set_7)) | dict(zip(['8' + w for w in well_list_96w], adapt_set_8))


    # create list of illumin index set numbers
    ill_sets = ['6', '7', '8']

    dest_id_dict = {}

    # get list of uniqued destination plate IDs
    tmp_list = result_df['Destination Plate Barcode'].unique()

    ## create dict were keys are destination plate barcides and values are illumina index set#
    # the modulo is used because the number of destination plates might exceed the number
    # of index sets, so the module wraps around ill_set list
    for cnt, dp in enumerate(tmp_list):
        id_set = str(ill_sets[cnt % len(ill_sets)])
        dest_id_dict[dp] = id_set

    # add new column with illumina set # based on Destination ID by looking up in dict
    result_df['Illumina_index_set'] = result_df['Destination Plate Barcode'].replace(
        dest_id_dict)

    # add new row that's a concat of the illumina index set and well postion
    result_df['Illumina_index'] = result_df['Illumina_index_set'] + \
        result_df['Destination_Well_96']

    # replace index set and well poistion wiht JGI illumina index ID using dict
    result_df['Illumina_index'] = result_df['Illumina_index'].replace(
        dict_index)

    # add new column that's a concat of the illumina index set and well postion
    result_df['Illumina_index_set'] = 'Nextera_Index-' + \
        result_df['Illumina_index_set']

    return result_df

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


    bc_file = open("labels_IlluminaIndex_FA_plates.txt", "w")

    bc_file.writelines(x)

    # bc_file.writelines('Buffer,Buffer.plate\r\n')

    # for s in source_list:
    #     bc_file.writelines(f'e{s},"e{s} echo.plate"\r\n')
    #     bc_file.writelines(f'h{s},"h{s} echo.plate"\r\n')

    # add barcodes of library destination plates, dna source plates, and buffer plate
    for p in dest_list:
        bc_file.writelines(f'{p},"SPS.lib.plate {p}"\r\n')
        bc_file.writelines(f'h{p},"SPS.lib.plate h{p}"\r\n')
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')
        
    bc_file.writelines(',\r\n')


    for p in dest_list:
        bc_file.writelines(f'{p}D,"FA.dilute {p}D"\r\n')

    bc_file.writelines(',\r\n')

    for p in dest_list:
        bc_file.writelines(f'{p}F,"FA.run {p}F"\r\n')

    bc_file.close()
    
    # move each echo file to new sub directory
    Path(BASE_DIR / "labels_IlluminaIndex_FA_plates.txt").rename(LIB_DIR / "labels_IlluminaIndex_FA_plates.txt")
   
    
    
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

    # make the project_summary.csv read only
    os.chmod("project_summary.csv", S_IREAD|S_IRGRP|S_IROTH)    

    return final_df

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
result_df = addIlluminaIndex(result_df)

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



# make threshold.txt file for FA output analysis in next step of SIP wetlab process
makeThreshold(final_df, dest_list)

# create df with info necessary for makign the FA plates
dilution_df = makeDilution(final_df)

# make hamilton transfer files for setting up FA plate
makeDilutionFile(dilution_df, dest_list)


# # move less inclusive .csv file to subdirectory 1)
# Path(BASE_DIR /
#       f"{less_inclusive}").rename(LIB_DIR / f"{less_inclusive}")


