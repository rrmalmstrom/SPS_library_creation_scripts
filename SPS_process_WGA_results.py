#!/usr/bin/env python3

"""
SPS Process WGA Results — Script 2

Reads WGA amplification kinetics files from B_WGA_results/, filters to passing
wells, assigns destination library plate numbers, and writes a consolidated
summary_MDA_results.csv for use by Script 3 (enhanced_generate_SPITS_input.py).

USAGE: python SPS_process_WGA_results.py

CRITICAL REQUIREMENTS:
- MUST use sip-lims conda environment
- Run from the project directory (same directory as project_summary.db)
- All WGA kinetics files must be placed in 2_sort_plates_and_amplify_genomes/B_WGA_results/
  before running this script
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

OUTPUT_COLUMNS = [
    'Plate_id',
    'Well',
    'Row',
    'Col',
    'Sample',
    'Type',
    'number_of_cells/capsules',
    'Group_1',
    'Group_2',
    'Group_3',
    'Delta_Fluorescence',
    'Crossing_Point',
    'Pass_Fail',
    'Dest_plate',
]


# ---------------------------------------------------------------------------
# Phase 1 Functions
# ---------------------------------------------------------------------------

def read_individual_plates_from_database(db_path):
    """
    Read the individual_plates table from the SQLite project database.

    Args:
        db_path (Path): Path to project_summary.db

    Returns:
        pd.DataFrame: DataFrame with columns: plate_name, project, sample,
                      plate_number, is_custom, barcode, created_timestamp

    Raises:
        SystemExit: If the database file does not exist, the table is missing,
                    or any other read error occurs.
    """
    db_path = Path(db_path)

    if not db_path.exists():
        print(f"FATAL ERROR: Database file not found: {db_path}")
        sys.exit()

    try:
        engine = create_engine(f"sqlite:///{db_path}")
        try:
            df = pd.read_sql("SELECT * FROM individual_plates", engine)
        except Exception as e:
            engine.dispose()
            # Distinguish "table not found" from other errors
            if "no such table" in str(e).lower():
                print(f"FATAL ERROR: 'individual_plates' table not found in database: {db_path}")
                sys.exit()
            raise
        engine.dispose()

    except SystemExit:
        raise
    except Exception as e:
        print(f"FATAL ERROR: Could not read database {db_path}: {e}")
        sys.exit()

    print(f"✅ Read {len(df)} plates from database")
    return df


def scan_kinetics_files(wga_results_dir):
    """
    Find all *_amplification_kinetics_summary.csv files in the B_WGA_results/
    directory.

    Args:
        wga_results_dir (Path): Path to
            2_sort_plates_and_amplify_genomes/B_WGA_results/

    Returns:
        list[Path]: Sorted list of matching CSV file paths.

    Raises:
        SystemExit: If the directory does not exist or no matching files are
                    found.
    """
    wga_results_dir = Path(wga_results_dir)

    if not wga_results_dir.exists():
        print(f"FATAL ERROR: WGA results directory not found: {wga_results_dir}")
        sys.exit()

    files = sorted(wga_results_dir.glob("*_amplification_kinetics_summary.csv"))

    if not files:
        print(f"FATAL ERROR: No amplification kinetics files found in {wga_results_dir}")
        sys.exit()

    print(f"✅ Found {len(files)} amplification kinetics file(s) in {wga_results_dir}")
    return files


def validate_layout_files(kinetics_files, layout_dir):
    """
    For each kinetics file, verify that a corresponding plate layout CSV exists
    in A_sort_plate_layouts/.

    Plate name is extracted by stripping '_amplification_kinetics_summary.csv'
    from the filename.  The expected layout filename is
    ``{plate_name}_plate_layout.csv``.

    Args:
        kinetics_files (list[Path]): List of kinetics file paths from
            scan_kinetics_files().
        layout_dir (Path): Path to
            2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/

    Returns:
        dict[str, str]: Mapping of plate_name → kinetics_file_path (as strings)
                        for all valid plates.

    Raises:
        SystemExit: If layout_dir does not exist, or if ANY layout file is
                    missing (all missing files are reported before exiting).
    """
    layout_dir = Path(layout_dir)

    if not layout_dir.exists():
        print(f"FATAL ERROR: Sort plate layouts directory not found: {layout_dir}")
        sys.exit()

    SUFFIX = "_amplification_kinetics_summary.csv"
    missing = []
    result = {}

    for kinetics_path in kinetics_files:
        kinetics_path = Path(kinetics_path)
        plate_name = kinetics_path.name.replace(SUFFIX, "")
        expected_layout = layout_dir / f"{plate_name}_plate_layout.csv"

        if not expected_layout.exists():
            missing.append(str(expected_layout))
        else:
            result[plate_name] = str(kinetics_path)

    if missing:
        print("FATAL ERROR: Missing plate layout file(s) for the following plates:")
        for missing_path in missing:
            print(f"  {missing_path}")
        sys.exit()

    print(f"✅ Validated layout files for {len(result)} plate(s)")
    return result


def read_kinetics_file(kinetics_path):
    """
    Read a single amplification kinetics CSV file and validate that its
    Plate_ID column matches the plate name embedded in the filename.

    Plate name is extracted by stripping '_amplification_kinetics_summary.csv'
    from the filename.

    Args:
        kinetics_path (Path): Path to a single
            *_amplification_kinetics_summary.csv file.

    Returns:
        pd.DataFrame: DataFrame with all columns from the kinetics file.

    Raises:
        SystemExit: If the file cannot be read, or if the Plate_ID column does
                    not contain exactly one unique value matching the plate name
                    from the filename.
    """
    kinetics_path = Path(kinetics_path)
    SUFFIX = "_amplification_kinetics_summary.csv"
    plate_name_from_file = kinetics_path.name.replace(SUFFIX, "")

    try:
        df = pd.read_csv(kinetics_path, encoding="utf-8-sig")
    except Exception as e:
        print(f"FATAL ERROR: Could not read kinetics file {kinetics_path}: {e}")
        sys.exit()

    unique_ids = df["Plate_ID"].unique().tolist()
    if len(unique_ids) != 1 or unique_ids[0] != plate_name_from_file:
        print(
            f"FATAL ERROR: Plate_ID mismatch in {kinetics_path}: "
            f"filename says '{plate_name_from_file}' but Plate_ID column contains {unique_ids}"
        )
        sys.exit()

    return df


# ---------------------------------------------------------------------------
# Phase 2 Functions
# ---------------------------------------------------------------------------

def filter_wells(df):
    """
    Filter a kinetics DataFrame to keep only rows where Pass_Fail == 'Pass'.

    Applies equally to all well types (sample, neg_cntrl, etc.).

    Args:
        df (pd.DataFrame): A single plate's kinetics DataFrame (as returned by
            read_kinetics_file).

    Returns:
        pd.DataFrame: Filtered DataFrame with reset index.
    """
    filtered = df[df['Pass_Fail'] == 'Pass'].reset_index(drop=True)
    return filtered


def sort_by_crossing_point(df):
    """
    Sort a filtered DataFrame by Crossing_Point ascending (lowest CP first).

    NaN values in Crossing_Point sort to the end.

    Args:
        df (pd.DataFrame): A filtered plate DataFrame.

    Returns:
        pd.DataFrame: Sorted DataFrame with reset index.
    """
    return df.sort_values("Crossing_Point", ascending=True, na_position="last").reset_index(drop=True)


def load_and_process_plates(kinetics_files, plates_df):
    """
    Load all kinetics files, filter and sort each one, then concatenate them
    in barcode order.

    Args:
        kinetics_files (list[Path]): List of kinetics file paths (from
            scan_kinetics_files).
        plates_df (pd.DataFrame): The individual_plates DataFrame from the
            database (from read_individual_plates_from_database).

    Returns:
        pd.DataFrame: Concatenated DataFrame of all filtered+sorted plates,
            in barcode order, with reset index.

    Raises:
        SystemExit: If any kinetics file's plate name is not found in
            plates_df, or if any other processing error occurs.
    """
    SUFFIX = "_amplification_kinetics_summary.csv"

    try:
        # Step 1: Build plate_name → barcode lookup from plates_df
        barcode_lookup = dict(zip(plates_df["plate_name"], plates_df["barcode"]))

        # Step 2: Build plate_name → kinetics_file_path lookup
        file_lookup = {}
        for kinetics_path in kinetics_files:
            kinetics_path = Path(kinetics_path)
            plate_name = kinetics_path.name.replace(SUFFIX, "")
            file_lookup[plate_name] = kinetics_path

        # Step 3: Validate — every plate name from kinetics files must be in plates_df
        missing_names = [name for name in file_lookup if name not in barcode_lookup]
        if missing_names:
            print(
                "FATAL ERROR: The following kinetics file plate names were not found in the database:"
            )
            for name in missing_names:
                print(f"  {name}")
            sys.exit()

        # Step 4: Sort kinetics files by barcode (numeric sort on suffix after last '-')
        def _barcode_sort_key(plate_name):
            barcode = barcode_lookup[plate_name]
            try:
                return int(barcode.rsplit("-", 1)[-1])
            except (ValueError, IndexError):
                return barcode

        sorted_plate_names = sorted(file_lookup.keys(), key=_barcode_sort_key)

        # Step 5: Process each plate in barcode order
        processed_dfs = []
        for plate_name in sorted_plate_names:
            kinetics_path = file_lookup[plate_name]
            df = read_kinetics_file(kinetics_path)
            filtered_df = filter_wells(df)
            sorted_df = sort_by_crossing_point(filtered_df)
            print(f"  Processing: {plate_name} ({len(sorted_df)} wells after filtering)")
            processed_dfs.append(sorted_df)

        # Step 6: Concatenate all DataFrames
        result = pd.concat(processed_dfs, ignore_index=True)

        # Step 7: Print summary
        print(
            f"✅ Loaded and processed {len(kinetics_files)} plate(s): "
            f"{len(result)} total rows after filtering"
        )

        # Step 8: Return
        return result

    except SystemExit:
        raise
    except Exception as e:
        print(f"FATAL ERROR: Could not process kinetics files: {e}")
        sys.exit()


# ---------------------------------------------------------------------------
# Phase 3 Functions
# ---------------------------------------------------------------------------

def rename_columns(df):
    """
    Rename columns from kinetics file format to Script 3 compatible format.

    Renames:
        'Plate_ID'  → 'Plate_id'
        'Well_Row'  → 'Row'
        'Well_Col'  → 'Col'

    All other columns remain unchanged.

    Args:
        df (pd.DataFrame): The concatenated DataFrame from load_and_process_plates.

    Returns:
        pd.DataFrame: New DataFrame with renamed columns.
    """
    return df.rename(columns={
        'Plate_ID': 'Plate_id',
        'Well_Row': 'Row',
        'Well_Col': 'Col',
    })


def remap_type_values(df):
    """
    Remap the Type column values from kinetics file format to Script 3 format.

    Remapping:
        'neg_cntrl' → 'negative'
        'sample'    → 'sample'  (unchanged)
        any other   → left unchanged

    Args:
        df (pd.DataFrame): DataFrame with a Type column.

    Returns:
        pd.DataFrame: New DataFrame with Type values remapped.
    """
    type_map = {'neg_cntrl': 'negative', 'sample': 'sample'}
    result = df.copy()
    result['Type'] = result['Type'].map(lambda v: type_map.get(v, v))
    return result


def assign_dest_plate(df):
    """
    Assign sequential Dest_plate integer values to all rows in 83-row bins.

    Row index 0–82   → Dest_plate = 1
    Row index 83–165 → Dest_plate = 2
    General formula:  Dest_plate = (row_position // 83) + 1

    row_position is the 0-based position in the DataFrame (range(len(df))),
    NOT the DataFrame index.

    Args:
        df (pd.DataFrame): The full concatenated DataFrame.

    Returns:
        pd.DataFrame: Same data with a new Dest_plate column added.
    """
    result = df.copy()
    result['Dest_plate'] = [i // 83 + 1 for i in range(len(df))]
    return result


def select_and_reorder_columns(df):
    """
    Select only the required output columns and put them in the correct order
    for summary_MDA_results.csv.

    Args:
        df (pd.DataFrame): The fully processed DataFrame.

    Returns:
        pd.DataFrame: DataFrame with exactly the 14 OUTPUT_COLUMNS in order.

    Raises:
        SystemExit: If any required column is missing from df.
    """
    missing_cols = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"FATAL ERROR: Missing required output columns: {missing_cols}")
        sys.exit()
    return df[OUTPUT_COLUMNS]


# ---------------------------------------------------------------------------
# Phase 4 Functions
# ---------------------------------------------------------------------------

def write_output_csv(df, output_dir):
    """
    Create the output directory if needed and write the final DataFrame to
    summary_MDA_results.csv.

    Args:
        df (pd.DataFrame): The fully processed DataFrame (14 columns, correct order).
        output_dir (Path): Path to
            2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS/

    Returns:
        Path: The full path to the written CSV file.

    Raises:
        SystemExit: If the CSV cannot be written.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "summary_MDA_results.csv"

    try:
        df.to_csv(output_path, index=False)
    except Exception as e:
        print(f"FATAL ERROR: Could not write output CSV {output_path}: {e}")
        sys.exit()

    print(f"✅ Written {len(df)} rows to {output_path}")
    return output_path


def create_success_marker():
    """
    Create a workflow status marker file, consistent with Script 1's pattern.

    Writes .workflow_status/SPS_process_WGA_results.success in the CWD.

    Raises:
        SystemExit: If the marker file cannot be created.
    """
    status_dir = Path(".workflow_status")
    marker_path = status_dir / "SPS_process_WGA_results.success"

    try:
        status_dir.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            f"SUCCESS: SPS_process_WGA_results completed at {datetime.now()}\n"
        )
    except Exception as e:
        print(f"FATAL ERROR: Could not create success marker: {e}")
        sys.exit()

    print(f"✅ Success marker created: .workflow_status/SPS_process_WGA_results.success")


def main():
    """
    Orchestrate the full SPS Process WGA Results pipeline.
    """
    print("=" * 60)
    print("SPS Process WGA Results")

    # Define paths (relative to CWD — the project directory)
    db_path = Path("project_summary.db")
    wga_results_dir = Path("2_sort_plates_and_amplify_genomes/B_WGA_results")
    layout_dir = Path("2_sort_plates_and_amplify_genomes/A_sort_plate_layouts")
    output_dir = Path("2_sort_plates_and_amplify_genomes/C_WGA_summary_and_SPITS")

    # Read database
    plates_df = read_individual_plates_from_database(db_path)

    # Scan for kinetics files
    kinetics_files = scan_kinetics_files(wga_results_dir)

    # Validate layout files
    plate_map = validate_layout_files(kinetics_files, layout_dir)

    # Load and process all plates
    combined_df = load_and_process_plates(kinetics_files, plates_df)

    # Transform columns
    combined_df = rename_columns(combined_df)
    combined_df = remap_type_values(combined_df)
    combined_df = assign_dest_plate(combined_df)
    combined_df = select_and_reorder_columns(combined_df)

    # Write output
    write_output_csv(combined_df, output_dir)

    # Create success marker
    create_success_marker()

    # Print final summary
    print(f"\n✅ Script complete.")
    print(f"   Output: {output_dir / 'summary_MDA_results.csv'}")
    print(f"   Total rows: {len(combined_df)}")
    print(f"   Dest plates assigned: {combined_df['Dest_plate'].max()}")


if __name__ == "__main__":
    main()
