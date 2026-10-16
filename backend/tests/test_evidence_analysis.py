"""Tests for Evidence-Based AI Analysis: Trends, Anomalies, Citations, Uncertainty, and Disclaimers."""
import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.graph_store import GraphStore
from app.trust_ledger import TrustLedgerManager
from app.global_intelligence import GlobalIntelligenceManager
from app.personal_intelligence import PersonalIntelligenceManager, AcademicRecordInput
from app.evidence_analysis import EvidenceAnalysisEngine, NO_PREDICTION_GUARANTEE


class TestEvidenceAnalysis(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = GraphStore()
        self.trust_ledger = TrustLedgerManager(self.store)
        self.global_mgr = GlobalIntelligenceManager(self.store, self.trust_ledger, cache_dir=self.temp_dir)
        self.personal_mgr = PersonalIntelligenceManager(self.store, self.trust_ledger, storage_dir=self.temp_dir)
        self.engine = EvidenceAnalysisEngine(self.global_mgr, self.personal_mgr, self.trust_ledger, self.store)
        self.client = TestClient(app)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("app.global_intelligence.WorldBankConnector.fetch_observations")
    def test_global_series_evidence_analysis(self, mock_fetch):
        # Mock realistic multi-year historical series with COVID-19 anomaly in 2020
        mock_fetch.return_value = {
            "country": {"code": "IND", "name": "India"},
            "indicator": {"code": "NY.GDP.PCAP.CD", "name": "GDP per capita (current US$)", "unit": "current US$"},
            "meta": {
                "source": "World Bank World Development Indicators",
                "source_id": "2",
                "last_updated": "2024-03-28",
                "fetched_at": "2026-10-15T10:00:00Z",
                "total_observations": 5,
                "valid_observations": 4,
                "missing_observations": 1,
            },
            "analytics": {
                "latest_value": 2410.0,
                "latest_year": 2022,
                "oldest_value": 1500.0,
                "oldest_year": 2018,
            },
            "observations": [
                {"year": 2018, "value": 1500.0, "is_missing": False},
                {"year": 2019, "value": 1650.0, "is_missing": False},
                {"year": 2020, "value": 1400.0, "is_missing": False},  # Drop (anomaly)
                {"year": 2021, "value": None, "is_missing": True},     # Missing year (never fabricated)
                {"year": 2022, "value": 2410.0, "is_missing": False},  # Rebound
            ],
        }

        res = self.engine.analyze_global_series("IND", "NY.GDP.PCAP.CD", 2018, 2022)

        # 1. Structure verification
        self.assertEqual(res["analysis_scope"], "GLOBAL_COUNTRY_INTELLIGENCE")
        self.assertEqual(res["country"]["code"], "IND")
        self.assertIn("India", res["summary"])

        # 2. Historical Trend
        trend = res["historical_trend"]
        self.assertEqual(trend["direction"], "Growth")
        self.assertEqual(trend["oldest_observation"]["year"], 2018)
        self.assertEqual(trend["latest_observation"]["year"], 2022)
        self.assertGreater(trend["percentage_change"], 50.0)
        self.assertIsNotNone(trend["cagr_percentage"])

        # 3. Anomaly detection
        anomalies = res["detected_anomalies"]
        self.assertTrue(any("2020" in a["period"] for a in anomalies))

        # 4. Citations and verified facts
        citations = res["citations"]
        self.assertGreaterEqual(len(citations), 2)
        self.assertEqual(citations[0]["source"], "World Bank World Development Indicators")
        self.assertEqual(citations[0]["source_id"], "2")
        self.assertEqual(citations[0]["last_updated"], "2024-03-28")

        # 5. Uncertainty and data limitations
        limitations = res["uncertainty_and_limitations"]
        self.assertTrue(any("2021" in lim for lim in limitations))
        self.assertTrue(any("causation" in lim.lower() for lim in limitations))

        # 6. Scenarios and disclaimer
        self.assertIn(NO_PREDICTION_GUARANTEE, res["disclaimer"])
        self.assertTrue(len(res["analytical_scenarios"]) >= 1)
        for s in res["analytical_scenarios"]:
            self.assertIn("Not Guaranteed", s["confidence_level"])

        # 7. Trust ledger entry recorded
        ledger_entry = self.trust_ledger.get_entry(res["trust_ledger_id"])
        self.assertIsNotNone(ledger_entry)
        self.assertIn(ledger_entry["verification_status"], ("VERIFIED", "PARTIALLY_GROUNDED"))

    @patch("app.global_intelligence.GlobalIntelligenceManager.compare_countries")
    def test_global_comparison_analysis(self, mock_compare):
        mock_compare.return_value = {
            "indicator": {"code": "NY.GDP.MKTP.CD", "name": "GDP", "unit": "current US$"},
            "years": [2020, 2021, 2022],
            "latest_rankings": [
                {"rank": 1, "country_code": "USA", "country_name": "United States", "latest_value": 25000000.0, "latest_year": 2022},
                {"rank": 2, "country_code": "IND", "country_name": "India", "latest_value": 3500000.0, "latest_year": 2022},
            ],
            "countries": {},
        }

        res = self.engine.analyze_global_comparison(["USA", "IND"], "NY.GDP.MKTP.CD", 2020, 2022)
        self.assertEqual(res["analysis_scope"], "GLOBAL_CROSS_COUNTRY_COMPARISON")
        self.assertEqual(len(res["rankings"]), 2)
        self.assertEqual(res["rankings"][0]["country_code"], "USA")
        self.assertIsNotNone(res["disparity_metrics"]["disparity_ratio"])
        self.assertIn("United States", res["summary"])
        self.assertTrue(any("purchasing power" in lim.lower() for lim in res["uncertainty_and_limitations"]))

    def test_personal_intelligence_analysis(self):
        # 1. Empty profile test
        empty_res = self.engine.analyze_personal_records()
        self.assertFalse(empty_res["has_records"])
        self.assertEqual(empty_res["recorded_milestones_count"], 0)
        self.assertIn("Zero-fabrication rule active", empty_res["summary"])

        # 2. Add records
        self.personal_mgr.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="Delhi Public School",
            board_or_university="CBSE",
            passing_year=2018,
            grading_system="percentage",
            score=92.0,
            roll_or_registration_number="CBSE10-847291",
        ))
        self.personal_mgr.add_or_update_record(AcademicRecordInput(
            level="Class 12",
            institution="Delhi Public School",
            board_or_university="CBSE",
            passing_year=2020,
            stream_or_major="Science (PCM)",
            grading_system="percentage",
            score=89.0,
            roll_or_registration_number="CBSE12-918230",
        ))
        self.personal_mgr.add_or_update_record(AcademicRecordInput(
            level="B.Tech",
            institution="IIT Varanasi",
            board_or_university="IIT",
            passing_year=2024,
            stream_or_major="Computer Science and Engineering",
            grading_system="cgpa",
            score=8.8,
            max_score=10.0,
            roll_or_registration_number="IIT-2020-048",
        ))

        res = self.engine.analyze_personal_records(mask_sensitive=True)
        self.assertTrue(res["has_records"])
        self.assertEqual(res["analysis_scope"], "PERSONAL_ACADEMIC_INTELLIGENCE")
        self.assertEqual(res["recorded_milestones_count"], 3)
        self.assertGreater(res["academic_average_percentage"], 85.0)

        # Citations check
        citations = res["citations"]
        self.assertEqual(len(citations), 3)
        self.assertEqual(citations[0]["source"], "User-Attested Academic Transcripts (Self-Reported)")
        # Masking check
        self.assertTrue(citations[0]["registration_ref"].endswith("7291"))
        self.assertTrue(citations[0]["registration_ref"].startswith("*"))

        # Limitations check
        limitations = res["uncertainty_and_limitations"]
        self.assertTrue(any("self-attested" in lim.lower() for lim in limitations))
        self.assertTrue(any("not guarantee" in lim.lower() for lim in limitations))

        # Disclaimer
        self.assertIn(NO_PREDICTION_GUARANTEE, res["disclaimer"])

    def test_error_handling_invalid_inputs(self):
        # Empty country code
        with self.assertRaises(ValueError):
            self.engine.analyze_global_series("", "SP.POP.TOTL")

        # Empty indicator code
        with self.assertRaises(ValueError):
            self.engine.analyze_global_series("USA", "")

        # Less than 2 countries for comparison
        with self.assertRaises(ValueError):
            self.engine.analyze_global_comparison(["USA"], "SP.POP.TOTL")

    def test_api_endpoints_evidence_analysis(self):
        # 1. Personal AI Analysis GET & POST
        res_personal_get = self.client.get("/api/ai/analyze/personal?mask=true")
        self.assertEqual(res_personal_get.status_code, 200)
        self.assertIn("analysis_scope", res_personal_get.json())

        res_personal_post = self.client.post("/api/ai/analyze/personal", json={"mask_sensitive": True})
        self.assertEqual(res_personal_post.status_code, 200)
        self.assertEqual(res_personal_post.json()["analysis_scope"], "PERSONAL_ACADEMIC_INTELLIGENCE")

        # 2. Validation error handling on Global Analysis POST
        res_global_err = self.client.post("/api/ai/analyze/global", json={
            "country": "A",  # Too short (< 2 chars)
            "indicator": "SP.POP.TOTL",
        })
        self.assertEqual(res_global_err.status_code, 422)

        # 3. Validation error handling on Global Compare Analysis POST
        res_comp_err = self.client.post("/api/ai/analyze/global/compare", json={
            "country_codes": ["USA"],  # Needs at least 2
            "indicator": "SP.POP.TOTL",
        })
        self.assertEqual(res_comp_err.status_code, 422)


if __name__ == "__main__":
    unittest.main()
