"""Graphwise Nexus — Temporal Graph Engine (Historical Intelligence).
Supports bitemporal queries, point-in-time graph state reconstruction,
graph diff comparisons across time horizons, and entity lifecycle histories.

Bitemporal Semantics:
- Valid-Time: The real-world timeframe during which a fact was true (valid_from <= T < valid_to).
- Recorded-Time: The system transaction timestamp when Graphwise Nexus ingested or recorded the fact.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone, timedelta
from typing import Any

try:
    from .temporal_universal import (
        UniversalTimestampParser,
        StructuredRecordTemporalParser,
        TemporalDataAnalyzer,
        TemporalRecord,
        UniversalTimestamp,
        TimestampPrecision,
        TemporalValidationStatus,
    )
except (ImportError, ValueError):
    from app.temporal_universal import (
        UniversalTimestampParser,
        StructuredRecordTemporalParser,
        TemporalDataAnalyzer,
        TemporalRecord,
        UniversalTimestamp,
        TimestampPrecision,
        TemporalValidationStatus,
    )


TIME_OFFSETS = {
    "now": 0,
    "current": 0,
    "today": 0,
    "yesterday": 1,
    "1_day_ago": 1,
    "1_week_ago": 7,
    "7_days_ago": 7,
    "2_weeks_ago": 14,
    "14_days_ago": 14,
    "1_month_ago": 30,
    "30_days_ago": 30,
    "2_months_ago": 60,
    "60_days_ago": 60,
}

# Reference baseline timestamp for simulation consistency (2026-10-15T00:00:00Z)
BASELINE_TIME = datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)


def parse_temporal_target(target: str | None) -> datetime:
    """Parse relative offset keywords or ISO timestamp strings into a timezone-aware datetime."""
    if not target or target.strip().lower() in ("now", "current", "today", ""):
        return BASELINE_TIME

    clean_target = target.strip().lower()
    if clean_target in TIME_OFFSETS:
        days = TIME_OFFSETS[clean_target]
        return BASELINE_TIME - timedelta(days=days)

    # Attempt ISO parsing
    try:
        # Replace trailing 'Z' if needed
        iso_str = target.strip()
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Fallback to baseline
        return BASELINE_TIME


def format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TemporalGraphEngine:
    """Reconstructs historical graph states and computes topological diffs across bitemporal points."""

    def __init__(self, store: Any) -> None:
        self.store = store

    def get_timeline_checkpoints(self) -> list[dict[str, Any]]:
        """Return standardized temporal checkpoints available for timeline exploration."""
        return [
            {
                "id": "1_month_ago",
                "label": "1 Month Ago",
                "offset_days": 30,
                "timestamp": format_iso(BASELINE_TIME - timedelta(days=30)),
                "description": "Pre-security audit baseline: Project Atlas in planning, task ownership under Engineering.",
            },
            {
                "id": "2_weeks_ago",
                "label": "2 Weeks Ago",
                "offset_days": 14,
                "timestamp": format_iso(BASELINE_TIME - timedelta(days=14)),
                "description": "Post-audit review: SOC2 task reassigned to Marcus Vance, deployment delay initiated.",
            },
            {
                "id": "1_week_ago",
                "label": "1 Week Ago",
                "offset_days": 7,
                "timestamp": format_iso(BASELINE_TIME - timedelta(days=7)),
                "description": "Zero-Trust Auth token bridge integration and Payments API circuit breaker decoupling.",
            },
            {
                "id": "yesterday",
                "label": "Yesterday",
                "offset_days": 1,
                "timestamp": format_iso(BASELINE_TIME - timedelta(days=1)),
                "description": "Final readiness evaluation prior to real-time event ingestion.",
            },
            {
                "id": "now",
                "label": "Current (Live)",
                "offset_days": 0,
                "timestamp": format_iso(BASELINE_TIME),
                "description": "Active graph state with all real-time events, approved decisions, and live dependencies.",
            },
        ]

    def reconstruct_snapshot(self, target_time: str | datetime) -> dict[str, Any]:
        """Reconstruct the graph topology as it existed at target_time based on valid-time intervals.
        Evaluates node presence, historical properties (e.g. status, owner), and edge validity.
        """
        if isinstance(target_time, str):
            dt = parse_temporal_target(target_time)
            query_time_str = target_time
        else:
            dt = target_time
            query_time_str = format_iso(dt)

        target_iso = format_iso(dt)
        all_nodes = self.store.get_all_nodes_with_history()
        all_edges = self.store.get_all_edges_with_history()

        reconstructed_nodes = []
        for n in all_nodes:
            # Check valid_time boundaries for node
            n_valid_from = n.get("valid_from", "2026-01-01T00:00:00Z")
            n_valid_to = n.get("valid_to")

            if n_valid_from <= target_iso and (n_valid_to is None or n_valid_to > target_iso):
                node_copy = copy.deepcopy(n)

                # Reconstruct status at target time
                status_history = node_copy.get("status_history", [])
                if status_history:
                    # Find status that was active at target_time
                    active_status = None
                    for sh in status_history:
                        if sh.get("changed_at", "") <= target_iso:
                            active_status = sh
                    if active_status:
                        node_copy["status"] = active_status.get("status", node_copy.get("status"))

                # Reconstruct owner at target time
                owner_history = node_copy.get("owner_history", [])
                if owner_history:
                    active_owner = None
                    for oh in owner_history:
                        if oh.get("assigned_at", "") <= target_iso:
                            active_owner = oh
                    if active_owner:
                        node_copy["current_owner_id"] = active_owner.get("owner")
                        node_copy["current_owner_name"] = active_owner.get("owner_name")

                reconstructed_nodes.append(node_copy)

        reconstructed_node_ids = {n["id"] for n in reconstructed_nodes}

        reconstructed_edges = []
        for e in all_edges:
            e_valid_from = e.get("valid_from", "2026-01-01T00:00:00Z")
            e_valid_to = e.get("valid_to")

            if e_valid_from <= target_iso and (e_valid_to is None or e_valid_to > target_iso):
                # Ensure both endpoints existed at this point in time
                if e["source"] in reconstructed_node_ids and e["target"] in reconstructed_node_ids:
                    reconstructed_edges.append(copy.deepcopy(e))

        return {
            "snapshot_time": target_iso,
            "query_target": query_time_str,
            "temporal_dimension": "valid_time",
            "nodes": reconstructed_nodes,
            "edges": reconstructed_edges,
            "stats": {
                "node_count": len(reconstructed_nodes),
                "edge_count": len(reconstructed_edges),
            },
        }

    def compute_diff(self, t1: str, t2: str = "now") -> dict[str, Any]:
        """Compute topological and property differences between snapshot at t1 and snapshot at t2.
        Identifies added nodes, removed nodes, modified entities (status/owner), added edges, and removed edges.
        """
        snap1 = self.reconstruct_snapshot(t1)
        snap2 = self.reconstruct_snapshot(t2)

        nodes1_by_id = {n["id"]: n for n in snap1["nodes"]}
        nodes2_by_id = {n["id"]: n for n in snap2["nodes"]}

        # Added nodes in T2
        added_node_ids = set(nodes2_by_id.keys()) - set(nodes1_by_id.keys())
        added_nodes = [nodes2_by_id[nid] for nid in added_node_ids]

        # Removed / superseded nodes in T2
        removed_node_ids = set(nodes1_by_id.keys()) - set(nodes2_by_id.keys())
        removed_nodes = [nodes1_by_id[nid] for nid in removed_node_ids]

        # Modified nodes
        modified_nodes = []
        common_node_ids = set(nodes1_by_id.keys()) & set(nodes2_by_id.keys())
        for nid in common_node_ids:
            n1 = nodes1_by_id[nid]
            n2 = nodes2_by_id[nid]
            changes = []

            if n1.get("status") != n2.get("status"):
                changes.append({
                    "field": "status",
                    "previous_value": n1.get("status"),
                    "new_value": n2.get("status"),
                })

            if n1.get("current_owner_id") != n2.get("current_owner_id") and n2.get("current_owner_id"):
                changes.append({
                    "field": "owner",
                    "previous_value": n1.get("current_owner_name", n1.get("current_owner_id", "Unassigned")),
                    "new_value": n2.get("current_owner_name", n2.get("current_owner_id")),
                })

            if n1.get("detail") != n2.get("detail"):
                changes.append({
                    "field": "detail",
                    "previous_value": n1.get("detail"),
                    "new_value": n2.get("detail"),
                })

            if changes:
                modified_nodes.append({
                    "id": nid,
                    "label": n2["label"],
                    "kind": n2["kind"],
                    "changes": changes,
                })

        # Edge comparisons
        def edge_key(e: dict[str, Any]) -> tuple[str, str, str]:
            return (e["source"], e["target"], e["label"])

        edges1_set = {edge_key(e): e for e in snap1["edges"]}
        edges2_set = {edge_key(e): e for e in snap2["edges"]}

        added_edges = [edges2_set[k] for k in (set(edges2_set.keys()) - set(edges1_set.keys()))]
        removed_edges = [edges1_set[k] for k in (set(edges1_set.keys()) - set(edges2_set.keys()))]

        # Generate human-readable narrative summary
        narrative_points = []
        if added_nodes:
            narrative_points.append(f"Added {len(added_nodes)} new entity(s): {', '.join(n['label'] for n in added_nodes[:3])}.")
        if removed_nodes:
            narrative_points.append(f"Superseded/retired {len(removed_nodes)} entity(s): {', '.join(n['label'] for n in removed_nodes[:3])}.")
        if modified_nodes:
            mod_summaries = []
            for mn in modified_nodes[:4]:
                for ch in mn["changes"]:
                    mod_summaries.append(f"{mn['label']} {ch['field']} changed from '{ch['previous_value']}' to '{ch['new_value']}'")
            narrative_points.append(f"Detected {len(modified_nodes)} modified entity(s): {'; '.join(mod_summaries)}.")
        if added_edges:
            narrative_points.append(f"Established {len(added_edges)} new relationship(s): {', '.join(e['label'] for e in added_edges[:3])}.")
        if removed_edges:
            narrative_points.append(f"Severed/relinked {len(removed_edges)} previous relationship(s).")

        summary_text = " ".join(narrative_points) if narrative_points else "Graph topology and attributes are identical between these two checkpoints."

        return {
            "t1": snap1["snapshot_time"],
            "t2": snap2["snapshot_time"],
            "t1_label": t1,
            "t2_label": t2,
            "summary": summary_text,
            "diff": {
                "added_nodes": added_nodes,
                "removed_nodes": removed_nodes,
                "modified_nodes": modified_nodes,
                "added_edges": added_edges,
                "removed_edges": removed_edges,
            },
            "counts": {
                "added_nodes_count": len(added_nodes),
                "removed_nodes_count": len(removed_nodes),
                "modified_nodes_count": len(modified_nodes),
                "added_edges_count": len(added_edges),
                "removed_edges_count": len(removed_edges),
            },
        }

    def get_entity_history(self, entity_id: str) -> dict[str, Any]:
        """Return the complete chronological lifecycle, ownership transitions, and status changes for an entity."""
        all_nodes = self.store.get_all_nodes_with_history()
        node = next((n for n in all_nodes if n["id"] == entity_id), None)
        if not node:
            return {"found": False, "entity_id": entity_id, "message": "Entity not found in graph."}

        # Collect chronological timeline events
        events: list[dict[str, Any]] = []

        # 1. Creation event
        events.append({
            "event_type": "CREATED",
            "timestamp": node.get("valid_from", "2026-08-01T00:00:00Z"),
            "recorded_at": node.get("recorded_at", "2026-08-01T00:00:00Z"),
            "description": f"Entity '{node['label']}' ({node['kind']}) instantiated in graph.",
            "actor": "System Baseline / Creation",
        })

        # 2. Status transitions
        for sh in node.get("status_history", []):
            events.append({
                "event_type": "STATUS_CHANGED",
                "timestamp": sh.get("changed_at", ""),
                "recorded_at": sh.get("recorded_at", ""),
                "description": f"Status changed to '{sh.get('status')}'",
                "actor": sh.get("changed_by", "Authorized User"),
                "reason": sh.get("reason", ""),
            })

        # 3. Ownership reassignments
        for oh in node.get("owner_history", []):
            prev = oh.get("previous_owner")
            prev_desc = f" (reassigned from {prev})" if prev else ""
            events.append({
                "event_type": "OWNER_REASSIGNED",
                "timestamp": oh.get("assigned_at", ""),
                "recorded_at": oh.get("recorded_at", ""),
                "description": f"Assigned to {oh.get('owner_name')}{prev_desc}",
                "actor": "Project Management",
                "reason": oh.get("reason", ""),
            })

        # 4. Associated decisions
        all_decisions = self.store.get_decisions_for_entity(entity_id) if hasattr(self.store, "get_decisions_for_entity") else []
        for d in all_decisions:
            events.append({
                "event_type": "DECISION_RECORDED",
                "timestamp": d.get("valid_from", d.get("created_at", "")),
                "recorded_at": d.get("created_at", ""),
                "description": f"Decision: {d.get('title')}",
                "actor": d.get("decided_by_name", d.get("decided_by", "Executive Sponsor")),
                "rationale": d.get("rationale", ""),
            })

        # Sort chronologically
        events.sort(key=lambda x: str(x.get("timestamp", "")))

        return {
            "found": True,
            "entity": {
                "id": node["id"],
                "label": node["label"],
                "kind": node["kind"],
                "current_status": node.get("status", "active"),
                "valid_from": node.get("valid_from"),
                "valid_to": node.get("valid_to"),
                "recorded_at": node.get("recorded_at"),
            },
            "timeline": events,
            "event_count": len(events),
        }

    def get_universal_temporal_records(
        self,
        precision: str | None = None,
        validation_status: str | None = None,
        requires_review_only: bool = False,
    ) -> list[TemporalRecord]:
        """Convert all store nodes and timeline checkpoints to Universal Temporal Records."""
        nodes = self.store.get_all_nodes_with_history()
        adapter = StructuredRecordTemporalParser()
        records: list[TemporalRecord] = []

        for n in nodes:
            # If node already has temporal attached from ingestion, load directly
            if "temporal" in n and isinstance(n["temporal"], dict):
                t_obj = UniversalTimestamp(**n["temporal"])
                rec = TemporalRecord(id=n["id"], record_type=n.get("kind", "Entity"), data=n, temporal=t_obj)
            else:
                rec = adapter.parse(n, source_name="knowledge_graph")
            records.append(rec)

        return TemporalDataAnalyzer.filter_records(
            records=records,
            precision=precision,
            validation_status=validation_status,
            requires_review_only=requires_review_only,
        )

    def analyze_temporal(
        self,
        records: list[dict[str, Any]] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        precision: str | None = None,
        validation_status: str | None = None,
        requires_review_only: bool = False,
        sort_order: str = "asc",
    ) -> dict[str, Any]:
        """Perform comprehensive temporal data analysis, filtering, sorting, and timeline visualization."""
        if records is not None:
            adapter = StructuredRecordTemporalParser()
            temporal_records = [adapter.parse(r, source_name="custom_input") for r in records]
        else:
            temporal_records = self.get_universal_temporal_records()

        filtered = TemporalDataAnalyzer.filter_records(
            records=temporal_records,
            start_time=start_time,
            end_time=end_time,
            precision=precision,
            validation_status=validation_status,
            requires_review_only=requires_review_only,
        )

        sorted_recs = TemporalDataAnalyzer.sort_chronologically(filtered, order=sort_order)
        viz_data = TemporalDataAnalyzer.build_timeline_visualization(sorted_recs)

        return {
            "query": {
                "start_time": start_time,
                "end_time": end_time,
                "precision": precision,
                "validation_status": validation_status,
                "requires_review_only": requires_review_only,
                "sort_order": sort_order,
            },
            "analysis": viz_data,
        }

    def compare_historical_windows(
        self,
        window_a_start: str,
        window_a_end: str,
        window_b_start: str,
        window_b_end: str,
        numeric_field: str | None = None,
    ) -> dict[str, Any]:
        """Compare data velocity, review flags, and metrics across two historical intervals."""
        all_recs = self.get_universal_temporal_records()
        return TemporalDataAnalyzer.compare_historical_windows(
            records=all_recs,
            window_a_start=window_a_start,
            window_a_end=window_a_end,
            window_b_start=window_b_start,
            window_b_end=window_b_end,
            numeric_field=numeric_field,
        )

    def get_review_flags(self) -> dict[str, Any]:
        """Retrieve all records flagged for human review (missing, malformed, conflicting, implausible)."""
        flagged = self.get_universal_temporal_records(requires_review_only=True)
        return {
            "total_flagged": len(flagged),
            "flagged_records": [
                {
                    "id": r.id,
                    "record_type": r.record_type,
                    "validation_status": r.temporal.validation_status.value,
                    "validation_flags": r.temporal.validation_flags,
                    "original_timestamp": r.temporal.original_event_time,
                    "timezone": r.temporal.timezone,
                    "provenance": r.temporal.source_provenance,
                }
                for r in flagged
            ],
        }

