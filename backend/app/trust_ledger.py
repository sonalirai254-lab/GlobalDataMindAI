"""Trust Ledger: Evidence-provenance layer for all AI conclusions and reasoning sessions.
Verifies facts against active graph nodes and edges, identifies assumptions, and logs auditable records.
"""
from __future__ import annotations

import time
import copy
from typing import Any
from collections import deque


class TrustLedgerManager:
    """Maintains an auditable log of AI reasoning sessions and verifiable claims."""

    def __init__(self, store: Any) -> None:
        self.store = store
        self._ledger: deque[dict[str, Any]] = deque(maxlen=100)
        self._seed_starter_ledger()

    def _seed_starter_ledger(self) -> None:
        """Seed starter historical audit entries for immediate inspection."""
        self._ledger.append({
            "id": "ledger_init_001",
            "query": "Why was the Q3 deployment postponed?",
            "conclusion": "Postponed to Oct 28 due to token propagation race conditions identified in the Security Audit.",
            "verified_facts": [
                "Zero-Trust Auth token bridge had high-priority race conditions in audit report doc_security_audit.",
                "Marcus Vance (Principal Security Architect) documented and executed postponement decision on Sep 01, 2026.",
                "Target Project Atlas deployment window adjusted to Oct 28, 2026."
            ],
            "assumptions": [
                "Engineering capacity of 5 weeks is sufficient to complete token bridge testing."
            ],
            "missing_evidence": [],
            "supporting_entities": [
                {"id": "person_marcus", "label": "Marcus Vance", "kind": "Person"},
                {"id": "project_atlas", "label": "Project Atlas", "kind": "Project"},
                {"id": "doc_security_audit", "label": "Security Audit 2026", "kind": "Document"},
                {"id": "decision_postpone_deploy", "label": "Postpone Q3 Enterprise Deployment to Oct 28", "kind": "Decision"},
            ],
            "traversed_edges": [
                {"source": "Marcus Vance", "rel": "AUTHORED", "target": "Security Audit 2026"},
                {"source": "Security Audit 2026", "rel": "INFORMS", "target": "Project Atlas"},
                {"source": "Marcus Vance", "rel": "DECIDED_BY", "target": "Postpone Q3 Enterprise Deployment"},
            ],
            "source_documents": [
                {"id": "doc_security_audit", "title": "Security Audit 2026", "checksum": "a8f3b20c91e4"}
            ],
            "retrieved_memories": [
                {"id": "mem_3", "text": "Marcus Vance confirmed Zero-Trust Auth passed SOC2 compliance verification.", "kind": "Security note"}
            ],
            "verification_status": "VERIFIED",
            "groundedness_percentage": 100,
            "database_source": "FalkorDB Graph Traversal",
            "timestamp": int(time.time()) - 3600,
            "created_at": "1 hour ago",
        })

    def record_conclusion(
        self,
        query: str,
        conclusion: str,
        verified_facts: list[str],
        assumptions: list[str],
        supporting_entities: list[dict[str, Any]],
        traversed_edges: list[dict[str, Any]],
        source_documents: list[dict[str, Any]] | None = None,
        retrieved_memories: list[dict[str, Any]] | None = None,
        missing_evidence: list[str] | None = None,
        database_source: str = "FalkorDB",
    ) -> dict[str, Any]:
        """Record an auditable conclusion with full provenance."""
        ledger_id = f"ledger_{int(time.time() * 1000) % 100000000}"

        total_claims = len(verified_facts) + len(assumptions)
        if total_claims == 0:
            groundedness = 0
            status = "UNVERIFIED"
        else:
            groundedness = int((len(verified_facts) / total_claims) * 100)
            if groundedness == 100 and not missing_evidence:
                status = "VERIFIED"
            elif groundedness >= 50:
                status = "PARTIALLY_GROUNDED"
            else:
                status = "UNVERIFIED"

        entry = {
            "id": ledger_id,
            "query": query,
            "conclusion": conclusion,
            "verified_facts": verified_facts,
            "assumptions": assumptions,
            "missing_evidence": missing_evidence or [],
            "supporting_entities": supporting_entities,
            "traversed_edges": traversed_edges,
            "source_documents": source_documents or [],
            "retrieved_memories": retrieved_memories or [],
            "verification_status": status,
            "groundedness_percentage": groundedness,
            "database_source": database_source,
            "timestamp": int(time.time()),
            "created_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
        }

        self._ledger.appendleft(entry)
        return entry

    def list_entries(self, limit: int = 25) -> list[dict[str, Any]]:
        return list(self._ledger)[:limit]

    def get_entry(self, entry_id: str) -> dict[str, Any] | None:
        for item in self._ledger:
            if item["id"] == entry_id:
                return copy.deepcopy(item)
        return None

    def verify_claim(self, claim: str) -> dict[str, Any]:
        """Verify whether an arbitrary natural-language claim is substantiated by the knowledge graph."""
        clean = claim.strip()
        data = self.store.graph_data()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        tokens = [w.lower() for w in clean.replace(",", "").replace(".", "").split() if len(w) > 2]
        matched_nodes = [
            n for n in nodes
            if any(tok in n["label"].lower() or tok in n.get("detail", "").lower() for tok in tokens)
        ]

        if not matched_nodes:
            return {
                "claim": clean,
                "verified": False,
                "evidence_found": False,
                "reason": "No entities matching the claim found in active knowledge graph.",
                "supporting_nodes": [],
            }

        matched_ids = {n["id"] for n in matched_nodes}
        substantiating_edges = [
            e for e in edges
            if e["source"] in matched_ids and e["target"] in matched_ids
        ]

        verified = len(substantiating_edges) > 0 or len(matched_nodes) >= 2
        return {
            "claim": clean,
            "verified": verified,
            "evidence_found": True,
            "confidence": "HIGH" if len(substantiating_edges) > 0 else "MODERATE",
            "supporting_nodes": matched_nodes[:4],
            "supporting_edges": substantiating_edges[:4],
            "audit_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
