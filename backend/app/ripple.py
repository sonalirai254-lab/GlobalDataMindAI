"""Ripple Intelligence Engine: Dependency-impact traversal, confirmed vs inferred connection analysis,
risk severity scoring, and actionable mitigation generation using FalkorDB graph topology.
"""
from __future__ import annotations

import time
from typing import Any
from collections import deque


class RippleEngine:
    """Calculates graph-reachable blast radius, dependency cascades, and risk trade-offs."""

    def __init__(self, store: Any) -> None:
        self.store = store

    def analyze_ripple(
        self,
        target_entity_id: str,
        change_type: str = "DOWNTIME",
        detail: str = "48-hour service outage",
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform bounded multi-hop dependency traversal around the target entity."""
        graph = self.store.graph_data()
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        by_id = {n["id"]: n for n in nodes}

        # Resolve target entity if passed by name or slug
        target = by_id.get(target_entity_id)
        if not target:
            target = next((n for n in nodes if n["label"].lower() == target_entity_id.lower()), None)

        if not target:
            return {
                "error": f"Target entity '{target_entity_id}' not found in knowledge graph.",
                "target_entity": None,
                "direct_impacts": [],
                "cascade_impacts": [],
                "risk_level": "UNKNOWN",
                "is_hypothetical": True,
            }

        # Build bidirectional dependency mappings:
        # Downstream: When target fails or changes, what is impacted downstream?
        # - A depends on B (A -[:DEPENDS_ON]-> B): If B changes, A is impacted downstream.
        # - B powers A (B -[:POWERS]-> A): If B changes, A is impacted downstream.
        # - Team owns Project (Team -[:OWNS]-> Project): If Project changes, Team is impacted.
        # - Person leads Team (Person -[:LEADS]-> Team): If Team changes, Person is impacted.
        from collections import defaultdict
        downstream_adj: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)
        upstream_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for n in nodes:
            downstream_adj[n["id"]] = []
            upstream_adj[n["id"]] = []

        for e in edges:
            src = e["source"]
            tgt = e["target"]
            lbl = e["label"]

            if lbl == "DEPENDS_ON":
                # tgt changes -> src impacted
                downstream_adj[tgt].append((src, lbl, True))
                upstream_adj[src].append((tgt, lbl))
            elif lbl == "POWERS":
                # src changes -> tgt impacted
                downstream_adj[src].append((tgt, lbl, True))
                upstream_adj[tgt].append((src, lbl))
            elif lbl in ("OWNS", "BUILDS"):
                # tgt changes -> src (owner) impacted
                downstream_adj[tgt].append((src, lbl, True))
            elif lbl == "DOCUMENTED_IN":
                # src changes -> doc needs updating
                downstream_adj[src].append((tgt, lbl, False))
            elif lbl in ("ENABLES", "EXPLAINS"):
                downstream_adj[src].append((tgt, lbl, True))
            elif lbl == "COLLABORATES_WITH":
                downstream_adj[src].append((tgt, lbl, False))
                downstream_adj[tgt].append((src, lbl, False))

        # BFS for downstream cascade up to depth 3
        visited = {target["id"]}
        # queue item: (node_id, depth, path_elements, is_confirmed)
        queue = deque([(target["id"], 0, [target["label"]], True)])

        direct_impacts: list[dict[str, Any]] = []
        cascade_impacts: list[dict[str, Any]] = []
        all_paths: list[dict[str, Any]] = []

        while queue:
            curr_id, depth, path, path_confirmed = queue.popleft()
            if depth >= 3:
                continue

            for next_id, rel, rel_confirmed in downstream_adj.get(curr_id, []):
                next_node = by_id.get(next_id)
                if not next_node:
                    continue

                full_path = path + [f"-[{rel}]->", next_node["label"]]
                confirmed_status = path_confirmed and rel_confirmed

                entry = {
                    "id": next_node["id"],
                    "label": next_node["label"],
                    "kind": next_node["kind"],
                    "detail": next_node.get("detail", ""),
                    "depth": depth + 1,
                    "relationship": rel,
                    "is_confirmed_dependency": confirmed_status,
                    "connection_type": "Confirmed Dependency" if confirmed_status else "Inferred / Governance Connection",
                    "path_string": " ".join(full_path),
                }

                all_paths.append({
                    "entity": next_node["label"],
                    "kind": next_node["kind"],
                    "depth": depth + 1,
                    "relationship": rel,
                    "confirmed": confirmed_status,
                    "trace": " ".join(full_path),
                })

                if next_id not in visited:
                    visited.add(next_id)
                    if depth == 0:
                        direct_impacts.append(entry)
                    else:
                        cascade_impacts.append(entry)
                    queue.append((next_id, depth + 1, full_path, confirmed_status))

        # Check for flagship or critical downstream nodes
        flagship_impacted = any(
            i["kind"] == "Project" and ("atlas" in i["label"].lower() or "search" in i["label"].lower())
            for i in direct_impacts + cascade_impacts
        )
        services_impacted = sum(1 for i in direct_impacts + cascade_impacts if i["kind"] == "Service")
        total_affected = len(direct_impacts) + len(cascade_impacts)

        # Risk scoring
        if flagship_impacted or services_impacted >= 2 or total_affected >= 5:
            risk_level = "CRITICAL"
        elif total_affected >= 3 or services_impacted == 1:
            risk_level = "HIGH"
        elif total_affected >= 1:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Trade-offs & Missing Information
        trade_offs = []
        missing_info = []

        governing_owners = [
            i["label"] for i in direct_impacts + cascade_impacts
            if i["kind"] in ("Team", "Person")
        ]

        if change_type == "DOWNTIME":
            trade_offs.append("Temporarily degrade non-critical background jobs to preserve core API responsiveness.")
            trade_offs.append("Queue write transactions into asynchronous message buffer until recovery.")
            if not any(i["kind"] == "Document" for i in direct_impacts):
                missing_info.append("No active disaster recovery runbook or SLA document linked to this service in graph.")
        elif change_type == "DELAY":
            trade_offs.append("Delaying delivery reduces integration bug risk but postpones customer rollout milestones.")
            trade_offs.append("May block dependent engineering sprints across collaborating teams.")
            if not governing_owners:
                missing_info.append("No designated team lead found in graph to officially authorize milestone shift.")
        elif change_type == "REASSIGN_OWNER":
            trade_offs.append("Reassignment requires knowledge transfer period, potentially slowing sprint velocity.")
        else:
            trade_offs.append("Requires architectural verification of interface contract compatibility.")

        # Actionable Proposed Action Plan
        action_plan = []
        lead_stakeholder = governing_owners[0] if governing_owners else "Engineering Lead"

        action_plan.append({
            "step": 1,
            "title": "Immediate Stakeholder Notification",
            "owner": lead_stakeholder,
            "action": f"Notify owners of affected systems: {', '.join(i['label'] for i in direct_impacts[:3]) or target['label']}.",
            "timeline": "Immediate (T + 1h)",
        })

        if change_type == "DOWNTIME":
            action_plan.append({
                "step": 2,
                "title": "Activate Circuit Breaker & Fallback Mock",
                "owner": "Platform Infra Team",
                "action": f"Route upstream requests around '{target['label']}' to circuit-broken cache or mock adapter.",
                "timeline": "T + 2h",
            })
        else:
            action_plan.append({
                "step": 2,
                "title": "Milestone & Dependency Alignment",
                "owner": lead_stakeholder,
                "action": f"Re-baseline release schedule for {', '.join(i['label'] for i in direct_impacts if i['kind'] == 'Project') or 'dependent deliverables'}.",
                "timeline": "T + 24h",
            })

        action_plan.append({
            "step": 3,
            "title": "Verification & Post-Change Validation",
            "owner": "Security & Architecture",
            "action": "Audit dependent token scopes and verify zero regression in integration testing.",
            "timeline": "Post-Resolution",
        })

        summary = (
            f"Ripple Intelligence: Hypothetical {change_type.lower()} on '{target['label']}' ({target['kind']}) "
            f"directly affects {len(direct_impacts)} entities and cascades to {len(cascade_impacts)} downstream nodes. "
            f"Blast radius spans {len(all_paths)} total relationship paths. Evaluated Risk: {risk_level}."
        )

        return {
            "target_entity": target,
            "change_type": change_type,
            "detail": detail,
            "risk_level": risk_level,
            "summary": summary,
            "direct_impacts": direct_impacts,
            "cascade_impacts": cascade_impacts,
            "all_paths": all_paths[:12],
            "confirmed_count": sum(1 for p in all_paths if p["confirmed"]),
            "inferred_count": sum(1 for p in all_paths if not p["confirmed"]),
            "trade_offs": trade_offs,
            "missing_information": missing_info,
            "action_plan": action_plan,
            "is_hypothetical": True,
            "production_graph_mutated": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }
