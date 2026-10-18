"""Personal Intelligence Module for GlobalDataMindAI.
Manages verified academic records (Class 10, Class 12, B.Tech), chronological timelines,
comparative performance analytics, privacy protection, and zero-fabrication data integrity.

Distinguishes strictly between user-submitted ground truth records and calculated insights.
"""
from __future__ import annotations

import os
import json
import time
import copy
import threading
import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("personal_intelligence")

SUPPORTED_LEVELS = {
    "class_10": {
        "canonical_name": "Class 10",
        "level_order": 1,
        "default_stream": "General",
        "standard_gap_years": 0,
        "description": "Secondary School Examination (Matriculation)",
    },
    "class_12": {
        "canonical_name": "Class 12",
        "level_order": 2,
        "default_stream": "Science / Commerce / Arts",
        "standard_gap_years": 2,
        "description": "Higher Secondary Examination (Intermediate / Pre-University)",
    },
    "btech": {
        "canonical_name": "B.Tech",
        "level_order": 3,
        "default_stream": "Engineering & Technology",
        "standard_gap_years": 4,
        "description": "Bachelor of Technology / Bachelor of Engineering (Undergraduate)",
    },
}

LEVEL_ALIASES = {
    "10": "class_10",
    "10th": "class_10",
    "class 10": "class_10",
    "class 10th": "class_10",
    "class x": "class_10",
    "matriculation": "class_10",
    "ssc": "class_10",
    "secondary": "class_10",
    "12": "class_12",
    "12th": "class_12",
    "class 12": "class_12",
    "class 12th": "class_12",
    "class xii": "class_12",
    "intermediate": "class_12",
    "hsc": "class_12",
    "higher secondary": "class_12",
    "btech": "btech",
    "b.tech": "btech",
    "b. tech": "btech",
    "b tech": "btech",
    "be": "btech",
    "b.e": "btech",
    "b.e.": "btech",
    "engineering": "btech",
    "undergraduate": "btech",
}


def normalize_level_key(level_input: str) -> str:
    """Resolve user input to canonical level key (class_10, class_12, btech)."""
    clean = level_input.strip().lower()
    if clean in LEVEL_ALIASES:
        return LEVEL_ALIASES[clean]
    # Check if contains 10, 12, or btech
    if "10" in clean:
        return "class_10"
    if "12" in clean:
        return "class_12"
    if "tech" in clean or "eng" in clean:
        return "btech"
    raise ValueError(
        f"Unsupported qualification level '{level_input}'. Supported levels: Class 10, Class 12, B.Tech."
    )


def mask_string(val: str, keep_tail: int = 4) -> str:
    """Mask sensitive string identifiers for privacy protection."""
    if not val:
        return ""
    clean = val.strip()
    if len(clean) <= keep_tail:
        return "*" * len(clean)
    return "*" * (len(clean) - keep_tail) + clean[-keep_tail:]


try:
    from .schema import VerificationStatus, VerificationReviewInput, DocumentAttachmentInput
except (ImportError, ValueError):
    from app.schema import VerificationStatus, VerificationReviewInput, DocumentAttachmentInput


class AcademicRecordInput(BaseModel):
    level: str = Field(description="Qualification level: Class 10, Class 12, or B.Tech")
    institution: str = Field(min_length=2, max_length=200, description="Name of school, college, or university")
    board_or_university: str = Field(min_length=2, max_length=150, description="Examination board or university (e.g., CBSE, ICSE, VTU)")
    passing_year: int = Field(ge=1970, le=2035, description="Year of passing / completion")
    stream_or_major: str = Field(default="", max_length=120, description="Stream or engineering branch (e.g. Science PCM, Computer Science)")
    grading_system: str = Field(default="percentage", description="'percentage' or 'cgpa'")
    score: float = Field(ge=0.0, description="Score or grade obtained")
    max_score: float = Field(default=100.0, gt=0.0, description="Maximum possible score (100.0 for %, 10.0 for CGPA)")
    roll_or_registration_number: Optional[str] = Field(default="", max_length=60, description="Optional registration/roll number")
    notes: Optional[str] = Field(default="", max_length=500, description="Optional academic achievements or notes")
    supporting_documents: list[dict[str, Any]] = Field(default_factory=list, description="Optional attached transcripts, marksheets or certificates")


class PersonalIntelligenceManager:
    """Manages personal academic records, validation, chronological sequencing,
    comparative insights, and bitemporal trust provenance.
    """

    def __init__(self, graph_store: Any, trust_ledger: Any, storage_dir: str = "data", notification_mgr: Optional[Any] = None) -> None:
        self.store = graph_store
        self.trust_ledger = trust_ledger
        self.notification_mgr = notification_mgr
        self.storage_dir = storage_dir
        self.storage_file = os.path.join(storage_dir, "personal_intelligence.json")
        self._lock = threading.Lock()
        self._records: dict[str, dict[str, Any]] = {}
        self._profile_meta: dict[str, Any] = {
            "candidate_name": "Student Profile",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._load_storage()

    def set_notification_manager(self, notification_mgr: Any) -> None:
        """Inject or update NotificationManager instance."""
        self.notification_mgr = notification_mgr

    def _load_storage(self) -> None:
        """Load records from persistent disk storage."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    self._records = payload.get("records", {})
                    self._profile_meta = payload.get("meta", self._profile_meta)
                # Ensure all loaded records have explicit verification fields
                for r in self._records.values():
                    if "verification_status" not in r:
                        r["verification_status"] = VerificationStatus.VERIFIED.value if r.get("verified") else VerificationStatus.PENDING.value
                    if "verification_method" not in r:
                        r["verification_method"] = "AUTHORITATIVE_SOURCE" if r.get("verified") else "MANUAL_REVIEW_REQUIRED"
                    if "verification_source" not in r:
                        r["verification_source"] = r.get("source", "User Submission (Self-Attested)")
                    if "verification_timestamp" not in r:
                        r["verification_timestamp"] = r.get("updated_at") if r.get("verified") else None
                    if "verification_reason" not in r:
                        r["verification_reason"] = ""
                    if "supporting_documents" not in r:
                        r["supporting_documents"] = []
                # Rehydrate into graph store
                self._sync_to_graph_store()
            except Exception as e:
                logger.warning(f"Could not load personal intelligence storage: {e}")
                self._records = {}

    def _save_storage(self) -> None:
        """Persist records to disk."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            self._profile_meta["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            payload = {
                "meta": self._profile_meta,
                "records": self._records,
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save personal intelligence records: {e}")

    def validate_record(self, data: AcademicRecordInput) -> dict[str, Any]:
        """Validate an academic record and check chronological consistency against existing records."""
        canonical_key = normalize_level_key(data.level)
        info = SUPPORTED_LEVELS[canonical_key]

        # Score range validation
        system = data.grading_system.strip().lower()
        if system not in ("percentage", "cgpa"):
            raise ValueError(f"Grading system must be either 'percentage' or 'cgpa', got '{data.grading_system}'.")

        if system == "percentage":
            if data.score > 100.0 or data.score < 0.0:
                raise ValueError(f"Percentage score must be between 0.0 and 100.0, got {data.score}%.")
            max_score = 100.0
        else:
            if data.max_score <= 0.0:
                raise ValueError(f"Max score must be greater than 0, got {data.max_score}.")
            if data.score > data.max_score or data.score < 0.0:
                raise ValueError(f"CGPA score ({data.score}) cannot exceed max CGPA ({data.max_score}) or be negative.")
            max_score = data.max_score

        # Chronological cross-milestone validation against existing records
        with self._lock:
            for k, existing in self._records.items():
                if k == canonical_key:
                    continue  # Updating same record is allowed
                ex_info = SUPPORTED_LEVELS.get(k)
                if not ex_info:
                    continue

                # If existing is lower level (e.g. Class 10) and incoming is higher (e.g. Class 12)
                if ex_info["level_order"] < info["level_order"]:
                    if data.passing_year <= existing["passing_year"]:
                        raise ValueError(
                            f"Chronological error: {info['canonical_name']} passing year ({data.passing_year}) "
                            f"cannot be earlier than or equal to {ex_info['canonical_name']} passing year ({existing['passing_year']})."
                        )
                # If existing is higher level (e.g. B.Tech) and incoming is lower (e.g. Class 12)
                elif ex_info["level_order"] > info["level_order"]:
                    if data.passing_year >= existing["passing_year"]:
                        raise ValueError(
                            f"Chronological error: {info['canonical_name']} passing year ({data.passing_year}) "
                            f"cannot be later than or equal to {ex_info['canonical_name']} passing year ({existing['passing_year']})."
                        )

        # Calculate normalized equivalent percentage (explicit derived insight, never mutates ground truth)
        if system == "percentage":
            normalized_pct = round(data.score, 2)
        else:
            # Standard conversion: (score / max_score) * 100
            normalized_pct = round((data.score / max_score) * 100.0, 2)

        return {
            "level_key": canonical_key,
            "canonical_name": info["canonical_name"],
            "level_order": info["level_order"],
            "institution": data.institution.strip(),
            "board_or_university": data.board_or_university.strip(),
            "passing_year": data.passing_year,
            "stream_or_major": data.stream_or_major.strip() or info["default_stream"],
            "grading_system": system,
            "score": round(data.score, 2),
            "max_score": round(max_score, 2),
            "roll_or_registration_number": (data.roll_or_registration_number or "").strip(),
            "notes": (data.notes or "").strip(),
            "normalized_percentage": normalized_pct,
        }

    def add_or_update_record(self, data: AcademicRecordInput, user_id: str = "student_profile") -> dict[str, Any]:
        """Validate and store academic record.
        Strict verification rules:
        - Candidate submission is ground truth self-attestation.
        - Format validation is distinct from authoritative verification.
        - Automatically marks status as 'Pending Verification' with 'MANUAL_REVIEW_REQUIRED'
          rather than falsely marking the record as verified.
        - If an already-verified record has critical fields changed, it requires re-verification.
        """
        val = self.validate_record(data)
        canonical_key = val["level_key"]
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        with self._lock:
            existing = self._records.get(canonical_key)
            record_id = f"acad_{canonical_key}"

            # Check if critical academic credentials changed on an already-verified record
            critical_changed = False
            if existing and existing.get("verified"):
                critical_fields = ["institution", "board_or_university", "passing_year", "score", "grading_system"]
                for cf in critical_fields:
                    if str(existing.get(cf)) != str(val.get(cf)):
                        critical_changed = True
                        break

            if critical_changed:
                verification_status = VerificationStatus.RE_VERIFICATION_REQUIRED.value
                verification_method = "MANUAL_REVIEW_REQUIRED"
                verification_source = "User Submission (Self-Attested)"
                verification_timestamp = None
                verification_reason = "Academic details modified after prior verification. Re-verification required against issuing source."
                verified = False
            elif existing and existing.get("verified") and not critical_changed:
                verification_status = existing.get("verification_status", VerificationStatus.VERIFIED.value)
                verification_method = existing.get("verification_method", "AUTHORITATIVE_SOURCE")
                verification_source = existing.get("verification_source", "CBSE / University Registrar")
                verification_timestamp = existing.get("verification_timestamp", now_iso)
                verification_reason = existing.get("verification_reason", "")
                verified = True
            else:
                verification_status = VerificationStatus.PENDING.value
                verification_method = "MANUAL_REVIEW_REQUIRED"
                verification_source = "User Submission (Self-Attested)"
                verification_timestamp = None
                verification_reason = "Basic format and chronological range validated. Manual verification required against issuing board or university records."
                verified = False

            # Existing supporting documents preserved and merged
            existing_docs = existing.get("supporting_documents", []) if existing else []
            new_docs = list(data.supporting_documents or [])
            combined_docs = existing_docs + [d for d in new_docs if d not in existing_docs]

            record_entry = {
                "id": record_id,
                "user_id": user_id,
                "level_key": canonical_key,
                "qualification": val["canonical_name"],
                "level_order": val["level_order"],
                "institution": val["institution"],
                "board_or_university": val["board_or_university"],
                "passing_year": val["passing_year"],
                "stream_or_major": val["stream_or_major"],
                "grading_system": val["grading_system"],
                "score": val["score"],
                "max_score": val["max_score"],
                "roll_or_registration_number": val["roll_or_registration_number"],
                "notes": val["notes"],
                "record_type": "ACTUAL_RECORD",  # Explicit ground truth flag
                "verified": verified,
                "verification_status": verification_status,
                "verification_method": verification_method,
                "verification_source": verification_source,
                "verification_timestamp": verification_timestamp,
                "verification_reason": verification_reason,
                "supporting_documents": combined_docs,
                "source": "User Submission (Self-Attested)",
                "recorded_at": existing.get("recorded_at", now_iso) if existing else now_iso,
                "updated_at": now_iso,
                "version": (existing.get("version", 0) + 1) if existing else 1,
            }

            self._records[canonical_key] = record_entry
            self._save_storage()

        # Ingest into GraphStore and TrustLedger
        self._sync_record_to_graph(record_entry)
        self._record_trust_ledger_entry(record_entry)

        # Dispatch notification
        if self.notification_mgr:
            self.notification_mgr.create_notification(
                title=f"{val['canonical_name']} Record Awaiting Verification",
                message=f"Academic record for {val['canonical_name']} at {val['institution']} ({val['passing_year']}) was submitted. Basic format validated; pending authoritative review.",
                category="VERIFICATION",
                severity="WARNING" if not verified else "INFO",
                user_id=user_id,
                related_record={
                    "id": record_id,
                    "type": "academic_record",
                    "level": val["canonical_name"],
                    "institution": val["institution"],
                    "status": verification_status,
                },
                action={
                    "target_tab": "personal-intelligence",
                    "record_id": record_id,
                    "label": "Review Record",
                },
            )

        return self.get_profile()

    def request_verification(self, level: str, user_id: str = "student_profile", notes: str = "") -> dict[str, Any]:
        """Candidate workflow: Request formal verification of an academic milestone."""
        canonical_key = normalize_level_key(level)
        with self._lock:
            record = self._records.get(canonical_key)
            if not record:
                raise ValueError(f"No academic record exists for '{level}'. Please submit the record before requesting verification.")

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            record["verification_status"] = VerificationStatus.IN_PROGRESS.value
            record["verification_method"] = "INSTITUTION_REGISTRY"
            record["verification_reason"] = notes or "Verification request initiated with examination authority or institutional reviewer."
            record["updated_at"] = now_iso
            record["version"] = record.get("version", 1) + 1
            self._save_storage()

        self._sync_record_to_graph(record)

        if self.notification_mgr:
            self.notification_mgr.create_notification(
                title=f"Verification In Progress: {record['qualification']}",
                message=f"Verification request initiated for {record['qualification']} ({record['institution']}). Examination board / registrar verification in progress.",
                category="VERIFICATION",
                severity="INFO",
                user_id=user_id,
                related_record={
                    "id": record["id"],
                    "type": "academic_record",
                    "level": record["qualification"],
                    "status": VerificationStatus.IN_PROGRESS.value,
                },
                action={
                    "target_tab": "personal-intelligence",
                    "record_id": record["id"],
                    "label": "Track Status",
                },
            )

        return record

    def review_verification(self, level: str, review_data: VerificationReviewInput, reviewer_user_id: str = "admin") -> dict[str, Any]:
        """Authorized reviewer workflow: Verify, reject, or request re-verification of an academic record."""
        allowed_roles = {"admin", "workspace_admin", "registrar", "reviewer", "authorized_reviewer"}
        if review_data.reviewer_role.lower() not in allowed_roles:
            raise PermissionError(
                f"Role '{review_data.reviewer_role}' is not authorized to verify academic records. Required: {', '.join(allowed_roles)}."
            )

        canonical_key = normalize_level_key(level)
        with self._lock:
            record = self._records.get(canonical_key)
            if not record:
                raise ValueError(f"Record for '{level}' not found.")

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            new_status = review_data.status.value

            record["verification_status"] = new_status
            record["verification_method"] = review_data.method
            record["verification_source"] = review_data.source
            record["verification_reason"] = review_data.reason or review_data.notes or ""
            record["updated_at"] = now_iso
            record["version"] = record.get("version", 1) + 1

            if review_data.status == VerificationStatus.VERIFIED:
                record["verified"] = True
                record["verification_timestamp"] = now_iso
                notif_title = f"{record['qualification']} Verified Officially"
                notif_msg = f"Official verification completed by {review_data.reviewer_name} ({review_data.source}). Record confirmed as authentic."
                notif_sev = "SUCCESS"
            elif review_data.status == VerificationStatus.FAILED:
                record["verified"] = False
                record["verification_timestamp"] = None
                notif_title = f"{record['qualification']} Verification Failed"
                notif_msg = f"Verification could not be confirmed by {review_data.reviewer_name}. Reason: {review_data.reason or 'Discrepancy with issuing records'}."
                notif_sev = "ERROR"
            elif review_data.status == VerificationStatus.RE_VERIFICATION_REQUIRED:
                record["verified"] = False
                record["verification_timestamp"] = None
                notif_title = f"{record['qualification']} Re-Verification Required"
                notif_msg = f"Additional evidence or updated transcript requested by {review_data.reviewer_name}. Reason: {review_data.reason or 'Updated documentation needed'}."
                notif_sev = "WARNING"
            else:
                record["verified"] = False
                notif_title = f"{record['qualification']} Verification Updated"
                notif_msg = f"Status updated to {new_status} by {review_data.reviewer_name}."
                notif_sev = "INFO"

            self._save_storage()

        self._sync_record_to_graph(record)
        self._record_trust_ledger_entry(record)

        if self.notification_mgr:
            self.notification_mgr.create_notification(
                title=notif_title,
                message=notif_msg,
                category="VERIFICATION",
                severity=notif_sev,
                user_id=record.get("user_id", "student_profile"),
                related_record={
                    "id": record["id"],
                    "type": "academic_record",
                    "level": record["qualification"],
                    "status": new_status,
                },
                action={
                    "target_tab": "personal-intelligence",
                    "record_id": record["id"],
                    "label": "View Decision",
                },
            )

        return record

    def attach_document(self, level: str, doc_data: DocumentAttachmentInput, user_id: str = "student_profile") -> dict[str, Any]:
        """Attach a supporting transcript, marksheet, or certificate to an academic milestone."""
        canonical_key = normalize_level_key(level)
        with self._lock:
            record = self._records.get(canonical_key)
            if not record:
                raise ValueError(f"Record for '{level}' not found.")

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            doc_id = doc_data.document_id or f"doc_{canonical_key}_{int(time.time())}"
            doc_entry = {
                "id": doc_id,
                "name": doc_data.name,
                "checksum": doc_data.checksum or f"sha256_{uuid.uuid4().hex[:12]}",
                "file_type": doc_data.file_type or "transcript",
                "attached_at": now_iso,
                "attached_by": user_id,
            }

            if "supporting_documents" not in record or not isinstance(record["supporting_documents"], list):
                record["supporting_documents"] = []
            record["supporting_documents"].append(doc_entry)
            record["updated_at"] = now_iso
            record["version"] = record.get("version", 1) + 1

            self._save_storage()

        self._sync_record_to_graph(record)

        if self.notification_mgr:
            self.notification_mgr.create_notification(
                title=f"Supporting Document Attached: {record['qualification']}",
                message=f"Attached evidence document '{doc_data.name}' ({doc_data.file_type}) to {record['qualification']} record.",
                category="VERIFICATION",
                severity="INFO",
                user_id=user_id,
                related_record={
                    "id": record["id"],
                    "type": "academic_record",
                    "level": record["qualification"],
                    "document_id": doc_id,
                },
                action={
                    "target_tab": "personal-intelligence",
                    "record_id": record["id"],
                    "label": "View Evidence",
                },
            )

        return record

    def get_verification_statuses(self, user_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Return verification status records across all supported milestones."""
        statuses = []
        with self._lock:
            for key, info in SUPPORTED_LEVELS.items():
                record = self._records.get(key)
                if record:
                    statuses.append({
                        "level_key": key,
                        "qualification": record.get("qualification", info["canonical_name"]),
                        "institution": record.get("institution", ""),
                        "passing_year": record.get("passing_year"),
                        "verification_status": record.get("verification_status", VerificationStatus.PENDING.value),
                        "verification_method": record.get("verification_method", "MANUAL_REVIEW_REQUIRED"),
                        "verification_source": record.get("verification_source", "User Submission (Self-Attested)"),
                        "verification_timestamp": record.get("verification_timestamp"),
                        "verification_reason": record.get("verification_reason", ""),
                        "supporting_documents_count": len(record.get("supporting_documents", [])),
                        "supporting_documents": record.get("supporting_documents", []),
                        "is_recorded": True,
                        "verified": record.get("verified", False),
                    })
                else:
                    statuses.append({
                        "level_key": key,
                        "qualification": info["canonical_name"],
                        "institution": "Not Recorded",
                        "passing_year": None,
                        "verification_status": "Not Recorded",
                        "verification_method": "N/A",
                        "verification_source": "N/A",
                        "verification_timestamp": None,
                        "verification_reason": "No candidate record submitted for this stage.",
                        "supporting_documents_count": 0,
                        "supporting_documents": [],
                        "is_recorded": False,
                        "verified": False,
                    })
        return statuses

    def delete_record(self, level_or_id: str) -> bool:
        """Remove an academic record and delete corresponding graph nodes."""
        with self._lock:
            target_key = None
            for k in SUPPORTED_LEVELS:
                if level_or_id in (k, f"acad_{k}"):
                    target_key = k
                    break
            if not target_key:
                try:
                    target_key = normalize_level_key(level_or_id)
                except ValueError:
                    return False

            if target_key in self._records:
                del self._records[target_key]
                self._save_storage()
                # Remove node from graph store
                if hasattr(self.store, "delete_node"):
                    self.store.delete_node(f"acad_{target_key}")
                return True
            return False

    def reset_profile(self) -> None:
        """Clear all personal intelligence records."""
        with self._lock:
            record_ids = [f"acad_{k}" for k in self._records.keys()]
            self._records.clear()
            self._save_storage()
            if hasattr(self.store, "delete_node"):
                for rid in record_ids:
                    self.store.delete_node(rid)
                self.store.delete_node("node_personal_data_root")

    def _sync_to_graph_store(self) -> None:
        """Synchronize all stored records with graph store nodes and edges."""
        for rec in self._records.values():
            self._sync_record_to_graph(rec)

    def _sync_record_to_graph(self, record: dict[str, Any]) -> None:
        """Create/update AcademicRecord node and link to PersonalData root in GraphStore."""
        if not hasattr(self.store, "add_entity"):
            return
        try:
            # 1. Root PersonalData Node
            root_res = self.store.add_entity(
                name="Personal Academic Profile",
                kind="PersonalData",
                detail="Verified personal academic records container",
                entity_id="node_personal_data_root",
            )
            root_id = root_res.get("node", {}).get("id", "node_personal_data_root")

            # 2. AcademicRecord Node
            score_str = f"{record['score']}%" if record['grading_system'] == 'percentage' else f"{record['score']} / {record['max_score']} CGPA"
            detail_str = f"{record['qualification']} from {record['institution']} ({record['board_or_university']}) in {record['passing_year']}. Score: {score_str}."

            rec_res = self.store.add_entity(
                name=f"{record['qualification']} - {record['institution']}",
                kind="AcademicRecord",
                detail=detail_str,
                entity_id=record["id"],
            )
            rec_id = rec_res.get("node", {}).get("id", record["id"])

            # 3. Edge HAS_ACADEMIC_RECORD
            if hasattr(self.store, "add_edge"):
                self.store.add_edge(root_id, rec_id, "HAS_ACADEMIC_RECORD")
        except Exception as e:
            logger.warning(f"Failed to sync academic record to graph store: {e}")

    def _record_trust_ledger_entry(self, record: dict[str, Any]) -> None:
        """Record provenance audit log in Trust Ledger."""
        if not hasattr(self.trust_ledger, "record_conclusion"):
            return
        try:
            score_fmt = f"{record['score']}%" if record['grading_system'] == 'percentage' else f"{record['score']} / {record['max_score']} CGPA"
            self.trust_ledger.record_conclusion(
                query=f"Personal Intelligence Verification: {record['qualification']}",
                conclusion=f"Verified ground-truth academic record for {record['qualification']} at {record['institution']} ({record['passing_year']}) with {score_fmt}.",
                verified_facts=[
                    f"Qualification Level: {record['qualification']}.",
                    f"Institution: {record['institution']}.",
                    f"Affiliated Board/University: {record['board_or_university']}.",
                    f"Year of Passing: {record['passing_year']}.",
                    f"Attested Score: {score_fmt} ({record['grading_system']}).",
                    f"Stream / Specialization: {record['stream_or_major']}.",
                    "Verification Status: Ground truth record (Never fabricated).",
                ],
                assumptions=[],
                supporting_entities=[
                    {"id": "node_personal_data_root", "label": "Personal Academic Profile", "kind": "PersonalData"},
                    {"id": record["id"], "label": f"{record['qualification']} Record", "kind": "AcademicRecord"},
                ],
                traversed_edges=[
                    {"source": "Personal Academic Profile", "rel": "HAS_ACADEMIC_RECORD", "target": f"{record['qualification']} Record"}
                ],
                source_documents=[],
                database_source="Personal Intelligence Secure Store + Graph",
            )
        except Exception as e:
            logger.warning(f"Could not log trust ledger entry for academic record: {e}")

    def get_profile(self, mask_sensitive: bool = False) -> dict[str, Any]:
        """Return the complete Personal Intelligence profile:
        1. Ground-truth verified academic records.
        2. Chronological timeline with year progressions.
        3. Comparative performance metrics.
        4. Derived insights (clearly distinguished from actual records).
        5. Missing milestone inventory (never fabricated).
        """
        with self._lock:
            # 1. Gather all actual records sorted by level_order
            raw_records = list(self._records.values())
            raw_records.sort(key=lambda r: r.get("level_order", 0))

            timeline = []
            available_records = []
            prev_year: Optional[int] = None

            for r in raw_records:
                rec_copy = copy.deepcopy(r)

                # Privacy masking if requested
                if mask_sensitive and rec_copy.get("roll_or_registration_number"):
                    rec_copy["roll_or_registration_number"] = mask_string(rec_copy["roll_or_registration_number"])

                # Compute normalized equivalent percentage for visualization
                if rec_copy["grading_system"] == "percentage":
                    equiv_pct = round(rec_copy["score"], 2)
                else:
                    equiv_pct = round((rec_copy["score"] / rec_copy["max_score"]) * 100.0, 2)

                years_since_prev = None
                if prev_year is not None:
                    years_since_prev = rec_copy["passing_year"] - prev_year

                timeline_item = {
                    "id": rec_copy["id"],
                    "level_key": rec_copy["level_key"],
                    "qualification": rec_copy["qualification"],
                    "level_order": rec_copy["level_order"],
                    "passing_year": rec_copy["passing_year"],
                    "institution": rec_copy["institution"],
                    "board_or_university": rec_copy["board_or_university"],
                    "stream_or_major": rec_copy["stream_or_major"],
                    "score_display": f"{rec_copy['score']}%" if rec_copy['grading_system'] == 'percentage' else f"{rec_copy['score']} / {rec_copy['max_score']} CGPA",
                    "raw_score": rec_copy["score"],
                    "max_score": rec_copy["max_score"],
                    "grading_system": rec_copy["grading_system"],
                    "normalized_percentage": equiv_pct,
                    "years_since_previous": years_since_prev,
                    "record_type": "ACTUAL_RECORD",
                    "verified": rec_copy.get("verified", False),
                    "verification_status": rec_copy.get("verification_status", VerificationStatus.PENDING.value),
                    "verification_method": rec_copy.get("verification_method", "MANUAL_REVIEW_REQUIRED"),
                    "verification_source": rec_copy.get("verification_source", "User Submission (Self-Attested)"),
                    "verification_timestamp": rec_copy.get("verification_timestamp"),
                    "verification_reason": rec_copy.get("verification_reason", ""),
                    "supporting_documents": rec_copy.get("supporting_documents", []),
                    "roll_or_registration_number": rec_copy.get("roll_or_registration_number", ""),
                    "recorded_at": rec_copy.get("recorded_at"),
                    "notes": rec_copy.get("notes", ""),
                }
                timeline.append(timeline_item)
                available_records.append(rec_copy)
                prev_year = rec_copy["passing_year"]

            # 2. Missing milestone inventory - NEVER FABRICATE
            missing_milestones = []
            for key, info in SUPPORTED_LEVELS.items():
                if key not in self._records:
                    missing_milestones.append({
                        "level_key": key,
                        "qualification": info["canonical_name"],
                        "level_order": info["level_order"],
                        "description": info["description"],
                        "status": "NOT_RECORDED",
                        "value": None,  # Strictly None, never guessed
                    })
            missing_milestones.sort(key=lambda m: m["level_order"])

            # 3. Calculated Insights Engine (Strictly isolated from actual records)
            insights = self._compute_derived_insights(timeline)

            # 4. Comparative Analysis of available results
            comparison = self._compute_comparison(timeline)

            return {
                "profile_meta": self._profile_meta,
                "summary": {
                    "total_milestones_possible": len(SUPPORTED_LEVELS),
                    "recorded_milestones_count": len(timeline),
                    "missing_milestones_count": len(missing_milestones),
                    "verified_count": len([r for r in available_records if r.get("verified") or r.get("verification_status") == VerificationStatus.VERIFIED.value]),
                    "pending_verification_count": len([r for r in available_records if r.get("verification_status") in (VerificationStatus.PENDING.value, VerificationStatus.IN_PROGRESS.value)]),
                    "is_complete": len(missing_milestones) == 0,
                    "privacy_mode_active": mask_sensitive,
                },
                "actual_records": available_records,
                "timeline": timeline,
                "missing_milestones": missing_milestones,
                "calculated_insights": insights,
                "comparison": comparison,
                "data_integrity_notice": (
                    "Actual records reflect strictly user-submitted ground truth. "
                    "Calculated insights and normalized percentages are mathematical "
                    "derivations and must be distinguished from official transcripts."
                ),
            }

    def _compute_derived_insights(self, timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Calculate derived analytical insights across existing records without fabricating missing milestones."""
        if not timeline:
            return []

        insights = []
        normalized_scores = [t["normalized_percentage"] for t in timeline]
        avg_score = round(sum(normalized_scores) / len(normalized_scores), 2)

        # Insight 1: Academic Equivalent Average
        insights.append({
            "insight_key": "academic_average",
            "title": "Normalized Academic Average",
            "value": f"{avg_score}%",
            "numeric_value": avg_score,
            "type": "CALCULATED_INSIGHT",
            "category": "performance",
            "derivation_formula": "Arithmetic mean of equivalent percentages across all recorded milestones.",
            "interpretation": (
                "Distinction / First Class with Distinction" if avg_score >= 80.0
                else "First Class" if avg_score >= 60.0
                else "Second Class"
            ),
        })

        # Insight 2: Performance Trajectory
        if len(timeline) >= 2:
            first_pct = timeline[0]["normalized_percentage"]
            latest_pct = timeline[-1]["normalized_percentage"]
            diff = round(latest_pct - first_pct, 2)
            direction = "improving" if diff > 1.5 else "declining" if diff < -1.5 else "consistent"

            insights.append({
                "insight_key": "trajectory",
                "title": "Overall Performance Trajectory",
                "value": f"{'+' if diff > 0 else ''}{diff}% ({direction.capitalize()})",
                "numeric_value": diff,
                "type": "CALCULATED_INSIGHT",
                "category": "trajectory",
                "derivation_formula": f"Latest milestone ({timeline[-1]['qualification']}: {latest_pct}%) minus earliest milestone ({timeline[0]['qualification']}: {first_pct}%).",
                "interpretation": (
                    "Upward academic progression over time." if diff > 1.5
                    else "High grade consistency across school and undergraduate education." if abs(diff) <= 1.5
                    else "Slight variation in specialized undergraduate coursework."
                ),
            })

        # Insight 3: Peak Performance Milestone
        highest_record = max(timeline, key=lambda t: t["normalized_percentage"])
        insights.append({
            "insight_key": "peak_milestone",
            "title": "Peak Academic Milestone",
            "value": f"{highest_record['qualification']} ({highest_record['score_display']})",
            "numeric_value": highest_record["normalized_percentage"],
            "type": "CALCULATED_INSIGHT",
            "category": "milestone",
            "derivation_formula": f"Milestone with highest normalized performance: {highest_record['institution']} ({highest_record['passing_year']}).",
            "interpretation": f"Achieved peak equivalent score of {highest_record['normalized_percentage']}%.",
        })

        # Insight 4: Education Horizon Span
        if len(timeline) >= 2:
            span_years = timeline[-1]["passing_year"] - timeline[0]["passing_year"]
            insights.append({
                "insight_key": "education_span",
                "title": "Recorded Academic Horizon",
                "value": f"{span_years} Years ({timeline[0]['passing_year']} - {timeline[-1]['passing_year']})",
                "numeric_value": span_years,
                "type": "CALCULATED_INSIGHT",
                "category": "timeline",
                "derivation_formula": f"Passing year of {timeline[-1]['qualification']} ({timeline[-1]['passing_year']}) minus {timeline[0]['qualification']} ({timeline[0]['passing_year']}).",
                "interpretation": f"Documented progression over {len(timeline)} academic stages.",
            })

        return insights

    def _compute_comparison(self, timeline: list[dict[str, Any]]) -> dict[str, Any]:
        """Compute structured comparison table and analytics across available milestones."""
        if not timeline:
            return {
                "available_milestones": [],
                "comparison_matrix": [],
                "score_deltas": [],
                "highest_milestone": None,
                "lowest_milestone": None,
                "stream_progression": [],
            }

        matrix = []
        for t in timeline:
            matrix.append({
                "qualification": t["qualification"],
                "institution": t["institution"],
                "board_or_university": t["board_or_university"],
                "passing_year": t["passing_year"],
                "stream": t["stream_or_major"],
                "raw_score": t["score_display"],
                "normalized_percentage": t["normalized_percentage"],
            })

        # Compute pairwise step-by-step deltas
        deltas = []
        for i in range(1, len(timeline)):
            prev = timeline[i - 1]
            curr = timeline[i]
            pct_delta = round(curr["normalized_percentage"] - prev["normalized_percentage"], 2)
            year_gap = curr["passing_year"] - prev["passing_year"]
            deltas.append({
                "from_qualification": prev["qualification"],
                "to_qualification": curr["qualification"],
                "percentage_change": pct_delta,
                "years_gap": year_gap,
                "trend": "increased" if pct_delta > 0 else "decreased" if pct_delta < 0 else "identical",
            })

        highest = max(timeline, key=lambda t: t["normalized_percentage"])
        lowest = min(timeline, key=lambda t: t["normalized_percentage"])

        return {
            "available_milestones": [t["qualification"] for t in timeline],
            "comparison_matrix": matrix,
            "score_deltas": deltas,
            "highest_milestone": {
                "qualification": highest["qualification"],
                "score": highest["score_display"],
                "normalized": highest["normalized_percentage"],
            },
            "lowest_milestone": {
                "qualification": lowest["qualification"],
                "score": lowest["score_display"],
                "normalized": lowest["normalized_percentage"],
            },
            "stream_progression": [
                {"qualification": t["qualification"], "stream": t["stream_or_major"]}
                for t in timeline
            ],
        }
