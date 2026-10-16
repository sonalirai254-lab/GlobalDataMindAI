"""Counterfactual Scenario Studio: Isolated workspace for simulating hypothetical decisions,
comparing alternatives side-by-side, and providing safe authorization for production changes.
"""
from __future__ import annotations

import time
import copy
from typing import Any
from .ripple import RippleEngine


PRESET_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "scenario_payments_outage",
        "name": "Payments API 48-Hour Unavailability",
        "description": "Evaluate cascade impact if third-party banking integration fails for 48 hours.",
        "target_entity_id": "service_payments",
        "target_label": "Payments API",
        "change_type": "DOWNTIME",
        "detail": "Payments API service unavailable for 48 hours due to upstream banking maintenance",
        "parameters": {"duration_hours": 48},
        "created_at": "Oct 15, 2026",
        "applied": False,
    },
    {
        "id": "scenario_atlas_delay",
        "name": "Project Atlas 4-Week Timeline Delay",
        "description": "Evaluate milestone shift of flagship enterprise release from Oct 28 to Nov 25.",
        "target_entity_id": "project_atlas",
        "target_label": "Project Atlas",
        "change_type": "DELAY",
        "detail": "Postpone Project Atlas launch by 4 weeks to accommodate extended compliance hardening",
        "parameters": {"weeks": 4, "new_date": "2026-11-25"},
        "created_at": "Oct 15, 2026",
        "applied": False,
    },
    {
        "id": "scenario_auth_reassign",
        "name": "Reassign Zero-Trust Auth to Platform Team",
        "description": "Shift primary ownership of Zero-Trust Auth token bridge from Security to Platform Engineering.",
        "target_entity_id": "project_zerotrust",
        "target_label": "Zero-Trust Auth",
        "change_type": "REASSIGN_OWNER",
        "detail": "Transfer project ownership to Platform Infra team for operational integration",
        "parameters": {"new_owner": "team_eng"},
        "created_at": "Oct 15, 2026",
        "applied": False,
    },
]


class ScenarioStudioManager:
    """Manages hypothetical scenarios and sandbox comparisons."""

    def __init__(self, store: Any, why_memory: Any, trust_ledger: Any) -> None:
        self.store = store
        self.why_memory = why_memory
        self.trust_ledger = trust_ledger
        self.ripple = RippleEngine(store)
        self._scenarios: list[dict[str, Any]] = copy.deepcopy(PRESET_SCENARIOS)

    def list_scenarios(self) -> list[dict[str, Any]]:
        results = []
        for s in self._scenarios:
            sim = self.ripple.analyze_ripple(
                target_entity_id=s["target_entity_id"],
                change_type=s["change_type"],
                detail=s["detail"],
                params=s.get("parameters"),
            )
            item = copy.deepcopy(s)
            item["risk_level"] = sim.get("risk_level", "MODERATE")
            item["affected_count"] = len(sim.get("direct_impacts", [])) + len(sim.get("cascade_impacts", []))
            item["simulation_summary"] = sim.get("summary", "")
            results.append(item)
        return results

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        for s in self._scenarios:
            if s["id"] == scenario_id:
                sim = self.ripple.analyze_ripple(
                    target_entity_id=s["target_entity_id"],
                    change_type=s["change_type"],
                    detail=s["detail"],
                    params=s.get("parameters"),
                )
                res = copy.deepcopy(s)
                res["simulation"] = sim
                return res
        return None

    def create_scenario(
        self,
        name: str,
        target_entity_id: str,
        change_type: str = "DELAY",
        detail: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        slug = name.lower().replace(" ", "_").replace("-", "_")
        clean_slug = "".join(ch for ch in slug if ch.isalnum() or ch == "_")[:32]
        s_id = f"scenario_{clean_slug}_{int(time.time()) % 10000}"

        target_node = self.store.get_entity_by_id(target_entity_id) if hasattr(self.store, "get_entity_by_id") else None
        target_label = target_node["label"] if target_node else target_entity_id

        record = {
            "id": s_id,
            "name": name.strip(),
            "description": detail.strip() or f"Hypothetical {change_type} scenario on {target_label}.",
            "target_entity_id": target_entity_id,
            "target_label": target_label,
            "change_type": change_type,
            "detail": detail.strip() or f"Simulation of {change_type} on {target_label}",
            "parameters": parameters or {},
            "created_at": time.strftime("%b %d, %Y", time.gmtime()),
            "applied": False,
        }

        self._scenarios.insert(0, record)
        sim = self.ripple.analyze_ripple(target_entity_id, change_type, record["detail"], parameters)
        res = copy.deepcopy(record)
        res["simulation"] = sim
        return res

    def compare_scenarios(self, scenario_ids: list[str]) -> dict[str, Any]:
        """Compare multiple scenarios side-by-side with graph blast radius and trade-offs."""
        selected = [s for s in self._scenarios if s["id"] in scenario_ids]
        if not selected:
            selected = self._scenarios[:2]

        comparisons = []
        for s in selected:
            sim = self.ripple.analyze_ripple(
                target_entity_id=s["target_entity_id"],
                change_type=s["change_type"],
                detail=s["detail"],
                params=s.get("parameters"),
            )
            comparisons.append({
                "scenario_id": s["id"],
                "name": s["name"],
                "target_entity": s["target_label"],
                "change_type": s["change_type"],
                "risk_level": sim.get("risk_level", "MODERATE"),
                "direct_impact_count": len(sim.get("direct_impacts", [])),
                "cascade_impact_count": len(sim.get("cascade_impacts", [])),
                "total_impacted": len(sim.get("direct_impacts", [])) + len(sim.get("cascade_impacts", [])),
                "direct_impacts": sim.get("direct_impacts", []),
                "cascade_impacts": sim.get("cascade_impacts", []),
                "trade_offs": sim.get("trade_offs", []),
                "missing_information": sim.get("missing_information", []),
                "action_plan": sim.get("action_plan", []),
                "summary": sim.get("summary", ""),
                "applied": s.get("applied", False),
            })

        return {
            "compared_count": len(comparisons),
            "scenarios": comparisons,
            "comparison_notes": (
                "Scenarios are evaluated in an isolated simulation sandbox. "
                "No live graph entities or edges have been altered."
            ),
        }

    def apply_scenario(self, scenario_id: str, confirm: bool = False, authorized_by: str = "Admin") -> dict[str, Any]:
        """Apply a simulated scenario to the production graph with explicit authorization."""
        if not confirm:
            return {
                "status": "rejected",
                "message": "Scenario cannot be applied without explicit confirmation parameter 'confirm=True'.",
            }

        target_scenario = next((s for s in self._scenarios if s["id"] == scenario_id), None)
        if not target_scenario:
            return {"status": "error", "message": f"Scenario '{scenario_id}' not found."}

        target_id = target_scenario["target_entity_id"]
        change_type = target_scenario["change_type"]
        detail = target_scenario["detail"]

        # 1. Mutate live graph entity record
        nodes = self.store.graph_data()["nodes"]
        target_node = next((n for n in nodes if n["id"] == target_id), None)
        if target_node:
            new_detail = f"{target_node.get('detail', '')} [Applied Scenario: {target_scenario['name']} - {detail}]"
            self.store.add_entity(name=target_node["label"], kind=target_node["kind"], detail=new_detail)

        # 2. Record in Why-Memory as an executed organizational decision
        decision_record = self.why_memory.add_decision(
            title=f"Authorized Scenario: {target_scenario['name']}",
            rationale=f"Scenario applied to production by {authorized_by}. {detail}",
            evidence=f"Pre-change blast radius simulated in Counterfactual Scenario Studio",
            outcome=f"Production graph updated with {change_type} on {target_scenario['target_label']}.",
            associated_entities=[target_id],
            status="executed",
            verified=True,
        )

        # 3. Log into Trust Ledger
        self.trust_ledger.record_conclusion(
            query=f"Apply scenario: {target_scenario['name']}",
            conclusion=f"Scenario successfully executed on production graph by {authorized_by}.",
            verified_facts=[
                f"Target entity '{target_scenario['target_label']}' updated in active graph.",
                f"Decision recorded into Why-Memory under ID '{decision_record['id']}'.",
            ],
            assumptions=["Post-change monitoring and stakeholder notifications will be completed per action plan."],
            supporting_entities=[{"id": target_id, "label": target_scenario["target_label"], "kind": "Target"}],
            traversed_edges=[],
            database_source="FalkorDB Production Graph",
        )

        target_scenario["applied"] = True

        return {
            "status": "success",
            "message": f"Successfully applied scenario '{target_scenario['name']}' to production graph.",
            "decision_id": decision_record["id"],
            "target_entity": target_scenario["target_label"],
            "authorized_by": authorized_by,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
