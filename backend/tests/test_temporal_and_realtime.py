import os
import sys
from pathlib import Path
import unittest

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app, store, temporal_engine, event_mgr

class TestTemporalAndRealtime(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_1_timeline_checkpoints(self):
        res = self.client.get("/api/graph/timeline")
        self.assertEqual(res.status_code, 200)
        checkpoints = res.json()
        self.assertGreaterEqual(len(checkpoints), 4)
        cp_ids = [cp["id"] for cp in checkpoints]
        self.assertIn("1_month_ago", cp_ids)
        self.assertIn("1_week_ago", cp_ids)
        self.assertIn("yesterday", cp_ids)
        self.assertIn("now", cp_ids)

    def test_2_historical_snapshot_reconstruction(self):
        # 1 Month ago snapshot
        res_past = self.client.get("/api/graph/historical?timestamp=1_month_ago")
        self.assertEqual(res_past.status_code, 200)
        data_past = res_past.json()
        self.assertIn("nodes", data_past)
        self.assertIn("edges", data_past)
        self.assertEqual(data_past["temporal_dimension"], "valid_time")

        # Live snapshot
        res_live = self.client.get("/api/graph/historical?timestamp=now")
        self.assertEqual(res_live.status_code, 200)
        data_live = res_live.json()
        self.assertGreaterEqual(len(data_live["nodes"]), len(data_past["nodes"]))

    def test_3_topological_diff_computation(self):
        diff_payload = {"t1": "1_month_ago", "t2": "now"}
        res = self.client.post("/api/graph/diff", json=diff_payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("summary", data)
        self.assertIn("diff", data)
        self.assertIn("counts", data)
        # Should detect modified nodes or added edges over 1 month
        self.assertGreater(len(data["summary"]), 10)
        self.assertIn("modified_nodes", data["diff"])

    def test_4_entity_historical_lifecycle(self):
        res = self.client.get("/api/graph/entity/task_soc2/history")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["found"])
        self.assertEqual(data["entity"]["id"], "task_soc2")
        timeline = data["timeline"]
        self.assertGreaterEqual(len(timeline), 2)
        # Verify ownership transition in timeline
        owner_events = [e for e in timeline if e["event_type"] == "OWNER_REASSIGNED"]
        self.assertGreaterEqual(len(owner_events), 1)
        self.assertTrue(any("Marcus Vance" in e["description"] for e in owner_events))

    def test_5_realtime_webhook_ingestion_and_deduplication(self):
        evt_id = "test_webhook_evt_001"
        payload = {
            "event_id": evt_id,
            "event_type": "STATUS_CHANGED",
            "source": "ci_pipeline",
            "timestamp": "2026-10-15T01:00:00Z",
            "entity_id": "project_atlas",
            "payload": {
                "new_status": "qa_validation",
                "reason": "Automated regression tests passed",
            },
        }

        # 1. First ingestion -> Success
        res1 = self.client.post("/api/events/webhook", json=payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1["status"], "success")
        self.assertEqual(data1["event_id"], evt_id)

        # 2. Duplicate ingestion -> Deduplication rejection
        res2 = self.client.post("/api/events/webhook", json=payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["status"], "duplicate")
        self.assertEqual(data2["event_id"], evt_id)

    def test_6_service_outage_generates_evidence_backed_alert(self):
        outage_evt_id = "test_outage_evt_002"
        payload = {
            "event_id": outage_evt_id,
            "event_type": "SERVICE_OUTAGE",
            "source": "pagerduty",
            "timestamp": "2026-10-15T01:15:00Z",
            "entity_id": "service_payments",
            "payload": {
                "reason": "Simulated Gateway Timeout 504 on Stripe webhook",
                "severity": "CRITICAL",
            },
        }

        res = self.client.post("/api/events/webhook", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"]["action"], "outage_recorded")
        self.assertIn("generated_alert_id", data["result"])

        # Check that alert appears in alerts list
        alerts_res = self.client.get("/api/events/alerts")
        self.assertEqual(alerts_res.status_code, 200)
        alerts = alerts_res.json()
        outage_alert = next((a for a in alerts if a.get("event_id") == outage_evt_id), None)
        self.assertIsNotNone(outage_alert)
        self.assertEqual(outage_alert["severity"], "CRITICAL")
        self.assertGreater(len(outage_alert["dependency_path"]), 0)
        self.assertGreater(len(outage_alert["action_plan"]), 0)

        # Acknowledge alert
        alert_id = outage_alert["id"]
        ack_res = self.client.post(f"/api/events/alerts/{alert_id}/acknowledge")
        self.assertEqual(ack_res.status_code, 200)
        self.assertTrue(ack_res.json()["alert"]["acknowledged"])

    def test_7_event_bus_telemetry_and_history(self):
        res = self.client.get("/api/events/status")
        self.assertEqual(res.status_code, 200)
        status_data = res.json()
        self.assertIn("status", status_data)
        self.assertIn("telemetry", status_data)
        self.assertGreater(status_data["telemetry"]["total_events_received"], 0)
        self.assertGreater(status_data["telemetry"]["duplicates_rejected"], 0)

        hist_res = self.client.get("/api/events/history")
        self.assertEqual(hist_res.status_code, 200)
        history = hist_res.json()
        self.assertGreater(len(history), 0)

    def test_8_unified_ai_temporal_questions(self):
        # A. Query previous owner of task
        res_prev = self.client.post("/api/chat", json={
            "message": "Who owned this task before the latest update?"
        })
        self.assertEqual(res_prev.status_code, 200)
        data_prev = res_prev.json()
        self.assertEqual(data_prev["intent"], "TEMPORAL_HISTORICAL")
        self.assertIn("time_period", data_prev)
        self.assertIn("Aarav Patel", data_prev["answer"])
        self.assertIn("Marcus Vance", data_prev["answer"])
        self.assertGreater(len(data_prev["verified_facts"]), 0)

        # B. Query changes over the last month
        res_month = self.client.post("/api/chat", json={
            "message": "What changed in Project Atlas over the last month?"
        })
        self.assertEqual(res_month.status_code, 200)
        data_month = res_month.json()
        self.assertEqual(data_month["intent"], "TEMPORAL_HISTORICAL")
        self.assertIn("time_period", data_month)
        self.assertIn("status", data_month["answer"].lower())

        # C. Query current status
        res_status = self.client.post("/api/chat", json={
            "message": "What is the current status of Project Atlas?"
        })
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertEqual(data_status["intent"], "CURRENT_STATUS")
        self.assertIn("Current / Live State", data_status["time_period"])
        self.assertIn("Project Atlas", data_status["answer"])

        # D. Graph comparison
        res_comp = self.client.post("/api/chat", json={
            "message": "Compare the current graph with its state last week."
        })
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.json()
        self.assertEqual(data_comp["intent"], "TEMPORAL_HISTORICAL")
        self.assertIn("time_period", data_comp)
        self.assertIn("Topological Graph Comparison", data_comp["answer"])

    def test_9_event_simulator_endpoint(self):
        # Test simulated owner reassignment
        sim_res = self.client.post("/api/events/simulate", json={"scenario": "OWNER_REASSIGN"})
        self.assertEqual(sim_res.status_code, 200)
        sim_data = sim_res.json()
        self.assertEqual(sim_data["status"], "success")
        self.assertEqual(sim_data["result"]["action"], "owner_reassigned")
        self.assertEqual(sim_data["result"]["new_owner"], "Elena Rostova")


if __name__ == "__main__":
    unittest.main()
