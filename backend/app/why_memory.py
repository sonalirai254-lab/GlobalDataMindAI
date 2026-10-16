"""Why-Memory Engine: Persistent organizational decision memory with provenance, rationale, and verification.
Preserves decision history and explains the 'why' behind dependencies and changes.
"""
from __future__ import annotations

import time
import copy
from typing import Any
from .schema import DecisionRecord

INITIAL_SEED_DECISIONS: list[dict[str, Any]] = [
    {
        "id": "decision_postpone_deploy",
        "title": "Postpone Q3 Enterprise Deployment to Oct 28",
        "rationale": "Security compliance audit identified token propagation race conditions in the legacy session bridge.",
        "evidence": "doc_security_audit (Findings section 3.2, zero critical but 2 high-priority token race warnings)",
        "outcome": "Granted engineering 5 weeks to implement Zero-Trust Auth token bridge before customer release.",
        "status": "executed",
        "valid_from": "2026-09-01",
        "valid_until": "2026-10-28",
        "decided_by": "person_marcus",
        "decided_by_name": "Marcus Vance",
        "associated_entities": ["project_atlas", "person_marcus", "team_security", "doc_security_audit", "project_zerotrust"],
        "source_refs": ["doc_security_audit", "doc_roadmap"],
        "verified": True,
        "created_at": "Sep 01, 2026",
        "timestamp": 1788220800,
    },
    {
        "id": "decision_falkordb",
        "title": "Adopt FalkorDB as Primary Graph Store",
        "rationale": "Selected FalkorDB for sub-millisecond Cypher traversals, entity merging, and graph-native memory persistence.",
        "evidence": "doc_arch (Section 4: Database Benchmarks showing <5ms 3-hop traversal latency)",
        "outcome": "Multi-hop dependency lookups dropped from 280ms to 4.2ms; enabled persistent organizational memory.",
        "status": "active",
        "valid_from": "2026-08-15",
        "valid_until": None,
        "decided_by": "person_aarav",
        "decided_by_name": "Aarav Patel",
        "associated_entities": ["project_search", "person_aarav", "team_eng", "doc_arch"],
        "source_refs": ["doc_arch"],
        "verified": True,
        "created_at": "Aug 15, 2026",
        "timestamp": 1786752000,
    },
    {
        "id": "decision_payments_sla",
        "title": "Decouple Payments API and Enforce Circuit Breaker",
        "rationale": "Prevent 3rd-party banking gateway latency spikes from cascading into core project atlas workflows.",
        "evidence": "doc_arch & Customer Research Incident #412 postmortem",
        "outcome": "Established standalone microservice with 48h asynchronous retry queue and graceful fallback.",
        "status": "active",
        "valid_from": "2026-07-20",
        "valid_until": None,
        "decided_by": "person_aarav",
        "decided_by_name": "Aarav Patel",
        "associated_entities": ["service_payments", "project_atlas", "team_eng"],
        "source_refs": ["doc_arch", "doc_research"],
        "verified": True,
        "created_at": "Jul 20, 2026",
        "timestamp": 1784505600,
    },
    {
        "id": "decision_zerotrust_mandate",
        "title": "Mandate Zero-Trust Token Verification for Inter-Service Calls",
        "rationale": "SOC2 Type II compliance mandate and cross-tenant graph memory isolation requirements.",
        "evidence": "doc_security_audit (SOC2 Control CC6.1 & CC6.3)",
        "outcome": "All services require mTLS and cryptographically signed JWTs; zero trust bridge operational.",
        "status": "active",
        "valid_from": "2026-09-10",
        "valid_until": None,
        "decided_by": "person_marcus",
        "decided_by_name": "Marcus Vance",
        "associated_entities": ["project_zerotrust", "person_marcus", "team_security", "doc_security_audit"],
        "source_refs": ["doc_security_audit"],
        "verified": True,
        "created_at": "Sep 10, 2026",
        "timestamp": 1788998400,
    },
]


class WhyMemoryManager:
    """Manages persistent decision memory with Cypher graph integration."""

    def __init__(self, store: Any) -> None:
        self.store = store
        self._decisions: list[dict[str, Any]] = copy.deepcopy(INITIAL_SEED_DECISIONS)

    def list_decisions(self, status: str | None = None) -> list[dict[str, Any]]:
        if status and status != "All":
            return [d for d in self._decisions if d.get("status") == status]
        return copy.deepcopy(self._decisions)

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        for d in self._decisions:
            if d["id"] == decision_id:
                return copy.deepcopy(d)
        return None

    def get_decisions_for_entity(self, entity_id: str) -> list[dict[str, Any]]:
        """Return all decisions associated with a specific entity."""
        matches = []
        for d in self._decisions:
            if entity_id in d.get("associated_entities", []) or entity_id == d.get("decided_by"):
                matches.append(copy.deepcopy(d))
        return matches

    def add_decision(
        self,
        title: str,
        rationale: str,
        evidence: str = "",
        decided_by: str = "",
        associated_entities: list[str] | None = None,
        source_refs: list[str] | None = None,
        outcome: str = "",
        valid_from: str = "",
        valid_until: str | None = None,
        status: str = "active",
        verified: bool = True,
    ) -> dict[str, Any]:
        slug = title.lower().replace(" ", "_").replace("-", "_")
        clean_slug = "".join(ch for ch in slug if ch.isalnum() or ch == "_")[:32]
        d_id = f"decision_{clean_slug}_{int(time.time()) % 10000}"

        record = {
            "id": d_id,
            "title": title.strip(),
            "rationale": rationale.strip(),
            "evidence": evidence.strip() or "Graph observation",
            "outcome": outcome.strip() or "Pending review",
            "status": status,
            "valid_from": valid_from or time.strftime("%Y-%m-%d", time.gmtime()),
            "valid_until": valid_until,
            "decided_by": decided_by,
            "associated_entities": associated_entities or [],
            "source_refs": source_refs or [],
            "verified": verified,
            "created_at": time.strftime("%b %d, %Y", time.gmtime()),
            "timestamp": int(time.time()),
        }

        self._decisions.insert(0, record)

        # Sync to GraphStore and FalkorDB as a Decision node
        self.store.add_entity(
            name=record["title"],
            kind="Decision",
            detail=f"{record['rationale']} Outcome: {record['outcome']}",
            entity_id=d_id,
        )

        # Create relationship edges if entities specified
        for target_id in record["associated_entities"]:
            self.store.add_edge(d_id, target_id, "EXPLAINS")

        if decided_by:
            self.store.add_edge(d_id, decided_by, "DECIDED_BY")

        for src in record["source_refs"]:
            self.store.add_edge(d_id, src, "DOCUMENTED_IN")

        return record

    def update_decision_status(self, decision_id: str, new_status: str, verification_note: str = "") -> dict[str, Any] | None:
        for d in self._decisions:
            if d["id"] == decision_id:
                d["status"] = new_status
                if verification_note:
                    d["evidence"] = f"{d.get('evidence', '')} | Verified: {verification_note}"
                return copy.deepcopy(d)
        return None

    def delete_decision(self, decision_id: str) -> bool:
        initial_len = len(self._decisions)
        self._decisions = [d for d in self._decisions if d["id"] != decision_id]
        if len(self._decisions) < initial_len:
            self.store.delete_node(decision_id)
            return True
        return False

    def query_why(self, question: str) -> dict[str, Any]:
        """Answer 'Why' and 'What changed' questions using persistent decision memory."""
        q_lower = question.lower()
        tokens = [w for w in q_lower.replace("?", "").replace(",", "").split() if len(w) > 2]

        scored: list[tuple[int, dict[str, Any]]] = []
        for d in self._decisions:
            score = 0
            searchable = f"{d['title']} {d['rationale']} {d['evidence']} {d['outcome']} {' '.join(d.get('associated_entities', []))}".lower()
            for tok in tokens:
                if tok in searchable:
                    score += 2
                if tok in d["title"].lower():
                    score += 3
            if score > 0:
                scored.append((score, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        matched_decisions = [item[1] for item in scored[:3]]

        if not matched_decisions:
            return {
                "found": False,
                "question": question,
                "explanation": (
                    f"No verified historical decision in Why-Memory explains '{question}'. "
                    "Graphwise Nexus only cites verified organizational decisions and does not invent speculative justifications."
                ),
                "matched_decisions": [],
                "verified": False,
                "source": "Why-Memory Store",
            }

        primary = matched_decisions[0]
        nodes_data = self.store.graph_data().get("nodes", [])
        by_id = {n["id"]: n for n in nodes_data}

        associated_details = [
            {"id": eid, "label": by_id[eid]["label"] if eid in by_id else eid, "kind": by_id[eid]["kind"] if eid in by_id else "Entity"}
            for eid in primary.get("associated_entities", [])
        ]

        explanation_parts = [
            f"**Decision: {primary['title']}** (Recorded on {primary['created_at']}, Status: *{primary['status']}*).",
            f"**Rationale**: {primary['rationale']}",
            f"**Supporting Evidence**: {primary['evidence']}.",
            f"**Resulting Outcome**: {primary['outcome']}.",
        ]

        return {
            "found": True,
            "question": question,
            "primary_decision": primary,
            "explanation": " ".join(explanation_parts),
            "matched_decisions": matched_decisions,
            "associated_entities": associated_details,
            "verified": primary.get("verified", True),
            "valid_from": primary.get("valid_from"),
            "valid_until": primary.get("valid_until"),
            "source": "Why-Memory (FalkorDB :Decision)",
        }
