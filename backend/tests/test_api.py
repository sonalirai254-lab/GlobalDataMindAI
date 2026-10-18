import os
import sys
from pathlib import Path
import unittest

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app, store, DEFAULT_API_PORT

class TestCompanyBrainAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_1_health_and_metrics(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "GlobalDataMind AI")
        self.assertIn("database", data)
        self.assertIn("stats", data)
        self.assertIsInstance(data["connected"], bool)
        # Truthful database reporting: if FalkorDB is offline, accurately report fallback mode
        if not data["connected"]:
            self.assertIn("offline", data["database_note"].lower())
            self.assertIn("persistent", data["database_note"].lower())
        self.assertEqual(data["node_count"], data["entity_count"])
        self.assertEqual(data["edge_count"], data["relationship_count"])

        metrics_res = self.client.get("/api/system/metrics")
        self.assertEqual(metrics_res.status_code, 200)
        metrics = metrics_res.json()
        self.assertIn("backend", metrics)
        self.assertIn("database", metrics)
        self.assertIn("avg_latency_ms", metrics["backend"])

    def test_2_interactive_graph_and_path(self):
        res = self.client.get("/api/graph")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data["nodes"]), 5)
        self.assertGreaterEqual(len(data["edges"]), 5)

        # Test path finding between Maya Chen and Project Atlas
        path_res = self.client.post("/api/graph/path", json={"source": "person_maya", "target": "project_atlas"})
        self.assertEqual(path_res.status_code, 200)
        path_data = path_res.json()
        self.assertTrue(path_data["found"])
        self.assertGreaterEqual(len(path_data["nodes"]), 2)

    def test_3_evidence_grounded_chat(self):
        # Query known entity
        res = self.client.post("/api/chat", json={"message": "Who is Maya Chen and what team does she lead?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("verified_facts", data)
        self.assertIn("supporting_evidence", data)
        self.assertGreaterEqual(len(data["verified_facts"]), 1)
        self.assertTrue(any("Maya Chen" in f for f in data["verified_facts"]))

        # Query unknown topic (honesty test: never invent evidence)
        unknown_res = self.client.post("/api/chat", json={"message": "What is Quantum Teleportation Hyperdrive?"})
        self.assertEqual(unknown_res.status_code, 200)
        unk_data = unknown_res.json()
        self.assertIn("No verified graph evidence", unk_data["answer"])
        self.assertEqual(len(unk_data["verified_facts"]), 0)

    def test_4_persistent_memory_lifecycle(self):
        # Create memory
        text = "Test memory: SOC2 compliance audit completed."
        res = self.client.post("/api/memory", json={"text": text, "kind": "Security note", "session_id": "test_session"})
        self.assertEqual(res.status_code, 200)
        item = res.json()
        mem_id = item["id"]
        self.assertTrue(item["approved"])

        # Inspect memory
        insp_res = self.client.get(f"/api/memory/{mem_id}")
        self.assertEqual(insp_res.status_code, 200)
        self.assertEqual(insp_res.json()["memory"]["text"], text)

        # Toggle approval
        toggle_res = self.client.patch(f"/api/memory/{mem_id}/approve")
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(toggle_res.json()["memory"]["approved"])

        # Delete memory
        del_res = self.client.delete(f"/api/memory/{mem_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()["deleted_id"], mem_id)

    def test_5_multi_agent_workflow(self):
        res = self.client.post("/api/agent/run", json={"goal": "Plan Q4 launch readiness for Project Atlas"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("timeline", data)
        self.assertGreaterEqual(len(data["timeline"]), 3)
        self.assertIn("plan", data)
        self.assertIn("verification", data)
        # Check that Research, Analysis, Planning, and Verification agents were invoked
        agent_names = {e["agent"] for e in data["timeline"]}
        self.assertIn("Research Agent", agent_names)
        self.assertIn("Analysis Agent", agent_names)
        self.assertIn("Planning Agent", agent_names)
        self.assertIn("Verification Agent", agent_names)

    def test_6_what_if_impact_simulator(self):
        # Simulate delay on Zero-Trust Auth
        res = self.client.post("/api/simulate/impact", json={
            "target_node_id": "project_zerotrust",
            "scenario": "DELAY",
            "detail": "4-week token migration push"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("direct_impacts", data)
        self.assertIn("risk_level", data)
        self.assertTrue(data["is_hypothetical"])
        self.assertFalse(data["graph_mutated"])
        # Project Atlas depends on Zero-Trust Auth, so Project Atlas must be in direct impacts!
        atlas_impacted = any(i["id"] == "project_atlas" for i in data["direct_impacts"])
        self.assertTrue(atlas_impacted)

    def test_7_knowledge_ingestion(self):
        # Ingest text markdown
        md_text = "# API Architecture Guidelines\nEngineering requires all microservices to use token authentication."
        res = self.client.post("/api/ingest/text", json={
            "title": "API Architecture Guidelines",
            "content": md_text,
            "source_name": "test_guidelines.md"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("checksum", data["provenance"])
        doc_id = data["document_node"]["id"]

        # Cleanup
        self.client.delete(f"/api/graph/node/{doc_id}")

    def test_8_knowledge_quality_checks(self):
        res = self.client.get("/api/quality/audit")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("health_score", data)
        self.assertIn("issues", data)
        self.assertIn("metrics", data)

    def test_9_why_memory_and_queries(self):
        # 1. List decisions
        res = self.client.get("/api/decisions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["count"], 3)
        self.assertTrue(any("Postpone Q3" in d["title"] for d in data["items"]))

        # 2. Why-Query
        why_res = self.client.post("/api/decisions/why-query", json={"question": "Why did we postpone the last deployment?"})
        self.assertEqual(why_res.status_code, 200)
        why_data = why_res.json()
        self.assertTrue(why_data["found"])
        self.assertIn("token propagation race conditions", why_data["explanation"].lower())
        self.assertTrue(why_data["verified"])

        # 3. Add custom decision
        new_dec_res = self.client.post("/api/decisions", json={
            "title": "Migrate Redis to FalkorDB Cluster",
            "rationale": "Scale sub-millisecond graph queries across multi-region deployment.",
            "evidence": "Internal benchmarks doc_arch",
            "decided_by": "person_aarav",
            "associated_entities": ["project_search"],
        })
        self.assertEqual(new_dec_res.status_code, 200)
        dec_id = new_dec_res.json()["decision"]["id"]

        # Cleanup
        self.client.delete(f"/api/decisions/{dec_id}")

    def test_10_ripple_intelligence(self):
        # Test Payments API 48h downtime simulation
        res = self.client.post("/api/ripple/analyze", json={
            "target_entity_id": "service_payments",
            "change_type": "DOWNTIME",
            "detail": "Payments API 48h banking gateway outage"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["change_type"], "DOWNTIME")
        self.assertIn(data["risk_level"], ("CRITICAL", "HIGH", "MODERATE"))
        self.assertTrue(data["is_hypothetical"])
        self.assertFalse(data["production_graph_mutated"])
        self.assertGreaterEqual(len(data["direct_impacts"]) + len(data["cascade_impacts"]), 1)
        self.assertGreaterEqual(len(data["action_plan"]), 1)
        self.assertIn("confirmed_count", data)

    def test_11_hidden_connection_discovery(self):
        # Multi-hop exploration between Sana Ali and Project Atlas
        res = self.client.post("/api/graph/connections", json={
            "source": "person_sana",
            "target": "project_atlas",
            "max_hops": 4
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["found"])
        self.assertGreaterEqual(len(data["paths"]), 1)
        first_path = data["paths"][0]
        self.assertIn("hop_count", first_path)
        self.assertIn("connection_type", first_path)
        self.assertIn("path_string", first_path)

        # Indirect discoveries for Sana Ali
        ind_res = self.client.get("/api/graph/indirect/person_sana?max_hops=3")
        self.assertEqual(ind_res.status_code, 200)
        ind_data = ind_res.json()
        self.assertIn("discoveries", ind_data)

    def test_12_counterfactual_scenario_studio(self):
        # 1. List scenarios
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        scenarios = res.json()["scenarios"]
        self.assertGreaterEqual(len(scenarios), 2)

        # 2. Compare scenarios
        compare_res = self.client.post("/api/scenarios/compare", json={
            "scenario_ids": [scenarios[0]["id"], scenarios[1]["id"]]
        })
        self.assertEqual(compare_res.status_code, 200)
        comp_data = compare_res.json()
        self.assertEqual(comp_data["compared_count"], 2)

        # 3. Create hypothetical scenario
        create_res = self.client.post("/api/scenarios", json={
            "name": "Hypothetical Security Audit Delay",
            "target_entity_id": "project_zerotrust",
            "change_type": "DELAY",
            "detail": "2-week compliance extension",
        })
        self.assertEqual(create_res.status_code, 200)
        scen_id = create_res.json()["id"]

        # 4. Authorized apply with confirmation
        apply_res = self.client.post(f"/api/scenarios/{scen_id}/apply", json={
            "confirm": True,
            "authorized_by": "Test Administrator"
        })
        self.assertEqual(apply_res.status_code, 200)
        self.assertEqual(apply_res.json()["status"], "success")

    def test_13_trust_ledger_and_claim_verification(self):
        # 1. List trust ledger
        res = self.client.get("/api/trust-ledger")
        self.assertEqual(res.status_code, 200)
        entries = res.json()["entries"]
        self.assertGreaterEqual(len(entries), 1)
        self.assertIn("groundedness_percentage", entries[0])

        # 2. Verify claim
        verify_res = self.client.post("/api/trust-ledger/verify-claim", json={
            "claim": "Maya Chen leads Product Team and owns Project Atlas"
        })
        self.assertEqual(verify_res.status_code, 200)
        v_data = verify_res.json()
        self.assertTrue(v_data["verified"])
        self.assertGreaterEqual(len(v_data["supporting_nodes"]), 1)

    def test_14_ai_router_pipeline_and_safety(self):
        # Query ripple intent through chat
        res = self.client.post("/api/chat", json={
            "message": "What happens if Payments API becomes unavailable for 48 hours?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "RIPPLE_IMPACT")
        self.assertIn("trust_ledger_id", data)
        self.assertIn("ripple_details", data)

        # Query why-memory intent through chat
        why_res = self.client.post("/api/chat", json={
            "message": "Why was the Q3 enterprise deployment postponed?"
        })
        self.assertEqual(why_res.status_code, 200)
        why_data = why_res.json()
        self.assertEqual(why_data["intent"], "WHY_DECISION")
        self.assertIn("decision_record", why_data)

        # Destructive Cypher statement block test
        bad_cypher = self.client.post("/api/cypher", json={"query": "DROP GRAPH global_datamind"})
        self.assertEqual(bad_cypher.status_code, 403)

    def test_15_profile_loading_endpoint(self):
        """Verify profile endpoint returns 200 with complete academic structure and no 503."""
        res = self.client.get("/api/personal/profile")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("actual_records", data)
        self.assertIn("summary", data)
        self.assertIn("timeline", data)
        self.assertIn("missing_milestones", data)
        self.assertIn("calculated_insights", data)
        self.assertIn("comparison", data)
        self.assertFalse(data["summary"]["privacy_mode_active"])

        # Masked profile request
        masked_res = self.client.get("/api/personal/profile?mask=true")
        self.assertEqual(masked_res.status_code, 200)
        masked_data = masked_res.json()
        self.assertTrue(masked_data["summary"]["privacy_mode_active"])

    def test_16_api_port_configuration(self):
        """Verify the standardized API default port is 8000."""
        self.assertEqual(DEFAULT_API_PORT, 8000)
        # Verify fallback port is 8000 when PORT is unset
        self.assertEqual(int(os.getenv("PORT", str(DEFAULT_API_PORT))), 8000)

if __name__ == "__main__":
    unittest.main()
