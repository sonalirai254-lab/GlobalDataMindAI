# Graphwise Nexus — Graph-Native Enterprise Intelligence Platform

**WeMakeDevs × FalkorDB Graph Hacks — Track: Company Brain**

Graphwise Nexus is a graph-native organizational intelligence system that understands dependencies, preserves decision history, evaluates hypothetical changes in an isolated simulation sandbox, and produces auditable, evidence-backed conclusions.

---

## The 5 Core Product Differentiators

Graphwise Nexus rejects superficial chatbot wrappers around static graph views. Its core intelligence depends natively on connected graph topology, persistent decision memory, multi-hop relationship traversal, and verifiable evidence.

```
+-----------------------------------------------------------------------------------------+
|                                GRAPHWISE NEXUS ARCHITECTURE                             |
|                                                                                         |
|  [ User Intent ]                                                                        |
|         │                                                                               |
|         ▼                                                                               |
|  [ Entity Resolution ] ──► [ FalkorDB Cypher Engine ] ──► [ Bounded Multi-Hop Traversal ]|
|                                    │                                 │                  |
|                                    ▼                                 ▼                  |
|                        [ Why-Memory Retrieval ]            [ Ripple Blast Radius ]      |
|                                    │                                 │                  |
|                                    ▼                                 ▼                  |
|                        [ Evidence Provenance ] ──► [ Trust Ledger Verification Layer ]  |
|                                                                      │                  |
|                                                                      ▼                  |
|                                                    [ Grounded Explainable Action Plan ] |
+-----------------------------------------------------------------------------------------+
```

### 1. Ripple Intelligence (Dependency-Impact Engine)
- Traverses incoming and outgoing relationships around any project, service, task, or team.
- Pinpoints direct dependents and cascading downstream blast radius.
- Distinguishes **Confirmed Dependencies** (`[:DEPENDS_ON]`, `[:POWERS]`, `[:OWNS]`) from **Inferred Connections** (transitive governance and shared documentation).
- Computes risk ratings (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`) based on flagship project criticality and blast radius.
- Identifies trade-offs, missing documentation/runbooks, and synthesizes an actionable mitigation plan.
- Evaluates hypothetical impacts (e.g. *"What happens if the Payments API becomes unavailable for 48 hours?"*) completely isolated from the production graph.

### 2. Why-Memory (Persistent Decision Memory)
- Stores organizational decisions and meaningful facts with rich context:
  * Decision title, rationale, and supporting evidence citations.
  * Associated people, teams, and projects.
  * Valid-time temporal windows (`valid_from`, `valid_until`).
  * Outcome and verification status.
- Persists as `(:Decision)` and `(:Memory)` nodes in FalkorDB, surviving session boundaries and server restarts.
- Directly answers organizational queries:
  * *"Why did we postpone the last deployment?"*
  * *"What changed since the previous planning session?"*
  * *"Which earlier decision explains this current dependency?"*
- Rejects unverified LLM hallucinations; only cites authentic, verified graph decisions.

### 3. Hidden Connection Discovery (Bounded Multi-Hop Traversal)
- Explores indirect relationships between entities that share no direct edge.
- Bounded traversal (up to 4-5 hops) prevents combinatorial explosion and expensive unconstrained queries.
- Discloses:
  * Complete relationship chain with intermediate bridge entities.
  * Exact hop length.
  * Explicit direct relations vs inferred multi-hop connections.
  * Supporting source evidence (shared documents and decisions along the path).

### 4. Counterfactual Scenario Studio
- Interactive visual workspace for comparing alternative organizational decisions side-by-side:
  * Service downtime simulations (`DOWNTIME`).
  * Timeline delays (`DELAY`).
  * Ownership reassignment (`REASSIGN_OWNER`).
- Compares blast radius, affected node count, risk severity, and proposed mitigations.
- Operates within an isolated simulation layer.
- Authorized apply workflow: Mutating the live production graph requires explicit administrative authorization (`/api/scenarios/{id}/apply`), which simultaneously records an approved decision into Why-Memory and logs the action to the Trust Ledger.

### 5. Trust Ledger (Evidence-Provenance Layer)
- Auditable provenance ledger for every AI conclusion and reasoning session.
- Exposes:
  * Groundedness percentage (e.g. 100% Grounded vs Partially Grounded).
  * Explicit verified facts versus assumptions and synthesis.
  * Traversed graph relationships and supporting nodes.
  * Source document citations and retrieved memories.
  * Retrieval timestamp.
- Includes an **Interactive Claim Verifier**: audits any arbitrary organizational assertion against active graph topology and outputs verified status with confidence rating.

---

## 9 Integrated Platform Areas

Graphwise Nexus features an enterprise AI command center designed with graphite and near-black surfaces (`#090d17`, `#0f172a`), accented with restrained violet, indigo, and cyan:

1. **Nexus Command Center**: High-level overview combining central graph canvas, NL query interface, selected-entity details, and real-time status.
2. **Interactive Knowledge Graph**: Canvas with drag/pan/zoom, type filters, real-time node search, active neighbor highlighting, and the **Hidden Connection Discovery panel**.
3. **AI Assistant**: Graph-grounded conversational agent with grounded entity badges, path citations, verified facts inspection, and Trust Ledger links.
4. **Decision Memory (Why-Memory)**: Dedicated decision memory browser with natural-language Why-Query engine and "+ Record Decision" modal.
5. **Scenario Studio**: Visual counterfactual workspace comparing scenarios side-by-side with safe sandbox apply controls.
6. **Trust Ledger**: Audit table of reasoning conclusions, fact vs assumption breakdowns, and interactive Claim Verifier.
7. **Knowledge Ingestion**: Upload Markdown, Text, PDF, or JSON documents into FalkorDB with SHA-256 provenance checksum tracking.
8. **Agent Activity**: Multi-agent orchestration timeline featuring 4 functional agents (Research, Analysis, Planning, Verification) with ms execution logging.
9. **System Health**: Real-time API latency telemetry, FalkorDB socket ping latency, knowledge quality audit with one-click issue resolutions, and built-in Cypher console.

---

## Documented Graph Data Model

The FalkorDB graph schema is strictly versioned (`Schema v2.0.0`):

### Entities (Nodes)
- `Person`: `id`, `name`, `kind='Person'`, `detail`
- `Team`: `id`, `name`, `kind='Team'`, `detail`
- `Project`: `id`, `name`, `kind='Project'`, `detail`
- `Service`: `id`, `name`, `kind='Service'`, `detail` (Tier 1/2 microservices)
- `Task`: `id`, `name`, `kind='Task'`, `detail`
- `Document`: `id`, `name`, `kind='Document'`, `checksum`, `detail`
- `Decision`: `id`, `name`, `kind='Decision'`, `rationale`, `evidence`, `outcome`, `valid_from`, `status`
- `Memory`: `id`, `text`, `kind`, `session_id`, `approved`, `timestamp`
- `Scenario`: `id`, `name`, `target_entity_id`, `change_type`, `risk_level`, `applied`

### Relationships (Edges)
- `LEADS`: `(:Person)-[:LEADS]->(:Team)`
- `OWNS`: `(:Team)-[:OWNS]->(:Project|:Service)`
- `BUILDS`: `(:Team)-[:BUILDS]->(:Project)`, `(:Person)-[:BUILDS]->(:Task)`
- `DEPENDS_ON`: `(:Project)-[:DEPENDS_ON]->(:Project|:Service)`, `(:Service)-[:DEPENDS_ON]->(:Service)`
- `POWERS`: `(:Project|:Service)-[:POWERS]->(:Project)`
- `DOCUMENTED_IN`: `(:Project|:Service|:Decision)-[:DOCUMENTED_IN]->(:Document)`
- `AUTHORED`: `(:Person)-[:AUTHORED]->(:Document|:Decision)`
- `INFORMS`: `(:Document)-[:INFORMS]->(:Project|:Decision)`
- `DECIDED_BY`: `(:Decision)-[:DECIDED_BY]->(:Person|:Team)`
- `ENABLES`: `(:Decision)-[:ENABLES]->(:Project|:Service)`
- `EXPLAINS`: `(:Decision)-[:EXPLAINS]->(:Project|:Service|:Task)`
- `REMEMBERS`: `(:Session)-[:REMEMBERS]->(:Memory)`

---

## Windows PowerShell Setup & Running Commands

### Option A: Local Development (FastAPI + Vite)

#### 1. Start the Backend API (PowerShell)
```powershell
cd C:\Users\Lenovo\Desktop\GlobalDataMindAI\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- API Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

#### 2. Start the Frontend (In a separate PowerShell window)
```powershell
cd C:\Users\Lenovo\Desktop\GlobalDataMindAI\frontend
npm install
npm run dev
```
- Open your browser at: [http://localhost:5173](http://localhost:5173)

The Vite proxy forwards `/api/*` to `http://127.0.0.1:8000` with graceful 503 error handling during startup.

---

### Option B: Running with Docker & FalkorDB

```powershell
cd C:\Users\Lenovo\Desktop\GlobalDataMindAI
docker compose up --build
```
This launches:
1. **FalkorDB** container on `localhost:6379`
2. **FastAPI backend** container on `localhost:8000` (with automated healthcheck)
3. **React frontend** container on `localhost:5173`

---

## Running Automated Tests

Run the full automated test suite (14 unit tests covering all 5 differentiators):

```powershell
cd C:\Users\Lenovo\Desktop\GlobalDataMindAI\backend
python -m unittest discover tests
```

To verify the production frontend build:
```powershell
cd C:\Users\Lenovo\Desktop\GlobalDataMindAI\frontend
npm run build
```

---

## Core API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System connectivity status, entity counts, database mode |
| `POST` | `/api/chat` | 8-stage AI reasoning pipeline with Trust Ledger logging |
| `POST` | `/api/ripple/analyze` | Ripple Intelligence blast radius & dependency cascade |
| `GET` | `/api/decisions` | List persistent organizational decisions in Why-Memory |
| `POST` | `/api/decisions/why-query` | Natural-language query for historical decision rationale |
| `POST` | `/api/graph/connections` | Bounded multi-hop hidden connection discovery |
| `GET` | `/api/scenarios` | List preset and custom counterfactual scenarios |
| `POST` | `/api/scenarios/compare` | Side-by-side scenario blast radius & risk comparison |
| `POST` | `/api/scenarios/{id}/apply`| Authorized apply of simulated scenario to live graph |
| `GET` | `/api/trust-ledger` | List auditable evidence provenance records |
| `POST` | `/api/trust-ledger/verify-claim` | Test arbitrary claims against active graph topology |
| `POST` | `/api/agent/run` | Multi-agent coordination (Research, Analysis, Planning, Verification) |
| `GET` | `/api/quality/audit` | Knowledge graph health score and automated issue detection |
| `POST` | `/api/cypher` | Parameterized Cypher query console with safety checks |
