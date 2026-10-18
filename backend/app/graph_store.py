"""FalkorDB graph access with dynamic fallback dataset for local UI development."""
from __future__ import annotations

import os
import time
import copy
from typing import Any

# Optional import of falkordb to prevent startup failure if package is missing
try:
    from falkordb import FalkorDB
except ImportError:
    FalkorDB = None

from pathlib import Path
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).resolve().parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

GRAPH_NAME = os.getenv("FALKORDB_GRAPH", "global_datamind_graph")
HOST = os.getenv("FALKORDB_HOST", "localhost")
PORT = int(os.getenv("FALKORDB_PORT", "6379"))

INITIAL_SEED_NODES = [
    {
        "id": "person_maya",
        "label": "Maya Chen",
        "kind": "Person",
        "detail": "Product Lead & Vision",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [
            {"status": "active", "changed_at": "2026-08-01T00:00:00Z", "recorded_at": "2026-08-01T00:00:00Z", "changed_by": "Org Admin", "reason": "Role established"}
        ],
        "owner_history": [],
    },
    {
        "id": "team_product",
        "label": "Product Team",
        "kind": "Team",
        "detail": "Product roadmap & strategy",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "project_atlas",
        "label": "Project Atlas",
        "kind": "Project",
        "detail": "Flagship Q4 enterprise platform",
        "status": "in_progress",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 3,
        "status_history": [
            {"status": "planning", "changed_at": "2026-08-01T00:00:00Z", "recorded_at": "2026-08-01T00:00:00Z", "changed_by": "Maya Chen", "reason": "Initial project kickoff and scoping"},
            {"status": "active_development", "changed_at": "2026-09-01T00:00:00Z", "recorded_at": "2026-09-01T00:00:00Z", "changed_by": "Aarav Patel", "reason": "Architecture approved and development sprints initiated"},
            {"status": "in_progress", "changed_at": "2026-10-01T00:00:00Z", "recorded_at": "2026-10-01T00:00:00Z", "changed_by": "Marcus Vance", "reason": "Deployment postponed to Oct 28 for zero-trust remediations"}
        ],
        "owner_history": [
            {"owner": "team_product", "owner_name": "Product Team", "assigned_at": "2026-08-01T00:00:00Z", "recorded_at": "2026-08-01T00:00:00Z", "previous_owner": "None", "reason": "Product leadership"}
        ],
    },
    {
        "id": "doc_roadmap",
        "label": "Product Roadmap",
        "kind": "Document",
        "detail": "Targeting Q4 enterprise milestone",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "person_aarav",
        "label": "Aarav Patel",
        "kind": "Person",
        "detail": "Engineering Lead & Architecture",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "team_eng",
        "label": "Engineering",
        "kind": "Team",
        "detail": "Platform, APIs, and retrieval infra",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "project_search",
        "label": "Knowledge Search",
        "kind": "Project",
        "detail": "Vector + Graph retrieval pipeline",
        "status": "active",
        "valid_from": "2026-08-15T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-15T00:00:00Z",
        "version": 1,
        "status_history": [
            {"status": "active", "changed_at": "2026-08-15T00:00:00Z", "recorded_at": "2026-08-15T00:00:00Z", "changed_by": "Aarav Patel", "reason": "FalkorDB graph store adoption"}
        ],
        "owner_history": [],
    },
    {
        "id": "doc_arch",
        "label": "System Architecture",
        "kind": "Document",
        "detail": "Microservices, FalkorDB & event bus",
        "status": "active",
        "valid_from": "2026-08-15T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-15T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "person_sana",
        "label": "Sana Ali",
        "kind": "Person",
        "detail": "Lead Research Analyst",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "doc_research",
        "label": "Customer Research",
        "kind": "Document",
        "detail": "18 enterprise user interviews",
        "status": "active",
        "valid_from": "2026-08-05T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-05T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "person_marcus",
        "label": "Marcus Vance",
        "kind": "Person",
        "detail": "Principal Security Architect",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "team_security",
        "label": "Security & Compliance",
        "kind": "Team",
        "detail": "SOC2, RBAC & graph privacy",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "project_zerotrust",
        "label": "Zero-Trust Auth",
        "kind": "Project",
        "detail": "Unified token & identity bridge",
        "status": "active",
        "valid_from": "2026-09-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-09-01T00:00:00Z",
        "version": 1,
        "status_history": [
            {"status": "active", "changed_at": "2026-09-01T00:00:00Z", "recorded_at": "2026-09-01T00:00:00Z", "changed_by": "Marcus Vance", "reason": "Initiated to resolve token race conditions"}
        ],
        "owner_history": [],
    },
    {
        "id": "doc_security_audit",
        "label": "Security Audit 2026",
        "kind": "Document",
        "detail": "Passed compliance review with zero critical findings",
        "status": "active",
        "valid_from": "2026-09-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-09-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "country_ind",
        "label": "India",
        "kind": "Country",
        "detail": "South Asia · Lower middle income · ISO: IND",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "country_usa",
        "label": "United States",
        "kind": "Country",
        "detail": "North America · High income · ISO: USA",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "country_deu",
        "label": "Germany",
        "kind": "Country",
        "detail": "Europe & Central Asia · High income · ISO: DEU",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "ind_gdp",
        "label": "GDP (current US$)",
        "kind": "Indicator",
        "detail": "NY.GDP.MKTP.CD · Economy & Growth",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "ind_pop",
        "label": "Population, total",
        "kind": "Indicator",
        "detail": "SP.POP.TOTL · Demographics & Society",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "ind_inf",
        "label": "Inflation, consumer prices (%)",
        "kind": "Indicator",
        "detail": "FP.CPI.TOTL.ZG · Economic Policy & Debt",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "src_worldbank",
        "label": "World Bank Open Data API",
        "kind": "Source",
        "detail": "World Development Indicators (v2) · Official Sovereign Datasets",
        "status": "active",
        "valid_from": "1960-01-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "acad_class_10",
        "label": "Class 10 (Secondary)",
        "kind": "AcademicRecord",
        "detail": "Delhi Public School (CBSE) · 92.4% · Ground Truth",
        "status": "active",
        "valid_from": "2018-05-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "acad_class_12",
        "label": "Class 12 (Higher Secondary)",
        "kind": "AcademicRecord",
        "detail": "Delhi Public School (CBSE) · 89.8% (PCM) · Ground Truth",
        "status": "active",
        "valid_from": "2020-07-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "acad_btech",
        "label": "B.Tech (Computer Science)",
        "kind": "AcademicRecord",
        "detail": "IIT (BHU) Varanasi · 8.85 / 10.0 CGPA · Ground Truth",
        "status": "active",
        "valid_from": "2024-06-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-10-16T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "decision_falkordb",
        "label": "Adopt FalkorDB",
        "kind": "Decision",
        "detail": "Selected FalkorDB for low-latency Cypher graph queries and memory persistence",
        "status": "active",
        "valid_from": "2026-08-15T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-15T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "service_payments",
        "label": "Payments API",
        "kind": "Service",
        "detail": "Core payment gateway & billing token service (Tier 1 Criticality)",
        "status": "active",
        "valid_from": "2026-07-20T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-07-20T00:00:00Z",
        "version": 2,
        "status_history": [
            {"status": "monolith_coupled", "changed_at": "2026-07-01T00:00:00Z", "recorded_at": "2026-07-01T00:00:00Z", "changed_by": "Aarav Patel", "reason": "Legacy backend coupling"},
            {"status": "active", "changed_at": "2026-07-20T00:00:00Z", "recorded_at": "2026-07-20T00:00:00Z", "changed_by": "Aarav Patel", "reason": "Decoupled standalone microservice with circuit breaker"}
        ],
        "owner_history": [],
    },
    {
        "id": "service_auth",
        "label": "Auth Gateway",
        "kind": "Service",
        "detail": "Distributed token & session validation microservice",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "decision_postpone_deploy",
        "label": "Postpone Q3 Release",
        "kind": "Decision",
        "detail": "Postponed deployment to Oct 28 due to token race conditions found in Security Audit",
        "status": "executed",
        "valid_from": "2026-09-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-09-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "task_soc2",
        "label": "SOC2 Audit Remediation",
        "kind": "Task",
        "detail": "Remediate token propagation race conditions before customer rollout",
        "status": "remediation_active",
        "valid_from": "2026-08-20T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-20T00:00:00Z",
        "version": 2,
        "status_history": [
            {"status": "assigned", "changed_at": "2026-08-20T00:00:00Z", "recorded_at": "2026-08-20T00:00:00Z", "changed_by": "Engineering", "reason": "Task created from preliminary findings"},
            {"status": "remediation_active", "changed_at": "2026-10-01T00:00:00Z", "recorded_at": "2026-10-01T00:00:00Z", "changed_by": "Marcus Vance", "reason": "Transferred ownership to Security team for dedicated sprint"}
        ],
        "owner_history": [
            {"owner": "person_aarav", "owner_name": "Aarav Patel", "assigned_at": "2026-08-20T00:00:00Z", "recorded_at": "2026-08-20T00:00:00Z", "previous_owner": "None", "reason": "Initial platform task assignment"},
            {"owner": "person_marcus", "owner_name": "Marcus Vance", "assigned_at": "2026-10-01T00:00:00Z", "recorded_at": "2026-10-01T00:00:00Z", "previous_owner": "Aarav Patel", "reason": "Transferred to Security team following audit findings"}
        ],
    },
    {
        "id": "person_elena",
        "label": "Elena Rostova",
        "kind": "Person",
        "detail": "Staff Site Reliability Engineer & Platform Infra Lead",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
    {
        "id": "team_infra",
        "label": "Platform Infra",
        "kind": "Team",
        "detail": "Cloud kubernetes, observability, and database clustering",
        "status": "active",
        "valid_from": "2026-08-01T00:00:00Z",
        "valid_to": None,
        "recorded_at": "2026-08-01T00:00:00Z",
        "version": 1,
        "status_history": [],
        "owner_history": [],
    },
]

INITIAL_SEED_EDGES = [
    {"source": "person_maya", "target": "team_product", "label": "LEADS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "team_product", "target": "project_atlas", "label": "OWNS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "project_atlas", "target": "doc_roadmap", "label": "DOCUMENTED_IN", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "person_aarav", "target": "team_eng", "label": "LEADS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "team_eng", "target": "project_search", "label": "BUILDS", "valid_from": "2026-08-15T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-15T00:00:00Z"},
    {"source": "project_search", "target": "doc_arch", "label": "DOCUMENTED_IN", "valid_from": "2026-08-15T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-15T00:00:00Z"},
    {"source": "person_sana", "target": "doc_research", "label": "AUTHORED", "valid_from": "2026-08-05T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-05T00:00:00Z"},
    {"source": "doc_research", "target": "project_atlas", "label": "INFORMS", "valid_from": "2026-08-05T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-05T00:00:00Z"},
    {"source": "team_product", "target": "team_eng", "label": "COLLABORATES_WITH", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "person_marcus", "target": "team_security", "label": "LEADS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "team_security", "target": "project_zerotrust", "label": "OWNS", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    {"source": "project_zerotrust", "target": "doc_security_audit", "label": "DOCUMENTED_IN", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    {"source": "project_atlas", "target": "project_zerotrust", "label": "DEPENDS_ON", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    {"source": "project_search", "target": "project_atlas", "label": "POWERS", "valid_from": "2026-08-15T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-15T00:00:00Z"},
    {"source": "decision_falkordb", "target": "project_search", "label": "ENABLES", "valid_from": "2026-08-15T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-15T00:00:00Z"},
    {"source": "person_aarav", "target": "decision_falkordb", "label": "DECIDED_BY", "valid_from": "2026-08-15T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-15T00:00:00Z"},
    {"source": "project_atlas", "target": "service_payments", "label": "DEPENDS_ON", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "service_payments", "target": "service_auth", "label": "DEPENDS_ON", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "team_eng", "target": "service_payments", "label": "OWNS", "valid_from": "2026-07-20T00:00:00Z", "valid_to": None, "recorded_at": "2026-07-20T00:00:00Z"},
    {"source": "person_elena", "target": "team_infra", "label": "LEADS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    {"source": "team_infra", "target": "service_auth", "label": "OWNS", "valid_from": "2026-08-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-01T00:00:00Z"},
    # Active assignment:
    {"source": "task_soc2", "target": "person_marcus", "label": "ASSIGNED_TO", "valid_from": "2026-10-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-01T00:00:00Z"},
    # Historical assignment (before Oct 01, Aarav owned task_soc2):
    {"source": "task_soc2", "target": "person_aarav", "label": "HISTORICAL_ASSIGNED", "valid_from": "2026-08-20T00:00:00Z", "valid_to": "2026-10-01T00:00:00Z", "recorded_at": "2026-08-20T00:00:00Z"},
    {"source": "task_soc2", "target": "project_zerotrust", "label": "PART_OF", "valid_from": "2026-08-20T00:00:00Z", "valid_to": None, "recorded_at": "2026-08-20T00:00:00Z"},
    {"source": "decision_postpone_deploy", "target": "project_atlas", "label": "EXPLAINS", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    {"source": "person_marcus", "target": "decision_postpone_deploy", "label": "DECIDED_BY", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    {"source": "decision_postpone_deploy", "target": "doc_security_audit", "label": "DOCUMENTED_IN", "valid_from": "2026-09-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-09-01T00:00:00Z"},
    # Global Intelligence Relationships:
    {"source": "country_ind", "target": "ind_gdp", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "country_ind", "target": "ind_pop", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "country_ind", "target": "ind_inf", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "country_usa", "target": "ind_gdp", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "country_usa", "target": "ind_pop", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "country_deu", "target": "ind_gdp", "label": "HAS_INDICATOR", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "ind_gdp", "target": "src_worldbank", "label": "SOURCED_FROM", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "ind_pop", "target": "src_worldbank", "label": "SOURCED_FROM", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "ind_inf", "target": "src_worldbank", "label": "SOURCED_FROM", "valid_from": "1960-01-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    # Personal Intelligence Credential Progression:
    {"source": "acad_class_10", "target": "acad_class_12", "label": "PROGRESSES_TO", "valid_from": "2018-05-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
    {"source": "acad_class_12", "target": "acad_btech", "label": "PROGRESSES_TO", "valid_from": "2020-07-01T00:00:00Z", "valid_to": None, "recorded_at": "2026-10-16T00:00:00Z"},
]

INITIAL_SEED_MEMORIES = [
    {"id": "mem_1", "text": "Project Atlas is targeting a Q4 enterprise launch with FalkorDB graph memory.", "kind": "Launch context", "created_at": "10m ago"},
    {"id": "mem_2", "text": "Knowledge Search depends on the System Architecture document and FalkorDB graph queries.", "kind": "Dependency", "created_at": "1h ago"},
    {"id": "mem_3", "text": "Marcus Vance confirmed Zero-Trust Auth passed SOC2 compliance verification.", "kind": "Security note", "created_at": "3h ago"},
    {"id": "mem_4", "text": "Maya Chen and Aarav Patel agreed on weekly cross-team alignment every Tuesday.", "kind": "Team context", "created_at": "Yesterday"},
    {"id": "mem_5", "text": "Payments API has circuit breaker fallback configured with 48h asynchronous retry queue.", "kind": "Architecture", "created_at": "Yesterday"},
]

# For backwards compatibility with external imports
DEMO_NODES = copy.deepcopy(INITIAL_SEED_NODES)
DEMO_EDGES = copy.deepcopy(INITIAL_SEED_EDGES)


import socket

def is_port_open(host: str, port: int, timeout: float = 0.08) -> bool:
    """Fast non-blocking socket probe to prevent hanging on offline database."""
    target_host = "127.0.0.1" if host == "localhost" else host
    try:
        with socket.create_connection((target_host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class GraphStore:
    """Robust adapter around FalkorDB; seamlessly operates in standalone demo mode when unavailable."""

    def __init__(self) -> None:
        self._graph = None
        self._client = None
        self._connected = False
        self._last_connect_attempt = 0.0

        # Mutable in-memory store for standalone demo mode
        self._demo_nodes: list[dict[str, Any]] = copy.deepcopy(INITIAL_SEED_NODES)
        self._demo_edges: list[dict[str, Any]] = copy.deepcopy(INITIAL_SEED_EDGES)
        self._demo_memories: list[dict[str, Any]] = copy.deepcopy(INITIAL_SEED_MEMORIES)
        self._demo_observations: dict[str, dict[str, Any]] = {}

        self.connect()

    def connect(self) -> bool:
        """Attempt to connect to FalkorDB and seed if successful."""
        self._last_connect_attempt = time.time()
        if FalkorDB is None:
            self._connected = False
            self._graph = None
            return False

        # Fast pre-check: if port is not open, return False immediately without blocking
        if not is_port_open(HOST, PORT, timeout=0.08):
            self._connected = False
            self._graph = None
            return False

        try:
            effective_host = "127.0.0.1" if HOST == "localhost" else HOST
            client = FalkorDB(host=effective_host, port=PORT, socket_timeout=0.5, socket_connect_timeout=0.5)
            graph = client.select_graph(GRAPH_NAME)
            graph.query("RETURN 1")
            self._client = client
            self._graph = graph
            self._connected = True
            self.seed()
            return True
        except Exception:
            self._client = None
            self._graph = None
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        if not self._connected and (time.time() - self._last_connect_attempt > 30.0):
            self.connect()
        return self._connected

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        if not self.connected or not self._graph:
            return []
        try:
            result = self._graph.query(cypher, params or {})
            return result.result_set
        except Exception as e:
            # If query failed due to connection loss, mark disconnected
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                self._connected = False
            return []

    def seed(self) -> None:
        """Create starter entities and relationships idempotently in FalkorDB."""
        if not self._connected or not self._graph:
            return
        try:
            for node in INITIAL_SEED_NODES:
                self.query(
                    "MERGE (n:Entity {id: $id}) "
                    "SET n.name=$name, n.kind=$kind, n.detail=$detail",
                    {"id": node["id"], "name": node["label"], "kind": node["kind"], "detail": node["detail"]},
                )
            for edge in INITIAL_SEED_EDGES:
                rel = "".join(ch for ch in edge["label"].upper() if ch.isalnum() or ch == "_")
                if not rel:
                    rel = "RELATED_TO"
                self.query(
                    f"MATCH (a:Entity {{id: $source}}), (b:Entity {{id: $target}}) "
                    f"MERGE (a)-[r:{rel}]->(b)",
                    {"source": edge["source"], "target": edge["target"]},
                )
        except Exception:
            pass

    def reset_graph(self) -> dict[str, Any]:
        """Reset the graph to the initial seed state."""
        self._demo_nodes = copy.deepcopy(INITIAL_SEED_NODES)
        self._demo_edges = copy.deepcopy(INITIAL_SEED_EDGES)
        self._demo_memories = copy.deepcopy(INITIAL_SEED_MEMORIES)
        self._demo_observations = {}

        if self.connected and self._graph:
            try:
                self.query("MATCH (n:Entity) DETACH DELETE n")
                self.seed()
            except Exception:
                pass
        return self.graph_data()

    def graph_data(self) -> dict[str, Any]:
        if self.connected:
            rows = self.query(
                "MATCH (n:Entity) RETURN n.id, n.name, n.kind, n.detail LIMIT 500"
            )
            nodes = [
                {"id": r[0], "label": r[1], "kind": r[2], "detail": r[3] or ""}
                for r in rows if len(r) >= 4
            ]
            rel_rows = self.query(
                "MATCH (a:Entity)-[r]->(b:Entity) RETURN a.id, b.id, type(r) LIMIT 1000"
            )
            edges = [
                {"source": r[0], "target": r[1], "label": r[2]}
                for r in rel_rows if len(r) >= 3
            ]
            if nodes:
                return {
                    "nodes": nodes,
                    "edges": edges,
                    "mode": "falkordb",
                    "stats": {"node_count": len(nodes), "edge_count": len(edges)},
                }

        # Standalone demo mode fallback
        return {
            "nodes": copy.deepcopy(self._demo_nodes),
            "edges": copy.deepcopy(self._demo_edges),
            "mode": "demo",
            "stats": {"node_count": len(self._demo_nodes), "edge_count": len(self._demo_edges)},
        }

    def get_all_nodes_with_history(self) -> list[dict[str, Any]]:
        """Return all nodes including bitemporal metadata and transition histories."""
        return copy.deepcopy(self._demo_nodes)

    def get_all_edges_with_history(self) -> list[dict[str, Any]]:
        """Return all edges including valid_from, valid_to, and recorded_at timestamps."""
        return copy.deepcopy(self._demo_edges)

    def update_entity_status(
        self,
        entity_id: str,
        new_status: str,
        changed_at: str,
        recorded_at: str,
        reason: str = "",
        changed_by: str = "",
    ) -> dict[str, Any]:
        """Update node status with bitemporal history tracking."""
        for n in self._demo_nodes:
            if n["id"] == entity_id:
                old_status = n.get("status", "unknown")
                n["status"] = new_status
                n["version"] = n.get("version", 1) + 1
                history_entry = {
                    "status": new_status,
                    "changed_at": changed_at,
                    "recorded_at": recorded_at,
                    "changed_by": changed_by,
                    "reason": reason,
                }
                if "status_history" not in n:
                    n["status_history"] = []
                n["status_history"].append(history_entry)

                if self.connected and self._graph:
                    try:
                        self.query(
                            "MATCH (n:Entity {id: $id}) "
                            "SET n.status=$status, n.version=$version",
                            {"id": entity_id, "status": new_status, "version": n["version"]},
                        )
                    except Exception:
                        pass
                return {"entity_id": entity_id, "old_status": old_status, "new_status": new_status}
        return {"entity_id": entity_id, "error": "Node not found"}

    def reassign_entity_owner(
        self,
        entity_id: str,
        new_owner_id: str,
        new_owner_name: str,
        assigned_at: str,
        recorded_at: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """Reassign entity ownership while preserving previous owner in historical records."""
        previous_owner = "Unassigned"
        for n in self._demo_nodes:
            if n["id"] == entity_id:
                owner_hist = n.setdefault("owner_history", [])
                if owner_hist:
                    previous_owner = owner_hist[-1].get("owner_name", owner_hist[-1].get("owner", "Unassigned"))

                owner_entry = {
                    "owner": new_owner_id,
                    "owner_name": new_owner_name,
                    "assigned_at": assigned_at,
                    "recorded_at": recorded_at,
                    "previous_owner": previous_owner,
                    "reason": reason,
                }
                owner_hist.append(owner_entry)
                n["version"] = n.get("version", 1) + 1

        # Invalidate old ASSIGNED_TO edges by setting valid_to = assigned_at
        for e in self._demo_edges:
            if e["source"] == entity_id and e["label"] == "ASSIGNED_TO" and e.get("valid_to") is None:
                e["valid_to"] = assigned_at

        # Add new ASSIGNED_TO edge
        new_edge = {
            "source": entity_id,
            "target": new_owner_id,
            "label": "ASSIGNED_TO",
            "valid_from": assigned_at,
            "valid_to": None,
            "recorded_at": recorded_at,
        }
        self._demo_edges.append(new_edge)

        if self.connected and self._graph:
            try:
                self.query(
                    "MATCH (a:Entity {id: $src})-[r:ASSIGNED_TO]->(b:Entity) "
                    "SET r.valid_to = $assigned_at",
                    {"src": entity_id, "assigned_at": assigned_at},
                )
                self.query(
                    "MATCH (a:Entity {{id: $src}}), (b:Entity {{id: $tgt}}) "
                    "MERGE (a)-[r:ASSIGNED_TO {{valid_from: $vfrom, recorded_at: $rec}}]->(b)",
                    {"src": entity_id, "tgt": new_owner_id, "vfrom": assigned_at, "rec": recorded_at},
                )
            except Exception:
                pass

        return {
            "entity_id": entity_id,
            "previous_owner": previous_owner,
            "new_owner_id": new_owner_id,
            "new_owner_name": new_owner_name,
            "assigned_at": assigned_at,
        }

    def add_edge_bitemporal(
        self,
        source_id: str,
        target_id: str,
        label: str,
        valid_from: str,
        recorded_at: str,
        valid_to: str | None = None,
    ) -> dict[str, Any]:
        """Add relationship with explicit bitemporal timestamps."""
        clean_rel = "".join(ch for ch in label.upper() if ch.isalnum() or ch == "_") or "RELATED_TO"
        edge = {
            "source": source_id,
            "target": target_id,
            "label": clean_rel,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "recorded_at": recorded_at,
        }
        self._demo_edges.append(edge)

        if self.connected and self._graph:
            try:
                self.query(
                    f"MATCH (a:Entity {{id: $source}}), (b:Entity {{id: $target}}) "
                    f"MERGE (a)-[r:{clean_rel} {{valid_from: $vfrom, recorded_at: $rec}}]->(b)",
                    {"source": source_id, "target": target_id, "vfrom": valid_from, "rec": recorded_at},
                )
            except Exception:
                pass
        return edge

    def add_entity(
        self,
        name: str,
        kind: str = "Entity",
        detail: str = "",
        related_to: str | None = None,
        relationship: str = "RELATED_TO",
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        """Add an entity and optional relationship."""
        clean_name = name.strip()
        clean_kind = kind.strip() or "Entity"
        clean_detail = detail.strip()
        if not entity_id:
            slug = clean_name.lower().replace(" ", "_").replace("-", "_")
            clean_slug = "".join(ch for ch in slug if ch.isalnum() or ch == "_")[:40]
            entity_id = f"{clean_kind.lower()}_{clean_slug}_{abs(hash(clean_name)) % 10000}"

        new_node = {
            "id": entity_id,
            "label": clean_name,
            "kind": clean_kind,
            "detail": clean_detail,
        }

        # Save to FalkorDB if connected
        if self.connected:
            self.query(
                "MERGE (n:Entity {id: $id}) SET n.name=$name, n.kind=$kind, n.detail=$detail",
                {"id": entity_id, "name": clean_name, "kind": clean_kind, "detail": clean_detail},
            )
            if related_to:
                clean_rel = "".join(ch for ch in relationship.upper() if ch.isalnum() or ch == "_") or "RELATED_TO"
                # Support matching related_to either by id or name
                self.query(
                    f"MATCH (a:Entity {{id: $id}}), (b:Entity) "
                    f"WHERE b.id = $target OR b.name = $target "
                    f"MERGE (a)-[:{clean_rel}]->(b)",
                    {"id": entity_id, "target": related_to},
                )

        # Always update in-memory state as well
        existing_idx = next((i for i, n in enumerate(self._demo_nodes) if n["id"] == entity_id), None)
        if existing_idx is not None:
            self._demo_nodes[existing_idx] = new_node
        else:
            self._demo_nodes.append(new_node)

        created_edge = None
        if related_to:
            clean_rel = "".join(ch for ch in relationship.upper() if ch.isalnum() or ch == "_") or "RELATED_TO"
            # Find target ID in demo nodes
            target_node = next((n for n in self._demo_nodes if n["id"] == related_to or n["label"].lower() == related_to.lower()), None)
            target_id = target_node["id"] if target_node else related_to
            created_edge = {"source": entity_id, "target": target_id, "label": clean_rel}
            if not any(e["source"] == entity_id and e["target"] == target_id and e["label"] == clean_rel for e in self._demo_edges):
                self._demo_edges.append(created_edge)

        return {
            "node": new_node,
            "edge": created_edge,
            "stored_in": "FalkorDB" if self.connected else "in-memory (demo mode)",
        }

    def delete_node(self, node_id: str) -> bool:
        """Delete an entity node and its edges."""
        if self.connected:
            self.query("MATCH (n:Entity {id: $id}) DETACH DELETE n", {"id": node_id})

        self._demo_nodes = [n for n in self._demo_nodes if n["id"] != node_id]
        self._demo_edges = [e for e in self._demo_edges if e["source"] != node_id and e["target"] != node_id]
        return True

    def add_edge(self, source_id: str, target_id: str, label: str = "RELATED_TO") -> dict[str, Any]:
        """Create a relationship between two nodes."""
        clean_rel = "".join(ch for ch in label.upper() if ch.isalnum() or ch == "_") or "RELATED_TO"
        edge = {"source": source_id, "target": target_id, "label": clean_rel}

        if self.connected:
            self.query(
                f"MATCH (a:Entity {{id: $source}}), (b:Entity {{id: $target}}) "
                f"MERGE (a)-[r:{clean_rel}]->(b)",
                {"source": source_id, "target": target_id},
            )

        if not any(e["source"] == source_id and e["target"] == target_id and e["label"] == clean_rel for e in self._demo_edges):
            self._demo_edges.append(edge)

        return edge

    def delete_edge(self, source_id: str, target_id: str, label: str) -> bool:
        """Delete an edge."""
        if self.connected:
            clean_rel = "".join(ch for ch in label.upper() if ch.isalnum() or ch == "_") or "RELATED_TO"
            self.query(
                f"MATCH (a:Entity {{id: $source}})-[r:{clean_rel}]->(b:Entity {{id: $target}}) "
                f"DELETE r",
                {"source": source_id, "target": target_id},
            )
        self._demo_edges = [
            e for e in self._demo_edges
            if not (e["source"] == source_id and e["target"] == target_id and e["label"] == label)
        ]
        return True

    def find_path(self, source_id: str, target_id: str) -> dict[str, Any]:
        """Find the shortest relationship path between two nodes."""
        data = self.graph_data()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        by_id = {n["id"]: n for n in nodes}

        if source_id not in by_id or target_id not in by_id:
            return {"found": False, "nodes": [], "edges": [], "path_string": "Node not found."}

        if source_id == target_id:
            return {"found": True, "nodes": [by_id[source_id]], "edges": [], "path_string": by_id[source_id]["label"]}

        # Cypher shortest path if connected
        if self.connected and self._graph:
            try:
                res = self.query(
                    "MATCH p = shortestPath((a:Entity {id: $src})-[*]-(b:Entity {id: $tgt})) "
                    "RETURN [n in nodes(p) | n.id], [r in relationships(p) | type(r)]",
                    {"src": source_id, "tgt": target_id},
                )
                if res and res[0] and len(res[0][0]) > 0:
                    node_ids = res[0][0]
                    rel_types = res[0][1] if len(res[0]) > 1 else []
                    path_nodes = [by_id[nid] for nid in node_ids if nid in by_id]
                    path_str = " -> ".join(n["label"] for n in path_nodes)
                    return {"found": True, "nodes": path_nodes, "edges": rel_types, "path_string": path_str}
            except Exception:
                pass

        # In-memory BFS
        from collections import deque
        adj: dict[str, list[tuple[str, str]]] = {n["id"]: [] for n in nodes}
        for e in edges:
            adj[e["source"]].append((e["target"], e["label"]))
            adj[e["target"]].append((e["source"], f"REV_{e['label']}"))

        queue = deque([(source_id, [source_id], [])])
        visited = {source_id}

        while queue:
            curr, p_nodes, p_edges = queue.popleft()
            if curr == target_id:
                path_nodes = [by_id[nid] for nid in p_nodes if nid in by_id]
                path_str = " -> ".join(n["label"] for n in path_nodes)
                return {"found": True, "nodes": path_nodes, "edges": p_edges, "path_string": path_str}

            for neighbor, rel in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, p_nodes + [neighbor], p_edges + [rel]))

        return {"found": False, "nodes": [], "edges": [], "path_string": "No path found."}

    def get_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
        nodes = self.graph_data().get("nodes", [])
        return next((n for n in nodes if n["id"] == entity_id), None)

    def find_hidden_connections(self, source_id: str, target_id: str, max_hops: int = 4) -> dict[str, Any]:
        """Bounded multi-hop exploration to discover indirect connections between entities.
        Returns path length, connecting entities, complete relationship path, and whether explicit or inferred.
        """
        data = self.graph_data()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        by_id = {n["id"]: n for n in nodes}

        if source_id not in by_id or target_id not in by_id:
            return {
                "found": False,
                "source": by_id.get(source_id),
                "target": by_id.get(target_id),
                "paths": [],
                "message": "Source or target entity not found in active graph."
            }

        # Build bidirectional adjacency
        adj: dict[str, list[tuple[str, str, str]]] = {n["id"]: [] for n in nodes}
        for e in edges:
            adj[e["source"]].append((e["target"], e["label"], "outgoing"))
            adj[e["target"]].append((e["source"], e["label"], "incoming"))

        # Find all simple paths up to max_hops (bounded BFS)
        from collections import deque
        found_paths = []
        queue = deque([(source_id, [source_id], [])])

        while queue and len(found_paths) < 6:
            curr, path_nodes, path_edges = queue.popleft()
            if len(path_nodes) - 1 >= max_hops:
                continue

            for neighbor, rel, direction in adj.get(curr, []):
                if neighbor == target_id:
                    new_nodes = path_nodes + [neighbor]
                    new_edges = path_edges + [{"source": curr, "target": neighbor, "label": rel, "direction": direction}]

                    hop_count = len(new_nodes) - 1
                    is_explicit = (hop_count == 1 and direction == "outgoing")

                    path_str_items = []
                    for i, nid in enumerate(new_nodes):
                        path_str_items.append(f"{by_id[nid]['label']} ({by_id[nid]['kind']})")
                        if i < len(new_edges):
                            ed = new_edges[i]
                            arrow = f"—[{ed['label']}]→" if ed['direction'] == 'outgoing' else f"←[{ed['label']}]—"
                            path_str_items.append(arrow)

                    docs_along_path = [by_id[nid]['label'] for nid in new_nodes if by_id[nid]['kind'] in ('Document', 'Decision')]

                    found_paths.append({
                        "hop_count": hop_count,
                        "is_explicit": is_explicit,
                        "connection_type": "Explicit Direct Dependency" if is_explicit else f"Inferred ({hop_count}-Hop Indirect Connection)",
                        "path_string": " ".join(path_str_items),
                        "intermediate_entities": [by_id[nid] for nid in new_nodes[1:-1]],
                        "all_nodes": [by_id[nid] for nid in new_nodes],
                        "edges": new_edges,
                        "source_evidence": docs_along_path,
                    })
                elif neighbor not in path_nodes and len(path_nodes) < max_hops:
                    new_nodes = path_nodes + [neighbor]
                    new_edges = path_edges + [{"source": curr, "target": neighbor, "label": rel, "direction": direction}]
                    queue.append((neighbor, new_nodes, new_edges))

        found_paths.sort(key=lambda p: p["hop_count"])

        return {
            "found": len(found_paths) > 0,
            "source": by_id[source_id],
            "target": by_id[target_id],
            "paths": found_paths,
            "path_count": len(found_paths),
            "shortest_hop_count": found_paths[0]["hop_count"] if found_paths else None,
            "bounded_max_hops": max_hops,
        }

    def discover_indirect_connections(self, entity_id: str, max_hops: int = 3, limit: int = 8) -> dict[str, Any]:
        """Discover hidden 2-hop and 3-hop connections for an entity that have no direct edge."""
        data = self.graph_data()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        by_id = {n["id"]: n for n in nodes}

        if entity_id not in by_id:
            return {"entity": None, "discoveries": []}

        direct_neighbors = {e["target"] for e in edges if e["source"] == entity_id} | \
                           {e["source"] for e in edges if e["target"] == entity_id}
        direct_neighbors.add(entity_id)

        adj: dict[str, list[tuple[str, str]]] = {n["id"]: [] for n in nodes}
        for e in edges:
            adj[e["source"]].append((e["target"], e["label"]))
            adj[e["target"]].append((e["source"], e["label"]))

        discoveries = []
        visited = set(direct_neighbors)
        from collections import deque
        queue = deque([(entity_id, 0, [entity_id])])

        while queue and len(discoveries) < limit:
            curr, depth, path = queue.popleft()
            if depth >= max_hops:
                continue

            for neighbor, rel in adj.get(curr, []):
                new_path = path + [neighbor]
                if neighbor not in direct_neighbors and neighbor not in visited:
                    visited.add(neighbor)
                    bridge_node = by_id[path[1]] if len(path) > 1 else by_id[curr]
                    discoveries.append({
                        "connected_entity": by_id[neighbor],
                        "hop_distance": depth + 1,
                        "bridge_entity": bridge_node,
                        "inference": f"Connected to {by_id[neighbor]['label']} via {bridge_node['label']} ({bridge_node['kind']}).",
                        "path": [by_id[nid]["label"] for nid in new_path],
                    })
                if neighbor not in path:
                    queue.append((neighbor, depth + 1, new_path))

        return {
            "entity": by_id[entity_id],
            "discoveries": discoveries,
            "total_discovered": len(discoveries),
        }

    def add_memory(
        self,
        text: str,
        session_id: str = "default",
        kind: str = "Context",
        approved: bool = True,
        source_context: str | None = None,
    ) -> dict[str, Any]:
        memory_id = f"mem_{int(time.time() * 1000) % 100000000}"
        now_str = "Just now"
        item = {
            "id": memory_id,
            "text": text,
            "kind": kind,
            "session_id": session_id,
            "approved": approved,
            "source_context": source_context,
            "created_at": now_str,
            "timestamp": int(time.time()),
        }

        if self.connected and self._graph:
            self.query(
                "MERGE (m:Memory {id: $id}) "
                "SET m.text=$text, m.kind=$kind, m.session_id=$session_id, "
                "m.approved=$approved, m.timestamp=$timestamp, m.source_context=$source_context",
                {
                    "id": memory_id,
                    "text": text,
                    "kind": kind,
                    "session_id": session_id,
                    "approved": approved,
                    "timestamp": item["timestamp"],
                    "source_context": source_context or "",
                },
            )
            self.query(
                "MATCH (m:Memory {id: $id}) MERGE (s:Session {id: $session_id}) "
                "MERGE (s)-[:REMEMBERS]->(m)",
                {"id": memory_id, "session_id": session_id},
            )
            if source_context:
                self.query(
                    "MATCH (m:Memory {id: $mid}), (e:Entity {id: $eid}) "
                    "MERGE (m)-[:REFERENCES]->(e)",
                    {"mid": memory_id, "eid": source_context},
                )

        # Always save in demo list for instant fallback access
        self._demo_memories.insert(0, item)
        return item

    def delete_memory(self, memory_id: str) -> bool:
        if self.connected and self._graph:
            self.query("MATCH (m:Memory {id: $id}) DETACH DELETE m", {"id": memory_id})
        self._demo_memories = [m for m in self._demo_memories if m["id"] != memory_id]
        return True

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        for m in self._demo_memories:
            if m["id"] == memory_id:
                return m
        return None

    def toggle_approve_memory(self, memory_id: str) -> dict[str, Any] | None:
        for m in self._demo_memories:
            if m["id"] == memory_id:
                m["approved"] = not m.get("approved", True)
                if self.connected and self._graph:
                    self.query(
                        "MATCH (m:Memory {id: $id}) SET m.approved=$app",
                        {"id": memory_id, "app": m["approved"]},
                    )
                return m
        return None

    def memories(self, session_id: str | None = None, approved_only: bool = False) -> list[dict[str, Any]]:
        if self.connected:
            cypher = (
                "MATCH (s:Session)-[:REMEMBERS]->(m:Memory) "
                + ("WHERE s.id = $session_id " if session_id else "")
                + ("AND m.approved = true " if approved_only and session_id else ("WHERE m.approved = true " if approved_only else ""))
                + "RETURN m.id, m.text, m.kind, m.session_id, m.timestamp, m.approved ORDER BY m.timestamp DESC LIMIT 50"
            )
            params = {"session_id": session_id} if session_id else {}
            rows = self.query(cypher, params)
            if rows:
                return [
                    {
                        "id": r[0],
                        "text": r[1],
                        "kind": r[2] if len(r) > 2 and r[2] else "Context",
                        "session_id": r[3] if len(r) > 3 else "default",
                        "approved": r[5] if len(r) > 5 else True,
                        "created_at": "Saved in FalkorDB",
                    }
                    for r in rows
                ]

        res = self._demo_memories
        if session_id:
            res = [m for m in res if m.get("session_id") == session_id]
        if approved_only:
            res = [m for m in res if m.get("approved", True)]
        return copy.deepcopy(res)

    # ---------------- Historical Observation Management ---------------- #

    @staticmethod
    def build_observation_id(country_code: str, indicator_code: str, year: int) -> str:
        """Deterministic composite primary key for an observation to prevent duplicate records."""
        clean_country = country_code.strip().upper()
        clean_indicator = "".join(ch if ch.isalnum() else "_" for ch in indicator_code.strip())
        return f"obs_{clean_country}_{clean_indicator}_{int(year)}"

    def store_observation(
        self,
        obs_data: dict[str, Any],
        country_id: str | None = None,
        indicator_id: str | None = None,
    ) -> dict[str, Any]:
        """Idempotently store or update a historical country-indicator observation.
        Prevents duplicate records by using a deterministic composite primary key.
        Preserves historical values, tracks data source, and maintains data integrity for missing values.
        """
        country_code = str(obs_data.get("country_code", "")).strip().upper()
        indicator_code = str(obs_data.get("indicator_code", "")).strip()
        year = int(obs_data["year"])
        obs_id = obs_data.get("id") or self.build_observation_id(country_code, indicator_code, year)

        raw_val = obs_data.get("value")
        if raw_val is not None:
            val: float | None = float(raw_val)
            is_missing = False
        else:
            val = None
            is_missing = True

        unit = str(obs_data.get("unit", "") or "")
        source = str(obs_data.get("source", "World Bank Indicators API") or "World Bank Indicators API")
        source_id = str(obs_data.get("source_id", "2") or "2")
        last_updated = str(obs_data.get("last_updated", "") or "")
        retrieved_at = str(obs_data.get("retrieved_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        country_name = str(obs_data.get("country_name", "") or "")
        indicator_name = str(obs_data.get("indicator_name", "") or "")

        # 1. Store/Update in in-memory collection
        existing = self._demo_observations.get(obs_id)
        if existing:
            # Update metadata and timestamps while preserving integrity
            existing["retrieved_at"] = retrieved_at
            if last_updated:
                existing["last_updated"] = last_updated
            if source:
                existing["source"] = source
            if source_id:
                existing["source_id"] = source_id
            if country_name and not existing.get("country_name"):
                existing["country_name"] = country_name
            if indicator_name and not existing.get("indicator_name"):
                existing["indicator_name"] = indicator_name
            if unit and not existing.get("unit"):
                existing["unit"] = unit

            # If incoming value is specified (even 0.0), update it
            if val is not None:
                existing["value"] = val
                existing["is_missing"] = False
            elif existing.get("value") is None and is_missing:
                existing["is_missing"] = True
                existing["value"] = None
            existing["version"] = existing.get("version", 1) + 1
            result_record = existing
            is_new = False
        else:
            result_record = {
                "id": obs_id,
                "country_code": country_code,
                "country_name": country_name,
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "year": year,
                "value": val,
                "is_missing": is_missing,
                "unit": unit,
                "source": source,
                "source_id": source_id,
                "last_updated": last_updated,
                "retrieved_at": retrieved_at,
                "version": 1,
            }
            self._demo_observations[obs_id] = result_record
            is_new = True

        # Sync with demo nodes/edges
        node_label = f"{country_code} {indicator_code} ({year})"
        val_str = f"{val} {unit}".strip() if val is not None else "MISSING"
        node_detail = f"Year: {year} | Value: {val_str} | Source: {source} (Retrieved: {retrieved_at})"
        existing_node = next((n for n in self._demo_nodes if n["id"] == obs_id), None)
        if existing_node:
            existing_node["detail"] = node_detail
            existing_node["version"] = result_record["version"]
        else:
            self._demo_nodes.append({
                "id": obs_id,
                "label": node_label,
                "kind": "Observation",
                "detail": node_detail,
                "status": "missing" if is_missing else "valid",
                "recorded_at": retrieved_at,
                "version": 1,
            })

        # Edges
        if country_id:
            c_target = next((n["id"] for n in self._demo_nodes if n["id"] == country_id or n.get("label") == country_id), country_id)
            if not any(e["source"] == c_target and e["target"] == obs_id and e["label"] == "RECORDED_OBSERVATION" for e in self._demo_edges):
                self._demo_edges.append({"source": c_target, "target": obs_id, "label": "RECORDED_OBSERVATION"})

        if indicator_id:
            i_target = next((n["id"] for n in self._demo_nodes if n["id"] == indicator_id or n.get("label") == indicator_id), indicator_id)
            if not any(e["source"] == obs_id and e["target"] == i_target and e["label"] == "MEASURES_INDICATOR" for e in self._demo_edges):
                self._demo_edges.append({"source": obs_id, "target": i_target, "label": "MEASURES_INDICATOR"})

        # 2. Persist in FalkorDB if connected
        if self.connected and self._graph:
            try:
                self.query(
                    "MERGE (o:Entity {id: $id}) "
                    "SET o.name=$name, o.kind='Observation', o.country_code=$cc, o.indicator_code=$ic, "
                    "o.year=$yr, o.value=$val, o.is_missing=$missing, o.unit=$unit, o.source=$src, "
                    "o.source_id=$src_id, o.last_updated=$last_up, o.retrieved_at=$ret_at, o.version=$ver",
                    {
                        "id": obs_id,
                        "name": node_label,
                        "cc": country_code,
                        "ic": indicator_code,
                        "yr": year,
                        "val": val,
                        "missing": is_missing,
                        "unit": unit,
                        "src": source,
                        "src_id": source_id,
                        "last_up": last_updated,
                        "ret_at": retrieved_at,
                        "ver": result_record["version"],
                    },
                )
                if country_id:
                    self.query(
                        "MATCH (c:Entity), (o:Entity {id: $id}) "
                        "WHERE c.id = $cid OR c.name = $cid "
                        "MERGE (c)-[:RECORDED_OBSERVATION]->(o)",
                        {"id": obs_id, "cid": country_id},
                    )
                if indicator_id:
                    self.query(
                        "MATCH (o:Entity {id: $id}), (i:Entity) "
                        "WHERE i.id = $iid OR i.name = $iid "
                        "MERGE (o)-[:MEASURES_INDICATOR]->(i)",
                        {"id": obs_id, "iid": indicator_id},
                    )
            except Exception:
                pass

        return {
            "observation": copy.deepcopy(result_record),
            "is_new": is_new,
            "id": obs_id,
        }

    def store_observations_batch(
        self,
        observations: list[dict[str, Any]],
        country_id: str | None = None,
        indicator_id: str | None = None,
    ) -> dict[str, Any]:
        """Batch store or update historical observations."""
        created_count = 0
        updated_count = 0
        stored_items = []

        for obs in observations:
            res = self.store_observation(obs, country_id=country_id, indicator_id=indicator_id)
            if res.get("is_new"):
                created_count += 1
            else:
                updated_count += 1
            stored_items.append(res.get("observation"))

        return {
            "total_processed": len(observations),
            "created": created_count,
            "updated": updated_count,
            "observations": stored_items,
        }

    def get_observations(
        self,
        country_code: str | None = None,
        indicator_code: str | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve historical observations filtered by country, indicator, and year window."""
        results = []
        cc_filter = country_code.strip().upper() if country_code else None
        ic_filter = indicator_code.strip().upper() if indicator_code else None

        for obs in self._demo_observations.values():
            if cc_filter and obs.get("country_code", "").upper() != cc_filter:
                continue
            if ic_filter and obs.get("indicator_code", "").upper() != ic_filter:
                continue
            obs_year = obs.get("year", 0)
            if start_year is not None and obs_year < start_year:
                continue
            if end_year is not None and obs_year > end_year:
                continue
            results.append(copy.deepcopy(obs))

        # Sort chronologically ascending
        results.sort(key=lambda x: (x.get("country_code", ""), x.get("indicator_code", ""), x.get("year", 0)))
        return results

    def count_observations(
        self,
        country_code: str | None = None,
        indicator_code: str | None = None,
    ) -> int:
        """Count total stored observations matching optional filters."""
        return len(self.get_observations(country_code=country_code, indicator_code=indicator_code))

