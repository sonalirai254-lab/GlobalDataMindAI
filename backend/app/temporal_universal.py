"""Universal Timestamp and Temporal Data Analysis System for GlobalDataMind AI.

Supports:
1. Multi-format timestamp extraction and parsing (ISO 8601, RFC 2822, UNIX epoch, CLF, Syslog, custom logs).
2. Internal UTC normalization while strictly preserving original timestamps and source timezones.
3. Explicit timestamp precision: year, month, day, hour, minute, second, millisecond, microsecond.
4. Separate temporal fields:
   - event_time: when the event actually occurred (if known, in UTC ISO 8601)
   - source_created_at: when the source record was created (if known, in UTC ISO 8601)
   - ingested_at: when the system imported the record (UTC ISO 8601)
   - verified_at: when verification was completed (UTC ISO 8601)
   - timestamp_precision: year, month, day, second, etc.
   - timezone and source provenance
5. Strict Zero-Fabrication & Quality Validation:
   - Never infers exact event times from year-only statistics or incomplete metadata.
   - Detects missing, malformed, conflicting, and implausible timestamps.
   - Flags them for review instead of inventing values.
   - For records without exact timestamps, reports the most precise supported date/time range with clear limitations.
6. Modular Parsers for:
   - Structured records
   - JSON
   - CSV
   - Server & Application Logs
   - Text & Document metadata (PDF CreationDate, Markdown frontmatter)
7. Temporal Data Analysis:
   - Time-based filtering
   - Chronological sorting
   - Historical window comparisons
   - Timeline visualizations with precision indicators
"""
from __future__ import annotations

import csv
import io
import re
import time
import calendar
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

# Common standard named timezones mapping for text abbreviations
TZ_ABBREVIATIONS: dict[str, str] = {
    "UTC": "UTC",
    "GMT": "UTC",
    "Z": "UTC",
    "EST": "-05:00",
    "EDT": "-04:00",
    "CST": "-06:00",
    "CDT": "-05:00",
    "MST": "-07:00",
    "MDT": "-06:00",
    "PST": "-08:00",
    "PDT": "-07:00",
    "IST": "+05:30",
    "JST": "+09:00",
    "BST": "+01:00",
    "CET": "+01:00",
    "CEST": "+02:00",
    "AEST": "+10:00",
    "AEDT": "+11:00",
}


class TimestampPrecision(str, Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    MILLISECOND = "millisecond"
    MICROSECOND = "microsecond"
    UNKNOWN = "unknown"


class TemporalValidationStatus(str, Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    MALFORMED = "MALFORMED"
    CONFLICTING = "CONFLICTING"
    IMPLAUSIBLE = "IMPLAUSIBLE"


class TimeRange(BaseModel):
    start: str  # UTC ISO 8601
    end: str    # UTC ISO 8601
    precision: str
    limitation_note: str


class UniversalTimestamp(BaseModel):
    """Normalized universal timestamp structure complying with all temporal provenance requirements."""
    event_time: Optional[str] = None  # Normalized UTC ISO 8601, None if inexact or unknown
    original_event_time: Optional[str] = None  # Exact verbatim representation from source
    source_created_at: Optional[str] = None  # Normalized UTC ISO 8601 of source publication/creation
    original_source_created_at: Optional[str] = None  # Exact verbatim source creation timestamp
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    verified_at: Optional[str] = None
    timestamp_precision: TimestampPrecision = TimestampPrecision.UNKNOWN
    timezone: str = "UTC"  # Preserved source timezone or offset
    source_provenance: dict[str, Any] = Field(default_factory=dict)
    is_inferred: bool = False
    inference_method: Optional[str] = None
    uncertainty_margin: Optional[str] = None
    time_range: Optional[TimeRange] = None
    validation_status: TemporalValidationStatus = TemporalValidationStatus.VALID
    validation_flags: list[str] = Field(default_factory=list)
    requires_review: bool = False


class TemporalRecord(BaseModel):
    """Universal temporal container for any ingested data entity or record."""
    id: str
    record_type: str = "generic"
    data: dict[str, Any] = Field(default_factory=dict)
    temporal: UniversalTimestamp


class UniversalTimestampParser:
    """Robust parser that normalizes multi-format timestamps to UTC while strictly enforcing zero fabrication."""

    # Plausible calendar year bounds for non-scenario organizational and macroeconomic records
    MIN_PLAUSIBLE_YEAR = 1800
    MAX_PLAUSIBLE_YEAR = 2050

    @classmethod
    def now_utc_iso(cls) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def parse(
        cls,
        raw_val: Any,
        source_name: str = "unknown_source",
        record_id: Optional[str] = None,
        source_created_raw: Any = None,
        verified_raw: Any = None,
        allow_inference: bool = False,
        inference_rule: Optional[str] = None,
        provenance_extra: Optional[dict[str, Any]] = None,
    ) -> UniversalTimestamp:
        """Parse raw timestamp inputs, validate boundaries, and construct UniversalTimestamp."""
        provenance = {
            "source_name": source_name,
            "record_id": record_id,
            "parser": "UniversalTimestampParser_v1.0",
        }
        if provenance_extra:
            provenance.update(provenance_extra)

        # 1. Missing timestamp check
        if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()) or raw_val in ("N/A", "null", "None", "undefined"):
            flags = ["MISSING_TIMESTAMP: No event timestamp provided in source data."]
            return UniversalTimestamp(
                event_time=None,
                original_event_time=None,
                source_created_at=cls._parse_exact_iso(source_created_raw)[0] if source_created_raw else None,
                original_source_created_at=str(source_created_raw) if source_created_raw is not None else None,
                ingested_at=cls.now_utc_iso(),
                verified_at=cls._parse_exact_iso(verified_raw)[0] if verified_raw else None,
                timestamp_precision=TimestampPrecision.UNKNOWN,
                timezone="UTC",
                source_provenance=provenance,
                validation_status=TemporalValidationStatus.MISSING,
                validation_flags=flags,
                requires_review=True,
            )

        str_val = str(raw_val).strip()

        # 2. Integer or string Year-only detection (e.g. 2024 or "2024")
        if isinstance(raw_val, int) or (isinstance(raw_val, str) and re.fullmatch(r"\d{4}", str_val)):
            year = int(str_val)
            if not (cls.MIN_PLAUSIBLE_YEAR <= year <= cls.MAX_PLAUSIBLE_YEAR):
                return UniversalTimestamp(
                    event_time=None,
                    original_event_time=str_val,
                    ingested_at=cls.now_utc_iso(),
                    timestamp_precision=TimestampPrecision.YEAR,
                    timezone="UTC",
                    source_provenance=provenance,
                    validation_status=TemporalValidationStatus.IMPLAUSIBLE,
                    validation_flags=[f"IMPLAUSIBLE_TIMESTAMP: Year {year} falls outside plausible range [{cls.MIN_PLAUSIBLE_YEAR}-{cls.MAX_PLAUSIBLE_YEAR}]."],
                    requires_review=True,
                )

            # Strictly Rule 10: Never infer an exact event time from a year-only statistic!
            range_info = TimeRange(
                start=f"{year:04d}-01-01T00:00:00Z",
                end=f"{year:04d}-12-31T23:59:59Z",
                precision="year",
                limitation_note=f"Year-only statistic ({year}). Exact event time is unrecorded by the source.",
            )
            return UniversalTimestamp(
                event_time=None,  # Intentionally null: zero fabrication rule active
                original_event_time=str_val,
                source_created_at=cls._parse_exact_iso(source_created_raw)[0] if source_created_raw else None,
                original_source_created_at=str(source_created_raw) if source_created_raw is not None else None,
                ingested_at=cls.now_utc_iso(),
                verified_at=cls._parse_exact_iso(verified_raw)[0] if verified_raw else None,
                timestamp_precision=TimestampPrecision.YEAR,
                timezone="UTC",
                source_provenance=provenance,
                time_range=range_info,
                validation_status=TemporalValidationStatus.VALID,
                validation_flags=[],
                requires_review=False,
            )

        # 3. Year-Month detection (e.g. "2024-05" or "2024/05")
        ym_match = re.fullmatch(r"(\d{4})[-/](\d{2})", str_val)
        if ym_match:
            year = int(ym_match.group(1))
            month = int(ym_match.group(2))
            if not (1 <= month <= 12):
                return UniversalTimestamp(
                    event_time=None,
                    original_event_time=str_val,
                    ingested_at=cls.now_utc_iso(),
                    timestamp_precision=TimestampPrecision.MONTH,
                    source_provenance=provenance,
                    validation_status=TemporalValidationStatus.MALFORMED,
                    validation_flags=[f"MALFORMED_TIMESTAMP: Invalid month {month} in '{str_val}'."],
                    requires_review=True,
                )
            last_day = calendar.monthrange(year, month)[1]
            range_info = TimeRange(
                start=f"{year:04d}-{month:02d}-01T00:00:00Z",
                end=f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z",
                precision="month",
                limitation_note=f"Month-bounded record ({year:04d}-{month:02d}). Exact day and time are unrecorded.",
            )
            return UniversalTimestamp(
                event_time=None,
                original_event_time=str_val,
                source_created_at=cls._parse_exact_iso(source_created_raw)[0] if source_created_raw else None,
                original_source_created_at=str(source_created_raw) if source_created_raw is not None else None,
                ingested_at=cls.now_utc_iso(),
                verified_at=cls._parse_exact_iso(verified_raw)[0] if verified_raw else None,
                timestamp_precision=TimestampPrecision.MONTH,
                timezone="UTC",
                source_provenance=provenance,
                time_range=range_info,
                validation_status=TemporalValidationStatus.VALID,
                validation_flags=[],
                requires_review=False,
            )

        # 4. Standard / Granular parsing (Day, Hour, Second, Millisecond)
        dt_utc, precision, orig_tz, error_msg = cls._parse_datetime(str_val)
        if error_msg:
            return UniversalTimestamp(
                event_time=None,
                original_event_time=str_val,
                ingested_at=cls.now_utc_iso(),
                timestamp_precision=TimestampPrecision.UNKNOWN,
                source_provenance=provenance,
                validation_status=TemporalValidationStatus.MALFORMED,
                validation_flags=[f"MALFORMED_TIMESTAMP: {error_msg}"],
                requires_review=True,
            )

        # Plausibility check
        if not (cls.MIN_PLAUSIBLE_YEAR <= dt_utc.year <= cls.MAX_PLAUSIBLE_YEAR):
            return UniversalTimestamp(
                event_time=None,
                original_event_time=str_val,
                ingested_at=cls.now_utc_iso(),
                timestamp_precision=precision,
                timezone=orig_tz,
                source_provenance=provenance,
                validation_status=TemporalValidationStatus.IMPLAUSIBLE,
                validation_flags=[f"IMPLAUSIBLE_TIMESTAMP: Year {dt_utc.year} is outside plausible range [{cls.MIN_PLAUSIBLE_YEAR}-{cls.MAX_PLAUSIBLE_YEAR}]."],
                requires_review=True,
            )

        # Format normalized UTC ISO
        if precision in (TimestampPrecision.MILLISECOND, TimestampPrecision.MICROSECOND):
            event_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" if precision == TimestampPrecision.MILLISECOND else dt_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            event_iso = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Range representation for day precision
        range_info = None
        if precision == TimestampPrecision.DAY:
            d_str = dt_utc.strftime("%Y-%m-%d")
            range_info = TimeRange(
                start=f"{d_str}T00:00:00Z",
                end=f"{d_str}T23:59:59Z",
                precision="day",
                limitation_note=f"Day-level precision ({d_str}). Sub-day time (hour/minute/second) was not captured.",
            )

        # Parse source created and verified timestamps
        src_created_iso, _, _, src_created_err = cls._parse_exact_iso(source_created_raw) if source_created_raw else (None, None, None, None)
        verified_iso, _, _, _ = cls._parse_exact_iso(verified_raw) if verified_raw else (None, None, None, None)

        # 5. Check for Conflicting Dates
        flags: list[str] = []
        validation_status = TemporalValidationStatus.VALID
        requires_review = False

        if src_created_iso and event_iso:
            # If source record claims to be created significantly BEFORE the event happened (e.g. created in 2020 for an event in 2024)
            # Some minor skew (+/- 5 minutes) is tolerated for clock drift
            try:
                dt_src = datetime.fromisoformat(src_created_iso.replace("Z", "+00:00"))
                if dt_utc - dt_src > timedelta(days=365 * 2):
                    flags.append(f"CONFLICTING_TIMESTAMPS: source_created_at ({src_created_iso}) is more than 2 years prior to event_time ({event_iso}).")
                    validation_status = TemporalValidationStatus.CONFLICTING
                    requires_review = True
                elif dt_src - dt_utc > timedelta(days=365 * 10):
                    flags.append(f"CONFLICTING_TIMESTAMPS: event_time ({event_iso}) is over 10 years before source_created_at ({src_created_iso}).")
                    validation_status = TemporalValidationStatus.CONFLICTING
                    requires_review = True
            except Exception:
                pass

        if src_created_err:
            flags.append(f"MALFORMED_SOURCE_CREATED_AT: {src_created_err}")
            requires_review = True

        return UniversalTimestamp(
            event_time=event_iso,
            original_event_time=str_val,
            source_created_at=src_created_iso,
            original_source_created_at=str(source_created_raw) if source_created_raw is not None else None,
            ingested_at=cls.now_utc_iso(),
            verified_at=verified_iso,
            timestamp_precision=precision,
            timezone=orig_tz,
            source_provenance=provenance,
            is_inferred=False,
            time_range=range_info,
            validation_status=validation_status,
            validation_flags=flags,
            requires_review=requires_review,
        )

    @classmethod
    def create_inferred_estimate(
        cls,
        estimated_start: str,
        estimated_end: str,
        method: str,
        uncertainty_margin: str,
        source_name: str = "inferred_analysis",
    ) -> UniversalTimestamp:
        """Explicitly construct an inferred/estimated temporal record with documented methodology."""
        provenance = {
            "source_name": source_name,
            "inference_engine": "TemporalInferenceEstimator",
        }
        range_info = TimeRange(
            start=estimated_start,
            end=estimated_end,
            precision="range_estimate",
            limitation_note=f"Inferred estimate using {method}. Margin of uncertainty: {uncertainty_margin}.",
        )
        return UniversalTimestamp(
            event_time=None,  # Never pretend an estimate is an exact event time
            original_event_time=f"Estimated window: [{estimated_start} to {estimated_end}]",
            ingested_at=cls.now_utc_iso(),
            timestamp_precision=TimestampPrecision.UNKNOWN,
            timezone="UTC",
            source_provenance=provenance,
            is_inferred=True,
            inference_method=method,
            uncertainty_margin=uncertainty_margin,
            time_range=range_info,
            validation_status=TemporalValidationStatus.VALID,
            validation_flags=[f"INFERRED_ESTIMATE: Derived via {method} with margin {uncertainty_margin}"],
            requires_review=False,
        )

    @classmethod
    def _parse_datetime(cls, s: str) -> tuple[Optional[datetime], TimestampPrecision, str, Optional[str]]:
        """Parse various string formats into UTC datetime, precision, and original timezone."""
        cleaned = s.strip()

        # Numeric UNIX epoch timestamp check
        if re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
            try:
                num = float(cleaned)
                # Distinguish seconds vs milliseconds vs microseconds
                if abs(num) >= 1e14:  # Microseconds
                    dt = datetime.fromtimestamp(num / 1e6, tz=timezone.utc)
                    return dt, TimestampPrecision.MICROSECOND, "UTC", None
                elif abs(num) >= 1e11:  # Milliseconds
                    dt = datetime.fromtimestamp(num / 1e3, tz=timezone.utc)
                    return dt, TimestampPrecision.MILLISECOND, "UTC", None
                else:  # Seconds
                    dt = datetime.fromtimestamp(num, tz=timezone.utc)
                    prec = TimestampPrecision.MILLISECOND if "." in cleaned else TimestampPrecision.SECOND
                    return dt, prec, "UTC", None
            except Exception as e:
                return None, TimestampPrecision.UNKNOWN, "UTC", f"Invalid epoch value: {str(e)}"

        # Common Log Format (CLF) / Apache / Nginx: e.g. 18/May/2024:10:30:00 -0400 or [18/May/2024:10:30:00 +0000]
        clf_match = re.search(r"\[?(\d{2})/([A-Za-z]{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})\s+([+-]\d{4})\]?", cleaned)
        if clf_match:
            day, mon_str, year, hr, mn, sc, tz_offset = clf_match.groups()
            try:
                dt_str = f"{day} {mon_str} {year} {hr}:{mn}:{sc} {tz_offset}"
                parsed = datetime.strptime(dt_str, "%d %b %Y %H:%M:%S %z")
                return parsed.astimezone(timezone.utc), TimestampPrecision.SECOND, tz_offset, None
            except Exception as e:
                return None, TimestampPrecision.UNKNOWN, tz_offset, f"CLF parse error: {str(e)}"

        # Extract timezone name abbreviation if present at the end (e.g. "2024-05-18 10:30:00 EDT")
        detected_tz = "UTC"
        tz_word_match = re.search(r"\b([A-Z]{3,4})$", cleaned)
        if tz_word_match:
            tz_code = tz_word_match.group(1)
            if tz_code in TZ_ABBREVIATIONS:
                detected_tz = tz_code
                cleaned = cleaned[:tz_word_match.start()].strip() + " " + TZ_ABBREVIATIONS[tz_code]

        # ISO 8601 parsing with regex-assisted timezone & precision identification
        # Patterns like: 2024-05-18, 2024-05-18T10:30:00Z, 2024-05-18 10:30:00.123+05:30
        iso_clean = cleaned.replace(" ", "T") if " " in cleaned and "T" not in cleaned and ":" in cleaned else cleaned

        # Date only: YYYY-MM-DD
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cleaned):
            try:
                dt = datetime.strptime(cleaned, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                return dt, TimestampPrecision.DAY, "UTC", None
            except Exception as e:
                return None, TimestampPrecision.DAY, "UTC", str(e)

        # Date with slash: DD/MM/YYYY or YYYY/MM/DD
        if "/" in cleaned:
            # Check YYYY/MM/DD
            if re.fullmatch(r"\d{4}/\d{2}/\d{2}", cleaned):
                try:
                    dt = datetime.strptime(cleaned, "%Y/%m/%d").replace(tzinfo=timezone.utc)
                    return dt, TimestampPrecision.DAY, "UTC", None
                except Exception as e:
                    return None, TimestampPrecision.DAY, "UTC", str(e)
            # DD/MM/YYYY
            if re.fullmatch(r"\d{2}/\d{2}/\d{4}", cleaned):
                try:
                    dt = datetime.strptime(cleaned, "%d/%m/%Y").replace(tzinfo=timezone.utc)
                    return dt, TimestampPrecision.DAY, "UTC", None
                except Exception as e:
                    return None, TimestampPrecision.DAY, "UTC", str(e)

        # Handle ISO strings with Z
        if iso_clean.endswith("Z"):
            iso_clean = iso_clean[:-1] + "+00:00"
            detected_tz = "UTC"

        # Check for timezone offset in string (+HH:MM, -HH:MM, +HHMM, -HHMM)
        tz_offset_match = re.search(r"([+-]\d{2}):?(\d{2})$", iso_clean)
        if tz_offset_match and detected_tz == "UTC":
            detected_tz = f"{tz_offset_match.group(1)}:{tz_offset_match.group(2)}"

        try:
            # Attempt datetime.fromisoformat
            dt = datetime.fromisoformat(iso_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                detected_tz = "UTC"
            utc_dt = dt.astimezone(timezone.utc)

            # Determine precision
            if dt.microsecond > 0:
                if dt.microsecond % 1000 == 0:
                    prec = TimestampPrecision.MILLISECOND
                else:
                    prec = TimestampPrecision.MICROSECOND
            elif dt.second > 0 or ":" in iso_clean.split("T")[-1]:
                prec = TimestampPrecision.SECOND
            elif dt.minute > 0 or (len(iso_clean.split("T")[-1].split(":")) == 2):
                prec = TimestampPrecision.MINUTE
            else:
                prec = TimestampPrecision.DAY

            return utc_dt, prec, detected_tz, None
        except Exception:
            pass

        # Try dateutil parser if standard library fromisoformat didn't capture special format
        try:
            from dateutil import parser as du_parser
            dt = du_parser.parse(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                detected_tz = "UTC"
            utc_dt = dt.astimezone(timezone.utc)
            prec = TimestampPrecision.MILLISECOND if dt.microsecond else TimestampPrecision.SECOND
            return utc_dt, prec, detected_tz, None
        except Exception as e:
            return None, TimestampPrecision.UNKNOWN, "UTC", f"Unrecognized date/time format: '{cleaned}' ({str(e)})"

    @classmethod
    def _parse_exact_iso(cls, val: Any) -> tuple[Optional[str], Optional[TimestampPrecision], str, Optional[str]]:
        if val is None or not str(val).strip():
            return None, None, "UTC", None
        dt_utc, prec, tz_name, err = cls._parse_datetime(str(val))
        if err or not dt_utc:
            return None, None, "UTC", err
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), prec, tz_name, None


# ==============================================================================
# Modular Parsers
# ==============================================================================

class BaseTemporalParser:
    """Abstract base class for all modular format parsers."""
    source_type: str = "generic"

    def parse(self, content: Any, source_name: str = "source", **kwargs) -> list[TemporalRecord]:
        raise NotImplementedError("Subclasses must implement parse()")


class JsonTemporalParser(BaseTemporalParser):
    """Modular parser for structured JSON payloads (entities, events, and records)."""
    source_type: str = "JSON"

    # Candidate field names indicating event timestamp
    EVENT_TIME_KEYS = (
        "event_time", "timestamp", "datetime", "occurred_at", "time", "date",
        "created_at", "valid_from", "year", "passing_year", "period"
    )
    SOURCE_CREATED_KEYS = ("source_created_at", "published_at", "recorded_at", "file_created_at")
    VERIFIED_KEYS = ("verified_at", "verification_timestamp")

    def parse(self, content: Any, source_name: str = "json_source", **kwargs) -> list[TemporalRecord]:
        import json
        if isinstance(content, (bytes, bytearray)):
            content = content.decode("utf-8", errors="replace")
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception as e:
                # Return single malformed record
                record_id = f"err_{int(time.time())}"
                return [
                    TemporalRecord(
                        id=record_id,
                        record_type="json_error",
                        data={"raw": content[:200]},
                        temporal=UniversalTimestamp(
                            event_time=None,
                            original_event_time=None,
                            ingested_at=UniversalTimestampParser.now_utc_iso(),
                            timestamp_precision=TimestampPrecision.UNKNOWN,
                            source_provenance={"source_name": source_name, "error": str(e)},
                            validation_status=TemporalValidationStatus.MALFORMED,
                            validation_flags=[f"JSON_SYNTAX_ERROR: {str(e)}"],
                            requires_review=True,
                        ),
                    )
                ]
        else:
            data = content

        items = data if isinstance(data, list) else data.get("entities", data.get("records", [data]))
        records: list[TemporalRecord] = []

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            rec_id = str(item.get("id") or item.get("name") or f"json_rec_{idx + 1}")

            # Extract candidate timestamp fields
            raw_event = self._find_first_val(item, self.EVENT_TIME_KEYS)
            raw_created = self._find_first_val(item, self.SOURCE_CREATED_KEYS)
            raw_verified = self._find_first_val(item, self.VERIFIED_KEYS)

            temporal = UniversalTimestampParser.parse(
                raw_val=raw_event,
                source_name=source_name,
                record_id=rec_id,
                source_created_raw=raw_created,
                verified_raw=raw_verified,
                provenance_extra={"item_index": idx, "format": "JSON"},
            )

            records.append(TemporalRecord(
                id=rec_id,
                record_type=item.get("kind", item.get("type", "json_entity")),
                data=item,
                temporal=temporal,
            ))

        return records

    def _find_first_val(self, d: dict[str, Any], keys: tuple[str, ...]) -> Any:
        for k in keys:
            if k in d and d[k] is not None:
                return d[k]
        return None


class CsvTemporalParser(BaseTemporalParser):
    """Modular parser for tabular CSV files with automatic delimiter and date column detection."""
    source_type: str = "CSV"

    DATE_COLUMN_CANDIDATES = (
        "event_time", "timestamp", "datetime", "date", "time", "occurred_at",
        "created_at", "year", "passing_year", "observation_year"
    )

    def parse(self, content: str | bytes, source_name: str = "csv_file", **kwargs) -> list[TemporalRecord]:
        if isinstance(content, bytes):
            text = content.decode("utf-8", errors="replace")
        else:
            text = content

        records: list[TemporalRecord] = []
        if not text.strip():
            return records

        # Auto-detect delimiter
        sample = text[:2048]
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            return records

        # Identify timestamp column
        date_col = None
        for cand in self.DATE_COLUMN_CANDIDATES:
            for fn in reader.fieldnames:
                if fn and fn.strip().lower() == cand:
                    date_col = fn
                    break
            if date_col:
                break

        for row_idx, row in enumerate(reader):
            rec_id = row.get("id") or row.get("name") or f"{source_name}_row_{row_idx + 1}"
            raw_val = row.get(date_col) if date_col else None

            temporal = UniversalTimestampParser.parse(
                raw_val=raw_val,
                source_name=source_name,
                record_id=rec_id,
                provenance_extra={
                    "row_number": row_idx + 2,  # 1-indexed header + 1
                    "detected_date_column": date_col,
                    "format": "CSV",
                },
            )

            records.append(TemporalRecord(
                id=rec_id,
                record_type="csv_row",
                data=dict(row),
                temporal=temporal,
            ))

        return records


class LogTemporalParser(BaseTemporalParser):
    """Modular parser for server and application logs (Apache, Nginx, Syslog, Key-Value, ISO logs)."""
    source_type: str = "LOG"

    # Regex patterns for popular log line formats
    PATTERNS = [
        # Apache / Nginx combined: IP - - [18/May/2024:10:30:00 -0400] "GET /api HTTP/1.1" 200 1234
        re.compile(r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<request>[^"]+)"\s+(?P<status>\d+)\s+(?P<size>\S+)'),
        # ISO-prefixed log: 2024-05-18T10:30:00.123Z [INFO] Message here
        re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+\[(?P<level>[A-Z]+)\]\s+(?P<message>.*)'),
        # Key-Value format: time="2024-05-18T10:30:00Z" level=info msg="hello"
        re.compile(r'time="(?P<timestamp>[^"]+)"\s+level=(?P<level>\S+)\s+msg="(?P<message>[^"]+)"'),
        # Syslog RFC 3164: May 18 10:30:00 host app[123]: message
        re.compile(r'^(?P<timestamp>[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<app>[^:]+):\s+(?P<message>.*)'),
    ]

    def parse(self, content: str | bytes, source_name: str = "app.log", **kwargs) -> list[TemporalRecord]:
        if isinstance(content, bytes):
            text = content.decode("utf-8", errors="replace")
        else:
            text = content

        records: list[TemporalRecord] = []
        lines = text.strip().splitlines()

        for line_idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            rec_id = f"{source_name}_line_{line_idx + 1}"
            parsed_data: dict[str, Any] = {"raw_line": line_str}
            raw_ts = None

            for pattern in self.PATTERNS:
                match = pattern.match(line_str)
                if match:
                    group_dict = match.groupdict()
                    raw_ts = group_dict.get("timestamp")
                    parsed_data.update(group_dict)
                    break

            temporal = UniversalTimestampParser.parse(
                raw_val=raw_ts,
                source_name=source_name,
                record_id=rec_id,
                provenance_extra={"line_number": line_idx + 1, "format": "LOG"},
            )

            records.append(TemporalRecord(
                id=rec_id,
                record_type="log_entry",
                data=parsed_data,
                temporal=temporal,
            ))

        return records


class DocumentTemporalParser(BaseTemporalParser):
    """Modular parser for Document files (Markdown, Text, PDF) extracting dates from metadata & headers."""
    source_type: str = "DOCUMENT"

    def parse(self, content: str | bytes, source_name: str = "document", **kwargs) -> list[TemporalRecord]:
        metadata = kwargs.get("metadata", {})
        pdf_bytes = kwargs.get("pdf_bytes")

        # Check for PDF CreationDate metadata if pdf_bytes provided
        doc_created_at = None
        if pdf_bytes:
            try:
                try:
                    import pypdf as pypdf_lib
                except ImportError:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", DeprecationWarning)
                        import PyPDF2 as pypdf_lib
                reader = pypdf_lib.PdfReader(io.BytesIO(pdf_bytes))
                doc_info = reader.metadata or {}
                raw_pdf_date = doc_info.get("/CreationDate") or doc_info.get("CreationDate")
                if raw_pdf_date and str(raw_pdf_date).startswith("D:"):
                    # Format: D:YYYYMMDDHHmmSSOHH'mm'
                    clean_pdf = str(raw_pdf_date)[2:16]
                    try:
                        doc_created_at = datetime.strptime(clean_pdf, "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
                    except Exception:
                        pass
            except Exception:
                pass

        if isinstance(content, bytes):
            text = content.decode("utf-8", errors="replace")
        else:
            text = str(content)

        # Look for YAML frontmatter date if Markdown
        frontmatter_date = None
        if text.startswith("---"):
            fm_match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if fm_match:
                fm_block = fm_match.group(1)
                d_match = re.search(r"^\s*date:\s*[\"']?([^\"'\n]+)[\"']?", fm_block, re.MULTILINE | re.IGNORECASE)
                if d_match:
                    frontmatter_date = d_match.group(1).strip()

        chosen_date = frontmatter_date or doc_created_at or metadata.get("created_at") or metadata.get("date")
        rec_id = metadata.get("id") or f"doc_{source_name}"

        temporal = UniversalTimestampParser.parse(
            raw_val=chosen_date,
            source_name=source_name,
            record_id=rec_id,
            source_created_raw=doc_created_at,
            provenance_extra={"format": "DOCUMENT", "has_frontmatter_date": bool(frontmatter_date)},
        )

        return [
            TemporalRecord(
                id=rec_id,
                record_type="document",
                data={"title": source_name, "char_length": len(text), "snippet": text[:200]},
                temporal=temporal,
            )
        ]


class StructuredRecordTemporalParser(BaseTemporalParser):
    """Adapter for internal domain entities (Academic Records, Global Observations, Trust Ledger, Decisions)."""
    source_type: str = "STRUCTURED_INTERNAL"

    def parse(self, record_dict: dict[str, Any], source_name: str = "internal_entity", **kwargs) -> TemporalRecord:
        rec_id = str(record_dict.get("id") or record_dict.get("level_key") or "entity")
        rec_kind = str(record_dict.get("kind") or record_dict.get("level") or "Entity")

        # Determine timestamp candidate
        # For academic records: passing_year is year-precision
        raw_val = (
            record_dict.get("event_time") or
            record_dict.get("timestamp") or
            record_dict.get("valid_from") or
            record_dict.get("passing_year") or
            record_dict.get("year") or
            record_dict.get("created_at")
        )
        source_created = record_dict.get("source_created_at") or record_dict.get("recorded_at")
        verified_at = record_dict.get("verified_at") or record_dict.get("verification_timestamp")

        temporal = UniversalTimestampParser.parse(
            raw_val=raw_val,
            source_name=source_name,
            record_id=rec_id,
            source_created_raw=source_created,
            verified_raw=verified_at,
            provenance_extra={"entity_kind": rec_kind},
        )

        return TemporalRecord(
            id=rec_id,
            record_type=rec_kind,
            data=record_dict,
            temporal=temporal,
        )


def get_temporal_parser(source_type: str) -> BaseTemporalParser:
    """Factory retrieving the appropriate modular parser."""
    st = source_type.upper().strip()
    if st == "JSON":
        return JsonTemporalParser()
    elif st == "CSV":
        return CsvTemporalParser()
    elif st in ("LOG", "LOGS"):
        return LogTemporalParser()
    elif st in ("DOCUMENT", "PDF", "MARKDOWN", "TEXT"):
        return DocumentTemporalParser()
    else:
        return StructuredRecordTemporalParser()


# ==============================================================================
# Temporal Data Analyzer (Filtering, Sorting, Window Comparison, Visualization)
# ==============================================================================

class TemporalDataAnalyzer:
    """Analytical engine providing time-based filtering, chronological sorting,
    historical comparisons, and timeline visualization series."""

    @classmethod
    def filter_records(
        cls,
        records: list[TemporalRecord],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        precision: Optional[TimestampPrecision | str] = None,
        validation_status: Optional[TemporalValidationStatus | str] = None,
        requires_review_only: bool = False,
        include_unbounded: bool = True,
    ) -> list[TemporalRecord]:
        """Filter records by normalized UTC timestamp range, precision, and validation status."""
        filtered = []

        for r in records:
            t = r.temporal
            if requires_review_only and not t.requires_review:
                continue

            if validation_status:
                v_stat = validation_status.value if isinstance(validation_status, TemporalValidationStatus) else str(validation_status)
                if t.validation_status.value != v_stat:
                    continue

            if precision:
                p_val = precision.value if isinstance(precision, TimestampPrecision) else str(precision)
                if t.timestamp_precision.value != p_val:
                    continue

            # Time range boundary check
            t_event = t.event_time
            t_range = t.time_range

            if start_time or end_time:
                # If record has an exact event_time
                if t_event:
                    if start_time and t_event < start_time:
                        continue
                    if end_time and t_event > end_time:
                        continue
                elif t_range:
                    # Inexact/Year-bounded record: match if intervals overlap
                    if start_time and t_range.end < start_time:
                        continue
                    if end_time and t_range.start > end_time:
                        continue
                else:
                    # Record has no temporal bounds
                    if not include_unbounded:
                        continue

            filtered.append(r)

        return filtered

    @classmethod
    def sort_chronologically(
        cls,
        records: list[TemporalRecord],
        order: str = "asc",
        nulls_last: bool = True,
    ) -> list[TemporalRecord]:
        """Sort records chronologically by event_time, falling back to time_range.start, then ingested_at."""
        is_asc = order.lower() == "asc"

        def sort_key(r: TemporalRecord) -> tuple[int, str]:
            t = r.temporal
            point = t.event_time or (t.time_range.start if t.time_range else None)
            if point is None:
                return (1 if nulls_last else -1, t.ingested_at)
            return (0, point)

        return sorted(records, key=sort_key, reverse=not is_asc)

    @classmethod
    def compare_historical_windows(
        cls,
        records: list[TemporalRecord],
        window_a_start: str,
        window_a_end: str,
        window_b_start: str,
        window_b_end: str,
        numeric_field: Optional[str] = None,
    ) -> dict[str, Any]:
        """Compare data volume, validation rates, and numeric metrics across two temporal windows."""
        records_a = cls.filter_records(records, start_time=window_a_start, end_time=window_a_end, include_unbounded=False)
        records_b = cls.filter_records(records, start_time=window_b_start, end_time=window_b_end, include_unbounded=False)

        count_a = len(records_a)
        count_b = len(records_b)

        # Measure review flags
        review_a = sum(1 for r in records_a if r.temporal.requires_review)
        review_b = sum(1 for r in records_b if r.temporal.requires_review)

        # Calculate optional numeric metric if specified (e.g. "score" or "value")
        metric_a: Optional[float] = None
        metric_b: Optional[float] = None

        if numeric_field:
            vals_a = [float(r.data[numeric_field]) for r in records_a if numeric_field in r.data and isinstance(r.data[numeric_field], (int, float))]
            vals_b = [float(r.data[numeric_field]) for r in records_b if numeric_field in r.data and isinstance(r.data[numeric_field], (int, float))]
            metric_a = sum(vals_a) / len(vals_a) if vals_a else None
            metric_b = sum(vals_b) / len(vals_b) if vals_b else None

        delta_count = count_b - count_a
        delta_pct = ((count_b - count_a) / count_a * 100.0) if count_a > 0 else 0.0

        return {
            "window_a": {
                "start": window_a_start,
                "end": window_a_end,
                "record_count": count_a,
                "flagged_for_review": review_a,
                "metric_average": metric_a,
            },
            "window_b": {
                "start": window_b_start,
                "end": window_b_end,
                "record_count": count_b,
                "flagged_for_review": review_b,
                "metric_average": metric_b,
            },
            "comparison": {
                "delta_records": delta_count,
                "percentage_change": round(delta_pct, 2),
                "metric_delta": (metric_b - metric_a) if (metric_a is not None and metric_b is not None) else None,
            },
        }

    @classmethod
    def build_timeline_visualization(
        cls,
        records: list[TemporalRecord],
    ) -> dict[str, Any]:
        """Construct structured timeline series for visualization with precision markers, gaps, and flags."""
        sorted_records = cls.sort_chronologically(records, order="asc")

        timeline_points = []
        precision_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        flagged_records = []

        for r in sorted_records:
            t = r.temporal
            prec = t.timestamp_precision.value
            status = t.validation_status.value

            precision_counts[prec] = precision_counts.get(prec, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

            if t.requires_review:
                flagged_records.append({
                    "id": r.id,
                    "record_type": r.record_type,
                    "status": status,
                    "flags": t.validation_flags,
                    "original_timestamp": t.original_event_time,
                })

            timeline_points.append({
                "id": r.id,
                "record_type": r.record_type,
                "event_time": t.event_time,
                "original_event_time": t.original_event_time,
                "timestamp_precision": prec,
                "timezone": t.timezone,
                "source_created_at": t.source_created_at,
                "ingested_at": t.ingested_at,
                "verified_at": t.verified_at,
                "is_inferred": t.is_inferred,
                "time_range": t.time_range.model_dump() if t.time_range else None,
                "validation_status": status,
                "requires_review": t.requires_review,
                "flags": t.validation_flags,
                "label": r.data.get("label") or r.data.get("name") or r.data.get("title") or r.id,
            })

        return {
            "total_records": len(sorted_records),
            "timeline_points": timeline_points,
            "precision_distribution": precision_counts,
            "validation_summary": status_counts,
            "flagged_for_review_count": len(flagged_records),
            "flagged_records": flagged_records,
        }
