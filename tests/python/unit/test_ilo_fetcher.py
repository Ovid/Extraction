"""Tests for ILO SDMX fetcher."""

import csv
from unittest.mock import patch

from fetchers.ilo import fetch, parse_sdmx_csv

HEADER = (
    "DATAFLOW,REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE,OBS_STATUS,"
    "UNIT_MEASURE_TYPE,UNIT_MEASURE,UNIT_MULT,SOURCE,NOTE_SOURCE,"
    "NOTE_INDICATOR,NOTE_CLASSIF,DECIMALS,UPPER_BOUND,LOWER_BOUND"
)

ROW_USA_2023 = "ILO:DF_LAP_2GDP_NOC_RT(1.0),USA,A,LAP_2GDP_RT,2023,55.385,I,RT,PT,0,ILO - Modelled Estimates,,,,1,,"
ROW_CAN_2023 = "ILO:DF_LAP_2GDP_NOC_RT(1.0),CAN,A,LAP_2GDP_RT,2023,58.495,I,RT,PT,0,ILO - Modelled Estimates,,,,1,,"
ROW_USA_2022 = "ILO:DF_LAP_2GDP_NOC_RT(1.0),USA,A,LAP_2GDP_RT,2022,56.163,I,RT,PT,0,ILO - Modelled Estimates,,,,1,,"
ROW_CAN_EMPTY = "ILO:DF_LAP_2GDP_NOC_RT(1.0),CAN,A,LAP_2GDP_RT,2023,,I,RT,PT,0,ILO - Modelled Estimates,,,,1,,"

SAMPLE_CSV = f"{HEADER}\n{ROW_USA_2023}\n{ROW_CAN_2023}\n{ROW_USA_2022}\n"
SAMPLE_CSV_WITH_EMPTY = f"{HEADER}\n{ROW_USA_2023}\n{ROW_CAN_EMPTY}\n"


class TestParseSDMXCSV:
    def test_parses_valid_csv(self):
        records = parse_sdmx_csv(SAMPLE_CSV)
        assert len(records) == 3
        assert records[0]["country_code"] == "USA"
        assert records[0]["year"] == 2023
        assert records[0]["value"] == 55.385

    def test_skips_rows_with_missing_values(self):
        records = parse_sdmx_csv(SAMPLE_CSV_WITH_EMPTY)
        assert len(records) == 1
        assert records[0]["country_code"] == "USA"


class TestFetch:
    def test_writes_csv_to_output_dir(self, tmp_path):
        with patch("fetchers.ilo.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = SAMPLE_CSV
            mock_get.return_value.raise_for_status = lambda: None
            files = fetch(tmp_path)

        output_file = tmp_path / "ilo" / "ilo_labor_share.csv"
        assert output_file.exists()
        assert "ilo/ilo_labor_share.csv" in files
        with open(output_file) as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert set(row.keys()) == {"country_code", "country_name", "year", "value", "indicator"}
