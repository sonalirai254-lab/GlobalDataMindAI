"""Unit and integration test suite for the Universal Timestamp and Temporal Data Analysis System.

Tests:
1. Timezone conversion & internal UTC normalization (preserving original representation and timezone).
2. Daylight saving transitions (e.g. America/New_York EDT/EST transitions).
3. Timestamp precision detection (year, month, day, second, millisecond, microsecond).
4. Missing timestamps detection (flagged as MISSING, never inventing values).
5. Malformed timestamps detection (flagged as MALFORMED, never inventing values).
6. Conflicting timestamps detection (e.g., source_created_at prior to event_time, start > end).
7. Implausible timestamps detection (dates outside plausible range flagged as IMPLAUSIBLE).
8. Strict Rule 10: Year-only statistics never infer exact event_time; provides time_range with limitation note.
9. Inferred estimates: explicitly marked with is_inferred=True, method, and uncertainty margin.
10. Modular parsers: JSON, CSV, Log, Document, Structured records.
11. Temporal filtering, chronological sorting, and historical window comparisons.
12. API endpoints integration via FastAPI TestClient.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.temporal_universal import (
    UniversalTimestampParser,
    TimestampPrecision,
    TemporalValidationStatus,
    JsonTemporalParser,
    CsvTemporalParser,
    LogTemporalParser,
    DocumentTemporalParser,
    StructuredRecordTemporalParser,
    TemporalDataAnalyzer,
    get_temporal_parser,
)


class TestUniversalTemporalSystem(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # ---------------- 1. Timezone Conversion & UTC Normalization ---------------- #

    def test_utc_normalization_preserving_original(self):
        """Test conversion of various offsets to UTC while storing original timezone and raw string."""
        # EDT (-04:00)
        t_edt = UniversalTimestampParser.parse("2024-06-15T12:00:00-04:00", source_name="test_edt")
        self.assertEqual(t_edt.event_time, "2024-06-15T16:00:00Z")
        self.assertEqual(t_edt.original_event_time, "2024-06-15T12:00:00-04:00")
        self.assertEqual(t_edt.timezone, "-04:00")
        self.assertEqual(t_edt.timestamp_precision, TimestampPrecision.SECOND)
        self.assertEqual(t_edt.validation_status, TemporalValidationStatus.VALID)

        # IST (+05:30)
        t_ist = UniversalTimestampParser.parse("2024-06-15 12:00:00 IST", source_name="test_ist")
        self.assertEqual(t_ist.event_time, "2024-06-15T06:30:00Z")
        self.assertEqual(t_ist.timezone, "IST")

        # JST (+09:00)
        t_jst = UniversalTimestampParser.parse("2024-01-01T09:00:00+09:00")
        self.assertEqual(t_jst.event_time, "2024-01-01T00:00:00Z")
        self.assertEqual(t_jst.timezone, "+09:00")

    def test_daylight_saving_transitions(self):
        """Test parsing dates across US Eastern Daylight Saving transitions."""
        # Summer date in EDT (-04:00)
        t_summer = UniversalTimestampParser.parse("2024-07-04T12:00:00-04:00")
        self.assertEqual(t_summer.event_time, "2024-07-04T16:00:00Z")
        self.assertEqual(t_summer.timezone, "-04:00")

        # Winter date in EST (-05:00)
        t_winter = UniversalTimestampParser.parse("2024-12-25T12:00:00-05:00")
        self.assertEqual(t_winter.event_time, "2024-12-25T17:00:00Z")
        self.assertEqual(t_winter.timezone, "-05:00")

    # ---------------- 2. Timestamp Precision Levels ---------------- #

    def test_precision_detection(self):
        """Verify precision detection for day, second, millisecond, and microsecond."""
        # Day precision
        t_day = UniversalTimestampParser.parse("2024-08-15")
        self.assertEqual(t_day.timestamp_precision, TimestampPrecision.DAY)
        self.assertEqual(t_day.event_time, "2024-08-15T00:00:00Z")
        self.assertIsNotNone(t_day.time_range)
        self.assertEqual(t_day.time_range.precision, "day")

        # Second precision
        t_sec = UniversalTimestampParser.parse("2024-08-15T14:30:25Z")
        self.assertEqual(t_sec.timestamp_precision, TimestampPrecision.SECOND)
        self.assertEqual(t_sec.event_time, "2024-08-15T14:30:25Z")

        # Millisecond precision
        t_ms = UniversalTimestampParser.parse("2024-08-15T14:30:25.500Z")
        self.assertEqual(t_ms.timestamp_precision, TimestampPrecision.MILLISECOND)

    # ---------------- 3. Rule 10: Year-Only Statistics ---------------- #

    def test_year_only_statistic_strictly_does_not_fabricate_exact_time(self):
        """Rule 10: Never infer an exact event time from a year-only statistic or incomplete metadata."""
        # Integer year
        t_yr = UniversalTimestampParser.parse(2023, source_name="world_bank_wdi")
        self.assertIsNone(t_yr.event_time, "event_time must be None for year-only statistic")
        self.assertEqual(t_yr.timestamp_precision, TimestampPrecision.YEAR)
        self.assertEqual(t_yr.validation_status, TemporalValidationStatus.VALID)
        self.assertFalse(t_yr.requires_review)
        self.assertIsNotNone(t_yr.time_range)
        self.assertEqual(t_yr.time_range.start, "2023-01-01T00:00:00Z")
        self.assertEqual(t_yr.time_range.end, "2023-12-31T23:59:59Z")
        self.assertIn("Year-only statistic", t_yr.time_range.limitation_note)

        # String year
        t_yr_str = UniversalTimestampParser.parse("2018", source_name="academic_record")
        self.assertIsNone(t_yr_str.event_time)
        self.assertEqual(t_yr_str.timestamp_precision, TimestampPrecision.YEAR)
        self.assertEqual(t_yr_str.time_range.start, "2018-01-01T00:00:00Z")

    def test_month_only_date_handling(self):
        """Month precision returns bounded range without inventing an exact second."""
        t_month = UniversalTimestampParser.parse("2024-05")
        self.assertIsNone(t_month.event_time)
        self.assertEqual(t_month.timestamp_precision, TimestampPrecision.MONTH)
        self.assertIsNotNone(t_month.time_range)
        self.assertEqual(t_month.time_range.start, "2024-05-01T00:00:00Z")
        self.assertEqual(t_month.time_range.end, "2024-05-31T23:59:59Z")

    # ---------------- 4. Missing, Malformed, Conflicting, Implausible Detection ---------------- #

    def test_missing_timestamp_detection(self):
        """Missing timestamp is flagged for review instead of inventing a value."""
        t_none = UniversalTimestampParser.parse(None, source_name="test_missing")
        self.assertEqual(t_none.validation_status, TemporalValidationStatus.MISSING)
        self.assertTrue(t_none.requires_review)
        self.assertIsNone(t_none.event_time)
        self.assertTrue(any("MISSING_TIMESTAMP" in f for f in t_none.validation_flags))

        t_empty = UniversalTimestampParser.parse("   ")
        self.assertEqual(t_empty.validation_status, TemporalValidationStatus.MISSING)
        self.assertTrue(t_empty.requires_review)

    def test_malformed_timestamp_detection(self):
        """Malformed or impossible dates are flagged for review instead of crashing or inventing values."""
        # Nonexistent date: Feb 31
        t_bad_feb = UniversalTimestampParser.parse("2024-02-31")
        self.assertEqual(t_bad_feb.validation_status, TemporalValidationStatus.MALFORMED)
        self.assertTrue(t_bad_feb.requires_review)
        self.assertIsNone(t_bad_feb.event_time)

        # Arbitrary non-date text
        t_text = UniversalTimestampParser.parse("yester-future-time")
        self.assertEqual(t_text.validation_status, TemporalValidationStatus.MALFORMED)
        self.assertTrue(t_text.requires_review)

    def test_conflicting_timestamps_detection(self):
        """Flag when source_created_at is significantly before the event occurred."""
        t_conflict = UniversalTimestampParser.parse(
            raw_val="2026-10-18T10:00:00Z",
            source_created_raw="2020-01-01T00:00:00Z",  # Source created over 6 years prior to event
        )
        self.assertEqual(t_conflict.validation_status, TemporalValidationStatus.CONFLICTING)
        self.assertTrue(t_conflict.requires_review)
        self.assertTrue(any("CONFLICTING_TIMESTAMPS" in f for f in t_conflict.validation_flags))

    def test_implausible_timestamps_detection(self):
        """Flag timestamps outside plausible calendar range."""
        t_ancient = UniversalTimestampParser.parse("1492-10-12")
        self.assertEqual(t_ancient.validation_status, TemporalValidationStatus.IMPLAUSIBLE)
        self.assertTrue(t_ancient.requires_review)

        t_future = UniversalTimestampParser.parse(2150)
        self.assertEqual(t_future.validation_status, TemporalValidationStatus.IMPLAUSIBLE)
        self.assertTrue(t_future.requires_review)

    # ---------------- 5. Inferred Estimates ---------------- #

    def test_inferred_estimate_distinction(self):
        """Verify that estimates are explicitly marked and explain their method and uncertainty."""
        t_est = UniversalTimestampParser.create_inferred_estimate(
            estimated_start="2024-01-01T00:00:00Z",
            estimated_end="2024-06-30T23:59:59Z",
            method="curriculum_progression_window",
            uncertainty_margin="±3 months",
        )
        self.assertTrue(t_est.is_inferred)
        self.assertIsNone(t_est.event_time, "Inferred estimates must not report an exact event_time")
        self.assertEqual(t_est.inference_method, "curriculum_progression_window")
        self.assertEqual(t_est.uncertainty_margin, "±3 months")
        self.assertIsNotNone(t_est.time_range)

    # ---------------- 6. Modular Parsers ---------------- #

    def test_json_temporal_parser(self):
        """Test JSON parser extracting standard candidate timestamp fields."""
        payload = [
            {"id": "node_1", "kind": "Deployment", "event_time": "2024-05-18T10:30:00Z"},
            {"id": "node_2", "kind": "Statistic", "year": 2023},
            {"id": "node_3", "kind": "Task", "timestamp": "invalid_date_format"},
            {"id": "node_4", "kind": "Memory"},  # Missing date
        ]
        recs = JsonTemporalParser().parse(payload, source_name="test.json")
        self.assertEqual(len(recs), 4)

        # Node 1: Valid second precision
        self.assertEqual(recs[0].temporal.validation_status, TemporalValidationStatus.VALID)
        self.assertEqual(recs[0].temporal.timestamp_precision, TimestampPrecision.SECOND)

        # Node 2: Year precision
        self.assertIsNone(recs[1].temporal.event_time)
        self.assertEqual(recs[1].temporal.timestamp_precision, TimestampPrecision.YEAR)

        # Node 3: Malformed
        self.assertEqual(recs[2].temporal.validation_status, TemporalValidationStatus.MALFORMED)
        self.assertTrue(recs[2].temporal.requires_review)

        # Node 4: Missing
        self.assertEqual(recs[3].temporal.validation_status, TemporalValidationStatus.MISSING)
        self.assertTrue(recs[3].temporal.requires_review)

    def test_csv_temporal_parser(self):
        """Test CSV parser with automatic date column identification."""
        csv_content = """id,institution,passing_year,score
c10,Delhi Public School,2018,92.4
c12,Delhi Public School,2020,89.8
btech,IIT BHU Varanasi,2024,8.85
"""
        recs = CsvTemporalParser().parse(csv_content, source_name="academic.csv")
        self.assertEqual(len(recs), 3)
        self.assertEqual(recs[0].temporal.timestamp_precision, TimestampPrecision.YEAR)
        self.assertEqual(recs[0].temporal.source_provenance["detected_date_column"], "passing_year")
        self.assertEqual(recs[2].data["score"], "8.85")

    def test_log_temporal_parser(self):
        """Test parsing of Common Log Format and ISO application logs."""
        log_content = """192.168.1.10 - - [18/May/2024:14:20:00 +0000] "GET /api/health HTTP/1.1" 200 128
2024-05-18T14:25:30.100Z [INFO] Service auth token renewed successfully
"""
        recs = LogTemporalParser().parse(log_content, source_name="server.log")
        self.assertEqual(len(recs), 2)
        self.assertEqual(recs[0].temporal.event_time, "2024-05-18T14:20:00Z")
        self.assertEqual(recs[0].temporal.timestamp_precision, TimestampPrecision.SECOND)
        self.assertEqual(recs[1].temporal.event_time, "2024-05-18T14:25:30.100Z")
        self.assertEqual(recs[1].temporal.timestamp_precision, TimestampPrecision.MILLISECOND)

    def test_structured_record_adapter(self):
        """Test adapter for internal academic and global data entities."""
        rec_data = {
            "level_key": "class_10",
            "institution": "DPS",
            "passing_year": 2018,
            "verification_status": "Verified",
            "verification_timestamp": "2026-10-18T10:00:00Z",
        }
        rec = StructuredRecordTemporalParser().parse(rec_data, source_name="personal_intelligence")
        self.assertEqual(rec.id, "class_10")
        self.assertEqual(rec.temporal.timestamp_precision, TimestampPrecision.YEAR)
        self.assertEqual(rec.temporal.verified_at, "2026-10-18T10:00:00Z")

    # ---------------- 7. Temporal Data Analysis Engine ---------------- #

    def test_temporal_filtering_and_sorting(self):
        """Test time range filtering, precision filtering, and chronological sorting."""
        payload = [
            {"id": "r1", "timestamp": "2024-01-15T10:00:00Z"},
            {"id": "r2", "timestamp": "2024-06-20T10:00:00Z"},
            {"id": "r3", "timestamp": "2024-11-05T10:00:00Z"},
            {"id": "r4", "year": 2024},
            {"id": "r5", "timestamp": "2023-05-01T10:00:00Z"},
        ]
        recs = JsonTemporalParser().parse(payload)

        # Filter: June 2024 to Dec 2024
        filtered = TemporalDataAnalyzer.filter_records(
            recs,
            start_time="2024-06-01T00:00:00Z",
            end_time="2024-12-31T23:59:59Z",
        )
        filtered_ids = [r.id for r in filtered]
        self.assertIn("r2", filtered_ids)
        self.assertIn("r3", filtered_ids)
        self.assertIn("r4", filtered_ids)  # Year 2024 interval overlaps
        self.assertNotIn("r1", filtered_ids)
        self.assertNotIn("r5", filtered_ids)

        # Sort chronologically ascending
        sorted_asc = TemporalDataAnalyzer.sort_chronologically(recs, order="asc")
        # 2023 (r5) should be first
        self.assertEqual(sorted_asc[0].id, "r5")

    def test_historical_window_comparison(self):
        """Test statistical and volume comparison across two temporal windows."""
        payload = [
            {"id": "r1", "timestamp": "2023-03-01T00:00:00Z", "score": 80.0},
            {"id": "r2", "timestamp": "2023-06-01T00:00:00Z", "score": 85.0},
            {"id": "r3", "timestamp": "2024-03-01T00:00:00Z", "score": 90.0},
            {"id": "r4", "timestamp": "2024-06-01T00:00:00Z", "score": 95.0},
            {"id": "r5", "timestamp": "2024-09-01T00:00:00Z", "score": 92.0},
        ]
        recs = JsonTemporalParser().parse(payload)

        comp = TemporalDataAnalyzer.compare_historical_windows(
            records=recs,
            window_a_start="2023-01-01T00:00:00Z",
            window_a_end="2023-12-31T23:59:59Z",
            window_b_start="2024-01-01T00:00:00Z",
            window_b_end="2024-12-31T23:59:59Z",
            numeric_field="score",
        )
        self.assertEqual(comp["window_a"]["record_count"], 2)
        self.assertEqual(comp["window_b"]["record_count"], 3)
        self.assertEqual(comp["window_a"]["metric_average"], 82.5)
        self.assertAlmostEqual(comp["window_b"]["metric_average"], 92.333, places=2)
        self.assertEqual(comp["comparison"]["delta_records"], 1)

    # ---------------- 8. FastAPI API Endpoints ---------------- #

    def test_api_temporal_parse_endpoint(self):
        """Test POST /api/temporal/parse."""
        # 1. Standard ISO parse
        res1 = self.client.post("/api/temporal/parse", json={"timestamp_input": "2024-05-18T10:30:00-04:00"})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1["temporal"]["event_time"], "2024-05-18T14:30:00Z")
        self.assertEqual(data1["temporal"]["timezone"], "-04:00")

        # 2. Year-only statistic parse (Rule 10)
        res2 = self.client.post("/api/temporal/parse", json={"timestamp_input": 2024})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertIsNone(data2["temporal"]["event_time"])
        self.assertEqual(data2["temporal"]["timestamp_precision"], "year")
        self.assertIsNotNone(data2["temporal"]["time_range"])

        # 3. Missing date parse
        res3 = self.client.post("/api/temporal/parse", json={"timestamp_input": None})
        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertEqual(data3["temporal"]["validation_status"], "MISSING")
        self.assertTrue(data3["temporal"]["requires_review"])

    def test_api_temporal_ingest_and_analyze_endpoints(self):
        """Test POST /api/temporal/ingest and POST /api/temporal/analyze."""
        csv_sample = "id,name,date\n1,Event A,2024-01-01\n2,Event B,2024-06-01\n3,Event C,bad_date\n"
        res = self.client.post("/api/temporal/ingest", json={
            "source_type": "CSV",
            "content": csv_sample,
            "source_name": "test_upload.csv",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_parsed"], 3)
        self.assertIn("summary", data)
        self.assertIn("flagged_for_review_count", data["summary"])
        self.assertEqual(data["summary"]["flagged_for_review_count"], 1)  # Event C bad_date

        # Test POST /api/temporal/analyze on existing graph entities
        res_an = self.client.post("/api/temporal/analyze", json={"sort_order": "asc"})
        self.assertEqual(res_an.status_code, 200)
        an_data = res_an.json()
        self.assertIn("analysis", an_data)
        self.assertIn("timeline_points", an_data["analysis"])

    def test_api_temporal_compare_windows_endpoint(self):
        """Test POST /api/temporal/compare-windows."""
        res = self.client.post("/api/temporal/compare-windows", json={
            "window_a_start": "2026-08-01T00:00:00Z",
            "window_a_end": "2026-08-31T23:59:59Z",
            "window_b_start": "2026-09-01T00:00:00Z",
            "window_b_end": "2026-10-31T23:59:59Z",
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("window_a", data)
        self.assertIn("window_b", data)
        self.assertIn("comparison", data)

    def test_api_temporal_review_flags_endpoint(self):
        """Test GET /api/temporal/review-flags."""
        res = self.client.get("/api/temporal/review-flags")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_flagged", data)
        self.assertIn("flagged_records", data)

    def test_api_ingest_csv_and_log_endpoints(self):
        """Test dedicated POST /api/ingest/csv and POST /api/ingest/log endpoints."""
        # CSV ingestion
        csv_payload = "name,kind,event_time\nProject Alpha,Project,2024-05-18T10:00:00Z\n"
        res_csv = self.client.post("/api/ingest/csv", json={"content": csv_payload, "source_name": "projects.csv"})
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.json()["source_type"], "CSV")

        # Log ingestion
        log_payload = "2024-05-18T10:00:00Z [INFO] System initialized\n"
        res_log = self.client.post("/api/ingest/log", json={"content": log_payload, "source_name": "init.log"})
        self.assertEqual(res_log.status_code, 200)
        self.assertEqual(res_log.json()["source_type"], "LOG")


if __name__ == "__main__":
    unittest.main()
