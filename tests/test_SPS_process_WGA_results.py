"""
Tests for Phase 1 of SPS_process_WGA_results.py

Covers:
  - read_individual_plates_from_database
  - scan_kinetics_files
  - validate_layout_files
  - read_kinetics_file
"""

import sqlite3
import pytest
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------
import sys
import os

# Ensure the workspace root is on the path so the import works regardless of
# where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).parent.parent))

from SPS_process_WGA_results import (
    read_individual_plates_from_database,
    scan_kinetics_files,
    validate_layout_files,
    read_kinetics_file,
    filter_wells,
    sort_by_crossing_point,
    load_and_process_plates,
    rename_columns,
    remap_type_values,
    assign_dest_plate,
    select_and_reorder_columns,
    write_output_csv,
    create_success_marker,
    OUTPUT_COLUMNS,
)


# ===========================================================================
# Helpers
# ===========================================================================

INDIVIDUAL_PLATES_COLUMNS = [
    "plate_name",
    "project",
    "sample",
    "plate_number",
    "is_custom",
    "barcode",
    "created_timestamp",
]

KINETICS_SUFFIX = "_amplification_kinetics_summary.csv"

# Minimal set of kinetics column names (13 columns as per spec)
KINETICS_COLUMNS = [
    "Plate_ID",
    "Well",
    "Row",
    "Column",
    "Type",
    "Sample",
    "Ct",
    "Tm",
    "Amplified",
    "Pass_Fail",
    "Notes",
    "Run_Date",
    "Instrument",
]


def _make_db_with_individual_plates(db_path, rows=None):
    """Create a SQLite database with an individual_plates table."""
    if rows is None:
        rows = [
            {
                "plate_name": "509735_WCBP1PR.1",
                "project": "509735",
                "sample": "WCBP1PR",
                "plate_number": 1,
                "is_custom": 0,
                "barcode": "ABCD1-1",
                "created_timestamp": "2026-01-01T00:00:00",
            }
        ]
    df = pd.DataFrame(rows, columns=INDIVIDUAL_PLATES_COLUMNS)
    conn = sqlite3.connect(db_path)
    df.to_sql("individual_plates", conn, if_exists="replace", index=False)
    conn.close()


def _make_kinetics_csv(path, plate_name, extra_columns=True):
    """Write a minimal kinetics CSV to *path*."""
    data = {col: ["val"] for col in KINETICS_COLUMNS}
    data["Plate_ID"] = [plate_name]
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)


# ===========================================================================
# Tests: read_individual_plates_from_database
# ===========================================================================


class TestReadIndividualPlatesFromDatabase:
    def test_valid_database_returns_dataframe(self, tmp_path):
        """Valid DB with individual_plates table → returns correct DataFrame."""
        db_path = tmp_path / "project_summary.db"
        _make_db_with_individual_plates(str(db_path))

        df = read_individual_plates_from_database(db_path)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert list(df.columns) == INDIVIDUAL_PLATES_COLUMNS
        assert df.iloc[0]["plate_name"] == "509735_WCBP1PR.1"
        assert df.iloc[0]["project"] == "509735"

    def test_nonexistent_path_calls_sys_exit(self, tmp_path):
        """Non-existent db_path → sys.exit() is called."""
        missing = tmp_path / "does_not_exist.db"
        with pytest.raises(SystemExit):
            read_individual_plates_from_database(missing)

    def test_missing_table_calls_sys_exit(self, tmp_path):
        """DB without individual_plates table → sys.exit() is called."""
        db_path = tmp_path / "project_summary.db"
        # Create a DB with a *different* table
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE other_table (id INTEGER)")
        conn.close()

        with pytest.raises(SystemExit):
            read_individual_plates_from_database(db_path)


# ===========================================================================
# Tests: scan_kinetics_files
# ===========================================================================


class TestScanKineticsFiles:
    def test_returns_sorted_list_of_matching_files(self, tmp_path):
        """Directory with 3 matching files → sorted list of 3 Paths."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()

        names = [
            "509735_WCBP1PR.3" + KINETICS_SUFFIX,
            "509735_WCBP1PR.1" + KINETICS_SUFFIX,
            "509735_WCBP1PR.2" + KINETICS_SUFFIX,
        ]
        for name in names:
            (wga_dir / name).touch()

        # Also add a non-matching file that should be ignored
        (wga_dir / "some_other_file.csv").touch()

        result = scan_kinetics_files(wga_dir)

        assert len(result) == 3
        assert all(isinstance(p, Path) for p in result)
        # Verify sorted order
        assert result[0].name == "509735_WCBP1PR.1" + KINETICS_SUFFIX
        assert result[1].name == "509735_WCBP1PR.2" + KINETICS_SUFFIX
        assert result[2].name == "509735_WCBP1PR.3" + KINETICS_SUFFIX

    def test_no_matching_files_calls_sys_exit(self, tmp_path):
        """Directory with no matching files → sys.exit() is called."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()
        (wga_dir / "unrelated.csv").touch()

        with pytest.raises(SystemExit):
            scan_kinetics_files(wga_dir)

    def test_nonexistent_directory_calls_sys_exit(self, tmp_path):
        """Non-existent directory → sys.exit() is called."""
        missing_dir = tmp_path / "B_WGA_results"

        with pytest.raises(SystemExit):
            scan_kinetics_files(missing_dir)


# ===========================================================================
# Tests: validate_layout_files
# ===========================================================================


class TestValidateLayoutFiles:
    def _make_kinetics_paths(self, wga_dir, plate_names):
        """Return a list of kinetics Path objects (files are created on disk)."""
        paths = []
        for name in plate_names:
            p = wga_dir / (name + KINETICS_SUFFIX)
            p.touch()
            paths.append(p)
        return paths

    def test_all_layouts_present_returns_correct_dict(self, tmp_path):
        """All layout files exist → returns dict mapping plate_name → kinetics path."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()
        layout_dir = tmp_path / "A_sort_plate_layouts"
        layout_dir.mkdir()

        plate_names = ["509735_WCBP1PR.1", "509735_WCBP1PR.2"]
        kinetics_paths = self._make_kinetics_paths(wga_dir, plate_names)

        # Create matching layout files
        for name in plate_names:
            (layout_dir / f"{name}_plate_layout.csv").touch()

        result = validate_layout_files(kinetics_paths, layout_dir)

        assert isinstance(result, dict)
        assert set(result.keys()) == set(plate_names)
        for name, kinetics_path in result.items():
            assert kinetics_path == str(wga_dir / (name + KINETICS_SUFFIX))

    def test_missing_layout_file_calls_sys_exit(self, tmp_path):
        """One layout file missing → sys.exit() is called."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()
        layout_dir = tmp_path / "A_sort_plate_layouts"
        layout_dir.mkdir()

        plate_names = ["509735_WCBP1PR.1", "509735_WCBP1PR.2"]
        kinetics_paths = self._make_kinetics_paths(wga_dir, plate_names)

        # Only create layout for the first plate
        (layout_dir / f"{plate_names[0]}_plate_layout.csv").touch()
        # plate_names[1] layout is intentionally missing

        with pytest.raises(SystemExit):
            validate_layout_files(kinetics_paths, layout_dir)

    def test_nonexistent_layout_dir_calls_sys_exit(self, tmp_path):
        """Non-existent layout_dir → sys.exit() is called."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()
        missing_layout_dir = tmp_path / "A_sort_plate_layouts"

        kinetics_paths = self._make_kinetics_paths(wga_dir, ["509735_WCBP1PR.1"])

        with pytest.raises(SystemExit):
            validate_layout_files(kinetics_paths, missing_layout_dir)


# ===========================================================================
# Tests: read_kinetics_file
# ===========================================================================


class TestReadKineticsFile:
    def test_valid_csv_returns_dataframe(self, tmp_path):
        """Valid CSV where Plate_ID matches filename → returns DataFrame."""
        plate_name = "509735_WCBP1PR.1"
        kinetics_path = tmp_path / (plate_name + KINETICS_SUFFIX)
        _make_kinetics_csv(kinetics_path, plate_name)

        df = read_kinetics_file(kinetics_path)

        assert isinstance(df, pd.DataFrame)
        assert "Plate_ID" in df.columns
        assert df["Plate_ID"].iloc[0] == plate_name
        # All 13 columns present
        for col in KINETICS_COLUMNS:
            assert col in df.columns

    def test_plate_id_mismatch_calls_sys_exit(self, tmp_path):
        """Plate_ID in CSV does not match filename → sys.exit() is called."""
        plate_name = "509735_WCBP1PR.1"
        wrong_plate_id = "509735_WCBP1PR.2"
        kinetics_path = tmp_path / (plate_name + KINETICS_SUFFIX)
        _make_kinetics_csv(kinetics_path, wrong_plate_id)

        with pytest.raises(SystemExit):
            read_kinetics_file(kinetics_path)

    def test_utf8_bom_file_reads_correctly(self, tmp_path):
        """CSV with UTF-8 BOM is read correctly without column name corruption."""
        plate_name = "509735_WCBP1PR.1"
        kinetics_path = tmp_path / (plate_name + KINETICS_SUFFIX)

        # Write CSV with UTF-8 BOM encoding
        data = {col: ["val"] for col in KINETICS_COLUMNS}
        data["Plate_ID"] = [plate_name]
        df_out = pd.DataFrame(data)
        df_out.to_csv(kinetics_path, index=False, encoding="utf-8-sig")

        df = read_kinetics_file(kinetics_path)

        assert isinstance(df, pd.DataFrame)
        # BOM must not corrupt the first column name
        assert "Plate_ID" in df.columns
        assert df["Plate_ID"].iloc[0] == plate_name


# ===========================================================================
# Tests: filter_wells
# ===========================================================================


def _make_filter_df(rows):
    """Build a minimal DataFrame with Type, Pass_Fail, and Well columns."""
    return pd.DataFrame(rows, columns=["Type", "Pass_Fail", "Well"])


class TestFilterWells:
    def test_pass_rows_kept_for_sample_type(self):
        """sample rows with Pass_Fail == 'Pass' are kept."""
        df = _make_filter_df([
            {"Type": "sample", "Pass_Fail": "Pass", "Well": "B1"},
        ])
        result = filter_wells(df)
        assert len(result) == 1
        assert result.iloc[0]["Well"] == "B1"

    def test_pass_rows_kept_for_neg_cntrl_type(self):
        """neg_cntrl rows with Pass_Fail == 'Pass' are kept."""
        df = _make_filter_df([
            {"Type": "neg_cntrl", "Pass_Fail": "Pass", "Well": "A1"},
        ])
        result = filter_wells(df)
        assert len(result) == 1
        assert result.iloc[0]["Well"] == "A1"

    def test_fail_rows_dropped_for_sample_type(self):
        """sample rows with Pass_Fail == 'Fail' are dropped."""
        df = _make_filter_df([
            {"Type": "sample", "Pass_Fail": "Fail", "Well": "C1"},
        ])
        result = filter_wells(df)
        assert len(result) == 0

    def test_fail_rows_dropped_for_neg_cntrl_type(self):
        """neg_cntrl rows with Pass_Fail == 'Fail' are dropped."""
        df = _make_filter_df([
            {"Type": "neg_cntrl", "Pass_Fail": "Fail", "Well": "A2"},
        ])
        result = filter_wells(df)
        assert len(result) == 0

    def test_mixed_dataframe_only_pass_rows_survive(self):
        """Mixed DataFrame: only Pass rows survive regardless of type."""
        df = _make_filter_df([
            {"Type": "neg_cntrl", "Pass_Fail": "Fail", "Well": "A1"},  # drop
            {"Type": "sample",    "Pass_Fail": "Pass", "Well": "B1"},  # keep
            {"Type": "sample",    "Pass_Fail": "Fail", "Well": "C1"},  # drop
            {"Type": "neg_cntrl", "Pass_Fail": "Pass", "Well": "D1"},  # keep
            {"Type": "sample",    "Pass_Fail": "Fail", "Well": "E1"},  # drop
        ])
        result = filter_wells(df)
        assert len(result) == 2
        assert set(result["Well"]) == {"B1", "D1"}

    def test_all_rows_fail_returns_empty_dataframe(self):
        """All rows with Fail → returns empty DataFrame."""
        df = _make_filter_df([
            {"Type": "sample",    "Pass_Fail": "Fail", "Well": "A1"},
            {"Type": "neg_cntrl", "Pass_Fail": "Fail", "Well": "B1"},
        ])
        result = filter_wells(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_index_is_reset_after_filtering(self):
        """Index is reset (0, 1, ...) after filtering."""
        df = _make_filter_df([
            {"Type": "sample", "Pass_Fail": "Fail", "Well": "A1"},   # drop → original index 0 gone
            {"Type": "sample", "Pass_Fail": "Pass", "Well": "B1"},   # keep → should be index 0
            {"Type": "sample", "Pass_Fail": "Pass", "Well": "C1"},   # keep → should be index 1
        ])
        result = filter_wells(df)
        assert list(result.index) == [0, 1]


# ===========================================================================
# Tests: sort_by_crossing_point
# ===========================================================================


class TestSortByCrossingPoint:
    def test_rows_sorted_ascending_by_crossing_point(self):
        """Rows are sorted ascending by Crossing_Point."""
        df = pd.DataFrame({
            "Well": ["A1", "B1", "C1"],
            "Crossing_Point": [30.5, 10.2, 20.8],
        })
        result = sort_by_crossing_point(df)
        assert list(result["Crossing_Point"]) == [10.2, 20.8, 30.5]
        assert list(result["Well"]) == ["B1", "C1", "A1"]

    def test_nan_crossing_point_sorts_to_end(self):
        """NaN Crossing_Point values sort to the end."""
        import numpy as np
        df = pd.DataFrame({
            "Well": ["A1", "B1", "C1"],
            "Crossing_Point": [25.0, float("nan"), 15.0],
        })
        result = sort_by_crossing_point(df)
        assert result.iloc[0]["Well"] == "C1"
        assert result.iloc[1]["Well"] == "A1"
        assert pd.isna(result.iloc[2]["Crossing_Point"])

    def test_index_is_reset_after_sorting(self):
        """Index is reset (0, 1, 2, ...) after sorting."""
        df = pd.DataFrame({
            "Well": ["A1", "B1", "C1"],
            "Crossing_Point": [30.0, 10.0, 20.0],
        })
        result = sort_by_crossing_point(df)
        assert list(result.index) == [0, 1, 2]


# ===========================================================================
# Tests: load_and_process_plates
# ===========================================================================

KINETICS_COLUMNS_FULL = [
    "Plate_ID", "Well", "Row", "Column", "Type", "Sample",
    "Crossing_Point", "Tm", "Amplified", "Pass_Fail", "Notes",
    "Run_Date", "Instrument",
]


def _make_full_kinetics_csv(path, plate_name, rows):
    """
    Write a kinetics CSV with all required columns including Crossing_Point.

    rows: list of dicts with at least Type, Pass_Fail, Crossing_Point.
    """
    base = {col: "val" for col in KINETICS_COLUMNS_FULL}
    records = []
    for i, row_override in enumerate(rows):
        r = dict(base)
        r["Plate_ID"] = plate_name
        r["Well"] = f"A{i + 1}"
        r.update(row_override)
        records.append(r)
    df = pd.DataFrame(records, columns=KINETICS_COLUMNS_FULL)
    df.to_csv(path, index=False)


def _make_plates_df(rows):
    """Build a minimal individual_plates DataFrame."""
    return pd.DataFrame(rows, columns=INDIVIDUAL_PLATES_COLUMNS)


class TestLoadAndProcessPlates:
    def test_two_plates_returns_concatenated_dataframe_in_barcode_order(self, tmp_path):
        """
        Two kinetics files with matching plates_df → concatenated DataFrame
        in barcode order (lower barcode number first).
        """
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()

        plate1 = "509735_WCBP1PR.1"
        plate2 = "509735_WCBP1PR.2"

        # plate2 has barcode MKD50-1 (lower), plate1 has MKD50-7 (higher)
        # So plate2 should appear first in output
        plates_df = _make_plates_df([
            {"plate_name": plate1, "project": "509735", "sample": "WCBP1PR",
             "plate_number": 1, "is_custom": 0, "barcode": "MKD50-7",
             "created_timestamp": "2026-01-01"},
            {"plate_name": plate2, "project": "509735", "sample": "WCBP1PR",
             "plate_number": 2, "is_custom": 0, "barcode": "MKD50-1",
             "created_timestamp": "2026-01-01"},
        ])

        path1 = wga_dir / f"{plate1}_amplification_kinetics_summary.csv"
        path2 = wga_dir / f"{plate2}_amplification_kinetics_summary.csv"

        _make_full_kinetics_csv(path1, plate1, [
            {"Type": "sample", "Pass_Fail": "Pass", "Crossing_Point": 20.0},
        ])
        _make_full_kinetics_csv(path2, plate2, [
            {"Type": "sample", "Pass_Fail": "Pass", "Crossing_Point": 15.0},
        ])

        result = load_and_process_plates([path1, path2], plates_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # plate2 (MKD50-1) should come first
        assert result.iloc[0]["Plate_ID"] == plate2
        assert result.iloc[1]["Plate_ID"] == plate1

    def test_plate_name_not_in_plates_df_calls_sys_exit(self, tmp_path):
        """Kinetics file plate name not in plates_df → sys.exit() is called."""
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()

        plate_name = "509735_WCBP1PR.1"
        path = wga_dir / f"{plate_name}_amplification_kinetics_summary.csv"
        _make_full_kinetics_csv(path, plate_name, [
            {"Type": "sample", "Pass_Fail": "Pass", "Crossing_Point": 20.0},
        ])

        # plates_df has a DIFFERENT plate name — mismatch
        plates_df = _make_plates_df([
            {"plate_name": "DIFFERENT_PLATE", "project": "509735", "sample": "X",
             "plate_number": 1, "is_custom": 0, "barcode": "MKD50-1",
             "created_timestamp": "2026-01-01"},
        ])

        with pytest.raises(SystemExit):
            load_and_process_plates([path], plates_df)

    def test_barcode_numeric_sort_not_lexicographic(self, tmp_path):
        """
        Barcode sort is numeric: MKD50-2 < MKD50-10, not lexicographic
        ('10' < '2' lexicographically but 2 < 10 numerically).
        """
        wga_dir = tmp_path / "B_WGA_results"
        wga_dir.mkdir()

        plate_low  = "509735_WCBP1PR.2"   # barcode MKD50-2
        plate_high = "509735_WCBP1PR.10"  # barcode MKD50-10

        plates_df = _make_plates_df([
            {"plate_name": plate_low,  "project": "509735", "sample": "WCBP1PR",
             "plate_number": 2,  "is_custom": 0, "barcode": "MKD50-2",
             "created_timestamp": "2026-01-01"},
            {"plate_name": plate_high, "project": "509735", "sample": "WCBP1PR",
             "plate_number": 10, "is_custom": 0, "barcode": "MKD50-10",
             "created_timestamp": "2026-01-01"},
        ])

        path_low  = wga_dir / f"{plate_low}_amplification_kinetics_summary.csv"
        path_high = wga_dir / f"{plate_high}_amplification_kinetics_summary.csv"

        _make_full_kinetics_csv(path_low, plate_low, [
            {"Type": "sample", "Pass_Fail": "Pass", "Crossing_Point": 18.0},
        ])
        _make_full_kinetics_csv(path_high, plate_high, [
            {"Type": "sample", "Pass_Fail": "Pass", "Crossing_Point": 22.0},
        ])

        # Pass high-numbered file first to ensure ordering is by barcode, not input order
        result = load_and_process_plates([path_high, path_low], plates_df)

        assert len(result) == 2
        # MKD50-2 (numeric 2) must come before MKD50-10 (numeric 10)
        assert result.iloc[0]["Plate_ID"] == plate_low
        assert result.iloc[1]["Plate_ID"] == plate_high


# ===========================================================================
# Tests: rename_columns
# ===========================================================================


class TestRenameColumns:
    def _make_df(self):
        """Build a minimal DataFrame with the three columns to be renamed plus extras."""
        return pd.DataFrame({
            'Plate_ID': ['P1'],
            'Well_Row': ['A'],
            'Well_Col': [1],
            'Well': ['A1'],
            'Sample': ['S1'],
        })

    def test_plate_id_renamed_to_plate_id_lower(self):
        """Plate_ID → Plate_id."""
        df = self._make_df()
        result = rename_columns(df)
        assert 'Plate_id' in result.columns
        assert 'Plate_ID' not in result.columns

    def test_well_row_renamed_to_row(self):
        """Well_Row → Row."""
        df = self._make_df()
        result = rename_columns(df)
        assert 'Row' in result.columns
        assert 'Well_Row' not in result.columns

    def test_well_col_renamed_to_col(self):
        """Well_Col → Col."""
        df = self._make_df()
        result = rename_columns(df)
        assert 'Col' in result.columns
        assert 'Well_Col' not in result.columns

    def test_other_columns_unchanged(self):
        """Columns not in the rename map are left unchanged."""
        df = self._make_df()
        result = rename_columns(df)
        assert 'Well' in result.columns
        assert 'Sample' in result.columns

    def test_original_dataframe_not_mutated(self):
        """rename_columns returns a new DataFrame; original still has Plate_ID."""
        df = self._make_df()
        _ = rename_columns(df)
        assert 'Plate_ID' in df.columns


# ===========================================================================
# Tests: remap_type_values
# ===========================================================================


class TestRemapTypeValues:
    def test_neg_cntrl_remapped_to_negative(self):
        """'neg_cntrl' → 'negative'."""
        df = pd.DataFrame({'Type': ['neg_cntrl']})
        result = remap_type_values(df)
        assert result.iloc[0]['Type'] == 'negative'

    def test_sample_stays_sample(self):
        """'sample' → 'sample' (unchanged)."""
        df = pd.DataFrame({'Type': ['sample']})
        result = remap_type_values(df)
        assert result.iloc[0]['Type'] == 'sample'

    def test_unknown_type_left_unchanged(self):
        """Unknown type values are left unchanged (no error)."""
        df = pd.DataFrame({'Type': ['unknown_type']})
        result = remap_type_values(df)
        assert result.iloc[0]['Type'] == 'unknown_type'

    def test_mixed_types_all_remapped_correctly(self):
        """Mixed Type column: each value remapped independently."""
        df = pd.DataFrame({'Type': ['neg_cntrl', 'sample', 'other']})
        result = remap_type_values(df)
        assert list(result['Type']) == ['negative', 'sample', 'other']


# ===========================================================================
# Tests: assign_dest_plate
# ===========================================================================


class TestAssignDestPlate:
    def test_first_83_rows_get_dest_plate_1(self):
        """Rows 0–82 (first 83 rows) all get Dest_plate = 1."""
        df = pd.DataFrame({'val': range(83)})
        result = assign_dest_plate(df)
        assert all(result['Dest_plate'] == 1)

    def test_row_83_gets_dest_plate_2(self):
        """Row at position 83 (84th row) gets Dest_plate = 2."""
        df = pd.DataFrame({'val': range(84)})
        result = assign_dest_plate(df)
        assert result.iloc[83]['Dest_plate'] == 2

    def test_row_165_gets_dest_plate_2_row_166_gets_3(self):
        """Row 165 → Dest_plate = 2; row 166 → Dest_plate = 3."""
        df = pd.DataFrame({'val': range(167)})
        result = assign_dest_plate(df)
        assert result.iloc[165]['Dest_plate'] == 2
        assert result.iloc[166]['Dest_plate'] == 3

    def test_single_row_gets_dest_plate_1(self):
        """A single-row DataFrame → Dest_plate = 1."""
        df = pd.DataFrame({'val': [42]})
        result = assign_dest_plate(df)
        assert result.iloc[0]['Dest_plate'] == 1

    def test_exactly_83_rows_all_get_dest_plate_1(self):
        """Exactly 83 rows → all Dest_plate = 1."""
        df = pd.DataFrame({'val': range(83)})
        result = assign_dest_plate(df)
        assert list(result['Dest_plate']) == [1] * 83

    def test_84_rows_first_83_get_1_last_gets_2(self):
        """84 rows → first 83 get Dest_plate = 1, last gets Dest_plate = 2."""
        df = pd.DataFrame({'val': range(84)})
        result = assign_dest_plate(df)
        assert list(result['Dest_plate'][:83]) == [1] * 83
        assert result.iloc[83]['Dest_plate'] == 2


# ===========================================================================
# Tests: select_and_reorder_columns
# ===========================================================================


def _make_full_output_df(extra_cols=None):
    """
    Build a one-row DataFrame containing all 14 OUTPUT_COLUMNS plus any extras.
    """
    data = {col: ['val'] for col in OUTPUT_COLUMNS}
    if extra_cols:
        for col in extra_cols:
            data[col] = ['extra']
    return pd.DataFrame(data)


class TestSelectAndReorderColumns:
    def test_returns_exactly_14_output_columns_in_order(self):
        """Result has exactly the 14 OUTPUT_COLUMNS in the correct order."""
        df = _make_full_output_df()
        result = select_and_reorder_columns(df)
        assert list(result.columns) == OUTPUT_COLUMNS

    def test_extra_columns_are_dropped(self):
        """Extra columns in input are not present in output."""
        df = _make_full_output_df(extra_cols=['Extra_Col_1', 'Extra_Col_2'])
        result = select_and_reorder_columns(df)
        assert 'Extra_Col_1' not in result.columns
        assert 'Extra_Col_2' not in result.columns
        assert list(result.columns) == OUTPUT_COLUMNS

    def test_missing_required_column_calls_sys_exit(self):
        """If a required column is absent, sys.exit() is called."""
        # Build a DataFrame missing 'Dest_plate'
        data = {col: ['val'] for col in OUTPUT_COLUMNS if col != 'Dest_plate'}
        df = pd.DataFrame(data)
        with pytest.raises(SystemExit):
            select_and_reorder_columns(df)


# ===========================================================================
# Tests: write_output_csv
# ===========================================================================


def _make_output_df(n_rows=3):
    """Build a minimal DataFrame with all 14 OUTPUT_COLUMNS."""
    data = {col: [f'val_{i}' for i in range(n_rows)] for col in OUTPUT_COLUMNS}
    # Dest_plate must be numeric for max() in main(); use ints here
    data['Dest_plate'] = list(range(1, n_rows + 1))
    return pd.DataFrame(data)


class TestWriteOutputCsv:
    def test_creates_output_dir_and_returns_correct_path(self, tmp_path):
        """Output directory is created if absent; returned path points to the CSV."""
        output_dir = tmp_path / "C_WGA_summary_and_SPITS"
        assert not output_dir.exists()

        df = _make_output_df()
        result = write_output_csv(df, output_dir)

        assert output_dir.exists()
        assert result == output_dir / "summary_MDA_results.csv"
        assert result.exists()

    def test_written_csv_has_correct_columns(self, tmp_path):
        """Reading the written CSV back yields exactly the 14 OUTPUT_COLUMNS."""
        output_dir = tmp_path / "C_WGA_summary_and_SPITS"
        df = _make_output_df()
        result_path = write_output_csv(df, output_dir)

        written = pd.read_csv(result_path)
        assert list(written.columns) == OUTPUT_COLUMNS

    def test_written_csv_has_correct_number_of_rows(self, tmp_path):
        """Reading the written CSV back yields the same number of rows as input."""
        output_dir = tmp_path / "C_WGA_summary_and_SPITS"
        n_rows = 7
        df = _make_output_df(n_rows=n_rows)
        result_path = write_output_csv(df, output_dir)

        written = pd.read_csv(result_path)
        assert len(written) == n_rows


# ===========================================================================
# Tests: create_success_marker
# ===========================================================================


class TestCreateSuccessMarker:
    def test_creates_workflow_status_dir_and_success_file(self, tmp_path, monkeypatch):
        """
        create_success_marker() creates .workflow_status/ and the success file
        inside a temp directory (via monkeypatch.chdir).
        """
        monkeypatch.chdir(tmp_path)

        create_success_marker()

        status_dir = tmp_path / ".workflow_status"
        marker_file = status_dir / "SPS_process_WGA_results.success"

        assert status_dir.exists()
        assert marker_file.exists()

    def test_success_file_contains_success_text(self, tmp_path, monkeypatch):
        """The success file content starts with 'SUCCESS:'."""
        monkeypatch.chdir(tmp_path)

        create_success_marker()

        marker_file = tmp_path / ".workflow_status" / "SPS_process_WGA_results.success"
        content = marker_file.read_text()
        assert content.startswith("SUCCESS:")
