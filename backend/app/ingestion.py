"""Knowledge Ingestion engine supporting JSON, CSV, Server/Application Logs, Text/Markdown, and PDF documents with universal temporal provenance tracking."""
from __future__ import annotations

import io
import time
import hashlib
from typing import Any

try:
    import pypdf as PyPDF2
except ImportError:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import PyPDF2
    except ImportError:
        PyPDF2 = None

try:
    from .temporal_universal import (
        UniversalTimestampParser,
        JsonTemporalParser,
        CsvTemporalParser,
        LogTemporalParser,
        DocumentTemporalParser,
        TemporalRecord,
        TimestampPrecision,
        TemporalValidationStatus,
        get_temporal_parser,
    )
except (ImportError, ValueError):
    from app.temporal_universal import (
        UniversalTimestampParser,
        JsonTemporalParser,
        CsvTemporalParser,
        LogTemporalParser,
        DocumentTemporalParser,
        TemporalRecord,
        TimestampPrecision,
        TemporalValidationStatus,
        get_temporal_parser,
    )


def compute_checksum(content: bytes | str) -> str:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(raw).hexdigest()[:16]


class KnowledgeIngestionManager:
    def __init__(self, store: Any) -> None:
        self.store = store
        self.json_parser = JsonTemporalParser()
        self.csv_parser = CsvTemporalParser()
        self.log_parser = LogTemporalParser()
        self.doc_parser = DocumentTemporalParser()

    def ingest_json(self, data: dict[str, Any] | list[dict[str, Any]], source_name: str = "json_import") -> dict[str, Any]:
        """Ingest structured JSON entities and relationships with universal temporal normalization."""
        items = data if isinstance(data, list) else data.get("entities", [])
        edges_to_create = data.get("relationships", []) if isinstance(data, dict) else []

        ingested_nodes = []
        errors = []
        temporal_records: list[dict[str, Any]] = []

        if not items and not edges_to_create:
            return {
                "status": "error",
                "message": "No entities or relationships found in JSON payload.",
                "ingested_count": 0,
                "errors": ["Empty payload"]
            }

        # Parse universal temporal metadata across items
        parsed_temporals = self.json_parser.parse(items, source_name=source_name)
        temporal_map = {r.id: r.temporal for r in parsed_temporals}

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"Item #{idx}: Expected dict, received {type(item).__name__}")
                continue
            name = item.get("name") or item.get("label")
            if not name or not str(name).strip():
                errors.append(f"Item #{idx}: Missing required 'name' or 'label' field.")
                continue

            kind = item.get("kind", "Entity").strip() or "Entity"
            detail = item.get("detail", "").strip()
            related_to = item.get("related_to")
            rel = item.get("relationship", "RELATED_TO")

            # Extract associated universal temporal record
            item_key = str(item.get("id") or name)
            t_obj = temporal_map.get(item_key)

            try:
                result = self.store.add_entity(
                    name=str(name).strip(),
                    kind=kind,
                    detail=detail,
                    related_to=related_to,
                    relationship=rel,
                )
                node = result["node"]

                # Enrich node with temporal provenance
                if t_obj:
                    t_dump = t_obj.model_dump()
                    node["temporal"] = t_dump
                    if t_obj.event_time:
                        node["valid_from"] = t_obj.event_time
                    temporal_records.append({"node_id": node["id"], "temporal": t_dump})

                ingested_nodes.append(node)
            except Exception as e:
                errors.append(f"Error ingesting '{name}': {str(e)}")

        for rel_def in edges_to_create:
            if isinstance(rel_def, dict) and "source" in rel_def and "target" in rel_def:
                try:
                    self.store.add_edge(rel_def["source"], rel_def["target"], rel_def.get("label", "RELATED_TO"))
                except Exception as e:
                    errors.append(f"Error creating edge: {str(e)}")

        # Calculate temporal summary
        temporal_summary = {
            "valid": sum(1 for t in temporal_records if t["temporal"]["validation_status"] == "VALID"),
            "flagged_for_review": sum(1 for t in temporal_records if t["temporal"]["requires_review"]),
        }

        return {
            "status": "partial_success" if errors and ingested_nodes else ("error" if errors else "success"),
            "source_type": "JSON",
            "source_name": source_name,
            "ingested_nodes_count": len(ingested_nodes),
            "errors": errors,
            "temporal_summary": temporal_summary,
            "temporal_records": temporal_records,
            "provenance": {
                "source": source_name,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_processed": len(items),
            },
        }

    def ingest_csv(self, content: str | bytes, source_name: str = "csv_import") -> dict[str, Any]:
        """Ingest tabular CSV rows with automatic delimiter & date column detection and universal timestamps."""
        parsed_records = self.csv_parser.parse(content=content, source_name=source_name)
        if not parsed_records:
            return {
                "status": "error",
                "message": f"No valid rows found in CSV source '{source_name}'.",
                "ingested_nodes_count": 0,
                "errors": ["Empty or unparseable CSV content"],
            }

        ingested_nodes = []
        errors = []
        temporal_records = []

        for prec in parsed_records:
            row_data = prec.data
            name = row_data.get("name") or row_data.get("title") or row_data.get("label") or prec.id
            kind = row_data.get("kind") or row_data.get("type") or "CsvRecord"

            # Create detailed summary from row keys
            detail_items = [f"{k}: {v}" for k, v in row_data.items() if k not in ("name", "title", "label", "kind", "type")][:5]
            detail_str = "; ".join(detail_items)

            try:
                result = self.store.add_entity(
                    name=str(name).strip(),
                    kind=kind,
                    detail=f"From {source_name}. {detail_str}",
                )
                node = result["node"]
                t_dump = prec.temporal.model_dump()
                node["temporal"] = t_dump
                if prec.temporal.event_time:
                    node["valid_from"] = prec.temporal.event_time

                ingested_nodes.append(node)
                temporal_records.append({"node_id": node["id"], "temporal": t_dump})
            except Exception as e:
                errors.append(f"Error ingesting CSV row '{name}': {str(e)}")

        temporal_summary = {
            "valid": sum(1 for t in temporal_records if t["temporal"]["validation_status"] == "VALID"),
            "flagged_for_review": sum(1 for t in temporal_records if t["temporal"]["requires_review"]),
        }

        return {
            "status": "partial_success" if errors and ingested_nodes else ("error" if errors else "success"),
            "source_type": "CSV",
            "source_name": source_name,
            "ingested_nodes_count": len(ingested_nodes),
            "errors": errors,
            "temporal_summary": temporal_summary,
            "temporal_records": temporal_records,
            "provenance": {
                "source": source_name,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_processed": len(parsed_records),
            },
        }

    def ingest_log(self, content: str | bytes, source_name: str = "app_log") -> dict[str, Any]:
        """Ingest server or application logs, extracting precise timestamps and event levels."""
        parsed_records = self.log_parser.parse(content=content, source_name=source_name)
        if not parsed_records:
            return {
                "status": "error",
                "message": f"No log entries found in source '{source_name}'.",
                "ingested_nodes_count": 0,
                "errors": ["Empty or unparseable log content"],
            }

        ingested_nodes = []
        errors = []
        temporal_records = []

        for prec in parsed_records:
            log_data = prec.data
            msg = log_data.get("message") or log_data.get("request") or log_data.get("raw_line") or "Log Event"
            level = log_data.get("level") or "INFO"
            name = f"Log_{prec.id}"

            try:
                result = self.store.add_entity(
                    name=name,
                    kind="LogEntry",
                    detail=f"[{level}] {msg[:240]}",
                )
                node = result["node"]
                t_dump = prec.temporal.model_dump()
                node["temporal"] = t_dump
                if prec.temporal.event_time:
                    node["valid_from"] = prec.temporal.event_time

                ingested_nodes.append(node)
                temporal_records.append({"node_id": node["id"], "temporal": t_dump})
            except Exception as e:
                errors.append(f"Error ingesting log entry '{name}': {str(e)}")

        temporal_summary = {
            "valid": sum(1 for t in temporal_records if t["temporal"]["validation_status"] == "VALID"),
            "flagged_for_review": sum(1 for t in temporal_records if t["temporal"]["requires_review"]),
        }

        return {
            "status": "partial_success" if errors and ingested_nodes else ("error" if errors else "success"),
            "source_type": "LOG",
            "source_name": source_name,
            "ingested_nodes_count": len(ingested_nodes),
            "errors": errors,
            "temporal_summary": temporal_summary,
            "temporal_records": temporal_records,
            "provenance": {
                "source": source_name,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_processed": len(parsed_records),
            },
        }

    def ingest_text_markdown(self, title: str, text: str, source_name: str = "document_upload") -> dict[str, Any]:
        """Ingest free-form text or Markdown document, extracting candidate relationships and temporal frontmatter."""
        clean_text = text.strip()
        if not clean_text:
            return {"status": "error", "message": "Content cannot be empty.", "errors": ["Empty text payload"]}

        checksum = compute_checksum(clean_text)
        doc_name = title.strip() or f"Doc_{checksum[:8]}"
        snippet = clean_text[:280] + ("..." if len(clean_text) > 280 else "")

        # Extract temporal metadata
        parsed_doc = self.doc_parser.parse(clean_text, source_name=source_name, metadata={"id": doc_name})
        t_dump = parsed_doc[0].temporal.model_dump() if parsed_doc else None

        # Create Document Node in Graph
        doc_result = self.store.add_entity(
            name=doc_name,
            kind="Document",
            detail=f"Ingested from {source_name}. {snippet}",
        )
        doc_node = doc_result["node"]
        if t_dump:
            doc_node["temporal"] = t_dump
            if t_dump.get("event_time"):
                doc_node["valid_from"] = t_dump["event_time"]

        # Link to existing entities mentioned in the text
        all_nodes = self.store.graph_data()["nodes"]
        linked_entities = []
        clean_lower = clean_text.lower()

        for n in all_nodes:
            if n["id"] != doc_node["id"] and len(n["label"]) > 3:
                if n["label"].lower() in clean_lower:
                    rel_type = "INFORMS" if n["kind"] == "Project" else "DOCUMENTED_IN"
                    self.store.add_edge(doc_node["id"], n["id"], rel_type)
                    linked_entities.append({"label": n["label"], "kind": n["kind"], "relation": rel_type})

        return {
            "status": "success",
            "source_type": "Markdown/Text",
            "source_name": source_name,
            "document_node": doc_node,
            "linked_entities": linked_entities,
            "temporal": t_dump,
            "provenance": {
                "source_name": source_name,
                "checksum": checksum,
                "character_count": len(clean_text),
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            },
        }

    def ingest_pdf(self, filename: str, pdf_bytes: bytes) -> dict[str, Any]:
        """Extract text from PDF using PyPDF2 and ingest with temporal metadata & provenance."""
        if PyPDF2 is None:
            return {
                "status": "error",
                "message": "PyPDF2 is not installed. PDF ingestion is unavailable.",
                "errors": ["Missing PyPDF2 library"],
            }

        try:
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            if reader.is_encrypted:
                return {"status": "error", "message": f"PDF '{filename}' is encrypted and password-protected.", "errors": ["Encrypted PDF"]}

            extracted_text = []
            page_count = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    extracted_text.append(f"--- Page {idx + 1} ---\n{txt}")

            full_text = "\n\n".join(extracted_text).strip()
            if not full_text:
                return {
                    "status": "error",
                    "message": f"No extractable text found in '{filename}' (may contain scanned images).",
                    "errors": ["No text extracted from PDF pages"],
                }

            doc_title = filename.replace(".pdf", "").replace("_", " ").title()
            # Extract PDF CreationDate metadata
            parsed_doc = self.doc_parser.parse(full_text, source_name=filename, pdf_bytes=pdf_bytes)
            t_dump = parsed_doc[0].temporal.model_dump() if parsed_doc else None

            result = self.ingest_text_markdown(title=doc_title, text=full_text, source_name=filename)
            result["provenance"]["page_count"] = page_count
            result["source_type"] = "PDF"
            if t_dump:
                result["temporal"] = t_dump
                if result.get("document_node"):
                    result["document_node"]["temporal"] = t_dump
                    if t_dump.get("event_time"):
                        result["document_node"]["valid_from"] = t_dump["event_time"]

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to parse PDF '{filename}': {str(e)}",
                "errors": [str(e)],
            }

    def ingest_payload(self, source_type: str, content: Any, source_name: str = "import") -> dict[str, Any]:
        """Universal dispatcher for modular ingestion of JSON, CSV, LOG, or Document."""
        st = source_type.upper().strip()
        if st == "JSON":
            return self.ingest_json(content, source_name=source_name)
        elif st == "CSV":
            return self.ingest_csv(content, source_name=source_name)
        elif st in ("LOG", "LOGS"):
            return self.ingest_log(content, source_name=source_name)
        elif st == "PDF" and isinstance(content, bytes):
            return self.ingest_pdf(source_name, content)
        else:
            return self.ingest_text_markdown(title=source_name, text=str(content), source_name=source_name)
