"""What-If Impact Simulator: Traverses graph dependencies for hypothetical changes without mutating graph data."""
from __future__ import annotations

from typing import Any
from collections import deque


class ImpactSimulator:
    def __init__(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
        self.nodes = nodes
        self.edges = edges
        self.by_id = {n["id"]: n for n in nodes}

    def simulate(
        self,
        target_node_id: str,
        scenario: str = "DELAY",
        detail: str = "4-week timeline delay",
    ) -> dict[str, Any]:
        target = self.by_id.get(target_node_id)
        if not target:
            return {
                "error": f"Target entity '{target_node_id}' not found in knowledge graph.",
                "affected_entities": [],
                "impact_paths": [],
            }

        # Build incoming dependency graph: child depends on parent
        # If A depends on B: edge is A -[:DEPENDS_ON]-> B, so B's delay impacts A!
        # Also if B powers A: B -[:POWERS]-> A, so B's delay impacts A!
        dependents_map: dict[str, list[tuple[str, str]]] = {n["id"]: [] for n in self.nodes}
        for e in self.edges:
            # If source depends on target: target changes -> source affected
            if e["label"] == "DEPENDS_ON":
                dependents_map[e["target"]].append((e["source"], "DEPENDS_ON"))
            # If source powers target: source changes -> target affected
            elif e["label"] == "POWERS":
                dependents_map[e["source"]].append((e["target"], "POWERS"))
            # If team owns project: project changes -> team affected
            elif e["label"] == "OWNS":
                dependents_map[e["target"]].append((e["source"], "OWNS"))
            # If document documents project: project changes -> document affected
            elif e["label"] == "DOCUMENTED_IN":
                dependents_map[e["source"]].append((e["target"], "DOCUMENTED_IN"))

        # BFS to find direct and cascade impacts with provenance paths
        visited = {target_node_id}
        queue = deque([(target_node_id, 0, [target["label"]])])

        direct_impacts: list[dict[str, Any]] = []
        cascade_impacts: list[dict[str, Any]] = []
        impact_paths: list[dict[str, Any]] = []

        while queue:
            curr_id, depth, path = queue.popleft()
            if depth >= 3:
                continue

            for next_id, rel in dependents_map.get(curr_id, []):
                next_node = self.by_id.get(next_id)
                if not next_node:
                    continue

                full_path = path + [f"-[{rel}]->", next_node["label"]]
                impact_entry = {
                    "id": next_node["id"],
                    "label": next_node["label"],
                    "kind": next_node["kind"],
                    "detail": next_node.get("detail", ""),
                    "depth": depth + 1,
                    "relation": rel,
                    "path_string": " ".join(full_path),
                }

                if next_id not in visited:
                    visited.add(next_id)
                    if depth == 0:
                        direct_impacts.append(impact_entry)
                    else:
                        cascade_impacts.append(impact_entry)
                    queue.append((next_id, depth + 1, full_path))

                impact_paths.append({
                    "target_entity": next_node["label"],
                    "relationship": rel,
                    "depth": depth + 1,
                    "trace": " ".join(full_path),
                })

        # Calculate Risk Score
        total_affected = len(direct_impacts) + len(cascade_impacts)
        has_flagship_project = any(
            i["kind"] == "Project" and "atlas" in i["label"].lower()
            for i in direct_impacts + cascade_impacts
        )
        if has_flagship_project or total_affected >= 4:
            risk_level = "CRITICAL"
        elif total_affected >= 2:
            risk_level = "HIGH"
        elif total_affected == 1:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Formulate actionable mitigation advice
        mitigations = []
        if scenario == "DELAY":
            mitigations.append(f"Notify governing teams of {target['label']} regarding the {detail}.")
            if direct_impacts:
                mitigations.append(f"Renegotiate delivery milestones for direct dependents: {', '.join(d['label'] for d in direct_impacts[:3])}.")
            if cascade_impacts:
                mitigations.append(f"Audit downstream cascade releases: {', '.join(c['label'] for c in cascade_impacts[:2])}.")
        elif scenario == "DEPRECATION":
            mitigations.append(f"Establish migration bridges for entities currently depending on {target['label']}.")
        else:
            mitigations.append(f"Activate fallback procedures and verify incident response with system architecture leads.")

        return {
            "scenario": scenario,
            "target_node": target,
            "detail": detail,
            "risk_level": risk_level,
            "summary": (
                f"Hypothetical {scenario.lower()} on '{target['label']}' ({target['kind']}) "
                f"directly impacts {len(direct_impacts)} entities and cascades to {len(cascade_impacts)} downstream systems. "
                f"Risk rating: {risk_level}."
            ),
            "direct_impacts": direct_impacts,
            "cascade_impacts": cascade_impacts,
            "impact_paths": impact_paths[:8],
            "mitigations": mitigations,
            "is_hypothetical": True,
            "graph_mutated": False,
        }
