"""Notification and Alert Engine for GlobalDataMind AI.
Manages persistent alerts, verification notifications, data source notifications,
user authorization isolation, and unread badge tracking.
"""
from __future__ import annotations

import os
import json
import time
import copy
import uuid
import threading
import logging
from typing import Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("notifications")


class NotificationManager:
    """Manages notifications for GlobalDataMind AI:
    - Verification lifecycle alerts (pending, in progress, verified, failed, re-verification)
    - Data source alerts (World Bank API status, observation revisions)
    - System integrity notifications
    - Multi-user isolation and authorization checks
    - JSON persistence with graceful fallback
    """

    def __init__(self, storage_dir: str = "data") -> None:
        self.storage_dir = storage_dir
        self.storage_file = os.path.join(storage_dir, "notifications.json")
        self._lock = threading.Lock()
        self._notifications: list[dict[str, Any]] = []
        self._storage_mode = "persistent_json_file"
        self._load_storage()

    def _load_storage(self) -> None:
        """Load notifications from persistent disk storage."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._notifications = data.get("notifications", [])
                    self._storage_mode = "persistent_json_file"
                    return
            except Exception as e:
                logger.warning(f"Could not load notifications from disk: {e}. Using in-memory fallback.")
                self._storage_mode = "in_memory_fallback"
                self._notifications = []
        else:
            self._storage_mode = "persistent_json_file"
            self._seed_default_notifications()
            self._save_storage()

    def _save_storage(self) -> bool:
        """Persist notifications to disk."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            payload = {
                "version": "2.2.0",
                "storage_mode": self._storage_mode,
                "last_saved": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_count": len(self._notifications),
                "notifications": self._notifications,
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to persist notifications: {e}")
            self._storage_mode = "in_memory_fallback"
            return False

    def _seed_default_notifications(self) -> None:
        """Seed realistic initial notifications for demonstration."""
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._notifications = [
            {
                "id": "notif_seed_001",
                "user_id": "student_profile",
                "title": "Class 12 Record Awaiting Verification",
                "message": "Class 12 (Higher Secondary) transcript submitted. Basic format validated; pending authoritative board verification.",
                "category": "VERIFICATION",
                "severity": "WARNING",
                "status": "UNREAD",
                "timestamp": now_iso,
                "related_record": {
                    "id": "acad_class_12",
                    "type": "academic_record",
                    "level": "Class 12",
                    "institution": "Springdales School",
                },
                "action": {
                    "target_tab": "personal-intelligence",
                    "record_id": "acad_class_12",
                    "label": "View Record",
                },
            },
            {
                "id": "notif_seed_002",
                "user_id": "student_profile",
                "title": "World Bank Indicator Repository Active",
                "message": "Connected to official World Bank Indicators API. Sourced 50+ country series with zero metric fabrication.",
                "category": "DATA_SOURCE",
                "severity": "INFO",
                "status": "READ",
                "timestamp": now_iso,
                "related_record": {
                    "id": "src_worldbank",
                    "type": "data_source",
                    "source": "World Bank Open Data API",
                },
                "action": {
                    "target_tab": "global-intelligence",
                    "label": "Explore Indicators",
                },
            },
        ]

    def create_notification(
        self,
        title: str,
        message: str,
        category: str = "VERIFICATION",  # VERIFICATION, DATA_SOURCE, SYSTEM
        severity: str = "INFO",           # INFO, WARNING, ERROR, SUCCESS
        user_id: str = "student_profile",
        related_record: Optional[dict[str, Any]] = None,
        action: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create and store a new notification."""
        notif_id = f"notif_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        notification = {
            "id": notif_id,
            "user_id": user_id,
            "title": title.strip(),
            "message": message.strip(),
            "category": category.upper(),
            "severity": severity.upper(),
            "status": "UNREAD",
            "timestamp": now_iso,
            "related_record": related_record or {},
            "action": action or {},
        }

        with self._lock:
            # Prepend to display newest first
            self._notifications.insert(0, notification)
            # Cap maximum historical notifications to 200
            if len(self._notifications) > 200:
                self._notifications = self._notifications[:200]
            self._save_storage()

        return copy.deepcopy(notification)

    def list_notifications(
        self,
        requesting_user_id: str,
        category: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Retrieve notifications accessible to the requesting user with unread count.
        Enforces user isolation: normal users cannot see other users' private notifications.
        Admins ('admin', 'workspace_admin') can view all notifications.
        """
        is_admin = requesting_user_id in ("admin", "workspace_admin")

        with self._lock:
            accessible = []
            for n in self._notifications:
                # Check user authorization
                if not is_admin and n.get("user_id") != requesting_user_id and n.get("user_id") != "all":
                    continue
                # Filter category
                if category and category.upper() != "ALL":
                    if n.get("category") != category.upper():
                        continue
                # Filter unread
                if unread_only and n.get("status") != "UNREAD":
                    continue
                accessible.append(copy.deepcopy(n))

            # Calculate total unread count for the requesting user
            unread_count = 0
            for n in self._notifications:
                if (is_admin or n.get("user_id") == requesting_user_id or n.get("user_id") == "all") and n.get("status") == "UNREAD":
                    unread_count += 1

            return {
                "notifications": accessible[:limit],
                "unread_count": unread_count,
                "total_accessible": len(accessible),
                "storage_mode": self._storage_mode,
                "user_id": requesting_user_id,
            }

    def mark_as_read(self, notification_id: str, requesting_user_id: str) -> dict[str, Any] | None:
        """Mark a single notification as read if authorized."""
        is_admin = requesting_user_id in ("admin", "workspace_admin")
        with self._lock:
            for n in self._notifications:
                if n["id"] == notification_id:
                    # Enforce authorization
                    if not is_admin and n.get("user_id") != requesting_user_id and n.get("user_id") != "all":
                        raise PermissionError(f"User '{requesting_user_id}' is not authorized to modify notification '{notification_id}'.")
                    n["status"] = "READ"
                    n["read_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    self._save_storage()
                    return copy.deepcopy(n)
        return None

    def mark_all_as_read(self, requesting_user_id: str, category: Optional[str] = None) -> int:
        """Mark all notifications accessible to requesting user as read."""
        is_admin = requesting_user_id in ("admin", "workspace_admin")
        count = 0
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        with self._lock:
            for n in self._notifications:
                if not is_admin and n.get("user_id") != requesting_user_id and n.get("user_id") != "all":
                    continue
                if category and category.upper() != "ALL" and n.get("category") != category.upper():
                    continue
                if n.get("status") == "UNREAD":
                    n["status"] = "READ"
                    n["read_at"] = now_iso
                    count += 1
            if count > 0:
                self._save_storage()

        return count

    def get_unread_count(self, requesting_user_id: str) -> int:
        """Return the unread count for the given user."""
        is_admin = requesting_user_id in ("admin", "workspace_admin")
        with self._lock:
            count = 0
            for n in self._notifications:
                if (is_admin or n.get("user_id") == requesting_user_id or n.get("user_id") == "all") and n.get("status") == "UNREAD":
                    count += 1
            return count

    def delete_notification(self, notification_id: str, requesting_user_id: str) -> bool:
        """Delete a notification if authorized."""
        is_admin = requesting_user_id in ("admin", "workspace_admin")
        with self._lock:
            for idx, n in enumerate(self._notifications):
                if n["id"] == notification_id:
                    if not is_admin and n.get("user_id") != requesting_user_id and n.get("user_id") != "all":
                        raise PermissionError("Unauthorized to delete this notification.")
                    self._notifications.pop(idx)
                    self._save_storage()
                    return True
        return False
