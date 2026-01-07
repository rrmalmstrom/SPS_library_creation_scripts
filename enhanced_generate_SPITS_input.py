#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## USAGE:  python enhanced_generate_SPITS_input.py <manually modified summary_MDA_results.csv> <SingleCell Query - Echo Barcodes.csv>

import pandas as pd
import numpy as np
import sys
import random
import string
from sqlalchemy import create_engine
from pathlib import Path
from datetime import datetime

# Constants
MAX_SAMPLES_PER_PLATE = 83  # Each Illumina index set has at least 83 validated indexes; set to 83 for consistency
NUM_ILLUMINA_INDEX_SETS = 4  # Number of available Illumina index sets (PE17-PE20)

# Illumina index exclude lists - wells to exclude from each index set
PE17_EXCLUDE = ['A1','H1','A12','H12','B2','B5']
PE18_EXCLUDE = ['A1','H1','A12','H12','D1','C2','H2','G3','C4','D4','C5','C10']
PE19_EXCLUDE = ['A1','H1','A12','H12','A4','B4','B6','A9','A10']
PE20_EXCLUDE = ['A1','H1','A12','H12','D2','B3','E7','C9','E10','A11','D11','E11','C12']


##########################
##########################
def importSCdata(input_file):
    df = pd.read_csv(input_file,header=0, usecols=['Plate_id','Well','Type','Dest_plate','Row','Col'], dtype={'Col':'int','Dest_plate':'int'})
    
    # sort df by dest_plate, plate id, column, and row
    df = df.sort_values(by=['Dest_plate', 'Plate_id','Type','Col','Row'])
    
    # create new column "pool" with same values as dest_plate
    df['Pool'] = df['Dest_plate']

    # reset index after sorting
    df.reset_index(inplace=True,drop=True)
    
    
    return df
##########################
##########################



##########################
##########################
def countLibsPerPlate(df):
    # count the number of samples assigned to each Dest_plate id
    df2 = df.groupby(['Dest_plate']).size().reset_index(name='counts')
    
    # abort program if >MAX_SAMPLES_PER_PLATE wells assigned to the same Dest_plate id
    if (df2.counts>MAX_SAMPLES_PER_PLATE).any():
        print(f'\n\nERROR: At least one destination plate has > {MAX_SAMPLES_PER_PLATE} libraries assigned.')
        print('Please check the input file and reassign samples.')
        print('Aborting script.\n')
               
        sys.exit()

##########################
##########################


##########################
##########################
def checkSourcePlateDistribution(df):
    # count the number of dest plates with DNA from the same source plate
    source_count = df.groupby('Plate_id')['Dest_plate'].nunique()
    
    # abort script immediately if multiple library plates have wells from the same source plate
    # this is no longer acceptable and requires reassignment of groupings
    if (source_count>1).any():
        print('\n\nERROR: At least one source plate has samples in multiple library plates.')
        print('This is no longer acceptable. Please reassign the groupings to avoid')
        print('splitting samples across multiple destination plates.')
        print('Aborting script.\n')
        sys.exit()

##########################
##########################


##########################
##########################
def assignLibPlateID(df):
    
    # generate unique 6 digit ID destination/lib creation plate, first digit is a letter
    destbc = random.choice(string.ascii_uppercase)

    # add next 4 digits to ID
    destbc = destbc + \
        "".join(random.choice(string.digits+string.ascii_uppercase)
                for _ in range(5))
        
    # add unique destination barcode name to destination plate number
    df['Dest_plate'] = destbc + "." + df.Dest_plate.astype(str)
    
    return df
##########################
##########################



##########################
##########################
def assignPlatePositions(df):
    
    ######## add new column with numbers to be used for determining position
    df['number'] = df.index + 1 

    # find the lowest df index number for each destination plate
    df3 = df.groupby(['Dest_plate'])['number'].min().reset_index()

    # make dict where destination plate is the key and lowest index number is the value
    dest_dict = dict(zip(df3['Dest_plate'], df3['number']))

    # add column with the lowest index value for the dest plate indicated in each row
    df['base'] = df['Dest_plate'].map(dest_dict)

    # substract the base (i.e. lowest index number from each dest plate) from the rows index +1
    # this gives a new column where the first row with the same dest plate will start with 1
    # and the next row is 2, and so on.  The first row of each dest plate starts at 1 and increments
    # up for each row in the dest plate
    df['Plate_position_number'] = df.number - df.base + 1
    
    # confirm position number is >=1 and <=MAX_SAMPLES_PER_PLATE
    if (df['Plate_position_number'] < 1).any() | (df['Plate_position_number'] > MAX_SAMPLES_PER_PLATE).any():
        print('\n\nERROR: Problem assigning plate position numbers.')
        print(f'Position numbers must be between 1 and {MAX_SAMPLES_PER_PLATE}.')
        print('Aborting script.\n')
               
        sys.exit()


    # remove unnecessary columns
    df.drop(['Row','Col','number','base'], axis=1, inplace = True)

    return df
##########################
##########################



##########################
##########################
def makeConversionKey():

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
     
    # make dict with key = 96well position and value = equivalent 384well position
    # assuming 96-well plates stamped into upper left corner of 384well plate (A1 = A1)
    convert_96w_to_384w = dict(zip(well_list_96w, well_list_384w))

    # make dict with key = 384well position and value = equivalent 96well position
    # assuming 96-well plates stamped into upper left corner of 384well plate (A1 = A1)
    convert_384w_to_96w = dict(zip(well_list_384w, well_list_96w))
    
    return convert_96w_to_384w, convert_384w_to_96w, well_list_96w
##########################
##########################


##########################
##########################
def makeIlluminaIndexSetToUse(well_list_96w):
    
    # create dict where key is illumina barcode set name PE17-PE20 and values are
    # lists of wells from 10bp nextera plates that can be used
    illum_set_dict = {"PE17":[x  for x in well_list_96w if x not in PE17_EXCLUDE],
                      "PE18":[x  for x in well_list_96w if x not in PE18_EXCLUDE],
                      "PE19": [x  for x in well_list_96w if x not in PE19_EXCLUDE],
                      "PE20": [x  for x in well_list_96w if x not in PE20_EXCLUDE]}
    
    # create list of 10bp nextera illumina index sets
    ill_set_list = sorted(illum_set_dict.keys())
    
    
    # create empty dict
    illum_dict = {}

    # loop through all four nextera index sets PE17-PE20
    for ill_set in (ill_set_list):
        
        # create illum_dict were key is set name plus position number in list (e.g. PE17_1, PE17_2, PE17_3 ...)
        # and value is the barcode well as that list position number (e.g. PE17_1 : B1, PE17_2 : C1, PE17_3 : D1 ...)
        for i, well in enumerate(illum_set_dict[ill_set]):
            illum_dict[ill_set + "_" + str(i+1)] = well
            
    
    return ill_set_list, illum_dict
##########################
##########################

##########################
##########################
def assignIlluminaIndex(df,ill_set_list ,illum_dict, convert_96w_to_384w):
    
    # get list of uniqued destination plate IDs
    dest_list = sorted(df['Dest_plate'].unique().tolist())


    # select random starting index set (0 to NUM_ILLUMINA_INDEX_SETS-1)
    rand_index_set_start = random.randint(0, NUM_ILLUMINA_INDEX_SETS - 1)

    # create empty dict
    dest_id_dict = {}

    ## createdest_id_dict were keys are destination plate IDs and values are illumin index set#
    # the modulo is used because the number of destination plates might exceed the number
    # of index sets, so the module wraps around ill_set list
    for cnt, dp in enumerate(dest_list):
        id_set = str(ill_set_list[(cnt+rand_index_set_start) % len(ill_set_list)])
        dest_id_dict[dp] = id_set


    # add new column with nextera index set for each library plate
    df['Illumina_set'] = df['Dest_plate'].replace(dest_id_dict) + "_" + df['Plate_position_number'].astype(str)

    # add new column with well position of nextera index set in 96 well format
    df['Dest_well_96'] = df['Illumina_set'].replace(illum_dict)

    # add new column with well postion of nextera index set in 384 well format
    df['Dest_well_384'] = df['Dest_well_96'].replace(convert_96w_to_384w)
    
    
    # confirm that destination wells do no match Illumina set or
    # contain null values. The former would happen if Illumins set
    # was not in illum_dict
    s = df['Dest_well_96'].isin(df['Illumina_set'])

    if s.any() | df['Dest_well_384'].isnull().any():

        print('\n\nERROR: Problem assigning destination wells.')
        print('Check Illumina index set assignments and well mappings.')
        print('Aborting script.\n')

        sys.exit()
    
    return df
##########################
##########################




##########################
##########################
def addEchoId(df, echo_file):

    echo_df = pd.read_csv(echo_file, header=1, usecols= ['Project Name','Echo Barcode','Sample Name','Window Name','Plate Index'])
    
    echo_cols = ['Project Name','Sample Name','Window Name','Plate Index']
    
    echo_df['combined'] = echo_df[echo_cols].apply(lambda row: '.'.join(row.values.astype(str)), axis=1)
    
    # make dict where destination plate is the key and lowest index number is the value
    echo_dict = dict(zip(echo_df['combined'], echo_df['Echo Barcode']))
    
    # add column with the lowest index value for the dest plate indicated in each row
    df['echo_id'] = df['Plate_id'].replace(echo_dict)
    
    # confirm that echo_id were assigned and that they
    # do not match Plate_id.  The latter will happen if
    # the plate id is not in the query file downloaded from
    # the single cell analysis tool website
    s = df['echo_id'].isin(df['Plate_id'])
    
    if s.any() | df['echo_id'].isnull().any():
        print('\n\nERROR: Problem finding echo plate ID.')
        print('Check for source plate ID in query file downloaded from single cell analysis website.')
        print('Aborting script.\n')
    
        sys.exit()
        
    return df

##########################
##########################



##########################
##########################
def addSPITScolumns(df):

    # add column with JGI internal  name    
    df['Internal_name'] = df['Plate_id'] + "_" + df['Well']
    


    # create sample names for SAGs and controls
    # assign NaN to any type other than "sample" or "negative"
    df['Sample_name'] = np.where(df['Type'] == 'sample',"Uncultured microbe JGI_" + df['Internal_name'],np.nan)

    df['Sample_name'] = np.where(df['Type'] == 'negative',"NoTemplate Control JGI_" + df['Internal_name'],df['Sample_name'])
    
    # abort script if sample name not assigned
    if df['Sample_name'].isnull().any():
        print('\n\nERROR: Problem assigning sample name.')
        print("Check that sample type is 'sample' or 'negative'.")
        print('Aborting script.\n')

        sys.exit()
    
    # NOTE: Internal_name should just be plate_id + "_" + well (no illumina_set)
    # Keep the original Internal_name format as requested by user
    # df['Internal_name'] =  df['Plate_id'] + "_" + df['Well'] + '_' + df['Illumina_set'].str.split('_', n=1).str[0]
    
    # add dummy DNA concentration and sample volumes
    df['DNA_conc'] = 10
    
    df['Sample_vol'] = 25
    
    df['Sample_container'] = 'plate'
    
    df['Sample_format'] = 'MDA reaction buffer'
    
    df['DNAse_treated'] = 'N'
    
    df['Biosafety_cat'] = 'Metagenome (Environmental)'
    
    df['Isolation_method'] = 'flow sorting'
    
    # Get current date for negative controls
    current_date = datetime.now()
    current_year = str(current_date.year)
    current_month = current_date.strftime('%B')  # Full month name (e.g., "January")
    current_day = str(current_date.day)
    
    # Add new metadata columns with empty values (to be filled manually later)
    # For negative controls, populate with specific values
    df['Collection_Year'] = np.where(df['Type'] == 'negative', current_year, '')
    df['Collection_Month'] = np.where(df['Type'] == 'negative', current_month, '')
    df['Collection_Day'] = np.where(df['Type'] == 'negative', current_day, '')
    df['Sample_Isolated_From'] = np.where(df['Type'] == 'negative', 'MDA reagents', '')
    df['Collection_Site'] = np.where(df['Type'] == 'negative', 'MDA reagents', '')
    df['Latitude'] = np.where(df['Type'] == 'negative', '37.87606', '')
    df['Longitude'] = np.where(df['Type'] == 'negative', '-122.25166', '')
    df['Depth'] = np.where(df['Type'] == 'negative', '0', '')
    df['Maximum_depth'] = np.where(df['Type'] == 'negative', '', '')
    df['Elevation'] = np.where(df['Type'] == 'negative', '75', '')
    df['Maximum_elevation'] = np.where(df['Type'] == 'negative', '', '')
    df['Country'] = np.where(df['Type'] == 'negative', 'USA', '')
    
    # replace 'sample' in type with empty string
    df['Type'] = df['Type'].replace('sample', "")


    return df
##########################
##########################


##########################
##########################
def makeSPITSformat(df):
    
    # Updated SPITS format: remove empty columns, replace echo_id with Dest_plate, replace Well with Dest_well_384
    # Include new metadata columns immediately before Pool and Internal_name
    df2 = df[['Sample_name','DNA_conc','Sample_vol','Dest_plate','Sample_container','Dest_well_384','Sample_format',
              'DNAse_treated','Biosafety_cat','Isolation_method',
              'Collection_Year','Collection_Month','Collection_Day','Sample_Isolated_From','Collection_Site',
              'Latitude','Longitude','Depth','Maximum_depth','Elevation','Maximum_elevation','Country',
              'Type','Pool','Internal_name']]

    # create csv summarizing single cell results
    df2.to_csv('output.csv', index=False)
    

##########################
##########################


##########################
##########################
def createIndividualIlluminaIndex(df):
    """
    Create individual illumina index names like PE17_E01
    Uses existing Illumina_set and Dest_well_96 columns to create final illumina index
    Must be called AFTER assignIlluminaIndex()
    """
    # Extract illumina index set from existing Illumina_set column (e.g., "PE17" from "PE17_1")
    df['Illumina_index_set'] = df['Illumina_set'].str.split('_', n=1).str[0]
    
    # Format the well position to add leading zero for single digit columns
    # E1 -> E01, F7 -> F07, G11 -> G11
    df['Formatted_well'] = df['Dest_well_96'].str.replace(r'([A-H])(\d)$', r'\g<1>0\g<2>', regex=True)
    
    # Create individual illumina index by concatenating set + formatted well position
    df['Individual_illumina_index'] = df['Illumina_index_set'] + '_' + df['Formatted_well']
    
    # Clean up temporary column
    df.drop(['Formatted_well'], axis=1, inplace=True)
    
    # Verify no null values
    if df['Individual_illumina_index'].isnull().any():
        print('\n\nERROR: Problem creating individual illumina indexes.')
        print('Check illumina index set assignments and well formatting.')
        print('Aborting script.\n')
        sys.exit()
    
    return df
##########################
##########################


##########################
##########################
def prepareDatabaseDataframe(df):
    """
    Prepare dataframe with specific columns for database storage
    Column order: internal_name, plate_id, echo_id, well, type, dest_plate, dest_well_384, illumina_index_set, illumina_index
    (Removed dna_conc and sample_vol as they are no longer needed)
    """
    # Required columns in specified order (removed DNA_conc and Sample_vol)
    required_columns = [
        'Internal_name', 'Plate_id', 'echo_id', 'Well', 'Type',
        'Dest_plate', 'Dest_well_384', 'Illumina_index_set', 'Individual_illumina_index'
    ]
    
    # Create database dataframe with only the required columns in specified order
    db_df = df[required_columns].copy()
    
    # Rename columns to match user's preferred naming convention (lowercase with underscores)
    db_df = db_df.rename(columns={
        'Internal_name': 'internal_name',
        'Plate_id': 'plate_id',
        'Well': 'source_well',
        'Type': 'type',
        'Dest_plate': 'dest_plate',
        'Dest_well_384': 'dest_well_384',
        'Individual_illumina_index': 'Illumina_index'
    })
    
    return db_df
##########################
##########################


##########################
##########################
def createProjectSummaryCSV(final_df):
    """
    Create CSV file with processed SPITS data
    Following the pattern from SPS_make_illumina_index_and_FA_files.py
    """
    # Create CSV file (following SPS script pattern)
    final_df.to_csv("project_summary.csv", index=False)
    
    return
##########################
##########################


##########################
##########################
def createSQLdb(final_df):
    """
    Create SQLite database with processed SPITS data
    Adapted from SPS_make_illumina_index_and_FA_files.py
    """

    final_df.rename(columns={'dest_plate': 'Destination_plate_name','dest_well_384':'Destination_Well'}, inplace=True)

    # Use current working directory for database (following SPS script pattern)
    sql_db_path = Path.cwd() / 'project_summary.db'
    
    # Create SQLAlchemy engine
    engine = create_engine(f'sqlite:///{sql_db_path}')
    
    # Specify table name
    table_name = 'project_summary'
    
    # Export DataFrame to SQLite database
    final_df.to_sql(table_name, engine, if_exists='replace', index=False)
    
    # Close engine connection
    engine.dispose()
    
    return final_df
##########################
##########################


##########################
##### MAIN PROGRAM
##########################

def main():
    """
    Main function to process single cell data and generate SPITS output with database functionality
    """
    # Check for correct number of command line arguments
    if len(sys.argv) != 3:
        print(f"\nUsage: {sys.argv[0]} <input_csv_file> <echo_barcodes_csv_file>")
        print("Example: python enhanced_generate_SPITS_input.py input.csv 'SingleCell Query - Echo Barcodes.csv'")
        sys.exit(1)
    
    # get input files from command line
    input_file = sys.argv[1]
    echo_file = sys.argv[2]

    # import file with list of single cell selected for sequencing
    df = importSCdata(input_file)

    # abort script if  >83 libs were assign to any library plate
    countLibsPerPlate(df)
        
    # check if a wells from a source plates are  distriubtion in >1 library plate
    # this isn't necessarily a fatal flaw, but generally should be avoided
    checkSourcePlateDistribution(df)

    # generate random ID for dest/lib plates
    df = assignLibPlateID(df)
        
    # add new column indicating position 1-83 of sample in library plate
    # the number will be used later to assign a nextera index to each well
    df = assignPlatePositions(df)

    # generate dicts that convert 96w to 384w format, and vice versa
    convert_96w_to_384w, convert_384w_to_96w, well_list_96w = makeConversionKey()

    # create illum_dict were key is set name plus position number in list (e.g. PE17_1, PE17_2, PE17_3 ...)
    # and value is the barcode well as that list position number (e.g. PE17_1 : B1, PE17_2 : C1, PE17_3 : D1 ...)
    ill_set_list, illum_dict = makeIlluminaIndexSetToUse(well_list_96w)

    # assign well positions in dest/lib plate and
    # assign Illumina indexes to be used with each samples
    df = assignIlluminaIndex(df,ill_set_list,illum_dict, convert_96w_to_384w)

    # add echo id's from file downloaded from single cell analysis website
    df = addEchoId(df, echo_file)

    # add columns expected by SPITS
    df = addSPITScolumns(df)

    # NEW: create individual illumina indexes (must be called after assignIlluminaIndex)
    df = createIndividualIlluminaIndex(df)

    # NEW: prepare dataframe for database storage
    db_df = prepareDatabaseDataframe(df)

    # NEW: create SQLite database
    db_df = createSQLdb(db_df)

    # NEW: create project summary CSV file (following SPS pattern)
    createProjectSummaryCSV(db_df)



    # EXISTING: make csv file in format that matches column arrangement of SPITS.xlsx
    makeSPITSformat(df)

    # NEW: print completion message
    print(f'\n\nCreated SPITS output file: output.csv')
    print(f'Created project summary CSV file: project_summary.csv')
    print(f'Created database file: project_summary.db')


if __name__ == "__main__":
    main()

