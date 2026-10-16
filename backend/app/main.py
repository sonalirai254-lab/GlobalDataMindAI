"""FastAPI endpoints for Graphwise Nexus: A Graph-Native Enterprise Organizational Intelligence Platform.
Supports:
1. Ripple Intelligence (dependency-impact engine & blast radius)
2. Why-Memory (persistent organizational decision memory)
3. Hidden Connection Discovery (bounded multi-hop graph exploration)
4. Counterfactual Scenario Studio (hypothetical comparisons & authorized apply)
5. Trust Ledger (evidence-provenance & fact audit layer)
6. Interactive Knowledge Graph & Cypher Console
7. Multi-Agent Coordination (Research, Analysis, Planning, Verification)
8. Real-time System Telemetry & Health Checks
"""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .graph_store import GraphStore
    from .metrics import metrics
    from .multi_agent import SharedGraphContext, MultiAgentRunner
    from .ingestion import KnowledgeIngestionManager
    from .quality import QualityAuditor
    from .why_memory import WhyMemoryManager
    from .trust_ledger import TrustLedgerManager
    from .ripple import RippleEngine
    from .scenario_studio import ScenarioStudioManager
    from .ai_router import AIRouter
    from .temporal import TemporalGraphEngine
    from .events import RealtimeEventManager
    from .global_intelligence import GlobalIntelligenceManager
    from .personal_intelligence import PersonalIntelligenceManager, AcademicRecordInput
    from .evidence_analysis import EvidenceAnalysisEngine
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    _backend_dir = Path(__file__).resolve().parent.parent
    if str(_backend_dir) not in sys.path:
        sys.path.insert(0, str(_backend_dir))
    from app.graph_store import GraphStore
    from app.metrics import metrics
    from app.multi_agent import SharedGraphContext, MultiAgentRunner
    from app.ingestion import KnowledgeIngestionManager
    from app.quality import QualityAuditor
    from app.why_memory import WhyMemoryManager
    from app.trust_ledger import TrustLedgerManager
    from app.ripple import RippleEngine
    from app.scenario_studio import ScenarioStudioManager
    from app.ai_router import AIRouter
    from app.temporal import TemporalGraphEngine
    from app.events import RealtimeEventManager
    from app.global_intelligence import GlobalIntelligenceManager
    from app.personal_intelligence import PersonalIntelligenceManager, AcademicRecordInput
    from app.evidence_analysis import EvidenceAnalysisEngine

app = FastAPI(
    title="GlobalDataMind AI API",
    description="Evidence-grounded global macroeconomic, personal academic, and graph intelligence platform.",
    version="2.2.0",
)

# Allow multiple CORS origins for local dev and production
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telemetry tracking middleware
@app.middleware("http")
async def track_latency(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000.0
    metrics.record_request(duration_ms, response.status_code)
    return response

# Core Singletons
store = GraphStore()
why_memory = WhyMemoryManager(store)
trust_ledger = TrustLedgerManager(store)
ripple_engine = RippleEngine(store)
scenario_studio = ScenarioStudioManager(store, why_memory, trust_ledger)
temporal_engine = TemporalGraphEngine(store)
event_mgr = RealtimeEventManager(store, ripple_engine, trust_ledger)
ai_router = AIRouter(store, why_memory, trust_ledger, ripple_engine, temporal_engine, event_mgr)
ingestion_mgr = KnowledgeIngestionManager(store)
quality_auditor = QualityAuditor(store)
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
global_intelligence = GlobalIntelligenceManager(store, trust_ledger, cache_dir=data_dir)
personal_intelligence = PersonalIntelligenceManager(store, trust_ledger, storage_dir=data_dir)
evidence_engine = EvidenceAnalysisEngine(global_intelligence, personal_intelligence, trust_ledger, store)

# Wire helper methods
store.get_decisions_for_entity = why_memory.get_decisions_for_entity



# ---------------- Pydantic Request Models ---------------- #

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = "default"


class MemoryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    kind: str = Field(default="Context", max_length=60)
    session_id: str = "default"
    approved: bool = True
    source_context: str | None = None


class EntityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    kind: str = Field(default="Document", max_length=60)
    detail: str = Field(default="", max_length=500)
    related_to: str | None = None
    relationship: str = Field(default="RELATED_TO", max_length=40)


class EdgeRequest(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    label: str = Field(default="RELATED_TO", max_length=50)


class PathRequest(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)


class HiddenConnectionRequest(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    max_hops: int = Field(default=4, ge=1, le=5)


class AgentGoalRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=500)


class RippleRequest(BaseModel):
    target_entity_id: str = Field(min_length=1, max_length=120)
    change_type: str = Field(default="DOWNTIME", max_length=40)
    detail: str = Field(default="48-hour service unavailability", max_length=300)
    params: dict[str, Any] = Field(default_factory=dict)


class ImpactSimulationRequest(BaseModel):
    target_node_id: str = Field(min_length=1, max_length=120)
    scenario: str = Field(default="DELAY", max_length=40)
    detail: str = Field(default="4-week timeline delay", max_length=200)


class DecisionCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    rationale: str = Field(min_length=5, max_length=1000)
    evidence: str = Field(default="", max_length=500)
    decided_by: str = Field(default="", max_length=120)
    associated_entities: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    outcome: str = Field(default="", max_length=500)
    valid_from: str = Field(default="", max_length=50)
    status: str = Field(default="active", max_length=40)


class WhyQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ScenarioCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    target_entity_id: str = Field(min_length=1, max_length=120)
    change_type: str = Field(default="DELAY", max_length=40)
    detail: str = Field(default="", max_length=500)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ScenarioCompareRequest(BaseModel):
    scenario_ids: list[str] = Field(default_factory=list)


class ScenarioApplyRequest(BaseModel):
    confirm: bool = Field(default=True)
    authorized_by: str = Field(default="Admin", max_length=80)


class ClaimVerifyRequest(BaseModel):
    claim: str = Field(min_length=3, max_length=500)


class QualityResolutionRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=50)
    payload: dict[str, Any] = Field(default_factory=dict)


class TextIngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=50000)
    source_name: str = "text_editor"


class JsonIngestRequest(BaseModel):
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    source_name: str = "json_import"


class CypherRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    params: dict[str, Any] = Field(default_factory=dict)


class DiffRequest(BaseModel):
    t1: str = Field(default="1_month_ago", max_length=80)
    t2: str = Field(default="now", max_length=80)


class EventWebhookRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=120)
    event_type: str = Field(min_length=1, max_length=60)
    source: str = Field(default="webhook", max_length=80)
    timestamp: str = Field(default="", max_length=80)
    entity_id: str = Field(min_length=1, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class EventSimulateRequest(BaseModel):
    scenario: str = Field(default="SERVICE_OUTAGE", max_length=80)


class GlobalCompareRequest(BaseModel):
    country_codes: list[str] = Field(min_length=1, max_length=8)
    indicator: str = Field(min_length=2, max_length=80)
    start_year: int = Field(default=2000, ge=1960, le=2030)
    end_year: int = Field(default=2024, ge=1960, le=2030)


class GlobalAnalysisRequest(BaseModel):
    country: str = Field(min_length=2, max_length=100)
    indicator: str = Field(min_length=2, max_length=100)
    start_year: int = Field(default=1990, ge=1960, le=2030)
    end_year: int = Field(default=2024, ge=1960, le=2030)


class GlobalCompareAnalysisRequest(BaseModel):
    country_codes: list[str] = Field(min_length=2, max_length=8)
    indicator: str = Field(min_length=2, max_length=100)
    start_year: int = Field(default=1990, ge=1960, le=2030)
    end_year: int = Field(default=2024, ge=1960, le=2030)


class PersonalAnalysisRequest(BaseModel):
    mask_sensitive: bool = True


# ---------------- System Health & Metrics ---------------- #

@app.get("/api/health")
def health() -> dict[str, Any]:
    connected = store.connected
    graph_info = store.graph_data()
    memories_list = store.memories()
    decisions_list = why_memory.list_decisions()
    active_alerts = event_mgr.get_alerts(unacknowledged_only=True)
    return {
        "status": "ok",
        "service": "GlobalDataMind AI",
        "database": "FalkorDB (Connected)" if connected else "Local Persistent Store (Standalone)",
        "connected": connected,
        "graph": os.getenv("FALKORDB_GRAPH", "global_datamind"),
        "host": os.getenv("FALKORDB_HOST", "localhost"),
        "port": int(os.getenv("FALKORDB_PORT", "6379")),
        "database_note": "FalkorDB container is active on port 6379" if connected else "FalkorDB port 6379 is offline; running in persistent local in-memory + disk mode",
        "stats": {
            "node_count": len(graph_info.get("nodes", [])),
            "edge_count": len(graph_info.get("edges", [])),
            "memory_count": len(memories_list),
            "decision_count": len(decisions_list),
            "ledger_count": len(trust_ledger.list_entries()),
            "active_alerts_count": len(active_alerts),
            "realtime_events_count": event_mgr.get_status()["telemetry"]["total_events_processed"],
            "global_intelligence_series_count": len(global_intelligence.list_stored_series()),
        },
    }


@app.get("/api/system/metrics")
def system_metrics() -> dict[str, Any]:
    return metrics.get_summary(
        db_connected=store.connected,
        host=os.getenv("FALKORDB_HOST", "localhost"),
        port=int(os.getenv("FALKORDB_PORT", "6379")),
        graph_name=os.getenv("FALKORDB_GRAPH", "global_datamind"),
    )


@app.post("/api/reconnect")
def reconnect() -> dict[str, Any]:
    success = store.connect()
    return {
        "connected": success,
        "database": "FalkorDB" if success else "Standalone Demo",
        "message": "Connected to FalkorDB successfully." if success else "FalkorDB is unreachable. Running in Standalone Demo mode.",
    }


# ---------------- Interactive Knowledge Graph ---------------- #

@app.get("/api/graph")
def graph(kind: str | None = None, limit: int = 500) -> dict[str, Any]:
    data = store.graph_data()
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if kind and kind != "All types":
        nodes = [n for n in nodes if n["kind"] == kind]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]

    if limit and len(nodes) > limit:
        nodes = nodes[:limit]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]

    return {
        "nodes": nodes,
        "edges": edges,
        "mode": data.get("mode", "demo"),
        "stats": {"node_count": len(nodes), "edge_count": len(edges)},
    }


@app.post("/api/graph/path")
def find_path(payload: PathRequest) -> dict[str, Any]:
    return store.find_path(payload.source, payload.target)


@app.post("/api/graph/connections")
def find_hidden_connections(payload: HiddenConnectionRequest) -> dict[str, Any]:
    """Bounded multi-hop graph exploration to uncover non-obvious indirect paths."""
    return store.find_hidden_connections(payload.source, payload.target, max_hops=payload.max_hops)


@app.get("/api/graph/indirect/{entity_id}")
def discover_indirect(entity_id: str, max_hops: int = 3, limit: int = 8) -> dict[str, Any]:
    """Discover indirect connections for a given entity that have no direct relationship."""
    return store.discover_indirect_connections(entity_id, max_hops=max_hops, limit=limit)


@app.post("/api/graph/reset")
def reset_graph() -> dict[str, Any]:
    return store.reset_graph()


@app.post("/api/graph/edge")
def create_edge(payload: EdgeRequest) -> dict[str, Any]:
    edge = store.add_edge(payload.source, payload.target, payload.label)
    return {"status": "ok", "edge": edge}


@app.delete("/api/graph/edge")
def delete_edge(source: str, target: str, label: str) -> dict[str, Any]:
    store.delete_edge(source, target, label)
    return {"status": "ok", "deleted": {"source": source, "target": target, "label": label}}


@app.delete("/api/graph/node/{node_id}")
def delete_node(node_id: str) -> dict[str, Any]:
    store.delete_node(node_id)
    return {"status": "ok", "deleted_id": node_id}


# ---------------- Global Intelligence (World Bank Live Data) ---------------- #

@app.get("/api/global/indicators")
def get_global_indicators(
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return verified indicator catalog with optional text/category search."""
    return global_intelligence.get_supported_indicators(query=q or "", category=category or "", limit=limit)


@app.get("/api/global/indicators/search")
def search_global_indicators(
    q: str = "",
    category: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Dedicated endpoint to search verified indicators by query or category."""
    return global_intelligence.search_indicators(query=q, category=category or "", limit=limit)


@app.get("/api/global/countries")
def get_global_countries(
    q: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return curated country catalog with optional text search."""
    return global_intelligence.get_supported_countries(query=q or "", limit=limit)


@app.get("/api/global/countries/search")
def search_global_countries(
    q: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Dedicated endpoint to search countries by name, ISO2, ISO3, capital, or region."""
    return global_intelligence.search_countries(query=q, limit=limit)


@app.get("/api/global/observations")
def get_global_observations(
    country: str,
    indicator: str,
    start_year: int = 1990,
    end_year: int = 2024,
    refresh: bool = False,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Retrieve verified historical observations from World Bank API for a country and indicator.
    Never fabricates data; missing observations from World Bank are strictly marked as None/null.
    """
    try:
        return global_intelligence.get_series(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
            force_refresh=refresh,
            timeout=timeout,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except TimeoutError as te:
        raise HTTPException(status_code=504, detail=str(te))
    except ConnectionError as ce:
        raise HTTPException(status_code=502, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch observations: {str(e)}")


@app.post("/api/global/compare")
def compare_global_countries(payload: GlobalCompareRequest) -> dict[str, Any]:
    """Compare multiple countries for a given indicator across a historical timeframe."""
    try:
        return global_intelligence.compare_countries(
            country_codes=payload.country_codes,
            indicator=payload.indicator,
            start_year=payload.start_year,
            end_year=payload.end_year,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except TimeoutError as te:
        raise HTTPException(status_code=504, detail=str(te))
    except ConnectionError as ce:
        raise HTTPException(status_code=502, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.get("/api/global/stored")
def get_stored_global_series() -> list[dict[str, Any]]:
    """List all stored and cached historical series in the persistent repository."""
    return global_intelligence.list_stored_series()


@app.get("/api/global/observations/stored")
def get_stored_global_observations(
    country: Optional[str] = None,
    indicator: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Retrieve historical observation entities directly from reliable database storage with optional filtering."""
    return global_intelligence.get_stored_observations(
        country=country,
        indicator=indicator,
        start_year=start_year,
        end_year=end_year,
    )


@app.get("/api/global/storage/stats")
def get_global_storage_stats() -> dict[str, Any]:
    """Retrieve database persistence metrics, observation counts, and data integrity health stats."""
    return global_intelligence.get_storage_stats()


# ---------------- Feature: Personal Intelligence (Academic Records & Timeline) ---------------- #

@app.get("/api/personal/profile")
def get_personal_profile(mask: bool = False) -> dict[str, Any]:
    """Retrieve verified academic profile, chronological timeline, comparisons, and calculated insights."""
    return personal_intelligence.get_profile(mask_sensitive=mask)


@app.post("/api/personal/record")
def save_personal_academic_record(payload: AcademicRecordInput) -> dict[str, Any]:
    """Validate and store a Class 10, Class 12, or B.Tech academic record."""
    try:
        return personal_intelligence.add_or_update_record(payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save academic record: {str(e)}")


@app.delete("/api/personal/record/{level}")
def delete_personal_academic_record(level: str) -> dict[str, Any]:
    """Delete a specific academic record (class_10, class_12, or btech)."""
    success = personal_intelligence.delete_record(level)
    if not success:
        raise HTTPException(status_code=404, detail=f"Record '{level}' not found.")
    return {"success": True, "level": level, "profile": personal_intelligence.get_profile()}


@app.delete("/api/personal/profile")
def reset_personal_profile() -> dict[str, Any]:
    """Reset all personal academic records."""
    personal_intelligence.reset_profile()
    return {"success": True, "message": "Personal profile reset successfully."}


@app.get("/api/personal/comparison")
def get_personal_academic_comparison() -> dict[str, Any]:
    """Compare performance across all available completed academic milestones."""
    profile = personal_intelligence.get_profile()
    return {
        "comparison": profile["comparison"],
        "calculated_insights": profile["calculated_insights"],
        "available_records_count": profile["summary"]["recorded_milestones_count"],
        "missing_milestones": profile["missing_milestones"],
    }


# ---------------- Feature: Evidence-Based AI Analysis ---------------- #

@app.post("/api/ai/analyze/global")
def analyze_global_intelligence(payload: GlobalAnalysisRequest) -> dict[str, Any]:
    """Perform evidence-based AI analysis on real country data: trends, anomalies, verified citations, and uncertainty."""
    try:
        return evidence_engine.analyze_global_series(
            country=payload.country,
            indicator=payload.indicator,
            start_year=payload.start_year,
            end_year=payload.end_year,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence analysis failed: {str(e)}")


@app.post("/api/ai/analyze/global/compare")
def analyze_global_comparison(payload: GlobalCompareAnalysisRequest) -> dict[str, Any]:
    """Perform evidence-based cross-country comparative analysis explaining disparities, rankings, and convergence."""
    try:
        return evidence_engine.analyze_global_comparison(
            country_codes=payload.country_codes,
            indicator=payload.indicator,
            start_year=payload.start_year,
            end_year=payload.end_year,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparative analysis failed: {str(e)}")


@app.post("/api/ai/analyze/personal")
def analyze_personal_intelligence(payload: PersonalAnalysisRequest) -> dict[str, Any]:
    """Perform evidence-based AI analysis on user-provided academic records in complete isolation from country data."""
    try:
        return evidence_engine.analyze_personal_records(mask_sensitive=payload.mask_sensitive)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personal academic analysis failed: {str(e)}")


@app.get("/api/ai/analyze/personal")
def get_personal_intelligence_analysis(mask: bool = True) -> dict[str, Any]:
    """Retrieve evidence-based AI analysis of user-provided academic records."""
    try:
        return evidence_engine.analyze_personal_records(mask_sensitive=mask)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personal academic analysis failed: {str(e)}")


# ---------------- Feature 1: Historical Intelligence ---------------- #

@app.get("/api/graph/timeline")
def get_timeline_checkpoints() -> list[dict[str, Any]]:
    """Return available temporal timeline checkpoints for historical reconstruction."""
    return temporal_engine.get_timeline_checkpoints()


@app.get("/api/graph/historical")
def get_historical_snapshot(timestamp: str = "now") -> dict[str, Any]:
    """Reconstruct the graph topology as it existed at a specific point-in-time."""
    return temporal_engine.reconstruct_snapshot(timestamp)


@app.post("/api/graph/diff")
def compute_graph_diff(payload: DiffRequest) -> dict[str, Any]:
    """Compute topological and property diffs between two temporal checkpoints."""
    return temporal_engine.compute_diff(t1=payload.t1, t2=payload.t2)


@app.get("/api/graph/entity/{entity_id}/history")
def get_entity_history(entity_id: str) -> dict[str, Any]:
    """Retrieve full chronological lifecycle, ownership transitions, and status changes for an entity."""
    return temporal_engine.get_entity_history(entity_id)


# ---------------- Feature 2: Real-Time Intelligence & Ingestion ---------------- #

@app.post("/api/events/webhook")
def receive_webhook_event(payload: EventWebhookRequest) -> dict[str, Any]:
    """Validated webhook ingestion with deduplication, idempotent graph update, and ripple alerting."""
    return event_mgr.process_event(payload.model_dump())


@app.get("/api/events/status")
def get_event_bus_status() -> dict[str, Any]:
    """Real-time event bus health, telemetry, deduplication metrics, and source connectivity."""
    return event_mgr.get_status()


@app.get("/api/events/alerts")
def get_impact_alerts(unacknowledged: bool = False) -> list[dict[str, Any]]:
    """Retrieve evidence-backed impact alerts generated by live dependency changes."""
    return event_mgr.get_alerts(unacknowledged_only=unacknowledged)


@app.post("/api/events/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """Mark an evidence-backed alert as acknowledged."""
    res = event_mgr.acknowledge_alert(alert_id)
    if not res:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"status": "ok", "alert": res}


@app.get("/api/events/history")
def get_event_history(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve recently ingested real-time events with idempotent processing metadata."""
    return event_mgr.get_event_history(limit=limit)


@app.post("/api/events/simulate")
def simulate_event(payload: EventSimulateRequest) -> dict[str, Any]:
    """Simulate realistic real-time events for live verification and operator testing."""
    scenario = payload.scenario.upper()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    evt_uuid = uuid.uuid4().hex[:8]

    if scenario == "SERVICE_OUTAGE":
        evt_data = {
            "event_id": f"sim_outage_{evt_uuid}",
            "event_type": "SERVICE_OUTAGE",
            "source": "pagerduty_webhook",
            "timestamp": now_iso,
            "entity_id": "service_payments",
            "payload": {
                "reason": "Simulated Tier-1 latency spike (>4000ms) and circuit breaker trip on core Payments API",
                "severity": "CRITICAL",
            },
        }
        return event_mgr.process_event(evt_data)

    elif scenario == "OWNER_REASSIGN":
        evt_data = {
            "event_id": f"sim_owner_{evt_uuid}",
            "event_type": "OWNER_REASSIGNED",
            "source": "jira_webhook",
            "timestamp": now_iso,
            "entity_id": "task_soc2",
            "payload": {
                "new_owner_id": "person_elena",
                "new_owner_name": "Elena Rostova",
                "reason": "Staff SRE assignment for high-throughput zero-trust token benchmarking",
            },
        }
        return event_mgr.process_event(evt_data)

    elif scenario == "SERVICE_RESTORED":
        evt_data = {
            "event_id": f"sim_restore_{evt_uuid}",
            "event_type": "SERVICE_RESTORED",
            "source": "pagerduty_webhook",
            "timestamp": now_iso,
            "entity_id": "service_payments",
            "payload": {
                "reason": "Payments API healthy: latency normal at 14ms, async queue cleared",
            },
        }
        return event_mgr.process_event(evt_data)

    elif scenario == "STATUS_CHANGED":
        evt_data = {
            "event_id": f"sim_status_{evt_uuid}",
            "event_type": "STATUS_CHANGED",
            "source": "github_actions",
            "timestamp": now_iso,
            "entity_id": "project_atlas",
            "payload": {
                "new_status": "release_candidate",
                "reason": "All SOC2 token propagation tests passed in staging environment",
            },
        }
        return event_mgr.process_event(evt_data)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown simulation scenario: {scenario}")


# ---------------- AI Assistant (8-Stage Reasoning Pipeline) ---------------- #

@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    return ai_router.execute_reasoning_pipeline(payload.message, payload.session_id)


# ---------------- 1. Ripple Intelligence (Dependency Impact) ---------------- #

@app.post("/api/ripple/analyze")
def analyze_ripple(payload: RippleRequest) -> dict[str, Any]:
    """Calculate graph-reachable blast radius, cascade impacts, risk rating, and action plan."""
    return ripple_engine.analyze_ripple(
        target_entity_id=payload.target_entity_id,
        change_type=payload.change_type,
        detail=payload.detail,
        params=payload.params,
    )


# Backwards compatibility alias for what-if impact simulation
@app.post("/api/simulate/impact")
def simulate_impact(payload: ImpactSimulationRequest) -> dict[str, Any]:
    change_type = payload.scenario.upper() if payload.scenario else "DELAY"
    res = ripple_engine.analyze_ripple(
        target_entity_id=payload.target_node_id,
        change_type=change_type,
        detail=payload.detail,
    )
    # Add backward compatibility fields
    res["target_node"] = res.get("target_entity")
    res["scenario"] = change_type
    res["impact_paths"] = [
        {"target_entity": p["entity"], "relationship": p["relationship"], "depth": p["depth"], "trace": p["trace"]}
        for p in res.get("all_paths", [])
    ]
    res["mitigations"] = [step["action"] for step in res.get("action_plan", [])]
    res["graph_mutated"] = False
    return res


# ---------------- 2. Why-Memory (Decision Memory) ---------------- #

@app.get("/api/decisions")
def get_decisions(status: str | None = None) -> dict[str, Any]:
    items = why_memory.list_decisions(status=status)
    return {
        "items": items,
        "count": len(items),
        "persistent": store.connected,
    }


@app.get("/api/decisions/{decision_id}")
def inspect_decision(decision_id: str) -> dict[str, Any]:
    item = why_memory.get_decision(decision_id)
    if not item:
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {"decision": item}


@app.post("/api/decisions")
def create_decision(payload: DecisionCreateRequest) -> dict[str, Any]:
    created = why_memory.add_decision(
        title=payload.title,
        rationale=payload.rationale,
        evidence=payload.evidence,
        decided_by=payload.decided_by,
        associated_entities=payload.associated_entities,
        source_refs=payload.source_refs,
        outcome=payload.outcome,
        valid_from=payload.valid_from,
        status=payload.status,
    )
    return {"status": "ok", "decision": created}


@app.post("/api/decisions/why-query")
def why_query(payload: WhyQueryRequest) -> dict[str, Any]:
    """Explain 'Why did we...', 'What changed...', and 'Which decision explains...'."""
    return why_memory.query_why(payload.question)


@app.delete("/api/decisions/{decision_id}")
def delete_decision(decision_id: str) -> dict[str, Any]:
    success = why_memory.delete_decision(decision_id)
    if not success:
        raise HTTPException(status_code=404, detail="Decision not found.")
    return {"status": "ok", "deleted_id": decision_id}


# Session Context Memory Endpoints
@app.get("/api/memory")
def get_memories(session_id: str | None = None, approved_only: bool = False) -> dict[str, Any]:
    saved = store.memories(session_id=session_id, approved_only=approved_only)
    return {
        "items": saved,
        "persistent": store.connected,
        "count": len(saved),
        "session_id": session_id or "all_sessions",
    }


@app.get("/api/memory/{memory_id}")
def inspect_memory(memory_id: str) -> dict[str, Any]:
    mem = store.get_memory(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"memory": mem, "persistent": store.connected}


@app.post("/api/memory")
def save_memory(payload: MemoryRequest) -> dict[str, Any]:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Memory text cannot be empty.")
    item = store.add_memory(
        text=text,
        session_id=payload.session_id,
        kind=payload.kind,
        approved=payload.approved,
        source_context=payload.source_context,
    )
    return item


@app.patch("/api/memory/{memory_id}/approve")
def toggle_approve(memory_id: str) -> dict[str, Any]:
    mem = store.toggle_approve_memory(memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"status": "ok", "memory": mem}


@app.delete("/api/memory/{memory_id}")
def delete_memory(memory_id: str) -> dict[str, Any]:
    store.delete_memory(memory_id)
    return {"status": "ok", "deleted_id": memory_id}


# ---------------- 4. Counterfactual Scenario Studio ---------------- #

@app.get("/api/scenarios")
def list_scenarios() -> dict[str, Any]:
    return {"scenarios": scenario_studio.list_scenarios()}


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    res = scenario_studio.get_scenario(scenario_id)
    if not res:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return res


@app.post("/api/scenarios")
def create_scenario(payload: ScenarioCreateRequest) -> dict[str, Any]:
    return scenario_studio.create_scenario(
        name=payload.name,
        target_entity_id=payload.target_entity_id,
        change_type=payload.change_type,
        detail=payload.detail,
        parameters=payload.parameters,
    )


@app.post("/api/scenarios/compare")
def compare_scenarios(payload: ScenarioCompareRequest) -> dict[str, Any]:
    return scenario_studio.compare_scenarios(payload.scenario_ids)


@app.post("/api/scenarios/{scenario_id}/apply")
def apply_scenario(scenario_id: str, payload: ScenarioApplyRequest) -> dict[str, Any]:
    """Authorized apply of hypothetical scenario to the production graph."""
    res = scenario_studio.apply_scenario(
        scenario_id=scenario_id,
        confirm=payload.confirm,
        authorized_by=payload.authorized_by,
    )
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res


# ---------------- 5. Trust Ledger (Evidence Provenance) ---------------- #

@app.get("/api/trust-ledger")
def get_trust_ledger(limit: int = 25) -> dict[str, Any]:
    entries = trust_ledger.list_entries(limit=limit)
    return {
        "entries": entries,
        "count": len(entries),
        "source": "FalkorDB Provenance Ledger",
    }


@app.get("/api/trust-ledger/{entry_id}")
def inspect_ledger_entry(entry_id: str) -> dict[str, Any]:
    entry = trust_ledger.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Trust ledger record not found.")
    return {"entry": entry}


@app.post("/api/trust-ledger/verify-claim")
def verify_claim(payload: ClaimVerifyRequest) -> dict[str, Any]:
    return trust_ledger.verify_claim(payload.claim)


# ---------------- Knowledge Ingestion ---------------- #

@app.post("/api/ingest")
def ingest(payload: EntityRequest) -> dict[str, Any]:
    result = store.add_entity(
        name=payload.name,
        kind=payload.kind,
        detail=payload.detail,
        related_to=payload.related_to,
        relationship=payload.relationship,
    )
    metrics.record_ingestion(1)
    return {
        "status": "ok",
        "node": result["node"],
        "edge": result.get("edge"),
        "stored_in": result["stored_in"],
        "message": f"Successfully ingested '{payload.name}' ({payload.kind}).",
    }


@app.post("/api/ingest/text")
def ingest_text(payload: TextIngestRequest) -> dict[str, Any]:
    res = ingestion_mgr.ingest_text_markdown(title=payload.title, text=payload.content, source_name=payload.source_name)
    metrics.record_ingestion(1 if res["status"] == "success" else 0, error=res.get("errors", [None])[0] if res.get("errors") else None)
    return res


@app.post("/api/ingest/json")
def ingest_json(payload: JsonIngestRequest) -> dict[str, Any]:
    data = {"entities": payload.entities, "relationships": payload.relationships}
    res = ingestion_mgr.ingest_json(data=data, source_name=payload.source_name)
    metrics.record_ingestion(res.get("ingested_nodes_count", 0), error=res.get("errors", [None])[0] if res.get("errors") else None)
    return res


@app.post("/api/ingest/file")
async def ingest_file(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or "uploaded_file"
    contents = await file.read()

    if filename.lower().endswith(".pdf"):
        res = ingestion_mgr.ingest_pdf(filename, contents)
    elif filename.lower().endswith(".json"):
        import json
        try:
            parsed = json.loads(contents.decode("utf-8"))
            res = ingestion_mgr.ingest_json(parsed, source_name=filename)
        except Exception as e:
            res = {"status": "error", "message": f"Malformed JSON: {str(e)}", "errors": [str(e)]}
    else:  # Text or Markdown
        text = contents.decode("utf-8", errors="replace")
        title = filename.rsplit(".", 1)[0].replace("_", " ").title()
        res = ingestion_mgr.ingest_text_markdown(title=title, text=text, source_name=filename)

    metrics.record_ingestion(
        1 if res["status"] == "success" else 0,
        error=res.get("errors", [None])[0] if res.get("errors") else None,
    )
    return res


# ---------------- Multi-Agent Workflow ---------------- #

@app.post("/api/agent/run")
def run_multi_agent(payload: AgentGoalRequest) -> dict[str, Any]:
    data = store.graph_data()
    ctx = SharedGraphContext(nodes=data.get("nodes", []), edges=data.get("edges", []))
    runner = MultiAgentRunner(ctx, max_steps=6, timeout_seconds=10.0)
    result = runner.run(payload.goal)
    metrics.record_agent_run(
        success=result["status"] == "completed",
        tool_calls_count=runner.tool_calls_count,
    )
    return result


# ---------------- Knowledge Quality Checks ---------------- #

@app.get("/api/quality/audit")
def quality_audit() -> dict[str, Any]:
    return quality_auditor.audit()


@app.post("/api/quality/resolve")
def quality_resolve(payload: QualityResolutionRequest) -> dict[str, Any]:
    return quality_auditor.resolve(payload.action_type, payload.payload)


# ---------------- Cypher Console ---------------- #

@app.post("/api/cypher")
def run_cypher(payload: CypherRequest) -> dict[str, Any]:
    # Check for destructive queries
    q_upper = payload.query.upper().strip()
    destructive_keywords = ["DROP GRAPH", "DROP DATABASE", "DETACH DELETE (N)"]
    if any(dk in q_upper for dk in destructive_keywords):
        raise HTTPException(status_code=403, detail="Unrestricted destructive Cypher statements are blocked for user safety.")

    if not store.connected:
        return {
            "error": "FalkorDB is not connected. Cypher execution is available when FalkorDB is active.",
            "mode": "demo",
            "results": [],
        }
    try:
        results = store.query(payload.query, payload.params)
        return {
            "query": payload.query,
            "results": results,
            "row_count": len(results),
            "mode": "falkordb",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    _backend_dir = Path(__file__).resolve().parent.parent
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True, app_dir=str(_backend_dir))

