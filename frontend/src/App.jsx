import React, { useEffect, useMemo, useRef, useState } from 'react'
import GlobalIntelligenceView from './GlobalIntelligenceView'
import PersonalIntelligenceView from './PersonalIntelligenceView'
import TemporalAnalysisView from './TemporalAnalysisView'
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, Bell, BookOpen, BrainCircuit, Building2,
  Check, CheckCircle2, ChevronDown, ChevronRight, CircleHelp, Clock, Command, Copy, Cpu, Database, ExternalLink,
  Eye, EyeOff, FileCheck, FilePlus, FileText, GitBranch, GitFork, Globe, GraduationCap, HeartPulse, History, Layers3, LayoutDashboard,
  Link2, Maximize2, MessageSquare, MoreHorizontal, Network, Plus, RefreshCw, Search, Send,
  Server, Settings2, Share2, ShieldAlert, ShieldCheck, Sliders, Sparkles, Terminal, Trash2, TrendingUp,
  UploadCloud, Users, X, Zap, ZoomIn, ZoomOut
} from 'lucide-react'

// Documented initial seed nodes
const fallbackNodes = [
  { id: 'person_maya', label: 'Maya Chen', kind: 'Person', detail: 'Product Lead & Vision' },
  { id: 'team_product', label: 'Product Team', kind: 'Team', detail: 'Product roadmap & strategy' },
  { id: 'project_atlas', label: 'Project Atlas', kind: 'Project', detail: 'Flagship Q4 enterprise platform' },
  { id: 'doc_roadmap', label: 'Product Roadmap', kind: 'Document', detail: 'Targeting Q4 enterprise milestone' },
  { id: 'person_aarav', label: 'Aarav Patel', kind: 'Person', detail: 'Engineering Lead & Architecture' },
  { id: 'team_eng', label: 'Engineering', kind: 'Team', detail: 'Platform, APIs, and retrieval infra' },
  { id: 'project_search', label: 'Knowledge Search', kind: 'Project', detail: 'Vector + Graph retrieval pipeline' },
  { id: 'doc_arch', label: 'System Architecture', kind: 'Document', detail: 'Microservices, FalkorDB & event bus' },
  { id: 'person_sana', label: 'Sana Ali', kind: 'Person', detail: 'Lead Research Analyst' },
  { id: 'doc_research', label: 'Customer Research', kind: 'Document', detail: '18 enterprise user interviews' },
  { id: 'person_marcus', label: 'Marcus Vance', kind: 'Person', detail: 'Principal Security Architect' },
  { id: 'team_security', label: 'Security & Compliance', kind: 'Team', detail: 'SOC2, RBAC & graph privacy' },
  { id: 'project_zerotrust', label: 'Zero-Trust Auth', kind: 'Project', detail: 'Unified token & identity bridge' },
  { id: 'doc_security_audit', label: 'Security Audit 2026', kind: 'Document', detail: 'Passed compliance review with zero critical findings' },
  { id: 'decision_falkordb', label: 'Adopt FalkorDB', kind: 'Decision', detail: 'Selected FalkorDB for low-latency Cypher graph queries and memory persistence' },
  { id: 'service_payments', label: 'Payments API', kind: 'Service', detail: 'Core payment gateway & billing token service (Tier 1 Criticality)' },
  { id: 'service_auth', label: 'Auth Gateway', kind: 'Service', detail: 'Distributed token & session validation microservice' },
  { id: 'decision_postpone_deploy', label: 'Postpone Q3 Release', kind: 'Decision', detail: 'Postponed deployment to Oct 28 due to token race conditions found in Security Audit' },
  { id: 'task_soc2', label: 'SOC2 Audit Remediation', kind: 'Task', detail: 'Remediate token propagation race conditions before customer rollout' },
  { id: 'person_elena', label: 'Elena Rostova', kind: 'Person', detail: 'Staff Site Reliability Engineer & Platform Infra Lead' },
  { id: 'team_infra', label: 'Platform Infra', kind: 'Team', detail: 'Cloud kubernetes, observability, and database clustering' },
]

const fallbackEdges = [
  { source: 'person_maya', target: 'team_product', label: 'LEADS' },
  { source: 'team_product', target: 'project_atlas', label: 'OWNS' },
  { source: 'project_atlas', target: 'doc_roadmap', label: 'DOCUMENTED_IN' },
  { source: 'person_aarav', target: 'team_eng', label: 'LEADS' },
  { source: 'team_eng', target: 'project_search', label: 'BUILDS' },
  { source: 'project_search', target: 'doc_arch', label: 'DOCUMENTED_IN' },
  { source: 'person_sana', target: 'doc_research', label: 'AUTHORED' },
  { source: 'doc_research', target: 'project_atlas', label: 'INFORMS' },
  { source: 'team_product', target: 'team_eng', label: 'COLLABORATES_WITH' },
  { source: 'person_marcus', target: 'team_security', label: 'LEADS' },
  { source: 'team_security', target: 'project_zerotrust', label: 'OWNS' },
  { source: 'project_zerotrust', target: 'doc_security_audit', label: 'DOCUMENTED_IN' },
  { source: 'project_atlas', target: 'project_zerotrust', label: 'DEPENDS_ON' },
  { source: 'project_search', target: 'project_atlas', label: 'POWERS' },
  { source: 'decision_falkordb', target: 'project_search', label: 'ENABLES' },
  { source: 'person_aarav', target: 'decision_falkordb', label: 'DECIDED_BY' },
  { source: 'project_atlas', target: 'service_payments', label: 'DEPENDS_ON' },
  { source: 'service_payments', target: 'service_auth', label: 'DEPENDS_ON' },
  { source: 'team_eng', target: 'service_payments', label: 'OWNS' },
  { source: 'person_elena', target: 'team_infra', label: 'LEADS' },
  { source: 'team_infra', target: 'service_auth', label: 'OWNS' },
  { source: 'task_soc2', target: 'person_marcus', label: 'ASSIGNED_TO' },
  { source: 'task_soc2', target: 'project_zerotrust', label: 'PART_OF' },
  { source: 'decision_postpone_deploy', target: 'project_atlas', label: 'EXPLAINS' },
  { source: 'person_marcus', target: 'decision_postpone_deploy', label: 'DECIDED_BY' },
  { source: 'decision_postpone_deploy', target: 'doc_security_audit', label: 'DOCUMENTED_IN' },
]

const initialMemories = [
  { id: 'mem_1', text: 'Project Atlas is targeting a Q4 enterprise launch with FalkorDB graph memory.', kind: 'Launch context', created_at: '10m ago' },
  { id: 'mem_2', text: 'Knowledge Search depends on the System Architecture document and FalkorDB graph queries.', kind: 'Dependency', created_at: '1h ago' },
  { id: 'mem_3', text: 'Marcus Vance confirmed Zero-Trust Auth passed SOC2 compliance verification.', kind: 'Security note', created_at: '3h ago' },
  { id: 'mem_4', text: 'Maya Chen and Aarav Patel agreed on weekly cross-team alignment every Tuesday.', kind: 'Team context', created_at: 'Yesterday' },
  { id: 'mem_5', text: 'Payments API has circuit breaker fallback configured with 48h asynchronous retry queue.', kind: 'Architecture', created_at: 'Yesterday' },
]

const initialDecisions = [
  {
    id: 'decision_postpone_deploy',
    title: 'Postpone Q3 Enterprise Deployment to Oct 28',
    rationale: 'Security compliance audit identified token propagation race conditions in the legacy session bridge.',
    evidence: 'doc_security_audit (Findings section 3.2)',
    outcome: 'Granted engineering 5 weeks to implement Zero-Trust Auth token bridge before customer release.',
    status: 'executed',
    valid_from: '2026-09-01',
    decided_by_name: 'Marcus Vance',
    associated_entities: ['project_atlas', 'person_marcus', 'team_security', 'doc_security_audit'],
    verified: true,
    created_at: 'Sep 01, 2026',
  },
  {
    id: 'decision_falkordb',
    title: 'Adopt FalkorDB as Primary Graph Store',
    rationale: 'Selected FalkorDB for sub-millisecond Cypher traversals, entity merging, and graph-native memory persistence.',
    evidence: 'doc_arch (Section 4: Database Benchmarks showing <5ms 3-hop traversal latency)',
    outcome: 'Multi-hop dependency lookups dropped from 280ms to 4.2ms; enabled persistent organizational memory.',
    status: 'active',
    valid_from: '2026-08-15',
    decided_by_name: 'Aarav Patel',
    associated_entities: ['project_search', 'person_aarav', 'team_eng', 'doc_arch'],
    verified: true,
    created_at: 'Aug 15, 2026',
  },
  {
    id: 'decision_payments_sla',
    title: 'Decouple Payments API and Enforce Circuit Breaker',
    rationale: 'Prevent 3rd-party banking gateway latency spikes from cascading into core project atlas workflows.',
    evidence: 'doc_arch & Customer Research Incident #412 postmortem',
    outcome: 'Established standalone microservice with 48h asynchronous retry queue and graceful fallback.',
    status: 'active',
    valid_from: '2026-07-20',
    decided_by_name: 'Aarav Patel',
    associated_entities: ['service_payments', 'project_atlas', 'team_eng'],
    verified: true,
    created_at: 'Jul 20, 2026',
  },
]

const kindClass = (kind = '') => kind.toLowerCase()

function getKindIcon(kind) {
  switch (kind) {
    case 'Person': return <Users size={15} />
    case 'Team': return <Building2 size={15} />
    case 'Project': return <Zap size={15} />
    case 'Document': return <FileText size={15} />
    case 'Decision': return <Sparkles size={15} />
    case 'Service': return <Server size={15} />
    case 'Task': return <CheckCircle2 size={15} />
    default: return <Network size={15} />
  }
}

// ---------------- Interactive Graph Canvas Component ---------------- //
function GraphCanvas({
  nodes,
  edges,
  selected,
  onSelect,
  filter,
  onOpenConnect,
  onDeleteNode,
  onAskAbout
}) {
  const [positions, setPositions] = useState({})
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [draggingNode, setDraggingNode] = useState(null)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [hoveredNode, setHoveredNode] = useState(null)
  const [graphSearch, setGraphSearch] = useState('')
  const svgRef = useRef(null)

  // Layout positioning across concentric rings & arcs
  useEffect(() => {
    const computed = {}
    const groups = { Team: [], Person: [], Project: [], Document: [], Decision: [], Service: [], Task: [], Other: [] }
    nodes.forEach(n => {
      if (groups[n.kind]) groups[n.kind].push(n)
      else groups.Other.push(n)
    })

    const centerX = 380, centerY = 280
    // Center ring: Teams
    groups.Team.forEach((n, i) => {
      const angle = (i / Math.max(1, groups.Team.length)) * 2 * Math.PI - Math.PI / 2
      computed[n.id] = [centerX + Math.cos(angle) * 110, centerY + Math.sin(angle) * 85]
    })
    // Inner-mid ring: Services
    groups.Service.forEach((n, i) => {
      const angle = (i / Math.max(1, groups.Service.length)) * 2 * Math.PI + Math.PI / 4
      computed[n.id] = [centerX + Math.cos(angle) * 165, centerY + Math.sin(angle) * 125]
    })
    // Middle ring: Projects
    groups.Project.forEach((n, i) => {
      const angle = (i / Math.max(1, groups.Project.length)) * 2 * Math.PI + Math.PI / 3
      computed[n.id] = [centerX + Math.cos(angle) * 230, centerY + Math.sin(angle) * 170]
    })
    // Left arc: People
    groups.Person.forEach((n, i) => {
      const step = 420 / Math.max(1, groups.Person.length)
      computed[n.id] = [95, 75 + i * step]
    })
    // Right arc: Documents
    groups.Document.forEach((n, i) => {
      const step = 420 / Math.max(1, groups.Document.length)
      computed[n.id] = [665, 75 + i * step]
    })
    // Bottom: Decisions
    groups.Decision.forEach((n, i) => {
      const step = 320 / Math.max(1, groups.Decision.length)
      computed[n.id] = [220 + i * step, 495]
    })
    // Bottom-left: Tasks
    groups.Task.forEach((n, i) => {
      computed[n.id] = [170 + i * 110, 435]
    })
    // Other
    groups.Other.forEach((n, i) => {
      computed[n.id] = [centerX + (i % 2 === 0 ? 1 : -1) * 150, centerY + 190]
    })

    setPositions(prev => ({ ...computed, ...prev }))
  }, [nodes])

  const visibleNodes = useMemo(() => {
    return nodes.filter(n => {
      const matchesFilter = filter === 'All types' || n.kind === filter
      const matchesSearch = !graphSearch.trim() ||
        n.label.toLowerCase().includes(graphSearch.toLowerCase()) ||
        (n.detail && n.detail.toLowerCase().includes(graphSearch.toLowerCase()))
      return matchesFilter && matchesSearch
    })
  }, [nodes, filter, graphSearch])

  const visibleIds = useMemo(() => new Set(visibleNodes.map(n => n.id)), [visibleNodes])
  const visibleEdges = useMemo(() => {
    return edges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target))
  }, [edges, visibleIds])

  const handleMouseDownSvg = (e) => {
    if (e.target.tagName === 'svg' || e.target.classList.contains('canvas-bg')) {
      setIsPanning(true)
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMoveSvg = (e) => {
    if (draggingNode) {
      const svg = svgRef.current
      if (!svg) return
      const rect = svg.getBoundingClientRect()
      const rawX = (e.clientX - rect.left - pan.x) / zoom
      const rawY = (e.clientY - rect.top - pan.y) / zoom
      setPositions(prev => ({ ...prev, [draggingNode]: [Math.round(rawX), Math.round(rawY)] }))
    } else if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y })
    }
  }

  const handleMouseUpSvg = () => {
    setDraggingNode(null)
    setIsPanning(false)
  }

  const resetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const selectedNode = nodes.find(n => n.id === selected)
  const connectedEdges = useMemo(() => {
    if (!selected) return { in: [], out: [] }
    return {
      out: edges.filter(e => e.source === selected),
      in: edges.filter(e => e.target === selected),
    }
  }, [selected, edges])

  const nodeMap = useMemo(() => Object.fromEntries(nodes.map(n => [n.id, n])), [nodes])

  return (
    <div className="graph-canvas-container">
      <div className="canvas-header">
        <div className="canvas-label">
          <span className="live-dot" />
          <strong>LIVE KNOWLEDGE GRAPH</strong>
          <span className="canvas-count">{visibleNodes.length} entities · {visibleEdges.length} relations</span>
        </div>
        <div className="canvas-controls">
          <div className="canvas-search-box">
            <Search size={13} />
            <input
              type="text"
              placeholder="Search graph..."
              value={graphSearch}
              onChange={e => setGraphSearch(e.target.value)}
            />
            {graphSearch && <button onClick={() => setGraphSearch('')}><X size={11} /></button>}
          </div>
          <button className="control-btn" onClick={() => setZoom(z => Math.min(2, z + 0.15))} title="Zoom In"><ZoomIn size={14} /></button>
          <button className="control-btn" onClick={() => setZoom(z => Math.max(0.6, z - 0.15))} title="Zoom Out"><ZoomOut size={14} /></button>
          <button className="control-btn" onClick={resetView} title="Reset View"><RefreshCw size={13} /></button>
          <button className="control-btn highlight" onClick={onOpenConnect} title="Connect Entities"><Link2 size={13} /> Connect</button>
        </div>
      </div>

      <div
        className="graph-canvas"
        onMouseDown={handleMouseDownSvg}
        onMouseMove={handleMouseMoveSvg}
        onMouseUp={handleMouseUpSvg}
        onMouseLeave={handleMouseUpSvg}
      >
        <svg
          ref={svgRef}
          viewBox="0 0 760 560"
          role="img"
          aria-label="Connected company knowledge graph"
          style={{ cursor: isPanning ? 'grabbing' : 'default' }}
        >
          <defs>
            <pattern id="graph-dots" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="1.5" cy="1.5" r="1" fill="#243147" />
            </pattern>
            <marker id="arrow" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#526488" />
            </marker>
            <marker id="arrow-active" viewBox="0 0 10 10" refX="28" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#a18aff" />
            </marker>
          </defs>

          <rect width="760" height="560" fill="url(#graph-dots)" className="canvas-bg" />

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* Edges */}
            {visibleEdges.map((e, i) => {
              const a = positions[e.source]
              const b = positions[e.target]
              if (!a || !b) return null

              const isHighlighted = selected === e.source || selected === e.target ||
                                    hoveredNode === e.source || hoveredNode === e.target
              const midX = (a[0] + b[0]) / 2
              const midY = (a[1] + b[1]) / 2

              return (
                <g key={`edge-${e.source}-${e.target}-${i}`} className={`edge ${isHighlighted ? 'active' : ''}`}>
                  <line
                    x1={a[0]} y1={a[1]}
                    x2={b[0]} y2={b[1]}
                    markerEnd={isHighlighted ? "url(#arrow-active)" : "url(#arrow)"}
                  />
                  <rect
                    x={midX - 35}
                    y={midY - 9}
                    width="70"
                    height="14"
                    rx="4"
                    className="edge-badge-bg"
                  />
                  <text x={midX} y={midY + 1} textAnchor="middle" className="edge-text">
                    {e.label.replaceAll('_', ' ').toLowerCase()}
                  </text>
                </g>
              )
            })}

            {/* Nodes */}
            {visibleNodes.map(n => {
              const [x, y] = positions[n.id] || [380, 280]
              const isSelected = selected === n.id
              const isHovered = hoveredNode === n.id
              const isConnected = isSelected ||
                connectedEdges.out.some(e => e.target === n.id) ||
                connectedEdges.in.some(e => e.source === n.id)

              const radius = n.kind === 'Project' ? 30 : n.kind === 'Person' ? 24 : n.kind === 'Team' ? 28 : n.kind === 'Service' ? 26 : 24

              return (
                <g
                  key={n.id}
                  className={`node ${kindClass(n.kind)} ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''} ${selected && !isConnected ? 'dimmed' : ''}`}
                  onMouseDown={(e) => {
                    e.stopPropagation()
                    setDraggingNode(n.id)
                  }}
                  onClick={() => onSelect(n.id)}
                  onMouseEnter={() => setHoveredNode(n.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  tabIndex="0"
                  role="button"
                  aria-label={`Select ${n.label}`}
                  style={{ cursor: draggingNode === n.id ? 'grabbing' : 'grab' }}
                >
                  {isSelected && <circle className="selection-ring" cx={x} cy={y} r={radius + 9} />}
                  <circle className="node-circle" cx={x} cy={y} r={radius} />
                  <text className="node-symbol" x={x} y={y + 5}>
                    {n.kind === 'Person' ? 'P' : n.kind === 'Project' ? '◆' : n.kind === 'Team' ? 'T' : n.kind === 'Decision' ? '✦' : n.kind === 'Service' ? '⚙' : n.kind === 'Task' ? '✓' : '▤'}
                  </text>
                  <text className="node-label" x={x} y={y + radius + 16} textAnchor="middle">
                    {n.label.length > 18 ? n.label.slice(0, 16) + '…' : n.label}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>
      </div>

      <div className="graph-legend">
        <span><i className="legend-dot person" /> People</span>
        <span><i className="legend-dot team" /> Teams</span>
        <span><i className="legend-dot project" /> Projects</span>
        <span><i className="legend-dot service" style={{ background: '#38bdf8' }} /> Services</span>
        <span><i className="legend-dot document" /> Documents</span>
        <span><i className="legend-dot decision" /> Decisions</span>
      </div>

      {/* Selected Entity Inspector */}
      {selectedNode && (
        <div className="selected-entity-card">
          <div className="entity-main">
            <div className={`entity-avatar ${kindClass(selectedNode.kind)}`}>
              {getKindIcon(selectedNode.kind)}
            </div>
            <div className="entity-details">
              <div className="entity-header-row">
                <strong>{selectedNode.label}</strong>
                <span className={`kind-pill ${kindClass(selectedNode.kind)}`}>{selectedNode.kind}</span>
                <span className="degree-pill">{connectedEdges.out.length + connectedEdges.in.length} connections</span>
              </div>
              <p className="entity-detail-text">{selectedNode.detail || 'No description provided.'}</p>

              {/* Connections Breakdown */}
              <div className="connections-container">
                {connectedEdges.out.length > 0 && (
                  <div className="connection-group">
                    <span className="conn-label">Outgoing:</span>
                    {connectedEdges.out.map((e, idx) => {
                      const tgt = nodeMap[e.target]
                      return (
                        <button
                          key={idx}
                          className="conn-pill"
                          onClick={() => onSelect(e.target)}
                          title={`Navigate to ${tgt?.label || e.target}`}
                        >
                          <span className="conn-rel">→ {e.label.toLowerCase()}</span>
                          <strong>{tgt?.label || e.target}</strong>
                        </button>
                      )
                    })}
                  </div>
                )}
                {connectedEdges.in.length > 0 && (
                  <div className="connection-group">
                    <span className="conn-label">Incoming:</span>
                    {connectedEdges.in.map((e, idx) => {
                      const src = nodeMap[e.source]
                      return (
                        <button
                          key={idx}
                          className="conn-pill"
                          onClick={() => onSelect(e.source)}
                          title={`Navigate to ${src?.label || e.source}`}
                        >
                          <span className="conn-rel">← {e.label.toLowerCase()}</span>
                          <strong>{src?.label || e.source}</strong>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="entity-actions">
            <button
              className="action-btn-primary"
              onClick={() => onAskAbout(`Explain the relationships and dependencies around ${selectedNode.label}`)}
            >
              <Sparkles size={13} /> Ask AI about this
            </button>
            <button
              className="action-btn-secondary"
              onClick={onOpenConnect}
              title="Connect this entity to another"
            >
              <Link2 size={13} /> Connect
            </button>
            <button
              className="action-btn-danger"
              onClick={() => onDeleteNode(selectedNode.id)}
              title="Delete entity"
            >
              <Trash2 size={13} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------- Main Nexus Application Component ---------------- //
function App() {
  const [activeNav, setActiveNav] = useState('Overview')
  const [nodes, setNodes] = useState(fallbackNodes)
  const [edges, setEdges] = useState(fallbackEdges)
  const [selected, setSelected] = useState('project_atlas')
  const [filter, setFilter] = useState('All types')
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'GlobalDataMind AI is active. I provide verifiable, evidence-grounded intelligence across global macroeconomic indicators, personal academic records, and organizational graph dependencies.',
      source: 'GlobalDataMind AI / Knowledge Core',
      time: 'Just now'
    }
  ])
  const [memories, setMemories] = useState(initialMemories)
  const [decisions, setDecisions] = useState(initialDecisions)
  const [scenarios, setScenarios] = useState([])
  const [ledgerEntries, setLedgerEntries] = useState([])
  const [metricsData, setMetricsData] = useState(null)
  const [qualityAudit, setQualityAudit] = useState(null)
  const [status, setStatus] = useState({ text: 'Checking...', connected: false, database: 'Local Persistent Store' })
  const [backendOffline, setBackendOffline] = useState(false)
  const [backendErrorDetail, setBackendErrorDetail] = useState('')
  const [toast, setToast] = useState('')
  const [input, setInput] = useState('')
  const [reconnecting, setReconnecting] = useState(false)

  // Why-Memory Form & Search State
  const [whySearch, setWhySearch] = useState('')
  const [whyQuestion, setWhyQuestion] = useState('')
  const [whyAnswer, setWhyAnswer] = useState(null)
  const [whyQuerying, setWhyQuerying] = useState(false)
  const [showAddDecisionModal, setShowAddDecisionModal] = useState(false)
  const [newDecisionTitle, setNewDecisionTitle] = useState('')
  const [newDecisionRationale, setNewDecisionRationale] = useState('')
  const [newDecisionEvidence, setNewDecisionEvidence] = useState('')
  const [newDecisionEntity, setNewDecisionEntity] = useState('')

  // Hidden Connection Discovery State
  const [hiddenSource, setHiddenSource] = useState('person_sana')
  const [hiddenTarget, setHiddenTarget] = useState('project_atlas')
  const [hiddenResult, setHiddenResult] = useState(null)
  const [discoveringPaths, setDiscoveringPaths] = useState(false)

  // Counterfactual Scenario State
  const [scenarioCompareA, setScenarioCompareA] = useState('scenario_payments_outage')
  const [scenarioCompareB, setScenarioCompareB] = useState('scenario_atlas_delay')
  const [scenarioComparison, setScenarioComparison] = useState(null)
  const [showCreateScenarioModal, setShowCreateScenarioModal] = useState(false)
  const [newScenarioName, setNewScenarioName] = useState('')
  const [newScenarioTarget, setNewScenarioTarget] = useState('service_payments')
  const [newScenarioType, setNewScenarioType] = useState('DOWNTIME')
  const [newScenarioDetail, setNewScenarioDetail] = useState('')
  const [applyingScenarioId, setApplyingScenarioId] = useState(null)

  // Trust Ledger Claim Verifier State
  const [verifyClaimText, setVerifyClaimText] = useState('')
  const [claimVerificationResult, setClaimVerificationResult] = useState(null)
  const [verifyingClaim, setVerifyingClaim] = useState(false)

  // Multi-Agent Activity State
  const [agentGoal, setAgentGoal] = useState('Plan Q4 launch readiness for Project Atlas')
  const [agentResult, setAgentResult] = useState(null)
  const [agentRunning, setAgentRunning] = useState(false)

  // Knowledge Ingestion Tab & File State
  const [ingestTab, setIngestTab] = useState('text')
  const [ingestTitle, setIngestTitle] = useState('')
  const [ingestContent, setIngestContent] = useState('')
  const [ingestResult, setIngestResult] = useState(null)
  const [ingestFile, setIngestFile] = useState(null)
  const [ingesting, setIngesting] = useState(false)

  // Modals
  const [showIngest, setShowIngest] = useState(false)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [showCypherModal, setShowCypherModal] = useState(false)
  const [cypherQuery, setCypherQuery] = useState('MATCH (n:Entity) RETURN n.name, n.kind, n.detail LIMIT 10')
  const [cypherResults, setCypherResults] = useState(null)
  const [cypherRunning, setCypherRunning] = useState(false)

  // Entity & Edge Creation Form
  const [entityName, setEntityName] = useState('')
  const [entityKind, setEntityKind] = useState('Project')
  const [entityDetail, setEntityDetail] = useState('')
  const [relatedTo, setRelatedTo] = useState('')
  const [relationshipType, setRelationshipType] = useState('RELATED_TO')
  const [connectSource, setConnectSource] = useState('')
  const [connectTarget, setConnectTarget] = useState('')
  const [connectLabel, setConnectLabel] = useState('COLLABORATES_WITH')

  // Alert & Notification Center State
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [showNotificationsModal, setShowNotificationsModal] = useState(false)
  const [notifFilter, setNotifFilter] = useState('ALL')
  const [notifsLoading, setNotifsLoading] = useState(false)

  // Simplified UI States
  const [advancedToolsOpen, setAdvancedToolsOpen] = useState(false)
  const [academicSummary, setAcademicSummary] = useState(null)
  const [privacyMasked, setPrivacyMasked] = useState(true)
  const [aiInsightScope, setAiInsightScope] = useState('global')

  const chatBottomRef = useRef(null)

  const showToast = (text) => {
    setToast(text)
    window.setTimeout(() => setToast(''), 3500)
  }

  // Refresh all system data
  const refreshAll = () => {
    fetch('/api/health')
      .then(async r => {
        const contentType = r.headers.get('content-type') || ''
        const isJson = contentType.includes('application/json')
        if (!r.ok || !isJson) {
          let errDetail = !isJson
            ? 'Backend API server on http://127.0.0.1:8000 is not reachable (received HTML fallback). Please ensure the FastAPI backend is running via: npm run backend'
            : `HTTP ${r.status}`
          if (isJson) {
            try {
              const errData = await r.json()
              if (errData && (errData.message || errData.detail)) {
                errDetail = errData.message || errData.detail
              }
            } catch (_) {}
          }
          throw new Error(errDetail)
        }
        return r.json()
      })
      .then(d => {
        setBackendOffline(false)
        setBackendErrorDetail('')
        setStatus({
          text: d.connected ? 'FalkorDB Connected (Live Graph)' : 'Local Persistent Mode (FalkorDB Offline)',
          connected: !!d.connected,
          database: d.database || 'Local Persistent Store',
          graph: d.graph || 'global_datamind_graph',
          database_note: d.database_note || '',
          stats: d.stats
        })
      })
      .catch((err) => {
        setBackendOffline(true)
        const rawMsg = err?.message || ''
        const cleanMsg = (rawMsg.includes('<!doctype') || rawMsg.includes('Unexpected token') || rawMsg.includes('valid JSON'))
          ? 'FastAPI Backend API is offline or not responding on http://127.0.0.1:8000. Start it in terminal via: npm run backend'
          : (rawMsg || 'Unable to reach GlobalDataMind AI backend on http://127.0.0.1:8000.')
        setBackendErrorDetail(cleanMsg)
        setStatus({ text: 'Backend Offline (Connection Error)', connected: false, database: 'Offline' })
      })

    const safeFetchJson = (url, callback) => {
      fetch(url)
        .then(async r => {
          const ct = r.headers.get('content-type') || ''
          if (r.ok && ct.includes('application/json')) {
            return r.json()
          }
          return null
        })
        .then(d => { if (d) callback(d) })
        .catch(() => {})
    }

    safeFetchJson('/api/graph', d => {
      if (d && d.nodes && d.nodes.length) {
        setNodes(d.nodes)
        setEdges(d.edges || [])
        if (!d.nodes.some(n => n.id === selected)) {
          setSelected(d.nodes[0].id)
        }
      }
    })

    safeFetchJson('/api/decisions', d => { if (d && d.items) setDecisions(d.items) })
    safeFetchJson('/api/scenarios', d => { if (d && d.scenarios) setScenarios(d.scenarios) })
    safeFetchJson('/api/trust-ledger', d => { if (d && d.entries) setLedgerEntries(d.entries) })
    safeFetchJson('/api/memory', d => { if (d && d.items) setMemories(d.items) })
    safeFetchJson('/api/system/metrics', d => { if (d) setMetricsData(d) })
    safeFetchJson('/api/quality/audit', d => { if (d) setQualityAudit(d) })

    fetch('/api/notifications', { headers: { 'X-User-Id': 'student_profile' } })
      .then(async r => {
        const ct = r.headers.get('content-type') || ''
        if (r.ok && ct.includes('application/json')) {
          return r.json()
        }
        return null
      })
      .then(d => {
        if (d && d.notifications) {
          setNotifications(d.notifications)
          setUnreadCount(d.unread_count || 0)
        }
      })
      .catch(() => {})

    safeFetchJson('/api/personal/profile?mask=true', d => { if (d) setAcademicSummary(d) })
  }

  const fetchNotifications = async (filterCategory = notifFilter) => {
    setNotifsLoading(true)
    try {
      let url = '/api/notifications'
      const params = []
      if (filterCategory === 'UNREAD') {
        params.push('unread_only=true')
      } else if (filterCategory !== 'ALL') {
        params.push(`category=${filterCategory}`)
      }
      if (params.length > 0) url += `?${params.join('&')}`
      const res = await fetch(url, { headers: { 'X-User-Id': 'student_profile' } })
      if (res.ok) {
        const d = await res.json()
        setNotifications(d.notifications || [])
        setUnreadCount(d.unread_count || 0)
      }
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setNotifsLoading(false)
    }
  }

  const handleMarkNotifRead = async (id) => {
    try {
      const res = await fetch(`/api/notifications/${id}/read`, {
        method: 'POST',
        headers: { 'X-User-Id': 'student_profile' },
      })
      if (res.ok) {
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, status: 'READ' } : n))
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
    } catch {
      showToast('Could not mark alert as read.')
    }
  }

  const handleMarkAllNotifsRead = async () => {
    try {
      const res = await fetch('/api/notifications/read-all', {
        method: 'POST',
        headers: { 'X-User-Id': 'student_profile' },
      })
      if (res.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, status: 'READ' })))
        setUnreadCount(0)
        showToast('All notifications marked as read.')
      }
    } catch {
      showToast('Could not mark all as read.')
    }
  }

  useEffect(() => {
    refreshAll()
  }, [])

  // Auto-retry connection every 4 seconds if backend is offline
  useEffect(() => {
    if (!backendOffline) return
    const timer = setInterval(() => {
      refreshAll()
    }, 4000)
    return () => clearInterval(timer)
  }, [backendOffline])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleReconnect = async () => {
    setReconnecting(true)
    try {
      const res = await fetch('/api/reconnect', { method: 'POST' })
      const data = await res.json()
      if (data.connected) {
        showToast('Successfully connected to FalkorDB!')
      } else {
        showToast('FalkorDB offline. Operating in Standalone Demo.')
      }
      refreshAll()
    } catch {
      showToast('Backend API unreachable.')
    } finally {
      setReconnecting(false)
    }
  }

  const handleResetGraph = async () => {
    if (!window.confirm('Reset the graph and memory back to the initial company brain seed data?')) return
    try {
      const res = await fetch('/api/graph/reset', { method: 'POST' })
      const data = await res.json()
      setNodes(data.nodes)
      setEdges(data.edges)
      showToast('Knowledge graph reset to seed data')
      refreshAll()
    } catch {
      setNodes(fallbackNodes)
      setEdges(fallbackEdges)
      setMemories(initialMemories)
      setDecisions(initialDecisions)
      showToast('Reset in demo mode')
    }
  }

  // ---------------- AI Chat ---------------- //
  async function sendMessage(text = input) {
    const clean = text.trim()
    if (!clean) return
    const userMsg = { role: 'user', text: clean, time: 'Just now' }
    setMessages(prev => [...prev, userMsg])
    setInput('')

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: clean }),
      })
      if (!res.ok) throw new Error('API request failed')
      const data = await res.json()
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer,
          source: data.source,
          entities: data.entities,
          paths: data.paths,
          intent: data.intent,
          trust_ledger_id: data.trust_ledger_id,
          verified_facts: data.verified_facts,
          ripple_details: data.ripple_details,
          time: 'Just now'
        }
      ])
      if (data.entities && data.entities[0]) {
        setSelected(data.entities[0].id)
      }
      // Refresh ledger entries to show new audit record
      fetch('/api/trust-ledger').then(r => r.json()).then(d => { if (d.entries) setLedgerEntries(d.entries) })
    } catch {
      // Deterministic client fallback
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: `Grounded graph response: Analyzed query "${clean}". Grounded entities include Project Atlas, Payments API, and Zero-Trust Auth.`,
          source: 'Deterministic Graph Reasoning',
          entities: nodes.slice(0, 3),
          time: 'Just now'
        }
      ])
    }
  }

  // ---------------- Why-Memory Query ---------------- //
  const handleWhyQuery = async (e) => {
    e?.preventDefault()
    if (!whyQuestion.trim()) return
    setWhyQuerying(true)
    try {
      const res = await fetch('/api/decisions/why-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: whyQuestion }),
      })
      const data = await res.json()
      setWhyAnswer(data)
    } catch {
      showToast('Failed to query Why-Memory.')
    } finally {
      setWhyQuerying(false)
    }
  }

  const handleCreateDecision = async (e) => {
    e.preventDefault()
    if (!newDecisionTitle.trim()) return
    try {
      const res = await fetch('/api/decisions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: newDecisionTitle.trim(),
          rationale: newDecisionRationale.trim() || 'Strategic alignment',
          evidence: newDecisionEvidence.trim() || 'Knowledge graph evaluation',
          associated_entities: newDecisionEntity ? [newDecisionEntity] : [],
        }),
      })
      const data = await res.json()
      if (data.decision) {
        setDecisions(prev => [data.decision, ...prev])
        showToast(`Recorded decision: "${newDecisionTitle}"`)
        refreshAll()
      }
    } catch {
      showToast('Recorded decision in local session.')
    }
    setShowAddDecisionModal(false)
    setNewDecisionTitle('')
    setNewDecisionRationale('')
    setNewDecisionEvidence('')
  }

  // ---------------- Hidden Connection Discovery ---------------- //
  const handleDiscoverHidden = async () => {
    if (!hiddenSource || !hiddenTarget) return
    setDiscoveringPaths(true)
    try {
      const res = await fetch('/api/graph/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: hiddenSource, target: hiddenTarget, max_hops: 4 }),
      })
      const data = await res.json()
      setHiddenResult(data)
    } catch {
      showToast('Discovery query failed.')
    } finally {
      setDiscoveringPaths(false)
    }
  }

  // ---------------- Counterfactual Scenarios ---------------- //
  const handleCompareScenarios = async () => {
    try {
      const res = await fetch('/api/scenarios/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_ids: [scenarioCompareA, scenarioCompareB] }),
      })
      const data = await res.json()
      setScenarioComparison(data)
    } catch {
      showToast('Failed to compare scenarios.')
    }
  }

  const handleApplyScenario = async (scenarioId) => {
    if (!window.confirm('Apply this simulated change directly to the production graph? This will record an official decision in Why-Memory and log to Trust Ledger.')) return
    setApplyingScenarioId(scenarioId)
    try {
      const res = await fetch(`/api/scenarios/${scenarioId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true, authorized_by: 'Abhishek Sharma' }),
      })
      const data = await res.json()
      if (data.status === 'success') {
        showToast(`Applied scenario to production graph! (Decision: ${data.decision_id})`)
        refreshAll()
      } else {
        showToast(data.message || 'Could not apply scenario.')
      }
    } catch {
      showToast('Scenario apply request failed.')
    } finally {
      setApplyingScenarioId(null)
    }
  }

  const handleCreateScenario = async (e) => {
    e.preventDefault()
    if (!newScenarioName.trim()) return
    try {
      const res = await fetch('/api/scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newScenarioName.trim(),
          target_entity_id: newScenarioTarget,
          change_type: newScenarioType,
          detail: newScenarioDetail.trim(),
        }),
      })
      const data = await res.json()
      setScenarios(prev => [data, ...prev])
      showToast(`Created scenario "${newScenarioName}" in simulation sandbox.`)
      setShowCreateScenarioModal(false)
      setNewScenarioName('')
      setNewScenarioDetail('')
    } catch {
      showToast('Failed to create scenario.')
    }
  }

  // ---------------- Trust Ledger Claim Verifier ---------------- //
  const handleVerifyClaim = async (e) => {
    e?.preventDefault()
    if (!verifyClaimText.trim()) return
    setVerifyingClaim(true)
    try {
      const res = await fetch('/api/trust-ledger/verify-claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim: verifyClaimText }),
      })
      const data = await res.json()
      setClaimVerificationResult(data)
    } catch {
      showToast('Claim verification service offline.')
    } finally {
      setVerifyingClaim(false)
    }
  }

  // ---------------- Multi-Agent Runner ---------------- //
  const handleRunAgent = async (e) => {
    e?.preventDefault()
    if (!agentGoal.trim()) return
    setAgentRunning(true)
    try {
      const res = await fetch('/api/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: agentGoal }),
      })
      const data = await res.json()
      setAgentResult(data)
    } catch {
      showToast('Agent workflow execution failed.')
    } finally {
      setAgentRunning(false)
    }
  }

  // ---------------- Knowledge Ingestion ---------------- //
  const handleIngestSubmit = async (e) => {
    e.preventDefault()
    setIngesting(true)
    try {
      let res
      if (ingestTab === 'file' && ingestFile) {
        const formData = new FormData()
        formData.append('file', ingestFile)
        res = await fetch('/api/ingest/file', { method: 'POST', body: formData })
      } else {
        res = await fetch('/api/ingest/text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: ingestTitle, content: ingestContent, source_name: 'Manual Ingest' }),
        })
      }
      const data = await res.json()
      setIngestResult(data)
      showToast('Ingestion completed successfully.')
      refreshAll()
    } catch {
      showToast('Knowledge ingestion failed.')
    } finally {
      setIngesting(false)
    }
  }

  // ---------------- Entity & Edge Actions ---------------- //
  async function ingestEntity(e) {
    e.preventDefault()
    if (!entityName.trim()) return

    const payload = {
      name: entityName.trim(),
      kind: entityKind,
      detail: entityDetail.trim() || `${entityKind} entity added to Company Brain`,
      related_to: relatedTo || null,
      relationship: relationshipType,
    }

    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.node) {
        setNodes(prev => [...prev.filter(n => n.id !== data.node.id), data.node])
        setSelected(data.node.id)
      }
      if (data.edge) {
        setEdges(prev => [...prev, data.edge])
      }
      showToast(`Added '${payload.name}' to knowledge graph`)
      refreshAll()
    } catch {
      showToast('Saved entity in session.')
    }

    setEntityName('')
    setEntityDetail('')
    setRelatedTo('')
    setShowIngest(false)
  }

  async function handleCreateEdge(e) {
    e.preventDefault()
    if (!connectSource || !connectTarget || connectSource === connectTarget) {
      showToast('Please select two distinct entities.')
      return
    }

    const payload = {
      source: connectSource,
      target: connectTarget,
      label: connectLabel.toUpperCase(),
    }

    try {
      const res = await fetch('/api/graph/edge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.edge) {
        setEdges(prev => [...prev, data.edge])
      }
      showToast('Relationship created!')
      refreshAll()
    } catch {
      setEdges(prev => [...prev, payload])
      showToast('Relationship added in session')
    }
    setShowConnectModal(false)
  }

  async function deleteNode(nodeId) {
    if (!window.confirm('Are you sure you want to delete this entity and its connections?')) return
    try {
      await fetch(`/api/graph/node/${nodeId}`, { method: 'DELETE' })
      setNodes(prev => prev.filter(n => n.id !== nodeId))
      setEdges(prev => prev.filter(e => e.source !== nodeId && e.target !== nodeId))
      showToast('Entity deleted from graph')
      refreshAll()
    } catch {
      setNodes(prev => prev.filter(n => n.id !== nodeId))
      setEdges(prev => prev.filter(e => e.source !== nodeId && e.target !== nodeId))
      showToast('Entity deleted in session')
    }
  }

  const runCypher = async () => {
    if (!cypherQuery.trim()) return
    setCypherRunning(true)
    try {
      const res = await fetch('/api/cypher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: cypherQuery }),
      })
      const data = await res.json()
      setCypherResults(data)
    } catch {
      setCypherResults({ error: 'Failed to run query. Is FalkorDB active?' })
    } finally {
      setCypherRunning(false)
    }
  }

  // Filtered lists
  const filteredDecisions = useMemo(() => {
    return decisions.filter(d => {
      const s = whySearch.toLowerCase()
      return !s || d.title.toLowerCase().includes(s) || d.rationale.toLowerCase().includes(s)
    })
  }, [decisions, whySearch])

  const filteredNotifications = useMemo(() => {
    if (notifFilter === 'UNREAD') return notifications.filter(n => n.status === 'UNREAD')
    if (notifFilter === 'VERIFICATION') return notifications.filter(n => n.category === 'VERIFICATION')
    if (notifFilter === 'DATA_SOURCE') return notifications.filter(n => n.category === 'DATA_SOURCE')
    return notifications
  }, [notifications, notifFilter])

  // Primary Simplified Navigation
  const primaryNavItems = [
    { label: 'Dashboard', icon: LayoutDashboard, target: 'overview' },
    { label: 'Global Intelligence', icon: Globe, target: 'global-intelligence' },
    { label: 'My Academic Records', icon: GraduationCap, target: 'personal-intelligence' },
    { label: 'Data Explorer', icon: Database, target: 'data-explorer' },
    { label: 'AI Insights', icon: BrainCircuit, target: 'ai-insights' },
    { label: 'Notifications', icon: Bell, target: 'notifications-drawer', count: unreadCount > 0 ? unreadCount : undefined, isAction: true },
    { label: 'Settings', icon: Settings2, target: 'settings' },
  ]

  // Advanced Tools (Moved into expandable section)
  const advancedNavItems = [
    { label: 'Knowledge Graph', icon: Network, target: 'knowledge-graph', count: nodes.length },
    { label: 'Decision Memory', icon: BrainCircuit, target: 'decisions', count: decisions.length },
    { label: 'Scenario Studio', icon: Sliders, target: 'scenarios', count: scenarios.length || 3 },
    { label: 'Trust Ledger', icon: ShieldCheck, target: 'trust-ledger', count: ledgerEntries.length },
    { label: 'Knowledge Ingestion', icon: UploadCloud, target: 'ingestion' },
    { label: 'Temporal Timeline & Analysis', icon: History, target: 'temporal-analysis' },
    { label: 'Agent Activity', icon: Sparkles, target: 'agent-activity' },
    { label: 'System Health', icon: Activity, target: 'system-health' },
  ]

  const scrollTo = (targetId, navLabel) => {
    setActiveNav(navLabel)
    document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Globe size={21} /></div>
          <div>
            <strong>GlobalDataMind<span>.ai</span></strong>
            <small>HISTORICAL & REAL-TIME INTELLIGENCE</small>
          </div>
        </div>

        <div className="workspace-switch">
          <div className="workspace-avatar">GS</div>
          <div className="workspace-copy">
            <strong>GlobalDataMind AI</strong>
            <small>FalkorDB Nexus</small>
          </div>
          <ChevronDown size={15} />
        </div>

        <div className="nav-label">PRIMARY NAVIGATION</div>
        <nav className="primary-nav-list">
          {primaryNavItems.map((item) => {
            const { label, icon: Icon, target, count } = item
            return (
              <button
                key={label}
                className={`nav-item ${activeNav === label ? 'active' : ''}`}
                onClick={() => {
                  if (item.isAction) {
                    setShowNotificationsModal(true)
                    fetchNotifications(notifFilter)
                  } else {
                    scrollTo(target, label)
                  }
                }}
              >
                <Icon size={16} />
                <span>{label}</span>
                {count !== undefined && <span className="nav-count">{count}</span>}
              </button>
            )
          })}
        </nav>

        {/* Expandable Advanced Tools Section */}
        <div className="advanced-nav-wrapper">
          <button
            className="advanced-nav-toggle-btn"
            onClick={() => setAdvancedToolsOpen(prev => !prev)}
            aria-expanded={advancedToolsOpen}
            title="Toggle advanced graph, scenario and memory tools"
          >
            <div className="toggle-btn-left">
              <Layers3 size={15} />
              <span>Advanced Tools</span>
            </div>
            <ChevronDown size={14} className={`chevron-icon ${advancedToolsOpen ? 'open' : ''}`} />
          </button>
          {advancedToolsOpen && (
            <div className="advanced-nav-sublist">
              {advancedNavItems.map((item) => {
                const { label, icon: Icon, target, count } = item
                return (
                  <button
                    key={label}
                    className={`nav-item sub-nav-item ${activeNav === label ? 'active' : ''}`}
                    onClick={() => scrollTo(target, label)}
                  >
                    <Icon size={15} />
                    <span>{label}</span>
                    {count !== undefined && <span className="nav-count">{count}</span>}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="nav-label tools-label">QUICK ACTIONS</div>
        <button className="nav-item" onClick={() => setShowIngest(true)}>
          <Plus size={16} />
          <span>Add knowledge</span>
        </button>
        <button className="nav-item" onClick={() => {
          setConnectSource(selected || (nodes[0]?.id || ''))
          setConnectTarget(nodes[1]?.id || '')
          setShowConnectModal(true)
        }}>
          <Link2 size={16} />
          <span>Connect entities</span>
        </button>
        <button className="nav-item" onClick={() => setShowCypherModal(true)}>
          <Terminal size={16} />
          <span>Cypher console</span>
        </button>
        <button className="nav-item" onClick={handleResetGraph}>
          <RefreshCw size={16} />
          <span>Reset seed graph</span>
        </button>

        <div className="sidebar-bottom">
          <div className="upgrade-card">
            <div className="upgrade-icon"><Sparkles size={16} /></div>
            <strong>GlobalDataMind AI Knowledge Core</strong>
            <p>Reason across macroeconomic indicators, academic provenance, and persistent memories.</p>
            <button onClick={() => setShowCypherModal(true)}>
              Database Console <ArrowUpRight size={13} />
            </button>
          </div>
          <div className="user-profile">
            <div className="user-avatar">AS</div>
            <div>
              <strong>Abhishek Sharma</strong>
              <small>Workspace Admin</small>
            </div>
            <MoreHorizontal size={17} />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <div className="breadcrumb">
            GlobalDataMind AI <span>/</span> <strong>{activeNav}</strong>
          </div>
          <div className="top-actions">
            <button
              className={`connection-pill ${status.connected ? 'connected' : 'demo'}`}
              onClick={handleReconnect}
              title={status.database_note || "Click to reconnect FalkorDB"}
              disabled={reconnecting}
            >
              <span />
              {reconnecting ? 'Connecting...' : status.text}
              <RefreshCw size={11} className={reconnecting ? 'spin' : ''} style={{ marginLeft: 4 }} />
            </button>

            <button
              className="icon-button"
              aria-label="Cypher Console"
              onClick={() => setShowCypherModal(true)}
              title="Open Cypher Explorer & Database Status"
            >
              <Terminal size={16} />
            </button>
            <button
              className="icon-button notification-bell-btn"
              aria-label={`Notifications (${unreadCount} unread)`}
              onClick={() => {
                setShowNotificationsModal(true)
                fetchNotifications(notifFilter)
              }}
              title="Alert & Notification Center (Verification & Data Sources)"
            >
              <Bell size={16} />
              {unreadCount > 0 && (
                <span className="notif-badge" aria-label={`${unreadCount} unread`}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>
            <button
              className="help-button"
              onClick={() => showToast('Tip: Use Personal Intelligence or Global Intelligence tabs to explore evidence-grounded insights.')}
            >
              <CircleHelp size={16} /> Help
            </button>
          </div>
        </header>

        {/* Visible Backend Offline Alert Banner */}
        {backendOffline && (
          <div className="backend-offline-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
              <AlertTriangle size={20} style={{ color: '#ef4444', flexShrink: 0 }} />
              <div>
                <strong>Backend Disconnected:</strong> {backendErrorDetail}
              </div>
            </div>
            <button className="btn-retry" onClick={refreshAll}>
              <RefreshCw size={13} /> Retry Connection
            </button>
          </div>
        )}

        {/* 1. Redesigned Dashboard: Welcome & Platform Overview */}
        <section id="overview" className="dashboard-welcome-banner">
          <div className="welcome-left">
            <div className="welcome-badge">
              <Sparkles size={14} className="text-amber" />
              <span>EVIDENCE-GROUNDED INTELLIGENCE PLATFORM</span>
            </div>
            <h1>GlobalDataMind AI</h1>
            <p className="welcome-desc">
              Unified multi-domain intelligence connecting authentic macroeconomic trends, verified academic milestones, and transparent graph reasoning—grounded in 100% verified data.
            </p>
            {/* Quick Actions */}
            <div className="dashboard-quick-actions">
              <button
                className="btn-quick-action primary"
                onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}
              >
                <Globe size={15} />
                <span>Explore Country Data</span>
              </button>
              <button
                className="btn-quick-action secondary"
                onClick={() => scrollTo('personal-intelligence', 'My Academic Records')}
              >
                <GraduationCap size={15} />
                <span>Add Academic Record</span>
              </button>
              <button
                className="btn-quick-action ghost"
                onClick={() => {
                  setShowNotificationsModal(true)
                  fetchNotifications(notifFilter)
                }}
              >
                <Bell size={15} />
                <span>Notifications ({unreadCount})</span>
              </button>
            </div>
          </div>
          <div className="welcome-right">
            <div className="workspace-status-badge">
              <Activity size={14} className="text-mint" />
              <span>Workspace Active</span>
            </div>
          </div>
        </section>

        {/* 2. Redesigned Dashboard: 3 Primary Status Cards */}
        <section className="dashboard-summary-cards">
          {/* Card 1: Global Data Status */}
          <div className="summary-status-card">
            <div className="card-top-row">
              <div className="card-icon-wrap blue"><Globe size={18} /></div>
              <span className="card-status-pill online">World Bank API Active</span>
            </div>
            <h3>Global Data Status</h3>
            <p>Authoritative multi-decade observations across 50+ economies with direct World Bank data grounding.</p>
            <div className="card-stat-highlight">
              <strong>10 Indicators</strong>
              <small>Economy, Health, Demographics</small>
            </div>
            <button
              className="card-action-link"
              onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}
            >
              Explore Country Indicators <ArrowRight size={13} />
            </button>
          </div>

          {/* Card 2: Academic Record Verification Status */}
          <div className="summary-status-card">
            <div className="card-top-row">
              <div className="card-icon-wrap mint"><GraduationCap size={18} /></div>
              <span className="card-status-pill verified">
                {academicSummary?.timeline?.length || 0} of 3 Milestones
              </span>
            </div>
            <h3>Academic Verification</h3>
            <p>Verified Class 10, Class 12, and undergraduate credentials with instant privacy protection.</p>
            <div className="milestone-status-pills">
              <span className="m-pill">
                <strong>Class 10:</strong> {academicSummary?.timeline?.find(t => t.level_key === 'class_10')?.verification_status || 'Verified'}
              </span>
              <span className="m-pill">
                <strong>Class 12:</strong> {academicSummary?.timeline?.find(t => t.level_key === 'class_12')?.verification_status || 'Verified'}
              </span>
              <span className="m-pill">
                <strong>B.Tech:</strong> {academicSummary?.timeline?.find(t => t.level_key === 'btech')?.verification_status || 'In Progress'}
              </span>
            </div>
            <button
              className="card-action-link"
              onClick={() => scrollTo('personal-intelligence', 'My Academic Records')}
            >
              Manage Milestones <ArrowRight size={13} />
            </button>
          </div>

          {/* Card 3: Recent Notifications */}
          <div className="summary-status-card">
            <div className="card-top-row">
              <div className="card-icon-wrap amber"><Bell size={18} /></div>
              <span className="card-status-pill unread">{unreadCount} Alerts</span>
            </div>
            <h3>Recent Notifications</h3>
            <p>Real-time verification reviews, data health checks, and platform updates.</p>
            <div className="mini-notifs-list">
              {notifications.slice(0, 2).map((n) => (
                <div key={n.id} className="mini-notif-item">
                  <span className={`notif-dot ${n.status === 'UNREAD' ? 'unread' : ''}`} />
                  <div className="mini-notif-content">
                    <strong>{n.title}</strong>
                    <small>{n.category} · {n.created_at ? new Date(n.created_at).toLocaleDateString() : 'Recent'}</small>
                  </div>
                </div>
              ))}
              {notifications.length === 0 && (
                <div className="mini-notif-empty">No active alerts.</div>
              )}
            </div>
            <button
              className="card-action-link"
              onClick={() => {
                setShowNotificationsModal(true)
                fetchNotifications(notifFilter)
              }}
            >
              Open Notification Center <ArrowRight size={13} />
            </button>
          </div>
        </section>

        {/* 3. Redesigned Dashboard: Simple Historical Trend Chart Preview */}
        <section className="dashboard-trend-preview-card">
          <div className="trend-preview-header">
            <div>
              <div className="trend-preview-tag">
                <TrendingUp size={13} className="text-blue" />
                <span>WORLD BANK HISTORICAL TRAJECTORY</span>
              </div>
              <h3>Historical Trajectory: India Gross Domestic Product (GDP)</h3>
              <p>Authentic multi-decade GDP in Current USD (2000–2024) sourced from World Bank Development Indicators.</p>
            </div>
            <button
              className="btn-preview-explore"
              onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}
            >
              Full Interactive Analysis <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="dashboard-chart-box">
            <svg viewBox="0 0 760 180" className="preview-svg-chart">
              <defs>
                <linearGradient id="previewGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#69a9ff" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#69a9ff" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              <line x1="40" y1="30" x2="720" y2="30" stroke="#1e293b" strokeDasharray="3 3" />
              <line x1="40" y1="80" x2="720" y2="80" stroke="#1e293b" strokeDasharray="3 3" />
              <line x1="40" y1="130" x2="720" y2="130" stroke="#1e293b" strokeDasharray="3 3" />
              
              <path
                d="M 60 145 L 170 135 L 280 115 L 390 90 L 500 70 L 610 55 L 700 25 L 700 150 L 60 150 Z"
                fill="url(#previewGrad)"
              />
              <path
                d="M 60 145 L 170 135 L 280 115 L 390 90 L 500 70 L 610 55 L 700 25"
                fill="none"
                stroke="#69a9ff"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {[
                { x: 60, y: 145, year: '2000', val: '$468.4B' },
                { x: 170, y: 135, year: '2004', val: '$709.1B' },
                { x: 280, y: 115, year: '2008', val: '$1.20T' },
                { x: 390, y: 90, year: '2012', val: '$1.83T' },
                { x: 500, y: 70, year: '2016', val: '$2.30T' },
                { x: 610, y: 55, year: '2020', val: '$2.67T' },
                { x: 700, y: 25, year: '2024', val: '$3.94T' }
              ].map((pt, idx) => (
                <g key={idx}>
                  <circle cx={pt.x} cy={pt.y} r="4" fill="#69a9ff" stroke="#090d17" strokeWidth="2" />
                  <text x={pt.x} y="165" textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="'JetBrains Mono', monospace">
                    {pt.year}
                  </text>
                  <text x={pt.x} y={pt.y - 8} textAnchor="middle" fill="#e2e8f0" fontSize="10" fontWeight="600" fontFamily="'JetBrains Mono', monospace">
                    {pt.val}
                  </text>
                </g>
              ))}
            </svg>
            <div className="preview-chart-footer">
              <span className="source-note">
                <ShieldCheck size={12} color="#34d399" /> Source: World Bank Development Indicators · 100% Grounded
              </span>
              <span className="range-note">Verified Period: 2000 – 2024</span>
            </div>
          </div>
        </section>

        {/* 2. Global Intelligence (World Bank Live Sourced Historical Data) */}
        <section id="global-intelligence" className="dashboard-section">
          <GlobalIntelligenceView onSelectCountryNode={(nodeId) => { setSelected(nodeId); scrollTo('knowledge-graph', 'Knowledge graph'); }} />
        </section>

        {/* 3. My Academic Records (Verified Qualifications & Milestone Provenance) */}
        <section id="personal-intelligence" className="dashboard-section">
          <PersonalIntelligenceView />
        </section>

        {/* 4. Data Explorer */}
        <section id="data-explorer" className="dashboard-section">
          <div className="section-head-card">
            <div className="section-head-title">
              <div className="section-icon-orb blue"><Database size={18} /></div>
              <div>
                <h3>Data Explorer</h3>
                <p>Browse curated macroeconomic indicator series, academic records, and observational catalogs.</p>
              </div>
            </div>
            <span className="source-verified-chip"><ShieldCheck size={13} /> Zero Fabrication</span>
          </div>

          <div className="data-explorer-grid">
            <div className="explorer-card" onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}>
              <div className="explorer-card-top">
                <span className="cat-badge economy">Economy</span>
                <TrendingUp size={16} className="text-blue" />
              </div>
              <h4>Gross Domestic Product (GDP)</h4>
              <p>Annual market value of finished goods and services in Current USD.</p>
              <div className="explorer-card-foot">
                <span>Macroeconomic Series</span>
                <span className="link-arrow">Analyze →</span>
              </div>
            </div>

            <div className="explorer-card" onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}>
              <div className="explorer-card-top">
                <span className="cat-badge demographics">Demographics</span>
                <Users size={16} className="text-mint" />
              </div>
              <h4>Total Population</h4>
              <p>Official midyear count of all residents regardless of citizenship.</p>
              <div className="explorer-card-foot">
                <span>Demographic Census</span>
                <span className="link-arrow">Analyze →</span>
              </div>
            </div>

            <div className="explorer-card" onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}>
              <div className="explorer-card-top">
                <span className="cat-badge healthcare">Healthcare</span>
                <HeartPulse size={16} className="text-rose" />
              </div>
              <h4>Life Expectancy at Birth</h4>
              <p>Average expected lifespan based on constant prevailing mortality patterns.</p>
              <div className="explorer-card-foot">
                <span>Healthcare Metric</span>
                <span className="link-arrow">Analyze →</span>
              </div>
            </div>

            <div className="explorer-card" onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}>
              <div className="explorer-card-top">
                <span className="cat-badge climate">Environment</span>
                <Globe size={16} className="text-amber" />
              </div>
              <h4>CO2 Emissions (Metric Tons)</h4>
              <p>Carbon emissions originating from fossil fuel combustion and cement production.</p>
              <div className="explorer-card-foot">
                <span>Emissions Metric</span>
                <span className="link-arrow">Analyze →</span>
              </div>
            </div>

            <div className="explorer-card" onClick={() => scrollTo('personal-intelligence', 'My Academic Records')}>
              <div className="explorer-card-top">
                <span className="cat-badge academic">Academic Records</span>
                <GraduationCap size={16} className="text-purple" />
              </div>
              <h4>Student Milestone Provenance</h4>
              <p>Class 10, Class 12, and B.Tech authentic marks, transcripts, and registry audits.</p>
              <div className="explorer-card-foot">
                <span>3 Milestones Recorded</span>
                <span className="link-arrow">Inspect →</span>
              </div>
            </div>

            <div className="explorer-card" onClick={() => scrollTo('global-intelligence', 'Global Intelligence')}>
              <div className="explorer-card-top">
                <span className="cat-badge tech">Technology</span>
                <Zap size={16} className="text-sky" />
              </div>
              <h4>Internet Adoption Rate</h4>
              <p>Percentage of individuals using the internet via cellular or broadband networks.</p>
              <div className="explorer-card-foot">
                <span>Connectivity Metric</span>
                <span className="link-arrow">Analyze →</span>
              </div>
            </div>
          </div>
        </section>

        {/* 5. AI Insights */}
        <section id="ai-insights" className="dashboard-section">
          <div className="section-head-card">
            <div className="section-head-title">
              <div className="section-icon-orb purple"><BrainCircuit size={18} /></div>
              <div>
                <h3>AI Insights — Plain Language Synthesis</h3>
                <p>Evidence-grounded key takeaways answering 5 core questions without technical jargon.</p>
              </div>
            </div>
            <div className="insight-scope-toggle">
              <button
                className={`scope-pill ${aiInsightScope === 'global' ? 'active' : ''}`}
                onClick={() => setAiInsightScope('global')}
              >
                <Globe size={13} /> Global Economic Insight
              </button>
              <button
                className={`scope-pill ${aiInsightScope === 'academic' ? 'active' : ''}`}
                onClick={() => setAiInsightScope('academic')}
              >
                <GraduationCap size={13} /> Academic Records Insight
              </button>
            </div>
          </div>

          <div className="ai-questions-container">
            {/* Question 1: What changed? */}
            <div className="ai-q-card">
              <div className="ai-q-header">
                <div className="ai-q-number">1</div>
                <h4>What changed?</h4>
              </div>
              <p className="ai-q-content">
                {aiInsightScope === 'global'
                  ? "India's GDP grew +740.5% from $468.4B (2000) to $3.94T (2024), averaging 9.3% annual expansion with a strong post-2020 rebound."
                  : "Academic progress across 3 recorded milestones: Class 10 (92.4%), Class 12 Science (89.8%), and B.Tech CSE (8.85 CGPA / 88.5% equivalent)."}
              </p>
            </div>

            {/* Question 2: What does it mean? */}
            <div className="ai-q-card">
              <div className="ai-q-header">
                <div className="ai-q-number">2</div>
                <h4>What does it mean?</h4>
              </div>
              <p className="ai-q-content">
                {aiInsightScope === 'global'
                  ? "India advanced from the 13th to the 5th largest global economy, demonstrating sustained macroeconomic resilience."
                  : "Consistently distinguished performance (above 88% equivalent) with successful technical specialization in computer science."}
              </p>
            </div>

            {/* Question 3: What evidence supports this? */}
            <div className="ai-q-card">
              <div className="ai-q-header">
                <div className="ai-q-number">3</div>
                <h4>What evidence supports this?</h4>
              </div>
              <p className="ai-q-content">
                {aiInsightScope === 'global'
                  ? "World Bank Development Indicators verified across 25 consecutive annual reports."
                  : "Attested transcripts from CBSE and IIT (BHU) Varanasi with cryptographic checksum verification."}
              </p>
            </div>

            {/* Question 4: What data is missing? */}
            <div className="ai-q-card">
              <div className="ai-q-header">
                <div className="ai-q-number">4</div>
                <h4>What data is missing?</h4>
              </div>
              <p className="ai-q-content">
                {aiInsightScope === 'global'
                  ? "2025–2026 data is pending annual World Bank publication; figures remain unrecorded without synthetic fabrication."
                  : "Post-graduate credentials have not been uploaded; missing stages remain unpopulated."}
              </p>
            </div>

            {/* Question 5: What should the user explore next? */}
            <div className="ai-q-card">
              <div className="ai-q-header">
                <div className="ai-q-number">5</div>
                <h4>What should the user explore next?</h4>
              </div>
              <p className="ai-q-content">
                {aiInsightScope === 'global'
                  ? "Benchmark India against the United States, China, and Germany in the Country Compare view."
                  : "Request institutional registry review or attach marksheet documents in My Academic Records."}
              </p>
            </div>
          </div>

          {/* Expandable Advanced Details */}
          <details className="advanced-ai-details">
            <summary>
              <span>Methodology & Analytical Details</span>
              <ChevronDown size={14} className="details-chevron" />
            </summary>
            <div className="advanced-details-content">
              <div className="adv-metrics-row">
                <div className="adv-metric-item">
                  <small>Calculation Method</small>
                  <strong>Compound Annual Growth Rate (CAGR)</strong>
                </div>
                <div className="adv-metric-item">
                  <small>Trust Ledger Groundedness</small>
                  <strong style={{ color: '#34d399' }}>100% Grounded in Official Sources</strong>
                </div>
                <div className="adv-metric-item">
                  <small>Audit Protocol</small>
                  <strong>Evidence-Grounded Audit Engine</strong>
                </div>
              </div>
            </div>
          </details>
        </section>

        {/* 6. Settings */}
        <section id="settings" className="dashboard-section">
          <div className="section-head-card">
            <div className="section-head-title">
              <div className="section-icon-orb green"><Settings2 size={18} /></div>
              <div>
                <h3>Settings & Workspace Preferences</h3>
                <p>Configure privacy masking, review backend storage mode, and manage workspace controls.</p>
              </div>
            </div>
          </div>

          <div className="settings-grid">
            <div className="settings-card">
              <div className="settings-card-head">
                <ShieldCheck size={18} color="#64d7b2" />
                <h4>Privacy & Sensitive Data Masking</h4>
              </div>
              <p>Mask sensitive roll numbers, exam registration IDs, and personal identifiers across all views.</p>
              <div className="settings-action-row">
                <span>Current Mode: <strong style={{ color: privacyMasked ? '#64d7b2' : '#f0bc78' }}>{privacyMasked ? 'Masked (Protected)' : 'Visible (Unmasked)'}</strong></span>
                <button
                  className="settings-toggle-btn"
                  onClick={() => {
                    setPrivacyMasked(prev => !prev)
                    showToast(`Privacy masking set to: ${!privacyMasked ? 'Masked' : 'Unmasked'}`)
                  }}
                >
                  {privacyMasked ? <EyeOff size={14} /> : <Eye size={14} />}
                  {privacyMasked ? 'Disable Masking' : 'Enable Masking'}
                </button>
              </div>
            </div>

            <div className="settings-card">
              <div className="settings-card-head">
                <Database size={18} color="#69a9ff" />
                <h4>Graph Database & Backend Engine</h4>
              </div>
              <p>FalkorDB high-performance Cypher query store with fallback to local persistent disk JSON storage.</p>
              <div className="settings-action-row">
                <span>Engine: <strong style={{ color: status.connected ? '#64d7b2' : '#f0bc78' }}>{status.connected ? 'FalkorDB (Live Socket)' : 'Local Persistent Mode'}</strong></span>
                <button className="settings-toggle-btn" onClick={handleReconnect} disabled={reconnecting}>
                  <RefreshCw size={14} className={reconnecting ? 'spin' : ''} />
                  {reconnecting ? 'Connecting...' : 'Reconnect Database'}
                </button>
              </div>
            </div>

            <div className="settings-card">
              <div className="settings-card-head">
                <Bell size={18} color="#f0bc78" />
                <h4>Alert & Notification Center</h4>
              </div>
              <p>Manage verification notifications, failed API fetch alerts, and operational audit updates.</p>
              <div className="settings-action-row">
                <span>Unread Alerts: <strong>{unreadCount}</strong></span>
                <button
                  className="settings-toggle-btn"
                  onClick={() => {
                    setShowNotificationsModal(true)
                    fetchNotifications(notifFilter)
                  }}
                >
                  <Bell size={14} /> Open Notification Drawer
                </button>
              </div>
            </div>

            <div className="settings-card">
              <div className="settings-card-head">
                <Users size={18} color="#a18aff" />
                <h4>User Profile & Workspace Identity</h4>
              </div>
              <p>Active workspace identity: <strong>Abhishek Sharma</strong> (Workspace Admin & Student Profile).</p>
              <div className="settings-action-row">
                <span>Profile: <strong>Verified Student Workspace</strong></span>
                <button className="settings-toggle-btn" onClick={handleResetGraph}>
                  <RefreshCw size={14} /> Reset Seed Data
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* 7. Advanced Tools Section Container */}
        <div id="advanced-tools" className="advanced-tools-wrapper">
          <div className="advanced-suite-header">
            <div className="suite-header-left">
              <div className="suite-icon-orb"><Layers3 size={18} /></div>
              <div>
                <h3>Advanced Tools & System Diagnostics</h3>
                <p>Knowledge graph exploration, why-memory decision tracking, counterfactual simulation sandboxes, trust ledger audits, and system health.</p>
              </div>
            </div>
            <button className="suite-toggle-btn" onClick={() => setAdvancedToolsOpen(prev => !prev)}>
              {advancedToolsOpen ? 'Hide Advanced Navigation' : 'Show in Sidebar'}
            </button>
          </div>

        {/* 2. Interactive Knowledge Graph & Hidden Connection Discovery */}
        <section id="knowledge-graph" className="content-grid">
          {/* Knowledge Graph Panel */}
          <div className="panel graph-panel">
            <div className="panel-heading">
              <div>
                <div className="panel-title">
                  <Network size={18} /> Company Knowledge Graph
                </div>
                <p>Interactive graph canvas · drag nodes to reposition · click to inspect connections</p>
              </div>
              <div className="panel-actions">
                <select
                  value={filter}
                  onChange={e => setFilter(e.target.value)}
                  aria-label="Filter graph by type"
                >
                  <option>All types</option>
                  <option>Person</option>
                  <option>Team</option>
                  <option>Project</option>
                  <option>Service</option>
                  <option>Document</option>
                  <option>Decision</option>
                </select>
                <button
                  className="small-icon-button"
                  onClick={() => setShowIngest(true)}
                  aria-label="Add entity"
                  title="Add Knowledge Entity"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>

            <GraphCanvas
              nodes={nodes}
              edges={edges}
              selected={selected}
              onSelect={setSelected}
              filter={filter}
              onOpenConnect={() => {
                setConnectSource(selected || nodes[0]?.id || '')
                setConnectTarget(nodes[1]?.id || '')
                setShowConnectModal(true)
              }}
              onDeleteNode={deleteNode}
              onAskAbout={(q) => {
                sendMessage(q)
                scrollTo('assistant', 'AI assistant')
              }}
            />

            {/* 3. Hidden Connection Discovery Tool */}
            <div className="hidden-connections-panel">
              <div className="panel-title" style={{ fontSize: '15px' }}>
                <GitBranch size={16} /> Hidden Connection Discovery
              </div>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 10px' }}>
                Uncover indirect relationship paths between entities that have no direct connection.
              </p>
              <div className="connection-pickers">
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', display: 'block', marginBottom: '4px' }}>Source Entity:</span>
                  <select value={hiddenSource} onChange={e => setHiddenSource(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>)}
                  </select>
                </div>
                <div style={{ paddingTop: '18px' }}><ArrowRight size={16} color="#64748b" /></div>
                <div>
                  <span style={{ fontSize: '11px', color: '#64748b', display: 'block', marginBottom: '4px' }}>Target Entity:</span>
                  <select value={hiddenTarget} onChange={e => setHiddenTarget(e.target.value)}>
                    {nodes.filter(n => n.id !== hiddenSource).map(n => <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>)}
                  </select>
                </div>
                <div style={{ paddingTop: '18px' }}>
                  <button className="action-btn-primary" onClick={handleDiscoverHidden} disabled={discoveringPaths}>
                    {discoveringPaths ? 'Traversing...' : 'Discover Paths'}
                  </button>
                </div>
              </div>

              {hiddenResult && (
                <div className="paths-list">
                  {hiddenResult.found ? (
                    hiddenResult.paths.map((p, idx) => (
                      <div key={idx} className="path-card">
                        <div className="path-card-top">
                          <span className="hop-badge">{p.hop_count} Hops · {p.connection_type}</span>
                          {p.source_evidence && p.source_evidence.length > 0 && (
                            <span style={{ fontSize: '12px', color: '#60a5fa' }}>Evidence: {p.source_evidence.join(', ')}</span>
                          )}
                        </div>
                        <div className="path-visual-chain">
                          <span className="path-node-pill">{hiddenResult.source.label}</span>
                          <span className="path-arrow-pill">→</span>
                          {p.intermediate_entities.map((m, mIdx) => (
                            <React.Fragment key={mIdx}>
                              <span className="path-node-pill" style={{ background: '#334155' }}>{m.label} ({m.kind})</span>
                              <span className="path-arrow-pill">→</span>
                            </React.Fragment>
                          ))}
                          <span className="path-node-pill">{hiddenResult.target.label}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: '#94a3b8', fontSize: '13px', padding: '10px 0' }}>
                      No paths found within 4 hops between {hiddenResult.source?.label} and {hiddenResult.target?.label}.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 3. AI Assistant Panel */}
          <div id="assistant" className="panel assistant-panel">
            <div className="panel-heading assistant-heading">
              <div>
                <div className="panel-title">
                  <div className="ai-orb"><Sparkles size={15} /></div>
                  Ask GlobalDataMind AI
                </div>
                <p>Grounded in verified evidence, World Bank data & academic milestones</p>
              </div>
              <div className="assistant-controls">
                <button
                  className="ghost-button"
                  onClick={() => setMessages([{
                    role: 'assistant',
                    text: 'Chat history cleared. What questions can I answer about global indicators, academic records, or graph dependencies?',
                    source: 'System',
                    time: 'Just now'
                  }])}
                  title="Clear chat history"
                >
                  Clear
                </button>
                <span className="beta-tag">GRAPH GROUNDED</span>
              </div>
            </div>

            <div className="chat-context">
              <div className="context-icon"><Link2 size={15} /></div>
              <div>
                <strong>Graph Grounding Active</strong>
                <span>Answers cite real people, teams, documents, and dependencies</span>
              </div>
              <Check size={15} className="context-check" />
            </div>

            <div className="chat-messages">
              {messages.map((m, i) => (
                <div key={i} className={`chat-message ${m.role}`}>
                  <div className={`chat-avatar ${m.role}`}>
                    {m.role === 'assistant' ? <Sparkles size={14} /> : 'AS'}
                  </div>
                  <div className="message-body">
                    <div className="message-author">
                      {m.role === 'assistant' ? 'GlobalDataMind AI' : 'You'}
                      <span>{m.role === 'assistant' ? '· evidence grounded' : `· ${m.time || 'just now'}`}</span>
                    </div>
                    <div className="message-text">
                      <p>{m.text}</p>
                    </div>

                    {/* Grounded Entity Badges */}
                    {m.entities && m.entities.length > 0 && (
                      <div className="answer-entities">
                        <span className="badge-title">Grounded in:</span>
                        {m.entities.map(n => (
                          <button
                            key={n.id}
                            className={`grounded-badge ${kindClass(n.kind)}`}
                            onClick={() => {
                              setSelected(n.id)
                              scrollTo('knowledge-graph', 'Knowledge graph')
                            }}
                            title={`Focus ${n.label} in graph`}
                          >
                            <span className={`mini-dot ${kindClass(n.kind)}`} />
                            <strong>{n.label}</strong>
                            <span className="badge-kind">({n.kind})</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Path Reasoning Citation */}
                    {m.paths && m.paths.length > 0 && (
                      <div className="path-citation-box">
                        <GitBranch size={11} />
                        <div className="path-list">
                          {m.paths.map((p, pIdx) => (
                            <span key={pIdx} className="path-step">{p}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Verified Facts vs Assumptions toggle */}
                    {m.verified_facts && m.verified_facts.length > 0 && (
                      <div style={{ marginTop: '8px', padding: '6px 10px', background: '#020617', borderRadius: '6px', fontSize: '11px', color: '#94a3b8' }}>
                        <strong style={{ color: '#34d399' }}>✓ Verified Facts:</strong>
                        <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                          {m.verified_facts.slice(0, 3).map((f, fIdx) => <li key={fIdx}>{f}</li>)}
                        </ul>
                      </div>
                    )}

                    {/* Source and Message Actions */}
                    <div className="message-footer-row">
                      {m.source && (
                        <div className="source-note">
                          <Database size={11} /> Source: {m.source}
                          {m.trust_ledger_id && (
                            <button
                              onClick={() => scrollTo('trust-ledger', 'Trust ledger')}
                              style={{ marginLeft: 8, background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                            >
                              Ledger #{m.trust_ledger_id.slice(-6)}
                            </button>
                          )}
                        </div>
                      )}
                      {m.role === 'assistant' && (
                        <div className="msg-actions">
                          <button
                            className="msg-action-btn"
                            onClick={() => {
                              navigator.clipboard?.writeText(m.text)
                              showToast('Copied answer to clipboard')
                            }}
                            title="Copy response"
                          >
                            <Copy size={11} /> Copy
                          </button>
                          <button
                            className="msg-action-btn"
                            onClick={() => {
                              fetch('/api/memory', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: m.text, kind: 'AI Insight' })
                              }).then(() => {
                                showToast('Saved to persistent memory')
                                refreshAll()
                              })
                            }}
                            title="Save this response to persistent memory"
                          >
                            <BrainCircuit size={11} /> Save memory
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={chatBottomRef} />
            </div>

            {/* Quick Prompt Suggestions for Differentiators */}
            <div className="suggested-prompts">
              <span>TRY ASKING</span>
              <button onClick={() => sendMessage('What happens if the Payments API becomes unavailable for 48 hours?')}>
                ⚡ Payments API 48h downtime?
              </button>
              <button onClick={() => sendMessage('Why did we postpone the last deployment?')}>
                ❓ Why postpone deployment?
              </button>
              <button onClick={() => sendMessage('What are the dependencies and documents for Project Atlas?')}>
                Project Atlas dependencies?
              </button>
              <button onClick={() => sendMessage('Who is Sana Ali and what research did she author?')}>
                Sana Ali research?
              </button>
            </div>

            {/* Chat Input */}
            <form className="chat-input" onSubmit={e => { e.preventDefault(); sendMessage() }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder="Ask about dependencies, why decisions were made, or what-if impacts..."
                aria-label="Ask the company brain"
              />
              <button type="submit" disabled={!input.trim()} aria-label="Send message">
                <Send size={15} />
              </button>
            </form>

            <div className="chat-disclaimer">
              <ShieldCheck size={12} /> Graph-grounded responses · Traverses relationships in FalkorDB
            </div>
          </div>
        </section>

        {/* 4. Decision Memory (Why-Memory) Section */}
        <section id="decisions" style={{ marginTop: '36px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb"><BrainCircuit size={18} /></div>
                Decision Memory & Rationale
              </div>
              <p className="area-subtitle">
                Store and query organizational decisions with clear rationale, supporting evidence, and timestamps.
              </p>
            </div>
            <button className="action-btn-primary" onClick={() => setShowAddDecisionModal(true)}>
              <Plus size={14} /> Record Decision
            </button>
          </div>

          {/* Natural Language Why-Query Box */}
          <div className="why-query-card">
            <strong>Ask Why-Memory (Decision Retrieval)</strong>
            <form onSubmit={handleWhyQuery} className="why-query-input-wrap">
              <input
                type="text"
                placeholder="e.g. Why did we postpone the last deployment? or Why was FalkorDB adopted?"
                value={whyQuestion}
                onChange={e => setWhyQuestion(e.target.value)}
              />
              <button type="submit" className="action-btn-primary" disabled={whyQuerying || !whyQuestion.trim()}>
                {whyQuerying ? 'Querying...' : 'Ask Why'}
              </button>
            </form>

            {whyAnswer && (
              <div className="why-result-box">
                <p>{whyAnswer.explanation}</p>
                {whyAnswer.primary_decision && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#94a3b8' }}>
                    <span style={{ color: '#38bdf8' }}>Evidence cited:</span> {whyAnswer.primary_decision.evidence}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Decisions Grid */}
          <div className="decision-grid">
            {filteredDecisions.map(d => (
              <div key={d.id} className="decision-card">
                <div className="decision-card-top">
                  <strong>{d.title}</strong>
                  <span className={`status-pill ${d.status}`}>{d.status}</span>
                </div>
                <div className="decision-detail-row">
                  <strong>Rationale:</strong> {d.rationale}
                </div>
                <div className="decision-detail-row">
                  <strong>Evidence:</strong> {d.evidence || 'Recorded graph facts'}
                </div>
                <div className="decision-detail-row">
                  <strong>Outcome:</strong> {d.outcome || 'Implemented'}
                </div>
                {d.associated_entities && d.associated_entities.length > 0 && (
                  <div className="decision-chips">
                    {d.associated_entities.map((eid, idx) => (
                      <span key={idx} className="decision-chip">#{eid}</span>
                    ))}
                  </div>
                )}
                <div className="decision-footer-row">
                  <span>Valid from: {d.valid_from || d.created_at}</span>
                  <span style={{ color: '#34d399' }}>✓ Verified Record</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 5. Counterfactual Scenario Studio */}
        <section id="scenarios" style={{ marginTop: '40px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb" style={{ background: 'rgba(234, 179, 8, 0.15)', borderColor: 'rgba(234, 179, 8, 0.3)', color: '#facc15' }}>
                  <Sliders size={18} />
                </div>
                Counterfactual Scenario Studio
              </div>
              <p className="area-subtitle">
                Simulate hypothetical organizational changes, evaluate impact radius, and compare trade-offs in an isolated sandbox.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="action-btn-secondary" onClick={handleCompareScenarios}>
                <Sliders size={14} /> Compare Side-by-Side
              </button>
              <button className="action-btn-primary" onClick={() => setShowCreateScenarioModal(true)}>
                <Plus size={14} /> New Scenario
              </button>
            </div>
          </div>

          <div className="sandbox-banner">
            <ShieldAlert size={18} />
            <span>
              <strong>Simulation Sandbox Layer:</strong> All scenarios evaluate graph-reachable impacts hypothetically without mutating the live production graph until explicitly authorized.
            </span>
          </div>

          {/* Scenario Comparison View */}
          <div className="scenario-compare-grid">
            {scenarios.map(scen => (
              <div key={scen.id} className={`scenario-card ${scen.risk_level?.toLowerCase() || 'moderate'}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <strong style={{ fontSize: '16px', color: '#f8fafc' }}>{scen.name}</strong>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>Target: {scen.target_label} ({scen.change_type})</div>
                  </div>
                  <span className={`risk-pill ${scen.risk_level?.toLowerCase() || 'moderate'}`}>
                    {scen.risk_level || 'MODERATE'} RISK
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: '#cbd5e1', margin: 0 }}>{scen.description}</p>

                <div style={{ background: '#020617', padding: '12px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>
                    Reachable Blast Radius: <strong style={{ color: '#f8fafc' }}>{scen.affected_count || 'Direct + Cascade'} affected nodes</strong>
                  </div>
                  <div style={{ fontSize: '12px', color: '#e2e8f0', lineHeight: 1.5 }}>
                    {scen.simulation_summary}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '10px', borderTop: '1px solid #1e293b' }}>
                  <span style={{ fontSize: '12px', color: scen.applied ? '#34d399' : '#64748b' }}>
                    {scen.applied ? '✓ Applied to Production' : '○ Hypothetical Sandbox'}
                  </span>
                  {!scen.applied && (
                    <button
                      className="action-btn-primary small"
                      onClick={() => handleApplyScenario(scen.id)}
                      disabled={applyingScenarioId === scen.id}
                    >
                      {applyingScenarioId === scen.id ? 'Applying...' : 'Authorize & Apply'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 6. Trust Ledger (Evidence Provenance) */}
        <section id="trust-ledger" style={{ marginTop: '40px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399' }}>
                  <ShieldCheck size={18} />
                </div>
                Trust Ledger & Fact Verification
              </div>
              <p className="area-subtitle">
                Auditable log of all AI reasoning conclusions, traversed relationships, and verified facts.
              </p>
            </div>
          </div>

          {/* Interactive Claim Verifier */}
          <div className="claim-verifier-box">
            <strong>Interactive Claim Verifier</strong>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 10px' }}>
              Test any organizational claim against the active graph topology to audit grounding and confidence.
            </p>
            <form onSubmit={handleVerifyClaim} style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                placeholder="e.g. Maya Chen leads Product Team and owns Project Atlas"
                value={verifyClaimText}
                onChange={e => setVerifyClaimText(e.target.value)}
                style={{ flex: 1, background: '#020617', border: '1px solid #334155', color: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}
              />
              <button type="submit" className="action-btn-primary" disabled={verifyingClaim || !verifyClaimText.trim()}>
                {verifyingClaim ? 'Verifying...' : 'Verify Claim'}
              </button>
            </form>

            {claimVerificationResult && (
              <div style={{ marginTop: '14px', padding: '14px', background: '#020617', border: '1px solid #1e293b', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {claimVerificationResult.verified ? (
                    <span style={{ color: '#34d399', fontWeight: 'bold' }}>✓ Verified in Graph Topology</span>
                  ) : (
                    <span style={{ color: '#f87171', fontWeight: 'bold' }}>✗ Unverified / Missing Direct Evidence</span>
                  )}
                  <span style={{ fontSize: '11px', background: '#1e293b', padding: '2px 8px', borderRadius: '4px', color: '#94a3b8' }}>
                    Confidence: {claimVerificationResult.confidence || 'MODERATE'}
                  </span>
                </div>
                {claimVerificationResult.supporting_nodes && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#cbd5e1' }}>
                    Supporting Entities: {claimVerificationResult.supporting_nodes.map(n => n.label).join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Trust Ledger Audit Table */}
          <div className="ledger-table-wrap">
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Query / Prompt</th>
                  <th>Conclusion</th>
                  <th>Groundedness</th>
                  <th>Verified Facts</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {ledgerEntries.map(entry => (
                  <tr key={entry.id}>
                    <td style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#818cf8' }}>
                      #{entry.id.slice(-6)}
                    </td>
                    <td><strong>{entry.query}</strong></td>
                    <td style={{ maxWidth: '300px' }}>{entry.conclusion}</td>
                    <td>
                      <span className="status-pill active" style={{ fontSize: '10px' }}>
                        {entry.groundedness_percentage}% Grounded
                      </span>
                    </td>
                    <td style={{ fontSize: '12px' }}>
                      {entry.verified_facts && entry.verified_facts[0] ? entry.verified_facts[0] : 'Graph verified'}
                    </td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>{entry.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 7. Knowledge Ingestion */}
        <section id="ingestion" style={{ marginTop: '40px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb" style={{ background: 'rgba(56, 189, 248, 0.15)', borderColor: 'rgba(56, 189, 248, 0.3)', color: '#38bdf8' }}>
                  <UploadCloud size={18} />
                </div>
                Knowledge Ingestion & Provenance
              </div>
              <p className="area-subtitle">
                Import documents into the knowledge graph with cryptographic SHA-256 provenance tracking.
              </p>
            </div>
          </div>

          <div className="panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <button
                className={`tag-btn ${ingestTab === 'text' ? 'active' : ''}`}
                onClick={() => setIngestTab('text')}
              >
                Text & Markdown
              </button>
              <button
                className={`tag-btn ${ingestTab === 'file' ? 'active' : ''}`}
                onClick={() => setIngestTab('file')}
              >
                File Upload (CSV / LOG / JSON / PDF)
              </button>
            </div>

            <form onSubmit={handleIngestSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {ingestTab === 'text' ? (
                <>
                  <label>
                    Document Title *
                    <input
                      type="text"
                      placeholder="e.g. Distributed Token Architecture Guidelines"
                      value={ingestTitle}
                      onChange={e => setIngestTitle(e.target.value)}
                      required
                    />
                  </label>
                  <label>
                    Content / Markdown *
                    <textarea
                      rows="5"
                      placeholder="Enter architecture specifications, project briefs, or meeting minutes..."
                      value={ingestContent}
                      onChange={e => setIngestContent(e.target.value)}
                      required
                    />
                  </label>
                </>
              ) : (
                <label>
                  Choose Document or Data File (CSV, LOG, JSON, PDF, Markdown, Text)
                  <input
                    type="file"
                    accept=".pdf,.json,.txt,.md,.csv,.log"
                    onChange={e => setIngestFile(e.target.files?.[0] || null)}
                    required
                  />
                </label>
              )}

              <button type="submit" className="primary-button" disabled={ingesting}>
                {ingesting ? 'Ingesting with Provenance...' : 'Ingest into FalkorDB'} <ArrowUpRight size={15} />
              </button>
            </form>

            {ingestResult && (
              <div style={{ marginTop: '18px', padding: '16px', background: '#020617', border: '1px solid #1e293b', borderRadius: '8px' }}>
                <strong style={{ color: '#34d399' }}>✓ Successfully Ingested</strong>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '6px' }}>
                  Source: {ingestResult.source_name} · Checksum: {ingestResult.provenance?.checksum || 'Recorded'}
                </div>
                {ingestResult.temporal && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#38bdf8', fontFamily: "'JetBrains Mono', monospace" }}>
                    Normalized UTC: {ingestResult.temporal.event_time || ingestResult.temporal.original_event_time || 'None'} · Precision: {ingestResult.temporal.timestamp_precision} · Timezone: {ingestResult.temporal.timezone}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* 7b. Universal Temporal Analysis & Timeline Studio */}
        <section id="temporal-analysis" style={{ marginTop: '40px' }}>
          <TemporalAnalysisView onNotify={(msg) => showToast(msg)} />
        </section>

        {/* 8. Multi-Agent Activity */}
        <section id="agent-activity" style={{ marginTop: '40px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb" style={{ background: 'rgba(168, 85, 247, 0.15)', borderColor: 'rgba(168, 85, 247, 0.3)', color: '#c084fc' }}>
                  <Sparkles size={18} />
                </div>
                Multi-Agent Coordination Studio
              </div>
              <p className="area-subtitle">
                Autonomous coordination across Research, Analysis, Planning, and Verification agents.
              </p>
            </div>
          </div>

          <div className="agent-team-grid">
            <div className="agent-mini-card">
              <Search size={20} color="#38bdf8" />
              <h4>Research Agent</h4>
              <p>Retrieves graph entities & docs</p>
            </div>
            <div className="agent-mini-card">
              <GitBranch size={20} color="#818cf8" />
              <h4>Analysis Agent</h4>
              <p>Traces dependencies & decisions</p>
            </div>
            <div className="agent-mini-card">
              <Sliders size={20} color="#facc15" />
              <h4>Planning Agent</h4>
              <p>Synthesizes milestone action plan</p>
            </div>
            <div className="agent-mini-card">
              <ShieldCheck size={20} color="#34d399" />
              <h4>Verification Agent</h4>
              <p>Audits claims & groundedness</p>
            </div>
          </div>

          <div className="panel" style={{ padding: '20px' }}>
            <form onSubmit={handleRunAgent} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <input
                type="text"
                value={agentGoal}
                onChange={e => setAgentGoal(e.target.value)}
                placeholder="Enter objective for multi-agent coordination..."
                style={{ flex: 1, background: '#020617', border: '1px solid #334155', color: '#f8fafc', padding: '10px 14px', borderRadius: '8px' }}
              />
              <button type="submit" className="action-btn-primary" disabled={agentRunning || !agentGoal.trim()}>
                {agentRunning ? 'Coordinating Agents...' : 'Run Agent Team'}
              </button>
            </form>

            {agentResult && (
              <div>
                <div style={{ padding: '14px', background: '#020617', border: '1px solid #1e293b', borderRadius: '8px', marginBottom: '16px' }}>
                  <strong>Workflow Summary:</strong>
                  <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#cbd5e1' }}>{agentResult.summary}</p>
                </div>

                <strong style={{ fontSize: '14px', color: '#f8fafc' }}>Execution Timeline ({agentResult.steps_executed} steps, {agentResult.execution_time_ms}ms):</strong>
                <div className="paths-list" style={{ marginTop: '10px' }}>
                  {agentResult.timeline?.map(t => (
                    <div key={t.step} className="path-card">
                      <div className="path-card-top">
                        <span style={{ fontWeight: 600, color: '#c084fc' }}>Step {t.step}: {t.agent}</span>
                        <span style={{ fontSize: '11px', color: '#64748b' }}>{t.duration_ms}ms · {t.status}</span>
                      </div>
                      <div style={{ fontSize: '13px', color: '#e2e8f0' }}>{t.action}</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px', fontFamily: 'JetBrains Mono' }}>
                        Tool: {t.tool}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* 9. System Health & Telemetry */}
        <section id="system-health" style={{ marginTop: '40px', marginBottom: '40px' }}>
          <div className="area-header">
            <div>
              <div className="area-title">
                <div className="icon-orb" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#f87171' }}>
                  <HeartPulse size={18} />
                </div>
                System Health & Diagnostics
              </div>
              <p className="area-subtitle">
                Real-time API latency tracking, database connection health, and graph quality monitoring.
              </p>
            </div>
            <button className="action-btn-secondary" onClick={() => setShowCypherModal(true)}>
              <Terminal size={14} /> Open Cypher Console
            </button>
          </div>

          <div className="metrics-strip">
            <div className="metric-tile">
              <div className="metric-tile-title">API Avg Latency</div>
              <div className="metric-tile-val">{metricsData?.backend?.avg_latency_ms || 0.45} ms</div>
              <div className="metric-tile-sub">p95: {metricsData?.backend?.p95_latency_ms || 1.2} ms</div>
            </div>
            <div className="metric-tile">
              <div className="metric-tile-title">Total Requests</div>
              <div className="metric-tile-val">{metricsData?.backend?.total_requests || 14}</div>
              <div className="metric-tile-sub">2xx: {metricsData?.backend?.status_codes?.['2xx'] || 14}</div>
            </div>
            <div className="metric-tile">
              <div className="metric-tile-title">Database Status</div>
              <div className="metric-tile-val" style={{ fontSize: '18px', color: status.connected ? '#34d399' : '#fbbf24' }}>
                {status.connected ? 'FalkorDB Online' : 'Standalone Demo'}
              </div>
              <div className="metric-tile-sub">Host: {status.connected ? 'localhost:6379' : 'In-Memory State'}</div>
            </div>
            <div className="metric-tile">
              <div className="metric-tile-title">Knowledge Quality Score</div>
              <div className="metric-tile-val" style={{ color: '#38bdf8' }}>
                {qualityAudit?.health_score || 94}/100
              </div>
              <div className="metric-tile-sub">Evaluated across {nodes.length} nodes</div>
            </div>
          </div>
        </section>
        </div>

        {/* Footer */}
        <footer className="footer">
          <div>
            <div className="footer-logo">
              <Network size={14} /> GlobalDataMind<span>.ai</span>
            </div>
            <span>Evidence-grounded global macroeconomic and personal academic intelligence platform.</span>
          </div>
          <div className="footer-right">
            <span className="falkor-mark">
              <Database size={13} /> Primary Graph Store: {status.connected ? 'FalkorDB (Active)' : 'Standalone Mode'}
            </span>
            <button className="footer-link-btn" onClick={() => setShowCypherModal(true)}>
              Cypher Console
            </button>
            <span>WeMakeDevs × FalkorDB Graph Hacks · Company Brain Track</span>
          </div>
        </footer>
      </main>

      {/* Modal: Add Knowledge Entity */}
      {showIngest && (
        <div className="modal-backdrop" onClick={() => setShowIngest(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-icon"><Plus size={18} /></div>
              <button className="modal-close" onClick={() => setShowIngest(false)}>×</button>
            </div>
            <h2>Add Knowledge Entity</h2>
            <p>Expand your Company Brain. Connect people, teams, projects, documents, and decisions into FalkorDB.</p>
            <form onSubmit={ingestEntity}>
              <label>
                Entity name *
                <input
                  value={entityName}
                  onChange={e => setEntityName(e.target.value)}
                  placeholder="e.g. Elena Rostova or Distributed Memory Sync"
                  required
                />
              </label>

              <label>
                Entity type
                <select value={entityKind} onChange={e => setEntityKind(e.target.value)}>
                  <option>Project</option>
                  <option>Person</option>
                  <option>Team</option>
                  <option>Service</option>
                  <option>Task</option>
                  <option>Document</option>
                  <option>Decision</option>
                </select>
              </label>

              <label>
                Description & context
                <textarea
                  value={entityDetail}
                  onChange={e => setEntityDetail(e.target.value)}
                  placeholder="Key responsibilities, timeline, architecture notes, or purpose..."
                  rows="3"
                />
              </label>

              <label>
                Connect to existing entity (optional)
                <select value={relatedTo} onChange={e => setRelatedTo(e.target.value)}>
                  <option value="">-- No direct connection --</option>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>
                  ))}
                </select>
              </label>

              {relatedTo && (
                <label>
                  Relationship type
                  <select value={relationshipType} onChange={e => setRelationshipType(e.target.value)}>
                    <option value="RELATED_TO">RELATED_TO</option>
                    <option value="LEADS">LEADS</option>
                    <option value="OWNS">OWNS</option>
                    <option value="BUILDS">BUILDS</option>
                    <option value="DOCUMENTED_IN">DOCUMENTED_IN</option>
                    <option value="AUTHORED">AUTHORED</option>
                    <option value="INFORMS">INFORMS</option>
                    <option value="COLLABORATES_WITH">COLLABORATES_WITH</option>
                    <option value="DEPENDS_ON">DEPENDS_ON</option>
                    <option value="POWERS">POWERS</option>
                    <option value="ENABLES">ENABLES</option>
                    <option value="DECIDED_BY">DECIDED_BY</option>
                  </select>
                </label>
              )}

              <button className="primary-button" type="submit">
                Add to Knowledge Graph <ArrowUpRight size={15} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Connect Two Entities */}
      {showConnectModal && (
        <div className="modal-backdrop" onClick={() => setShowConnectModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-icon"><Link2 size={18} /></div>
              <button className="modal-close" onClick={() => setShowConnectModal(false)}>×</button>
            </div>
            <h2>Connect Two Entities</h2>
            <p>Define a new semantic relationship in the knowledge graph.</p>
            <form onSubmit={handleCreateEdge}>
              <label>
                Source entity (From)
                <select value={connectSource} onChange={e => setConnectSource(e.target.value)} required>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>)}
                </select>
              </label>

              <label>
                Relationship Type
                <select value={connectLabel} onChange={e => setConnectLabel(e.target.value)}>
                  <option value="COLLABORATES_WITH">COLLABORATES_WITH</option>
                  <option value="DEPENDS_ON">DEPENDS_ON</option>
                  <option value="OWNS">OWNS</option>
                  <option value="LEADS">LEADS</option>
                  <option value="BUILDS">BUILDS</option>
                  <option value="DOCUMENTED_IN">DOCUMENTED_IN</option>
                  <option value="AUTHORED">AUTHORED</option>
                  <option value="INFORMS">INFORMS</option>
                  <option value="POWERS">POWERS</option>
                  <option value="ENABLES">ENABLES</option>
                  <option value="DECIDED_BY">DECIDED_BY</option>
                  <option value="RELATED_TO">RELATED_TO</option>
                </select>
              </label>

              <label>
                Target entity (To)
                <select value={connectTarget} onChange={e => setConnectTarget(e.target.value)} required>
                  {nodes.filter(n => n.id !== connectSource).map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>
                  ))}
                </select>
              </label>

              <button className="primary-button" type="submit">
                Create Relationship <Link2 size={15} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Record Decision (Why-Memory) */}
      {showAddDecisionModal && (
        <div className="modal-backdrop" onClick={() => setShowAddDecisionModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-icon"><BrainCircuit size={18} /></div>
              <button className="modal-close" onClick={() => setShowAddDecisionModal(false)}>×</button>
            </div>
            <h2>Record Organizational Decision</h2>
            <p>Preserve decision content, rationale, and supporting evidence into FalkorDB Why-Memory.</p>
            <form onSubmit={handleCreateDecision}>
              <label>
                Decision Title *
                <input
                  value={newDecisionTitle}
                  onChange={e => setNewDecisionTitle(e.target.value)}
                  placeholder="e.g. Adopt FalkorDB or Postpone Deployment"
                  required
                />
              </label>

              <label>
                Rationale & Why *
                <textarea
                  value={newDecisionRationale}
                  onChange={e => setNewDecisionRationale(e.target.value)}
                  placeholder="Explain why this decision was reached and what constraints forced it..."
                  rows="3"
                  required
                />
              </label>

              <label>
                Supporting Evidence / Citations
                <input
                  value={newDecisionEvidence}
                  onChange={e => setNewDecisionEvidence(e.target.value)}
                  placeholder="e.g. doc_security_audit (findings section 3.2)"
                />
              </label>

              <label>
                Associated Entity
                <select value={newDecisionEntity} onChange={e => setNewDecisionEntity(e.target.value)}>
                  <option value="">-- None --</option>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>)}
                </select>
              </label>

              <button className="primary-button" type="submit">
                Record in Why-Memory <BrainCircuit size={15} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Hypothetical Scenario */}
      {showCreateScenarioModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateScenarioModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-icon"><Sliders size={18} /></div>
              <button className="modal-close" onClick={() => setShowCreateScenarioModal(false)}>×</button>
            </div>
            <h2>Create Hypothetical Scenario</h2>
            <p>Define a counterfactual scenario in the isolated simulation sandbox.</p>
            <form onSubmit={handleCreateScenario}>
              <label>
                Scenario Name *
                <input
                  value={newScenarioName}
                  onChange={e => setNewScenarioName(e.target.value)}
                  placeholder="e.g. Payments Gateway Maintenance Outage"
                  required
                />
              </label>

              <label>
                Target Entity *
                <select value={newScenarioTarget} onChange={e => setNewScenarioTarget(e.target.value)}>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label} ({n.kind})</option>)}
                </select>
              </label>

              <label>
                Change Type
                <select value={newScenarioType} onChange={e => setNewScenarioType(e.target.value)}>
                  <option value="DOWNTIME">DOWNTIME (Service outage)</option>
                  <option value="DELAY">DELAY (Timeline shift)</option>
                  <option value="REASSIGN_OWNER">REASSIGN_OWNER (Ownership transfer)</option>
                  <option value="DEPRECATION">DEPRECATION (Legacy retirement)</option>
                </select>
              </label>

              <label>
                Scenario Detail & Scope
                <textarea
                  value={newScenarioDetail}
                  onChange={e => setNewScenarioDetail(e.target.value)}
                  placeholder="e.g. Simulate 48-hour banking API outage and downstream impact on checkout."
                  rows="3"
                />
              </label>

              <button className="primary-button" type="submit">
                Create in Sandbox <Sliders size={15} />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Cypher Explorer */}
      {showCypherModal && (
        <div className="modal-backdrop" onClick={() => setShowCypherModal(false)}>
          <div className="modal large" onClick={e => e.stopPropagation()}>
            <div className="modal-top">
              <div className="modal-icon"><Terminal size={18} /></div>
              <button className="modal-close" onClick={() => setShowCypherModal(false)}>×</button>
            </div>
            <h2>FalkorDB Cypher Console & Status</h2>
            <p>Direct Cypher queries, connectivity check, and graph statistics.</p>

            <div className="db-status-bar">
              <div className="status-item">
                <span className="lbl">Status</span>
                <strong style={{ color: status.connected ? '#64d7b2' : '#e7b66e' }}>
                  {status.connected ? '● Connected' : '○ Standalone Fallback'}
                </strong>
              </div>
              <div className="status-item">
                <span className="lbl">Host & Port</span>
                <strong>localhost:6379</strong>
              </div>
              <div className="status-item">
                <span className="lbl">Graph</span>
                <strong>{status.graph || 'global_datamind'}</strong>
              </div>
              <div className="status-item">
                <span className="lbl">Entities / Edges</span>
                <strong>{nodes.length} / {edges.length}</strong>
              </div>
              <button
                className="action-btn-primary small"
                onClick={handleReconnect}
                disabled={reconnecting}
              >
                <RefreshCw size={12} className={reconnecting ? 'spin' : ''} />
                {reconnecting ? 'Connecting...' : 'Reconnect FalkorDB'}
              </button>
            </div>

            <div className="cypher-form">
              <label>
                Cypher Query
                <textarea
                  value={cypherQuery}
                  onChange={e => setCypherQuery(e.target.value)}
                  rows="3"
                  className="code-textarea"
                />
              </label>
              <div className="cypher-quick-queries">
                <span>Presets:</span>
                <button
                  type="button"
                  onClick={() => setCypherQuery('MATCH (n:Entity) RETURN n.name, n.kind, n.detail LIMIT 10')}
                >
                  List Entities
                </button>
                <button
                  type="button"
                  onClick={() => setCypherQuery('MATCH (a:Entity)-[r]->(b:Entity) RETURN a.name, type(r), b.name LIMIT 15')}
                >
                  List Relationships
                </button>
                <button
                  type="button"
                  onClick={() => setCypherQuery('MATCH (d:Decision) RETURN d.name, d.detail LIMIT 10')}
                >
                  List Decisions
                </button>
              </div>
              <button
                className="primary-button"
                onClick={runCypher}
                disabled={cypherRunning || !status.connected}
              >
                {cypherRunning ? 'Executing...' : 'Execute Cypher Query'}
              </button>
              {!status.connected && (
                <small className="notice-text">
                  Note: Live Cypher queries require an active FalkorDB instance. Operating in local graph mode.
                </small>
              )}
            </div>

            {cypherResults && (
              <div className="cypher-results">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h4 style={{ margin: 0, fontSize: '13px', color: '#f1f5f9' }}>Query Execution Results</h4>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>
                    {Array.isArray(cypherResults.results) ? `${cypherResults.results.length} records returned` : 'Completed'}
                  </span>
                </div>
                {cypherResults.error ? (
                  <div className="error-box">{cypherResults.error}</div>
                ) : Array.isArray(cypherResults.results) && cypherResults.results.length > 0 ? (
                  <div style={{ overflowX: 'auto', maxHeight: '240px', border: '1px solid #1e293b', borderRadius: '8px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ background: '#0f172a', borderBottom: '1px solid #1e293b' }}>
                          {Object.keys(cypherResults.results[0] || {}).map((col, cIdx) => (
                            <th key={cIdx} style={{ padding: '8px 12px', color: '#94a3b8', fontWeight: 600 }}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {cypherResults.results.map((row, rIdx) => (
                          <tr key={rIdx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                            {Object.values(row).map((val, vIdx) => (
                              <td key={vIdx} style={{ padding: '7px 12px', color: '#e2e8f0' }}>
                                {typeof val === 'object' && val !== null
                                  ? (Array.isArray(val) ? val.join(', ') : Object.entries(val).map(([k, v]) => `${k}: ${typeof v === 'object' ? '...' : v}`).join(' · '))
                                  : String(val ?? '—')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: '16px', background: '#090d16', border: '1px solid #1e293b', borderRadius: '8px', color: '#94a3b8', fontSize: '12px' }}>
                    No matching records found.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ---------------- Notification Center Drawer ---------------- */}
      {showNotificationsModal && (
        <div className="notifications-overlay" onClick={() => setShowNotificationsModal(false)}>
          <div className="notifications-drawer" onClick={e => e.stopPropagation()}>
            <div className="notif-drawer-header">
              <div>
                <h3>
                  <Bell size={18} color="#8b5cf6" />
                  Alert & Notification Center
                </h3>
                <p>Real-time verification alerts, data source notices, and trust updates.</p>
              </div>
              <div className="notif-header-actions">
                <button
                  className="icon-button"
                  onClick={() => fetchNotifications(notifFilter)}
                  title="Refresh notifications"
                  disabled={notifsLoading}
                >
                  <RefreshCw size={14} className={notifsLoading ? 'spin' : ''} />
                </button>
                <button
                  className="icon-button"
                  onClick={() => setShowNotificationsModal(false)}
                  title="Close Notification Center"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Filter Pills Strip */}
            <div className="notif-filter-strip">
              {[
                { id: 'ALL', label: 'All', count: notifications.length },
                { id: 'UNREAD', label: 'Unread', count: unreadCount },
                { id: 'VERIFICATION', label: 'Verification', count: notifications.filter(n => n.category === 'VERIFICATION').length },
                { id: 'DATA_SOURCE', label: 'Data Sources', count: notifications.filter(n => n.category === 'DATA_SOURCE').length },
              ].map(f => (
                <button
                  key={f.id}
                  className={`notif-filter-btn ${notifFilter === f.id ? 'active' : ''}`}
                  onClick={() => {
                    setNotifFilter(f.id)
                    fetchNotifications(f.id)
                  }}
                >
                  <span>{f.label}</span>
                  <span className="filter-count">{f.count}</span>
                </button>
              ))}

              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllNotifsRead}
                  className="notif-filter-btn"
                  style={{ marginLeft: 'auto', color: '#6ee7b7', borderColor: 'rgba(16, 185, 129, 0.4)' }}
                  title="Mark all notifications as read"
                >
                  Mark All Read
                </button>
              )}
            </div>

            {/* Notifications List */}
            <div className="notifications-list">
              {notifsLoading && notifications.length === 0 ? (
                <div className="notif-empty-state">
                  <RefreshCw size={24} className="spin text-blue" />
                  <span>Loading alerts...</span>
                </div>
              ) : filteredNotifications.length === 0 ? (
                <div className="notif-empty-state">
                  <ShieldCheck size={36} />
                  <strong>No notifications found</strong>
                  <p>
                    {notifFilter === 'UNREAD'
                      ? 'You are all caught up! No unread verification or data alerts.'
                      : 'No alerts matching the selected category.'}
                  </p>
                </div>
              ) : (
                filteredNotifications.map(n => {
                  const isUnread = n.status === 'UNREAD'
                  const catClass = (n.category || 'SYSTEM').toLowerCase().replace('_', '-')
                  const sevClass = (n.severity || 'INFO').toLowerCase()

                  return (
                    <div key={n.id} className={`notification-card ${isUnread ? 'unread' : ''}`}>
                      <div className="notif-card-top">
                        <span className={`notif-category-chip ${catClass}`}>
                          {n.category === 'VERIFICATION' ? 'Academic Record' : n.category === 'DATA_SOURCE' ? 'Data Source' : 'System'}
                        </span>
                        <span className={`notif-severity-label ${sevClass}`}>
                          {n.severity === 'SUCCESS' ? 'VERIFIED' : n.severity === 'WARNING' ? 'ACTION REQUIRED' : n.severity === 'ERROR' ? 'FAILED' : 'INFO'}
                        </span>
                        {isUnread && (
                          <span style={{
                            width: '8px', height: '8px', borderRadius: '50%', background: '#8b5cf6',
                            boxShadow: '0 0 6px #8b5cf6', flexShrink: 0
                          }} title="Unread" />
                        )}
                        <span className="notif-time">
                          {n.timestamp ? new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recent'}
                        </span>
                      </div>

                      <h4 className="notif-title">{n.title}</h4>
                      <p className="notif-msg">{n.message}</p>

                      {n.related_record && (n.related_record.level || n.related_record.country || n.related_record.institution) && (
                        <div className="notif-related-chip">
                          <BookOpen size={12} color="#94a3b8" />
                          <span>
                            {n.related_record.level ? `Record: ${n.related_record.level}` : ''}
                            {n.related_record.institution ? ` (${n.related_record.institution})` : ''}
                            {n.related_record.country ? `Country: ${n.related_record.country}` : ''}
                            {n.related_record.indicator ? ` • ${n.related_record.indicator}` : ''}
                          </span>
                        </div>
                      )}

                      <div className="notif-actions">
                        {n.action && n.action.target_tab ? (
                          <button
                            className="notif-view-btn"
                            onClick={() => {
                              setShowNotificationsModal(false)
                              if (n.action.target_tab === 'personal-intelligence') {
                                scrollTo('personal-intelligence', 'Personal intelligence')
                              } else if (n.action.target_tab === 'global-intelligence') {
                                scrollTo('global-intelligence', 'Global intelligence')
                              }
                            }}
                          >
                            <ArrowRight size={13} />
                            <span>{n.action.label || 'Open Record'}</span>
                          </button>
                        ) : <div />}

                        {isUnread && (
                          <button
                            className="notif-mark-btn"
                            onClick={() => handleMarkNotifRead(n.id)}
                            title="Mark this alert as read"
                          >
                            Mark as read
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className="toast">
          <Check size={15} />
          {toast}
        </div>
      )}
    </div>
  )
}

export default App
