"""GlobalDataMind AI — Documented & Versioned Graph Schema.
Schema Version: 2.1.0 (Bitemporal & Real-Time Event Architecture)

Bitemporal Distinctions:
- Valid-Time (valid_from, valid_to): When a fact or relationship was true in the real-world organization.
- Recorded-Time (recorded_at / tx_time): When the GlobalDataMind AI system ingested or learned the fact.
"""
from __future__ import annotations

from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

SCHEMA_VERSION = "2.1.0"

class EntityKind(str, Enum):
    PERSON = "Person"
    TEAM = "Team"
    PROJECT = "Project"
    TASK = "Task"
    DOCUMENT = "Document"
    DECISION = "Decision"
    SERVICE = "Service"
    MEMORY = "Memory"
    SCENARIO = "Scenario"
    EVIDENCE = "Evidence"
    COUNTRY = "Country"
    INDICATOR = "Indicator"
    OBSERVATION = "Observation"
    ACADEMIC_RECORD = "AcademicRecord"
    PERSONAL_DATA = "PersonalData"


class VerificationStatus(str, Enum):
    PENDING = "Pending Verification"
    IN_PROGRESS = "Verification In Progress"
    VERIFIED = "Verified"
    FAILED = "Verification Failed"
    RE_VERIFICATION_REQUIRED = "Re-verification Required"


class RelationType(str, Enum):
    LEADS = "LEADS"
    MEMBER_OF = "MEMBER_OF"
    OWNS = "OWNS"
    BUILDS = "BUILDS"
    ASSIGNED_TO = "ASSIGNED_TO"
    PART_OF = "PART_OF"
    DEPENDS_ON = "DEPENDS_ON"
    POWERS = "POWERS"
    DOCUMENTED_IN = "DOCUMENTED_IN"
    AUTHORED = "AUTHORED"
    INFORMS = "INFORMS"
    DECIDED_BY = "DECIDED_BY"
    ENABLES = "ENABLES"
    EXPLAINS = "EXPLAINS"
    REFERENCES = "REFERENCES"
    REMEMBERS = "REMEMBERS"
    IMPACTS = "IMPACTS"
    MITIGATES = "MITIGATES"
    SUPERSEDES = "SUPERSEDES"
    HISTORICAL_ASSIGNED = "HISTORICAL_ASSIGNED"
    HAS_INDICATOR = "HAS_INDICATOR"
    BELONGS_TO_COUNTRY = "BELONGS_TO_COUNTRY"
    RECORDED_OBSERVATION = "RECORDED_OBSERVATION"
    MEASURES_INDICATOR = "MEASURES_INDICATOR"
    RECORDED_AS = "RECORDED_AS"
    HAS_ACADEMIC_RECORD = "HAS_ACADEMIC_RECORD"


# Allowed source and target entity pairings for schema validation
SCHEMA_ALLOWED_RELATIONS: dict[str, list[tuple[str, str]]] = {
    RelationType.LEADS.value: [("Person", "Team")],
    RelationType.MEMBER_OF.value: [("Person", "Team")],
    RelationType.OWNS.value: [("Team", "Project"), ("Team", "Service")],
    RelationType.BUILDS.value: [("Team", "Project"), ("Person", "Task"), ("Team", "Service")],
    RelationType.ASSIGNED_TO.value: [("Task", "Person")],
    RelationType.PART_OF.value: [("Task", "Project")],
    RelationType.DEPENDS_ON.value: [
        ("Project", "Project"),
        ("Project", "Service"),
        ("Service", "Service"),
        ("Task", "Task"),
        ("Project", "Decision"),
    ],
    RelationType.POWERS.value: [("Project", "Project"), ("Service", "Project"), ("Service", "Service")],
    RelationType.DOCUMENTED_IN.value: [
        ("Project", "Document"),
        ("Service", "Document"),
        ("Decision", "Document"),
        ("Team", "Document"),
    ],
    RelationType.AUTHORED.value: [("Person", "Document"), ("Person", "Decision")],
    RelationType.INFORMS.value: [("Document", "Project"), ("Document", "Decision")],
    RelationType.DECIDED_BY.value: [("Decision", "Person"), ("Decision", "Team")],
    RelationType.ENABLES.value: [("Decision", "Project"), ("Decision", "Service")],
    RelationType.EXPLAINS.value: [("Decision", "Project"), ("Decision", "Service"), ("Decision", "Task")],
    RelationType.REFERENCES.value: [("Memory", "Entity"), ("Evidence", "Entity")],
    RelationType.REMEMBERS.value: [("Session", "Memory")],
    RelationType.SUPERSEDES.value: [("Decision", "Decision"), ("Task", "Task")],
    RelationType.HISTORICAL_ASSIGNED.value: [("Task", "Person")],
    # New relations for GlobalDataMindAI
    RelationType.HAS_INDICATOR.value: [("Country", "Indicator")],
    RelationType.BELONGS_TO_COUNTRY.value: [("Indicator", "Country"), ("Observation", "Country")],
    RelationType.RECORDED_OBSERVATION.value: [("Country", "Observation")],
    RelationType.MEASURES_INDICATOR.value: [("Observation", "Indicator")],
    RelationType.RECORDED_AS.value: [("Person", "AcademicRecord")],
    RelationType.HAS_ACADEMIC_RECORD.value: [("PersonalData", "AcademicRecord")],
}


class StatusHistoryRecord(BaseModel):
    status: str
    changed_at: str  # Valid-time
    recorded_at: str  # Recorded-time
    changed_by: str = ""
    reason: str = ""


class OwnerHistoryRecord(BaseModel):
    owner: str  # Entity ID of owner
    owner_name: str
    assigned_at: str  # Valid-time
    recorded_at: str  # Recorded-time
    previous_owner: str = ""
    reason: str = ""


class NodeDefinition(BaseModel):
    id: str
    label: str
    kind: str
    detail: str = ""
    status: str = "active"
    valid_from: str = "2026-08-01T00:00:00Z"
    valid_to: str | None = None
    recorded_at: str = "2026-08-01T00:00:00Z"
    version: int = 1
    status_history: list[StatusHistoryRecord] = Field(default_factory=list)
    owner_history: list[OwnerHistoryRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EdgeDefinition(BaseModel):
    source: str
    target: str
    label: str
    valid_from: str = "2026-08-01T00:00:00Z"
    valid_to: str | None = None
    recorded_at: str = "2026-08-01T00:00:00Z"
    is_inferred: bool = False
    evidence: str = ""
    weight: float = 1.0


class DecisionRecord(BaseModel):
    id: str
    title: str
    rationale: str
    evidence: str = ""
    outcome: str = ""
    status: str = "approved"  # approved, pending, superseded, executed
    valid_from: str = ""
    valid_until: str | None = None
    decided_by: str = ""
    associated_entities: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    verified: bool = True
    created_at: str = ""
    recorded_at: str = ""
    timestamp: int = 0


class EventType(str, Enum):
    STATUS_CHANGED = "STATUS_CHANGED"
    OWNER_REASSIGNED = "OWNER_REASSIGNED"
    DEPENDENCY_ADDED = "DEPENDENCY_ADDED"
    DEPENDENCY_REMOVED = "DEPENDENCY_REMOVED"
    DEADLINE_UPDATED = "DEADLINE_UPDATED"
    SERVICE_OUTAGE = "SERVICE_OUTAGE"
    SERVICE_RESTORED = "SERVICE_RESTORED"
    DECISION_RECORDED = "DECISION_RECORDED"


class IngestionEvent(BaseModel):
    event_id: str
    event_type: EventType
    source: str = "system"  # e.g., github, jira, pagerduty, webhook
    timestamp: str  # Valid-time of the event
    entity_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 0


class ImpactAlert(BaseModel):
    id: str
    alert_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    summary: str
    target_entity: dict[str, Any]
    affected_entities: list[dict[str, Any]]
    dependency_path: list[str]
    action_plan: list[str]
    timestamp: str
    acknowledged: bool = False
    event_id: str = ""


def validate_relation(src_kind: str, rel_type: str, tgt_kind: str) -> bool:
    """Validate whether an edge complies with the versioned graph schema."""
    allowed = SCHEMA_ALLOWED_RELATIONS.get(rel_type.upper(), [])
    if not allowed:
        return True  # Permissive fallback for custom semantic edges
    return any(s == src_kind and t == tgt_kind for s, t in allowed) or (src_kind == "Entity" or tgt_kind == "Entity")


class VerificationRequestInput(BaseModel):
    notes: Optional[str] = Field(default="", max_length=500, description="Optional notes or context for verification")
    user_id: Optional[str] = Field(default="student_profile", description="Requesting candidate user ID")


class VerificationReviewInput(BaseModel):
    status: VerificationStatus = Field(description="New verification status")
    reviewer_role: str = Field(default="reviewer", description="Role of reviewer (admin, registrar, reviewer)")
    reviewer_name: str = Field(min_length=2, max_length=150, description="Name or identifier of reviewer")
    method: str = Field(default="AUTHORIZED_REVIEWER", description="Verification method: AUTHORITATIVE_SOURCE, AUTHORIZED_REVIEWER, INSTITUTION_REGISTRY, MANUAL_REVIEW_REQUIRED")
    source: str = Field(min_length=2, max_length=200, description="Verification source (e.g., CBSE Digital Portal, University Registrar)")
    reason: Optional[str] = Field(default="", max_length=500, description="Reason for failure or requirements if not verified")
    notes: Optional[str] = Field(default="", max_length=500, description="Additional audit or reviewer notes")


class DocumentAttachmentInput(BaseModel):
    name: str = Field(min_length=2, max_length=255, description="Document filename (e.g. Class_10_Marksheet.pdf)")
    checksum: Optional[str] = Field(default="", max_length=64, description="Cryptographic SHA-256 checksum for tamper evidence")
    document_id: Optional[str] = Field(default="", max_length=100, description="Optional referenced Document entity ID in knowledge graph")
    file_type: Optional[str] = Field(default="transcript", description="Document type: transcript, degree_certificate, marksheet, migration_cert")


VerificationRequestInput.model_rebuild()
VerificationReviewInput.model_rebuild()
DocumentAttachmentInput.model_rebuild()

# ---------------- Universal Timestamp & Temporal Schemas ---------------- #

class TemporalParseRequest(BaseModel):
    timestamp_input: Optional[Any] = Field(default=None, description="Raw date/time string, numeric epoch, or year integer to normalize")
    raw_val: Optional[Any] = Field(default=None, description="Alias for timestamp_input")
    source_name: Optional[str] = Field(default="api_request", description="Source or file identifier")
    source_created_at: Optional[Any] = Field(default=None, description="Optional raw timestamp of source document creation")
    source_created_raw: Optional[Any] = Field(default=None, description="Alias for source_created_at")
    verified_at: Optional[Any] = Field(default=None, description="Optional raw timestamp of verification completion")
    verified_raw: Optional[Any] = Field(default=None, description="Alias for verified_at")
    allow_inference: Optional[bool] = Field(default=False, description="Whether to allow documented inference if date is missing")


class TemporalIngestRequest(BaseModel):
    source_type: str = Field(default="JSON", description="Data format: JSON, CSV, LOG, DOCUMENT")
    content: Any = Field(description="Raw payload string, list, or JSON object")
    source_name: str = Field(default="uploaded_data", description="Source filename or origin identifier")


class TemporalAnalyzeRequest(BaseModel):
    records: Optional[list[dict[str, Any]]] = Field(default=None, description="Optional records to analyze. If omitted, analyzes existing graph entities.")
    start_time: Optional[str] = Field(default=None, description="UTC start bound ISO 8601")
    end_time: Optional[str] = Field(default=None, description="UTC end bound ISO 8601")
    precision: Optional[str] = Field(default=None, description="Filter by precision: year, month, day, second, millisecond")
    validation_status: Optional[str] = Field(default=None, description="Filter by status: VALID, MISSING, MALFORMED, CONFLICTING, IMPLAUSIBLE")
    requires_review_only: Optional[bool] = Field(default=False, description="Filter only records flagged for operator review")
    sort_order: Optional[str] = Field(default="asc", description="Chronological sorting: asc or desc")


class TemporalWindowCompareRequest(BaseModel):
    window_a_start: str = Field(description="UTC start bound for Window A")
    window_a_end: str = Field(description="UTC end bound for Window A")
    window_b_start: str = Field(description="UTC start bound for Window B")
    window_b_end: str = Field(description="UTC end bound for Window B")
    numeric_field: Optional[str] = Field(default=None, description="Optional numeric field in data to compare averages across windows")
    source_type: Optional[str] = Field(default=None, description="Optional filter by source type")


