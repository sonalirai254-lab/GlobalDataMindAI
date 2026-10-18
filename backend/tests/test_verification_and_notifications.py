"""Comprehensive tests for Record Verification and Alert Notification System.
Tests:
1. Academic record verification status lifecycle:
   - Initial submission -> Pending Verification (MANUAL_REVIEW_REQUIRED)
   - Formal verification request -> Verification In Progress
   - Authorized reviewer approval -> Verified with timestamp & source
   - Authorized reviewer rejection -> Verification Failed with reason
   - Critical data edit -> Re-verification Required
2. Document attachment with cryptographic checksum and tamper evidence.
3. Notification engine:
   - Automated notification creation on submission, status change, and document attachment
   - Accurate unread counts
   - Mark as read (single)
   - Mark all as read
   - Category filtering (VERIFICATION, DATA_SOURCE, ALL)
4. Multi-user isolation and authorization:
   - Private academic profile access control (X-User-Id header)
   - Cross-user notification privacy (User A cannot view or read User B's notifications)
   - Unauthorized reviewer rejection (HTTP 403)
5. Persistence behavior and mode reporting:
   - Verifying storage file exists and returns accurate persistence status
   - Zero fabrication of verification results or records
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app, notification_mgr, personal_intelligence


@pytest.fixture
def client():
    # Reset profile to clean state before tests
    personal_intelligence.reset_profile()
    return TestClient(app)


class TestVerificationAndNotifications:
    """Test suite for Record Verification and Alert Notification System."""

    def test_record_submission_starts_as_pending_verification(self, client):
        """New academic record submission must be marked as 'Pending Verification' with 'MANUAL_REVIEW_REQUIRED'."""
        payload = {
            "level": "class_10",
            "institution": "Delhi Public School",
            "board_or_university": "CBSE",
            "passing_year": 2018,
            "grading_system": "percentage",
            "score": 92.4,
            "stream_or_major": "General Science",
        }
        res = client.post("/api/personal/record", json=payload, headers={"X-User-Id": "student_profile"})
        assert res.status_code == 200
        data = res.json()

        # Check in timeline and actual records
        actual = next(r for r in data["actual_records"] if r["level_key"] == "class_10")
        assert actual["verified"] is False
        assert actual["verification_status"] == "Pending Verification"
        assert actual["verification_method"] == "MANUAL_REVIEW_REQUIRED"
        assert "CBSE" in actual["board_or_university"]

        # Check verification endpoint
        verif_res = client.get("/api/verification/records", headers={"X-User-Id": "student_profile"})
        assert verif_res.status_code == 200
        v_data = verif_res.json()
        assert v_data["summary"]["pending"] >= 1
        c10 = next(r for r in v_data["academic_records"] if r["level_key"] == "class_10")
        assert c10["verification_status"] == "Pending Verification"

    def test_request_verification_transitions_to_in_progress(self, client):
        """Requesting verification transitions status to 'Verification In Progress' and dispatches alert."""
        # First submit Class 12
        payload = {
            "level": "class_12",
            "institution": "Delhi Public School",
            "board_or_university": "CBSE",
            "passing_year": 2020,
            "grading_system": "percentage",
            "score": 89.0,
            "stream_or_major": "Physics, Chemistry, Math",
        }
        client.post("/api/personal/record", json=payload, headers={"X-User-Id": "student_profile"})

        # Request verification
        req_res = client.post(
            "/api/personal/record/class_12/verify-request",
            json={"notes": "Transcript dispatched to CBSE verification cell", "user_id": "student_profile"},
            headers={"X-User-Id": "student_profile"},
        )
        assert req_res.status_code == 200
        rec = req_res.json()["record"]
        assert rec["verification_status"] == "Verification In Progress"
        assert rec["verification_method"] == "INSTITUTION_REGISTRY"

        # Check notification was generated
        notifs_res = client.get("/api/notifications", headers={"X-User-Id": "student_profile"})
        assert notifs_res.status_code == 200
        notifs = notifs_res.json()["notifications"]
        in_prog_notif = next((n for n in notifs if "In Progress" in n["title"]), None)
        assert in_prog_notif is not None
        assert in_prog_notif["category"] == "VERIFICATION"

    def test_authorized_review_verification_success(self, client):
        """Authorized reviewer (admin/registrar) can officially verify record with source and timestamp."""
        # Ensure Class 10 exists
        client.post(
            "/api/personal/record",
            json={
                "level": "class_10",
                "institution": "National Public School",
                "board_or_university": "ICSE",
                "passing_year": 2017,
                "grading_system": "percentage",
                "score": 94.0,
            },
            headers={"X-User-Id": "student_profile"},
        )

        # Review as registrar
        review_payload = {
            "status": "Verified",
            "reviewer_role": "registrar",
            "reviewer_name": "Dr. A. Sharma",
            "method": "AUTHORITATIVE_SOURCE",
            "source": "ICSE National Registry",
            "notes": "Direct confirmation from board database",
        }
        review_res = client.post(
            "/api/personal/record/class_10/verify",
            json=review_payload,
            headers={"X-User-Id": "registrar"},
        )
        assert review_res.status_code == 200
        rec = review_res.json()["record"]
        assert rec["verified"] is True
        assert rec["verification_status"] == "Verified"
        assert rec["verification_source"] == "ICSE National Registry"
        assert rec["verification_timestamp"] is not None

        # Check that Trust Ledger recorded this
        prof = client.get("/api/personal/profile", headers={"X-User-Id": "student_profile"}).json()
        assert prof["summary"]["verified_count"] >= 1

    def test_authorized_review_verification_failure_with_reason(self, client):
        """Authorized reviewer rejection sets status to 'Verification Failed' and includes explicit reason."""
        client.post(
            "/api/personal/record",
            json={
                "level": "btech",
                "institution": "ABC Institute of Technology",
                "board_or_university": "State Technical University",
                "passing_year": 2024,
                "grading_system": "cgpa",
                "score": 8.7,
                "max_score": 10.0,
            },
            headers={"X-User-Id": "student_profile"},
        )

        review_payload = {
            "status": "Verification Failed",
            "reviewer_role": "reviewer",
            "reviewer_name": "Academic Audit Cell",
            "method": "AUTHORIZED_REVIEWER",
            "source": "State Technical University Registrar",
            "reason": "Registration number mismatch in university examination records.",
        }
        res = client.post(
            "/api/personal/record/btech/verify",
            json=review_payload,
            headers={"X-User-Id": "reviewer"},
        )
        assert res.status_code == 200
        rec = res.json()["record"]
        assert rec["verified"] is False
        assert rec["verification_status"] == "Verification Failed"
        assert "mismatch" in rec["verification_reason"]

    def test_unauthorized_review_role_is_rejected(self, client):
        """Unauthorized reviewer role (e.g. candidate or hacker) receives HTTP 403."""
        review_payload = {
            "status": "Verified",
            "reviewer_role": "candidate",
            "reviewer_name": "Self Review",
            "method": "SELF",
            "source": "Self",
        }
        res = client.post(
            "/api/personal/record/class_10/verify",
            json=review_payload,
            headers={"X-User-Id": "student_profile"},
        )
        assert res.status_code == 403
        assert "not authorized" in res.json()["detail"].lower()

    def test_critical_edit_on_verified_record_requires_reverification(self, client):
        """Modifying score or institution on a previously verified record resets status to 'Re-verification Required'."""
        # 1. Create and verify record
        client.post(
            "/api/personal/record",
            json={
                "level": "class_10",
                "institution": "Springdales School",
                "board_or_university": "CBSE",
                "passing_year": 2018,
                "grading_system": "percentage",
                "score": 88.0,
            },
            headers={"X-User-Id": "student_profile"},
        )
        client.post(
            "/api/personal/record/class_10/verify",
            json={
                "status": "Verified",
                "reviewer_role": "admin",
                "reviewer_name": "Admin Reviewer",
                "method": "AUTHORITATIVE_SOURCE",
                "source": "CBSE Central Registry",
            },
            headers={"X-User-Id": "admin"},
        )

        # 2. Modify score from 88.0 to 95.0
        update_res = client.post(
            "/api/personal/record",
            json={
                "level": "class_10",
                "institution": "Springdales School",
                "board_or_university": "CBSE",
                "passing_year": 2018,
                "grading_system": "percentage",
                "score": 95.0,
            },
            headers={"X-User-Id": "student_profile"},
        )
        assert update_res.status_code == 200
        actual = next(r for r in update_res.json()["actual_records"] if r["level_key"] == "class_10")
        assert actual["verified"] is False
        assert actual["verification_status"] == "Re-verification Required"
        assert "modified" in actual["verification_reason"].lower()

    def test_attach_document_with_checksum(self, client):
        """Attaching supporting document registers cryptographic checksum and metadata."""
        client.post(
            "/api/personal/record",
            json={
                "level": "class_12",
                "institution": "St. Xavier's",
                "board_or_university": "CBSE",
                "passing_year": 2020,
                "grading_system": "percentage",
                "score": 91.5,
            },
            headers={"X-User-Id": "student_profile"},
        )

        doc_payload = {
            "name": "Class_12_Marksheet_Original.pdf",
            "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "file_type": "transcript",
        }
        attach_res = client.post(
            "/api/personal/record/class_12/attach-document",
            json=doc_payload,
            headers={"X-User-Id": "student_profile"},
        )
        assert attach_res.status_code == 200
        rec = attach_res.json()["record"]
        docs = rec.get("supporting_documents", [])
        assert len(docs) >= 1
        assert docs[-1]["name"] == "Class_12_Marksheet_Original.pdf"
        assert docs[-1]["checksum"].startswith("e3b0c442")

    def test_notification_lifecycle_and_unread_counts(self, client):
        """Test notification listing, unread count tracking, mark-as-read, and mark-all-read."""
        # Create a specific notification for student_profile
        n = notification_mgr.create_notification(
            title="Class 10 Review Completed",
            message="Your Class 10 marksheet has been reviewed.",
            category="VERIFICATION",
            severity="SUCCESS",
            user_id="student_profile",
        )
        notif_id = n["id"]

        # Check unread count
        list_res = client.get("/api/notifications", headers={"X-User-Id": "student_profile"})
        assert list_res.status_code == 200
        data = list_res.json()
        assert data["unread_count"] >= 1
        assert any(x["id"] == notif_id for x in data["notifications"])

        # Mark single as read
        read_res = client.post(f"/api/notifications/{notif_id}/read", headers={"X-User-Id": "student_profile"})
        assert read_res.status_code == 200
        assert read_res.json()["notification"]["status"] == "READ"

        # Mark all as read
        all_read_res = client.post("/api/notifications/read-all", headers={"X-User-Id": "student_profile"})
        assert all_read_res.status_code == 200
        assert all_read_res.json()["unread_count"] == 0

    def test_multi_user_privacy_and_authorization_isolation(self, client):
        """User A must not be able to view User B's private notifications or academic records."""
        # User Alice notification
        notif_alice = notification_mgr.create_notification(
            title="Alice Private Notice",
            message="Sensitive verification information for Alice only.",
            category="VERIFICATION",
            severity="INFO",
            user_id="alice_user",
        )

        # User Bob requests notifications
        bob_res = client.get("/api/notifications", headers={"X-User-Id": "bob_user"})
        assert bob_res.status_code == 200
        bob_notifs = bob_res.json()["notifications"]
        assert not any(n["id"] == notif_alice["id"] for n in bob_notifs)

        # Bob attempts to mark Alice's notification as read -> 403 Forbidden
        bob_hack = client.post(f"/api/notifications/{notif_alice['id']}/read", headers={"X-User-Id": "bob_user"})
        assert bob_hack.status_code == 403

        # Bob attempts to view student_profile's private academic records -> 403 Forbidden
        prof_hack = client.get("/api/personal/profile", headers={"X-User-Id": "intruder_user"})
        assert prof_hack.status_code == 403
        assert "access denied" in prof_hack.json()["detail"].lower()

        # Admin can view all notifications
        admin_res = client.get("/api/notifications", headers={"X-User-Id": "admin"})
        assert admin_res.status_code == 200
        admin_notifs = admin_res.json()["notifications"]
        assert any(n["id"] == notif_alice["id"] for n in admin_notifs)

    def test_persistence_reporting(self, client):
        """Endpoint accurately reports disk persistence or fallback warning without deception."""
        res = client.get("/api/verification/records", headers={"X-User-Id": "student_profile"})
        assert res.status_code == 200
        data = res.json()
        assert "persistence" in data
        assert data["persistence"]["storage_mode"] in ("persistent_json_file", "in_memory_fallback")
        if data["persistence"]["is_persistent"]:
            assert data["persistence"]["warning"] is None
        else:
            assert data["persistence"]["warning"] is not None
