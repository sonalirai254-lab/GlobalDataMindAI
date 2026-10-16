"""Graphwise Nexus — Real-Time Event & Webhook Ingestion Engine.
Processes validated events, detects duplicates idempotently, updates FalkorDB,
triggers live dependency blast-radius evaluation, and generates evidence-backed alerts.

Features:
- Validated event payloads with strict schema enforcement.
- Duplicate event rejection via event_id cache / deduplication registry.
- Bitemporal graph updates (preserves historical transitions with valid-time).
- Automated dependency ripple analysis on outage/reassignment/delay.
- Evidence-backed impact alert dispatching with traversed graph paths.
- Dead-letter error handling and telemetry tracking.
"""
from __future__ import annotations

import time
import uuid
import copy
from datetime import datetime, timezone
from typing import Any
from .schema import IngestionEvent, EventType, ImpactAlert


class RealtimeEventManager:
    """Manages real-time event ingestion, deduplication, graph updates, and dependency alerts."""

    def __init__(self, store: Any, ripple_engine: Any, trust_ledger: Any) -> None:
        self.store = store
        self.ripple_engine = ripple_engine
        self.trust_ledger = trust_ledger

        # Deduplication registry: event_id -> {timestamp, status, response}
        self._processed_events: dict[str, dict[str, Any]] = {}

        # Dead-letter error log
        self._error_log: list[dict[str, Any]] = []

        # Active & acknowledged alerts
        self._alerts: list[dict[str, Any]] = []

        # Ingestion metrics
        self._metrics = {
            "total_received": 0,
            "total_processed": 0,
            "duplicates_rejected": 0,
            "processing_errors": 0,
            "last_event_time": None,
            "last_successful_ingest": None,
            "sources_active": set(),
        }

        # Seed with initial simulated baseline alert for demonstration
        self._seed_initial_alerts()

    def _seed_initial_alerts(self) -> None:
        """Seed a realistic evidence-backed alert for demonstration purposes."""
        self._alerts.append({
            "id": "alert_sec_token_audit",
            "alert_type": "SECURITY_FINDING",
            "severity": "HIGH",
            "title": "Token Propagation Race Condition in Legacy Bridge",
            "summary": "Security Audit 2026 identified asynchronous token race conditions during cross-tenant graph traversal.",
            "target_entity": {"id": "project_zerotrust", "label": "Zero-Trust Auth", "kind": "Project"},
            "affected_entities": [
                {"id": "project_atlas", "label": "Project Atlas", "kind": "Project", "impact": "Deployment dependency blocked"},
                {"id": "service_auth", "label": "Auth Gateway", "kind": "Service", "impact": "Session token verification retry delay"}
            ],
            "dependency_path": ["Zero-Trust Auth (Project) —[POWERS]→ Project Atlas (Project)"],
            "action_plan": [
                "Deploy Zero-Trust Auth token bridge before customer release.",
                "Review Decision 'Postpone Q3 Release' for approved timeline adjustment."
            ],
            "timestamp": "2026-09-02T10:30:00Z",
            "acknowledged": True,
            "event_id": "seed_evt_sec_001",
        })

    def get_status(self) -> dict[str, Any]:
        """Return real-time ingestion health, telemetry, and source connectivity."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        db_connected = getattr(self.store, "connected", False)

        return {
            "status": "healthy" if self._metrics["processing_errors"] == 0 else "degraded",
            "engine": "Graphwise Real-Time Event Bus",
            "database_connected": db_connected,
            "database_mode": "FalkorDB (Live Graph Engine)" if db_connected else "Standalone Demo Mode",
            "telemetry": {
                "total_events_received": self._metrics["total_received"],
                "total_events_processed": self._metrics["total_processed"],
                "duplicates_rejected": self._metrics["duplicates_rejected"],
                "processing_errors": self._metrics["processing_errors"],
                "active_alerts_count": len([a for a in self._alerts if not a.get("acknowledged", False)]),
                "total_alerts_count": len(self._alerts),
                "last_event_time": self._metrics["last_event_time"],
                "last_successful_ingest": self._metrics["last_successful_ingest"] or "Initialized",
                "sources_active": list(self._metrics["sources_active"]) or ["webhook", "internal_bus"],
            },
            "server_time": now_utc,
        }

    def get_alerts(self, unacknowledged_only: bool = False) -> list[dict[str, Any]]:
        """Return evidence-backed impact alerts."""
        if unacknowledged_only:
            return [a for a in self._alerts if not a.get("acknowledged", False)]
        return copy.deepcopy(self._alerts)

    def acknowledge_alert(self, alert_id: str) -> dict[str, Any] | None:
        """Mark an alert as acknowledged by an operator."""
        for a in self._alerts:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                a["acknowledged_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                return copy.deepcopy(a)
        return None

    def get_event_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recently processed events."""
        history = list(self._processed_events.values())
        history.sort(key=lambda x: str(x.get("processed_at", "")), reverse=True)
        return history[:limit]

    def process_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Ingest, validate, deduplicate, and idempotently apply an event to the graph."""
        self._metrics["total_received"] += 1
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Validation
        try:
            event = IngestionEvent(**event_data)
        except Exception as e:
            self._metrics["processing_errors"] += 1
            error_entry = {
                "error": "Validation failed",
                "details": str(e),
                "raw_event": event_data,
                "timestamp": now_iso,
            }
            self._error_log.append(error_entry)
            return {
                "status": "error",
                "error_code": "INVALID_EVENT_SCHEMA",
                "message": f"Event validation error: {str(e)}",
            }

        # 2. Deduplication check
        if event.event_id in self._processed_events:
            self._metrics["duplicates_rejected"] += 1
            prev = self._processed_events[event.event_id]
            return {
                "status": "duplicate",
                "event_id": event.event_id,
                "message": "Duplicate event rejected idempotently. Original result returned.",
                "original_processed_at": prev.get("processed_at"),
                "result": prev.get("result"),
            }

        source = event.source or "webhook"
        self._metrics["sources_active"].add(source)

        # 3. Process according to EventType
        try:
            result = self._apply_event_to_graph(event, now_iso)
            self._metrics["total_processed"] += 1
            self._metrics["last_event_time"] = event.timestamp or now_iso
            self._metrics["last_successful_ingest"] = now_iso

            event_record = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "source": source,
                "entity_id": event.entity_id,
                "valid_time": event.timestamp,
                "recorded_at": now_iso,
                "processed_at": now_iso,
                "status": "processed",
                "result": result,
            }
            self._processed_events[event.event_id] = event_record

            return {
                "status": "success",
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "recorded_at": now_iso,
                "result": result,
            }

        except Exception as e:
            self._metrics["processing_errors"] += 1
            error_entry = {
                "error": "Processing error",
                "event_id": event.event_id,
                "details": str(e),
                "timestamp": now_iso,
            }
            self._error_log.append(error_entry)
            return {
                "status": "error",
                "event_id": event.event_id,
                "error_code": "INGESTION_EXECUTION_FAILURE",
                "message": str(e),
            }

    def _apply_event_to_graph(self, event: IngestionEvent, recorded_at: str) -> dict[str, Any]:
        """Apply mutations to graph entities with bitemporal preservation."""
        e_type = event.event_type
        target_id = event.entity_id
        payload = event.payload
        valid_time = event.timestamp or recorded_at

        # A. SERVICE_OUTAGE
        if e_type == EventType.SERVICE_OUTAGE:
            outage_detail = payload.get("reason", "Unexpected service degradation / connection failure")
            # Update entity status bitemporally
            self.store.update_entity_status(
                entity_id=target_id,
                new_status="outage",
                changed_at=valid_time,
                recorded_at=recorded_at,
                reason=outage_detail,
                changed_by=f"Monitor: {event.source}",
            )

            # Automated Ripple Blast Radius Analysis
            ripple_analysis = self.ripple_engine.analyze_ripple(
                target_entity_id=target_id,
                change_type="DOWNTIME",
                detail=outage_detail,
            )

            # Generate Evidence-Backed Impact Alert
            target_node = self.store.get_entity_by_id(target_id) or {"id": target_id, "label": target_id, "kind": "Service"}
            directs = ripple_analysis.get("direct_impacts", [])
            cascades = ripple_analysis.get("cascade_impacts", [])
            all_affected = directs + cascades

            alert_id = f"alert_outage_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            derived_severity = (payload.get("severity") or ("CRITICAL" if ripple_analysis.get("risk_level") == "HIGH" else "HIGH")).upper()
            new_alert = {
                "id": alert_id,
                "alert_type": "SERVICE_OUTAGE_IMPACT",
                "severity": derived_severity,
                "title": f"Service Outage Alert: {target_node.get('label', target_id)}",
                "summary": f"Detected outage on {target_node.get('label')}. Directly impacts {len(directs)} downstream dependencies and {len(cascades)} cascade entities.",
                "target_entity": target_node,
                "affected_entities": all_affected,
                "dependency_path": [p["trace"] for p in ripple_analysis.get("all_paths", [])[:4]],
                "action_plan": [a["action"] for a in ripple_analysis.get("action_plan", [])],
                "timestamp": valid_time,
                "acknowledged": False,
                "event_id": event.event_id,
            }
            self._alerts.insert(0, new_alert)

            # Log to Trust Ledger
            self.trust_ledger.record_conclusion(
                query=f"Real-time event: Service Outage on {target_node.get('label')}",
                conclusion=new_alert["summary"],
                verified_facts=[
                    f"Outage verified from source: {event.source} at {valid_time}.",
                    f"Identified {len(all_affected)} graph-reachable dependent services and projects.",
                ],
                assumptions=["Blast radius assumes standard failure propagation without active bypass."],
                supporting_entities=[target_node] + all_affected[:3],
                traversed_edges=[{"source": p["entity"], "rel": p["relationship"], "target": "Downstream"} for p in ripple_analysis.get("all_paths", [])[:3]],
                database_source="FalkorDB Real-Time Event Bus",
            )

            return {
                "action": "outage_recorded",
                "entity_id": target_id,
                "new_status": "outage",
                "blast_radius_risk": ripple_analysis.get("risk_level"),
                "affected_entities_count": len(all_affected),
                "generated_alert_id": alert_id,
            }

        # B. SERVICE_RESTORED
        if e_type == EventType.SERVICE_RESTORED:
            self.store.update_entity_status(
                entity_id=target_id,
                new_status="active",
                changed_at=valid_time,
                recorded_at=recorded_at,
                reason=payload.get("reason", "Service restored to healthy operating status"),
                changed_by=f"Monitor: {event.source}",
            )
            # Auto-acknowledge corresponding outage alerts
            for a in self._alerts:
                if a.get("target_entity", {}).get("id") == target_id and not a.get("acknowledged", False):
                    a["acknowledged"] = True
                    a["acknowledged_at"] = recorded_at

            return {
                "action": "service_restored",
                "entity_id": target_id,
                "new_status": "active",
            }

        # C. OWNER_REASSIGNED
        if e_type == EventType.OWNER_REASSIGNED:
            new_owner_id = payload.get("new_owner_id")
            new_owner_name = payload.get("new_owner_name", new_owner_id)
            reason = payload.get("reason", "Resource balancing and domain expertise realignment")

            update_res = self.store.reassign_entity_owner(
                entity_id=target_id,
                new_owner_id=new_owner_id,
                new_owner_name=new_owner_name,
                assigned_at=valid_time,
                recorded_at=recorded_at,
                reason=reason,
            )

            # Check if reassignment affects critical path tasks
            target_node = self.store.get_entity_by_id(target_id) or {"id": target_id, "label": target_id, "kind": "Task"}
            alert_id = f"alert_owner_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            new_alert = {
                "id": alert_id,
                "alert_type": "OWNERSHIP_CHANGE",
                "severity": "INFO",
                "title": f"Ownership Reassigned: {target_node.get('label')}",
                "summary": f"Task '{target_node.get('label')}' reassigned to {new_owner_name}. Previous owner preserved in temporal history.",
                "target_entity": target_node,
                "affected_entities": [{"id": new_owner_id, "label": new_owner_name, "kind": "Person"}],
                "dependency_path": [f"{target_node.get('label')} —[ASSIGNED_TO]→ {new_owner_name}"],
                "action_plan": [f"Notify {new_owner_name} and schedule handoff alignment."],
                "timestamp": valid_time,
                "acknowledged": False,
                "event_id": event.event_id,
            }
            self._alerts.insert(0, new_alert)

            return {
                "action": "owner_reassigned",
                "entity_id": target_id,
                "previous_owner": update_res.get("previous_owner"),
                "new_owner": new_owner_name,
                "generated_alert_id": alert_id,
            }

        # D. STATUS_CHANGED
        if e_type == EventType.STATUS_CHANGED:
            new_status = payload.get("new_status", "in_progress")
            reason = payload.get("reason", "Milestone transition")
            self.store.update_entity_status(
                entity_id=target_id,
                new_status=new_status,
                changed_at=valid_time,
                recorded_at=recorded_at,
                reason=reason,
                changed_by=payload.get("changed_by", event.source),
            )
            return {
                "action": "status_updated",
                "entity_id": target_id,
                "new_status": new_status,
            }

        # E. DEPENDENCY_ADDED
        if e_type == EventType.DEPENDENCY_ADDED:
            depends_on_id = payload.get("depends_on_id")
            rel_label = payload.get("relationship", "DEPENDS_ON")
            if depends_on_id:
                self.store.add_edge_bitemporal(
                    source_id=target_id,
                    target_id=depends_on_id,
                    label=rel_label,
                    valid_from=valid_time,
                    recorded_at=recorded_at,
                )

                # Check blast radius of this new dependency
                ripple_res = self.ripple_engine.analyze_ripple(
                    target_entity_id=depends_on_id,
                    change_type="NEW_DEPENDENCY",
                    detail=f"New link from {target_id}",
                )

                return {
                    "action": "dependency_added",
                    "source": target_id,
                    "target": depends_on_id,
                    "relationship": rel_label,
                    "ripple_impact_count": len(ripple_res.get("direct_impacts", [])),
                }

        # F. DECISION_RECORDED
        if e_type == EventType.DECISION_RECORDED:
            title = payload.get("title", "Real-Time Decision")
            rationale = payload.get("rationale", "")
            d_res = self.store.add_decision(
                title=title,
                rationale=rationale,
                evidence=payload.get("evidence", ""),
                decided_by=payload.get("decided_by", ""),
                associated_entities=payload.get("associated_entities", [target_id]),
                outcome=payload.get("outcome", ""),
                valid_from=valid_time,
            )
            return {
                "action": "decision_recorded",
                "decision": d_res,
            }

        return {"action": "unhandled_event_type", "type": str(e_type)}
