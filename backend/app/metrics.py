"""Real-time system health and telemetry metrics tracker (no fabricated data)."""
from __future__ import annotations

import time
import socket
from typing import Any
from collections import deque


class MetricsTracker:
    def __init__(self) -> None:
        self.start_time = time.time()
        self.total_requests = 0
        self.request_latencies = deque(maxlen=200)  # stores last 200 request times in ms
        self.status_codes = {"2xx": 0, "4xx": 0, "5xx": 0}
        self.ingestion_stats = {
            "total_ingested": 0,
            "errors": 0,
            "last_ingested_at": None,
            "last_error": None,
        }
        self.agent_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run_at": None,
            "total_tool_calls": 0,
        }

    def record_request(self, duration_ms: float, status_code: int) -> None:
        self.total_requests += 1
        self.request_latencies.append(duration_ms)
        if 200 <= status_code < 300:
            self.status_codes["2xx"] += 1
        elif 400 <= status_code < 500:
            self.status_codes["4xx"] += 1
        elif status_code >= 500:
            self.status_codes["5xx"] += 1

    def record_ingestion(self, count: int, error: str | None = None) -> None:
        if error:
            self.ingestion_stats["errors"] += 1
            self.ingestion_stats["last_error"] = error
        else:
            self.ingestion_stats["total_ingested"] += count
            self.ingestion_stats["last_ingested_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    def record_agent_run(self, success: bool, tool_calls_count: int) -> None:
        self.agent_stats["total_runs"] += 1
        if success:
            self.agent_stats["successful_runs"] += 1
        else:
            self.agent_stats["failed_runs"] += 1
        self.agent_stats["total_tool_calls"] += tool_calls_count
        self.agent_stats["last_run_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    def check_falkordb_socket(self, host: str, port: int) -> dict[str, Any]:
        """Measure actual socket connection latency to FalkorDB port."""
        target_host = "127.0.0.1" if host == "localhost" else host
        start = time.perf_counter()
        try:
            with socket.create_connection((target_host, port), timeout=0.15):
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return {"reachable": True, "latency_ms": round(elapsed_ms, 2)}
        except Exception as e:
            return {"reachable": False, "latency_ms": None, "error": str(e)}

    def get_summary(self, db_connected: bool, host: str, port: int, graph_name: str) -> dict[str, Any]:
        avg_latency = round(sum(self.request_latencies) / len(self.request_latencies), 2) if self.request_latencies else 0.0
        p95_latency = 0.0
        if self.request_latencies:
            sorted_lat = sorted(self.request_latencies)
            idx = int(len(sorted_lat) * 0.95)
            p95_latency = round(sorted_lat[min(idx, len(sorted_lat) - 1)], 2)

        socket_health = self.check_falkordb_socket(host, port)

        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "backend": {
                "status": "healthy",
                "total_requests": self.total_requests,
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": p95_latency,
                "status_codes": self.status_codes,
            },
            "database": {
                "type": "FalkorDB",
                "connected": db_connected,
                "graph_name": graph_name,
                "host": host,
                "port": port,
                "socket_reachable": socket_health["reachable"],
                "socket_latency_ms": socket_health["latency_ms"],
                "mode": "FalkorDB (Live)" if db_connected else "Standalone Demo (In-Memory Fallback)",
            },
            "ingestion": self.ingestion_stats,
            "multi_agent": self.agent_stats,
        }


metrics = MetricsTracker()
