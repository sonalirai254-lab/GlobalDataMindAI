"""Knowledge Quality Checks: Detects duplicates, orphans, missing relationships, and provides actionable resolutions."""
from __future__ import annotations

import difflib
from typing import Any


class QualityAuditor:
    def __init__(self, store: Any) -> None:
        self.store = store

    def audit(self) -> dict[str, Any]:
        graph_data = self.store.graph_data()
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        issues: list[dict[str, Any]] = []

        # 1. Detect Duplicates by Fuzzy Name Similarity
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                n1, n2 = nodes[i], nodes[j]
                if n1["kind"] == n2["kind"]:
                    ratio = difflib.SequenceMatcher(None, n1["label"].lower(), n2["label"].lower()).ratio()
                    if ratio >= 0.85:
                        issues.append({
                            "id": f"dup_{n1['id']}_{n2['id']}",
                            "category": "DUPLICATE_ENTITY",
                            "severity": "Warning",
                            "title": f"Possible duplicate {n1['kind']}s detected",
                            "description": f"'{n1['label']}' and '{n2['label']}' have a name similarity ratio of {round(ratio * 100)}%.",
                            "entities": [n1, n2],
                            "action": {
                                "type": "MERGE_ENTITIES",
                                "label": f"Merge into '{n1['label']}'",
                                "surviving_id": n1["id"],
                                "duplicate_id": n2["id"],
                            },
                        })

        # 2. Detect Orphan Entities (0 in and 0 out edges)
        connected_ids = {e["source"] for e in edges} | {e["target"] for e in edges}
        for n in nodes:
            if n["id"] not in connected_ids:
                issues.append({
                    "id": f"orphan_{n['id']}",
                    "category": "ORPHAN_ENTITY",
                    "severity": "Warning",
                    "title": f"Isolated entity without connections: '{n['label']}'",
                    "description": f"This {n['kind']} has no relationships connecting it to the company brain.",
                    "entities": [n],
                    "action": {
                        "type": "CONNECT_ORPHAN",
                        "label": f"Connect '{n['label']}' to another entity",
                        "source_id": n["id"],
                    },
                })

        # 3. Detect Missing Governance: Projects with no Owner Team
        projects = [n for n in nodes if n["kind"] == "Project"]
        owned_projects = {e["target"] for e in edges if e["label"] == "OWNS"}
        for p in projects:
            if p["id"] not in owned_projects:
                issues.append({
                    "id": f"unowned_proj_{p['id']}",
                    "category": "MISSING_OWNERSHIP",
                    "severity": "Notice",
                    "title": f"Project '{p['label']}' has no assigned owner team",
                    "description": "Every active project should have an owning Team in the knowledge graph.",
                    "entities": [p],
                    "action": {
                        "type": "ASSIGN_OWNER",
                        "label": f"Assign team to '{p['label']}'",
                        "project_id": p["id"],
                    },
                })

        # 4. Detect Teams with no Lead Person
        teams = [n for n in nodes if n["kind"] == "Team"]
        led_teams = {e["target"] for e in edges if e["label"] == "LEADS"}
        for t in teams:
            if t["id"] not in led_teams:
                issues.append({
                    "id": f"unled_team_{t['id']}",
                    "category": "MISSING_LEAD",
                    "severity": "Notice",
                    "title": f"Team '{t['label']}' has no designated lead person",
                    "description": "Assign a Person with LEADS relationship to represent team accountability.",
                    "entities": [t],
                    "action": {
                        "type": "ASSIGN_LEAD",
                        "label": f"Assign leader to '{t['label']}'",
                        "team_id": t["id"],
                    },
                })

        # 5. Detect Stale / Sparse Entity Records (< 10 chars detail)
        for n in nodes:
            detail = n.get("detail", "").strip()
            if len(detail) < 10:
                issues.append({
                    "id": f"sparse_{n['id']}",
                    "category": "SPARSE_RECORD",
                    "severity": "Notice",
                    "title": f"Incomplete context for '{n['label']}'",
                    "description": "Entity description is sparse. Adding architecture, purpose, or role context improves AI reasoning.",
                    "entities": [n],
                    "action": {
                        "type": "ENRICH_DETAIL",
                        "label": f"Enrich '{n['label']}' description",
                        "entity_id": n["id"],
                    },
                })

        # Calculate Overall Health Score
        total_checks = max(1, len(nodes) * 2 + len(projects))
        health_score = max(20, min(100, int(100 - (len(issues) * 7))))

        return {
            "health_score": health_score,
            "total_issues": len(issues),
            "summary": f"Audit evaluated {len(nodes)} entities and {len(edges)} relationships. Found {len(issues)} items for attention.",
            "issues": issues,
            "metrics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "orphan_count": sum(1 for i in issues if i["category"] == "ORPHAN_ENTITY"),
                "missing_links": sum(1 for i in issues if i["category"] in ("MISSING_OWNERSHIP", "MISSING_LEAD")),
                "duplicate_count": sum(1 for i in issues if i["category"] == "DUPLICATE_ENTITY"),
            },
        }

    def resolve(self, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute actionable resolution workflow."""
        if action_type == "MERGE_ENTITIES":
            surviving_id = payload.get("surviving_id")
            duplicate_id = payload.get("duplicate_id")
            if not surviving_id or not duplicate_id:
                return {"status": "error", "message": "Missing surviving_id or duplicate_id."}

            graph_data = self.store.graph_data()
            edges = graph_data.get("edges", [])

            # Re-route edges from duplicate to surviving
            for e in edges:
                if e["source"] == duplicate_id and e["target"] != surviving_id:
                    self.store.add_edge(surviving_id, e["target"], e["label"])
                elif e["target"] == duplicate_id and e["source"] != surviving_id:
                    self.store.add_edge(e["source"], surviving_id, e["label"])

            # Delete duplicate node
            self.store.delete_node(duplicate_id)
            return {"status": "success", "message": f"Merged duplicate entity into '{surviving_id}'."}

        elif action_type == "CONNECT_ORPHAN":
            source_id = payload.get("source_id")
            target_id = payload.get("target_id")
            rel = payload.get("relationship", "RELATED_TO")
            if not source_id or not target_id:
                return {"status": "error", "message": "Missing source_id or target_id."}
            edge = self.store.add_edge(source_id, target_id, rel)
            return {"status": "success", "message": f"Connected orphan: {source_id} —[{rel}]→ {target_id}", "edge": edge}

        elif action_type == "ASSIGN_OWNER":
            project_id = payload.get("project_id")
            team_id = payload.get("team_id")
            if not project_id or not team_id:
                return {"status": "error", "message": "Missing project_id or team_id."}
            edge = self.store.add_edge(team_id, project_id, "OWNS")
            return {"status": "success", "message": "Owner relationship created.", "edge": edge}

        elif action_type == "ASSIGN_LEAD":
            team_id = payload.get("team_id")
            person_id = payload.get("person_id")
            if not team_id or not person_id:
                return {"status": "error", "message": "Missing team_id or person_id."}
            edge = self.store.add_edge(person_id, team_id, "LEADS")
            return {"status": "success", "message": "Lead relationship created.", "edge": edge}

        elif action_type == "ENRICH_DETAIL":
            entity_id = payload.get("entity_id")
            detail = payload.get("detail", "").strip()
            nodes = self.store.graph_data()["nodes"]
            target = next((n for n in nodes if n["id"] == entity_id), None)
            if not target:
                return {"status": "error", "message": "Entity not found."}
            self.store.add_entity(name=target["label"], kind=target["kind"], detail=detail)
            return {"status": "success", "message": f"Enriched detail for '{target['label']}'."}

        return {"status": "error", "message": f"Unknown resolution action '{action_type}'."}
