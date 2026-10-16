"""Tests for Personal Intelligence: Academic Records, Timeline, Comparison, Validation, Privacy, and Integrity."""
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.graph_store import GraphStore
from app.trust_ledger import TrustLedgerManager
from app.personal_intelligence import (
    PersonalIntelligenceManager,
    AcademicRecordInput,
    normalize_level_key,
    mask_string,
)


class TestPersonalIntelligence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = GraphStore()
        self.trust_ledger = TrustLedgerManager(self.store)
        self.manager = PersonalIntelligenceManager(
            graph_store=self.store,
            trust_ledger=self.trust_ledger,
            storage_dir=self.temp_dir,
        )
        self.client = TestClient(app)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_normalize_level_keys(self):
        self.assertEqual(normalize_level_key("Class 10"), "class_10")
        self.assertEqual(normalize_level_key("10th"), "class_10")
        self.assertEqual(normalize_level_key("Class XII"), "class_12")
        self.assertEqual(normalize_level_key("12th"), "class_12")
        self.assertEqual(normalize_level_key("B.Tech"), "btech")
        self.assertEqual(normalize_level_key("Engineering"), "btech")

        with self.assertRaises(ValueError):
            normalize_level_key("PhD in Quantum Physics")

    def test_mask_string(self):
        self.assertEqual(mask_string("12345678", keep_tail=4), "****5678")
        self.assertEqual(mask_string("CBSE2018999", keep_tail=3), "********999")
        self.assertEqual(mask_string("ABC"), "***")
        self.assertEqual(mask_string(""), "")

    def test_add_and_validate_records(self):
        # 1. Valid Class 10 (Percentage)
        rec_10 = AcademicRecordInput(
            level="Class 10",
            institution="Delhi Public School",
            board_or_university="CBSE",
            passing_year=2018,
            stream_or_major="General",
            grading_system="percentage",
            score=91.4,
            roll_or_registration_number="CBSE10-998811",
        )
        profile = self.manager.add_or_update_record(rec_10)
        self.assertEqual(profile["summary"]["recorded_milestones_count"], 1)
        actual_10 = profile["actual_records"][0]
        self.assertEqual(actual_10["qualification"], "Class 10")
        self.assertEqual(actual_10["score"], 91.4)
        self.assertEqual(actual_10["grading_system"], "percentage")
        self.assertEqual(actual_10["record_type"], "ACTUAL_RECORD")

        # 2. Valid Class 12 (Percentage)
        rec_12 = AcademicRecordInput(
            level="Class 12",
            institution="St. Xavier's Senior Secondary School",
            board_or_university="CBSE",
            passing_year=2020,
            stream_or_major="Science (PCM)",
            grading_system="percentage",
            score=88.6,
            roll_or_registration_number="CBSE12-445566",
        )
        profile = self.manager.add_or_update_record(rec_12)
        self.assertEqual(profile["summary"]["recorded_milestones_count"], 2)

        # 3. Valid B.Tech (CGPA)
        rec_btech = AcademicRecordInput(
            level="B.Tech",
            institution="National Institute of Technology",
            board_or_university="Autonomous / Central University",
            passing_year=2024,
            stream_or_major="Computer Science and Engineering",
            grading_system="cgpa",
            score=8.75,
            max_score=10.0,
            roll_or_registration_number="NIT-CSE-2024-042",
        )
        profile = self.manager.add_or_update_record(rec_btech)
        self.assertEqual(profile["summary"]["recorded_milestones_count"], 3)
        self.assertTrue(profile["summary"]["is_complete"])

    def test_chronological_sequence_validation_error(self):
        """Passing year of higher degree cannot be earlier than lower degree."""
        # Enter Class 10 in 2020
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="School A",
            board_or_university="CBSE",
            passing_year=2020,
            grading_system="percentage",
            score=85.0,
        ))

        # Attempt to enter Class 12 in 2019 (chronologically invalid)
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_or_update_record(AcademicRecordInput(
                level="Class 12",
                institution="School B",
                board_or_university="CBSE",
                passing_year=2019,
                grading_system="percentage",
                score=80.0,
            ))
        self.assertIn("Chronological error", str(ctx.exception))

    def test_score_bounds_validation(self):
        """Percentage > 100 or CGPA > max_score must be rejected."""
        with self.assertRaises(ValueError):
            self.manager.validate_record(AcademicRecordInput(
                level="Class 10",
                institution="School A",
                board_or_university="CBSE",
                passing_year=2020,
                grading_system="percentage",
                score=105.0,  # Invalid
            ))

        with self.assertRaises(ValueError):
            self.manager.validate_record(AcademicRecordInput(
                level="B.Tech",
                institution="Univ A",
                board_or_university="Tech Univ",
                passing_year=2024,
                grading_system="cgpa",
                score=11.2,  # Invalid for 10.0 scale
                max_score=10.0,
            ))

    def test_chronological_timeline_ordering(self):
        """Verify timeline is ordered Class 10 -> Class 12 -> B.Tech even if entered in reverse."""
        # Enter B.Tech (2024) first
        self.manager.add_or_update_record(AcademicRecordInput(
            level="B.Tech",
            institution="College C",
            board_or_university="Univ C",
            passing_year=2024,
            stream_or_major="Information Technology",
            grading_system="cgpa",
            score=8.5,
            max_score=10.0,
        ))
        # Enter Class 10 (2018)
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="School A",
            board_or_university="State Board",
            passing_year=2018,
            grading_system="percentage",
            score=90.0,
        ))
        # Enter Class 12 (2020)
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 12",
            institution="School B",
            board_or_university="State Board",
            passing_year=2020,
            stream_or_major="Science",
            grading_system="percentage",
            score=86.0,
        ))

        profile = self.manager.get_profile()
        timeline = profile["timeline"]
        self.assertEqual(len(timeline), 3)

        # Verify progression
        self.assertEqual(timeline[0]["qualification"], "Class 10")
        self.assertEqual(timeline[0]["passing_year"], 2018)
        self.assertIsNone(timeline[0]["years_since_previous"])

        self.assertEqual(timeline[1]["qualification"], "Class 12")
        self.assertEqual(timeline[1]["passing_year"], 2020)
        self.assertEqual(timeline[1]["years_since_previous"], 2)  # 2020 - 2018

        self.assertEqual(timeline[2]["qualification"], "B.Tech")
        self.assertEqual(timeline[2]["passing_year"], 2024)
        self.assertEqual(timeline[2]["years_since_previous"], 4)  # 2024 - 2020

    def test_distinction_actual_records_vs_calculated_insights(self):
        """Verify actual records remain untouched and calculated insights are distinctly flagged."""
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="School A",
            board_or_university="CBSE",
            passing_year=2018,
            grading_system="percentage",
            score=90.0,
        ))
        self.manager.add_or_update_record(AcademicRecordInput(
            level="B.Tech",
            institution="College B",
            board_or_university="Univ B",
            passing_year=2024,
            grading_system="cgpa",
            score=8.0,
            max_score=10.0,  # 80.0% equivalent
        ))

        profile = self.manager.get_profile()

        # Actual records verification
        actual_records = profile["actual_records"]
        self.assertEqual(len(actual_records), 2)
        for r in actual_records:
            self.assertEqual(r["record_type"], "ACTUAL_RECORD")
        # Raw score for B.Tech remains 8.0, not converted
        btech_rec = next(r for r in actual_records if r["level_key"] == "btech")
        self.assertEqual(btech_rec["score"], 8.0)
        self.assertEqual(btech_rec["max_score"], 10.0)

        # Calculated insights verification
        insights = profile["calculated_insights"]
        self.assertGreaterEqual(len(insights), 3)
        for insight in insights:
            self.assertEqual(insight["type"], "CALCULATED_INSIGHT")
            self.assertIn("derivation_formula", insight)
            self.assertTrue(len(insight["derivation_formula"]) > 5)

        # Average is (90.0 + 80.0) / 2 = 85.0%
        avg_insight = next(i for i in insights if i["insight_key"] == "academic_average")
        self.assertEqual(avg_insight["numeric_value"], 85.0)

    def test_comparison_handles_missing_data_without_fabrication(self):
        """If only Class 10 is entered, compare available results and flag missing milestones as strictly None."""
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="School 10",
            board_or_university="ICSE",
            passing_year=2019,
            grading_system="percentage",
            score=92.0,
        ))

        profile = self.manager.get_profile()
        comparison = profile["comparison"]

        # Only 1 milestone available
        self.assertEqual(comparison["available_milestones"], ["Class 10"])
        self.assertEqual(len(comparison["comparison_matrix"]), 1)
        self.assertEqual(len(comparison["score_deltas"]), 0)

        # Missing milestones: Class 12 and B.Tech are explicitly missing and have value None
        missing = profile["missing_milestones"]
        self.assertEqual(len(missing), 2)
        missing_keys = [m["level_key"] for m in missing]
        self.assertIn("class_12", missing_keys)
        self.assertIn("btech", missing_keys)
        for m in missing:
            self.assertEqual(m["status"], "NOT_RECORDED")
            self.assertIsNone(m["value"])  # Never fabricated

    def test_privacy_masking_mode(self):
        """Verify sensitive roll numbers are masked in privacy mode."""
        self.manager.add_or_update_record(AcademicRecordInput(
            level="Class 10",
            institution="Public School",
            board_or_university="CBSE",
            passing_year=2018,
            grading_system="percentage",
            score=88.0,
            roll_or_registration_number="ROLL-12345678",
        ))

        # Unmasked profile
        unmasked = self.manager.get_profile(mask_sensitive=False)
        self.assertEqual(unmasked["actual_records"][0]["roll_or_registration_number"], "ROLL-12345678")

        # Masked profile
        masked = self.manager.get_profile(mask_sensitive=True)
        self.assertEqual(masked["actual_records"][0]["roll_or_registration_number"], "*********5678")
        self.assertTrue(masked["summary"]["privacy_mode_active"])

    def test_graph_and_trust_ledger_integration(self):
        """Storing a record adds node to GraphStore and records auditable entry in TrustLedger."""
        self.manager.add_or_update_record(AcademicRecordInput(
            level="B.Tech",
            institution="IIT Roorkee",
            board_or_university="IIT",
            passing_year=2024,
            stream_or_major="Electrical Engineering",
            grading_system="cgpa",
            score=8.9,
            max_score=10.0,
        ))

        # Graph node check
        nodes = self.store.graph_data()["nodes"]
        btech_node = next((n for n in nodes if n["id"] == "acad_btech"), None)
        self.assertIsNotNone(btech_node)
        self.assertEqual(btech_node["kind"], "AcademicRecord")

        # Trust ledger check
        ledger_entries = self.trust_ledger.list_entries(limit=5)
        acad_entry = next((e for e in ledger_entries if "Personal Intelligence" in e.get("query", "")), None)
        self.assertIsNotNone(acad_entry)
        self.assertEqual(acad_entry["verification_status"], "VERIFIED")

    def test_api_endpoints_integration(self):
        """Verify FastAPI endpoints for profile, record creation, comparison, and reset."""
        # 1. Reset profile first
        del_res = self.client.delete("/api/personal/profile")
        self.assertEqual(del_res.status_code, 200)

        # 2. Add Class 10
        post_res = self.client.post("/api/personal/record", json={
            "level": "Class 10",
            "institution": "Springdales School",
            "board_or_university": "CBSE",
            "passing_year": 2018,
            "stream_or_major": "General",
            "grading_system": "percentage",
            "score": 93.2,
            "roll_or_registration_number": "1800921",
        })
        self.assertEqual(post_res.status_code, 200)
        profile_data = post_res.json()
        self.assertEqual(profile_data["summary"]["recorded_milestones_count"], 1)

        # 3. Add Class 12
        post_res_12 = self.client.post("/api/personal/record", json={
            "level": "Class 12",
            "institution": "Springdales School",
            "board_or_university": "CBSE",
            "passing_year": 2020,
            "stream_or_major": "Science (PCM)",
            "grading_system": "percentage",
            "score": 91.0,
            "roll_or_registration_number": "2000843",
        })
        self.assertEqual(post_res_12.status_code, 200)

        # 4. Get profile with mask=true
        get_res = self.client.get("/api/personal/profile?mask=true")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertEqual(data["summary"]["recorded_milestones_count"], 2)
        self.assertTrue(data["summary"]["privacy_mode_active"])

        # 5. Get comparison endpoint
        comp_res = self.client.get("/api/personal/comparison")
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.json()
        self.assertEqual(comp_data["available_records_count"], 2)
        self.assertEqual(comp_data["comparison"]["available_milestones"], ["Class 10", "Class 12"])

        # 6. Delete Class 10
        del_10 = self.client.delete("/api/personal/record/class_10")
        self.assertEqual(del_10.status_code, 200)
        after_del = self.client.get("/api/personal/profile").json()
        self.assertEqual(after_del["summary"]["recorded_milestones_count"], 1)


if __name__ == "__main__":
    unittest.main()
