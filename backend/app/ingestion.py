"""Knowledge Ingestion engine supporting JSON, Text/Markdown, and PDF documents with provenance tracking."""
from __future__ import annotations

import io
import time
import hashlib
from typing import Any

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def compute_checksum(content: bytes | str) -> str:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(raw).hexdigest()[:16]


class KnowledgeIngestionManager:
    def __init__(self, store: Any) -> None:
        self.store = store

    def ingest_json(self, data: dict[str, Any] | list[dict[str, Any]], source_name: str = "json_import") -> dict[str, Any]:
        """Ingest structured JSON entities and relationships."""
        items = data if isinstance(data, list) else data.get("entities", [])
        edges_to_create = data.get("relationships", []) if isinstance(data, dict) else []

        ingested_nodes = []
        errors = []

        if not items and not edges_to_create:
            return {"status": "error", "message": "No entities or relationships found in JSON payload.", "ingested_count": 0, "errors": ["Empty payload"]}

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

            try:
                result = self.store.add_entity(
                    name=str(name).strip(),
                    kind=kind,
                    detail=detail,
                    related_to=related_to,
                    relationship=rel,
                )
                ingested_nodes.append(result["node"])
            except Exception as e:
                errors.append(f"Error ingesting '{name}': {str(e)}")

        for rel in edges_to_create:
            if isinstance(rel, dict) and "source" in rel and "target" in rel:
                try:
                    self.store.add_edge(rel["source"], rel["target"], rel.get("label", "RELATED_TO"))
                except Exception as e:
                    errors.append(f"Error creating edge: {str(e)}")

        return {
            "status": "partial_success" if errors and ingested_nodes else ("error" if errors else "success"),
            "source_type": "JSON",
            "source_name": source_name,
            "ingested_nodes_count": len(ingested_nodes),
            "errors": errors,
            "provenance": {
                "source": source_name,
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "total_processed": len(items),
            },
        }

    def ingest_text_markdown(self, title: str, text: str, source_name: str = "document_upload") -> dict[str, Any]:
        """Ingest free-form text or Markdown document, extracting candidate relationships."""
        clean_text = text.strip()
        if not clean_text:
            return {"status": "error", "message": "Content cannot be empty.", "errors": ["Empty text payload"]}

        checksum = compute_checksum(clean_text)
        doc_name = title.strip() or f"Doc_{checksum[:8]}"
        snippet = clean_text[:280] + ("..." if len(clean_text) > 280 else "")

        # Create Document Node in Graph
        doc_result = self.store.add_entity(
            name=doc_name,
            kind="Document",
            detail=f"Ingested from {source_name}. {snippet}",
        )
        doc_node = doc_result["node"]

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
            "provenance": {
                "source_name": source_name,
                "checksum": checksum,
                "character_count": len(clean_text),
                "ingested_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            },
        }

    def ingest_pdf(self, filename: str, pdf_bytes: bytes) -> dict[str, Any]:
        """Extract text from PDF using PyPDF2 and ingest with provenance."""
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
            result = self.ingest_text_markdown(title=doc_title, text=full_text, source_name=filename)
            result["provenance"]["page_count"] = page_count
            result["source_type"] = "PDF"
            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to parse PDF '{filename}': {str(e)}",
                "errors": [str(e)],
            }
