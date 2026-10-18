import React, { useState, useEffect, useMemo } from 'react'
import {
  Clock, Calendar, AlertTriangle, ShieldCheck, CheckCircle2,
  Filter, ArrowUpDown, History, Layers, BarChart2, Eye,
  RefreshCw, FileText, Terminal, HelpCircle, Info, Sparkles,
  ArrowRight, ShieldAlert, Cpu, Database, ChevronRight, Check
} from 'lucide-react'

export default function TemporalAnalysisView({ onNotify }) {
  // Navigation sub-tabs
  const [activeSubTab, setActiveSubTab] = useState('timeline') // 'timeline' | 'inspector' | 'compare' | 'review'

  // Records & data state
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [reviewFlags, setReviewFlags] = useState([])

  // Filters & sorting
  const [filterPrecision, setFilterPrecision] = useState('ALL')
  const [filterStatus, setFilterStatus] = useState('ALL')
  const [sortAsc, setSortAsc] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Universal Timestamp Inspector State
  const [inspectRaw, setInspectRaw] = useState('2024-05-18T14:30:00-04:00')
  const [inspectSourceCreated, setInspectSourceCreated] = useState('')
  const [inspectVerified, setInspectVerified] = useState('')
  const [inspectSource, setInspectSource] = useState('test_source')
  const [inspectResult, setInspectResult] = useState(null)
  const [inspecting, setInspecting] = useState(false)

  // Ingestion snippet state
  const [ingestType, setIngestType] = useState('CSV')
  const [ingestContent, setIngestContent] = useState(
`id,event_time,kind,detail
tx_101,2024-06-15T09:30:00+02:00,Transaction,Core ledger transfer
stat_102,2023,Statistic,World Bank GDP observation
log_103,2024-02-31T12:00:00Z,LogEntry,Implausible calendar date
task_104,2024-05-18 10:30:00 EDT,Task,DST transition task`
  )
  const [ingestStatus, setIngestStatus] = useState(null)
  const [ingestingData, setIngestingData] = useState(false)

  // Window Comparison State
  const [windowAStart, setWindowAStart] = useState('2020-01-01T00:00:00Z')
  const [windowAEnd, setWindowAEnd] = useState('2022-12-31T23:59:59Z')
  const [windowBStart, setWindowBStart] = useState('2023-01-01T00:00:00Z')
  const [windowBEnd, setWindowBEnd] = useState('2025-12-31T23:59:59Z')
  const [compareResult, setCompareResult] = useState(null)
  const [comparing, setComparing] = useState(false)

  // Load records and review flags on mount
  useEffect(() => {
    fetchReviewFlags()
    loadSampleRecords()
  }, [])

  const fetchReviewFlags = async () => {
    try {
      const res = await fetch('/api/temporal/review-flags')
      if (res.ok) {
        const data = await res.json()
        setReviewFlags(data.flagged_records || [])
      }
    } catch {
      // Offline fallback
    }
  }

  const loadSampleRecords = async () => {
    setLoading(true)
    try {
      // Analyze current default sample dataset through backend
      const res = await fetch('/api/temporal/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: 'CSV',
          content: ingestContent,
          source_name: 'initial_demo.csv'
        })
      })
      if (res.ok) {
        const data = await res.json()
        setRecords(data.records || [])
      }
    } catch {
      // Local fallback records
      setRecords([
        {
          id: 'demo_1',
          record_type: 'Deployment',
          temporal: {
            event_time: '2024-05-18T14:30:00Z',
            original_event_time: '2024-05-18T10:30:00-04:00',
            timestamp_precision: 'second',
            timezone: 'EDT',
            validation_status: 'valid',
            requires_review: false,
            source_provenance: { source_name: 'ci_pipeline' }
          },
          data: { label: 'Platform Deployment v2.4' }
        },
        {
          id: 'demo_2',
          record_type: 'Statistic',
          temporal: {
            event_time: null,
            original_event_time: '2023',
            timestamp_precision: 'year',
            timezone: 'UTC',
            validation_status: 'valid',
            requires_review: false,
            time_range: {
              start: '2023-01-01T00:00:00Z',
              end: '2023-12-31T23:59:59Z',
              precision: 'year',
              limitation_note: 'Precision is year-only; exact event instant cannot be fabricated'
            },
            source_provenance: { source_name: 'World Bank' }
          },
          data: { label: 'National GDP Indicator' }
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  // Handle Universal Timestamp Parsing
  const handleParseInspect = async () => {
    setInspecting(true)
    try {
      const res = await fetch('/api/temporal/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_val: inspectRaw,
          source_name: inspectSource,
          record_id: `inspect_${Date.now()}`,
          source_created_raw: inspectSourceCreated || undefined,
          verified_raw: inspectVerified || undefined
        })
      })
      if (res.ok) {
        const data = await res.json()
        setInspectResult(data)
      } else {
        const err = await res.json()
        setInspectResult({ error: err.detail || 'Parsing failed' })
      }
    } catch {
      setInspectResult({ error: 'Failed to connect to backend parsing service' })
    } finally {
      setInspecting(false)
    }
  }

  // Handle Modular Ingestion
  const handleIngestSubmit = async () => {
    setIngestingData(true)
    setIngestStatus(null)
    try {
      const res = await fetch('/api/temporal/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_type: ingestType,
          content: ingestContent,
          source_name: `user_snippet.${ingestType.toLowerCase()}`
        })
      })
      if (res.ok) {
        const data = await res.json()
        setIngestStatus({
          success: true,
          total: data.total_parsed,
          valid: data.valid_count,
          reviewNeeded: data.review_needed_count
        })
        if (data.records) {
          setRecords(data.records)
        }
        fetchReviewFlags()
      } else {
        const err = await res.json()
        setIngestStatus({ success: false, error: err.detail || 'Ingestion failed' })
      }
    } catch {
      setIngestStatus({ success: false, error: 'Connection error while ingesting' })
    } finally {
      setIngestingData(false)
    }
  }

  // Handle Historical Window Comparison
  const handleCompareWindows = async () => {
    setComparing(true)
    setCompareResult(null)
    try {
      const res = await fetch('/api/temporal/compare-windows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          window_a_start: windowAStart,
          window_a_end: windowAEnd,
          window_b_start: windowBStart,
          window_b_end: windowBEnd,
          records: records.length > 0 ? records : undefined
        })
      })
      if (res.ok) {
        const data = await res.json()
        setCompareResult(data)
      } else {
        const err = await res.json()
        setCompareResult({ error: err.detail || 'Comparison failed' })
      }
    } catch {
      setCompareResult({ error: 'Connection error during window comparison' })
    } finally {
      setComparing(false)
    }
  }

  // Filtered and Sorted Records
  const displayRecords = useMemo(() => {
    return records.filter(r => {
      const temp = r.temporal || {}
      if (filterPrecision !== 'ALL' && temp.timestamp_precision !== filterPrecision.toLowerCase()) {
        return false
      }
      if (filterStatus === 'VALID' && temp.validation_status !== 'valid') return false
      if (filterStatus === 'REVIEW' && !temp.requires_review) return false

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const idMatch = (r.id || '').toLowerCase().includes(q)
        const typeMatch = (r.record_type || '').toLowerCase().includes(q)
        const dateMatch = (temp.event_time || temp.original_event_time || '').toLowerCase().includes(q)
        return idMatch || typeMatch || dateMatch
      }
      return true
    }).sort((a, b) => {
      const aTime = a.temporal?.event_time || a.temporal?.time_range?.start || '1970-01-01'
      const bTime = b.temporal?.event_time || b.temporal?.time_range?.start || '1970-01-01'
      return sortAsc ? aTime.localeCompare(bTime) : bTime.localeCompare(aTime)
    })
  }, [records, filterPrecision, filterStatus, sortAsc, searchQuery])

  // Precision Badge Color Helper
  const getPrecisionColor = (prec) => {
    switch (prec) {
      case 'second':
      case 'millisecond':
      case 'microsecond':
        return '#38bdf8' // cyan/sky
      case 'day':
        return '#34d399' // mint
      case 'month':
        return '#a78bfa' // purple
      case 'year':
        return '#f59e0b' // amber
      default:
        return '#94a3b8' // slate
    }
  }

  return (
    <div className="temporal-analysis-container" style={{ color: '#f1f5f9' }}>
      {/* Header Banner */}
      <div className="section-head-card" style={{ marginBottom: '24px' }}>
        <div className="section-head-title">
          <div className="section-icon-orb" style={{ background: 'rgba(56, 189, 248, 0.15)', borderColor: 'rgba(56, 189, 248, 0.3)', color: '#38bdf8' }}>
            <History size={18} />
          </div>
          <div>
            <h3>Universal Temporal Data Analysis & Verification System</h3>
            <p>
              Normalized UTC temporal intelligence, multi-format parsing (JSON, CSV, Logs, Documents),
              strict zero-fabrication precision tiers, and audit-grade review flagging.
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="source-verified-chip" style={{ background: 'rgba(16, 185, 129, 0.12)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399' }}>
            <ShieldCheck size={13} /> Strict Zero-Fabrication (Rule 10)
          </span>
          {reviewFlags.length > 0 && (
            <span className="source-verified-chip" style={{ background: 'rgba(239, 68, 68, 0.12)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#ef4444' }}>
              <AlertTriangle size={13} /> {reviewFlags.length} Flagged for Review
            </span>
          )}
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #1e293b', paddingBottom: '12px', marginBottom: '20px' }}>
        <button
          className={`tag-btn ${activeSubTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('timeline')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Clock size={14} /> Chronological Timeline ({displayRecords.length})
        </button>
        <button
          className={`tag-btn ${activeSubTab === 'inspector' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('inspector')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sparkles size={14} /> Timestamp Inspector & Formats
        </button>
        <button
          className={`tag-btn ${activeSubTab === 'ingest' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('ingest')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Database size={14} /> Modular Ingest (CSV / LOG / JSON)
        </button>
        <button
          className={`tag-btn ${activeSubTab === 'compare' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('compare')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <BarChart2 size={14} /> Historical Window Comparison
        </button>
        <button
          className={`tag-btn ${activeSubTab === 'review' ? 'active' : ''}`}
          onClick={() => { setActiveSubTab('review'); fetchReviewFlags(); }}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', color: reviewFlags.length > 0 ? '#ef4444' : undefined }}
        >
          <ShieldAlert size={14} /> Review Queue ({reviewFlags.length})
        </button>
      </div>

      {/* ============================================================== */}
      {/* 1. CHRONOLOGICAL TIMELINE TAB                                 */}
      {/* ============================================================== */}
      {activeSubTab === 'timeline' && (
        <div>
          {/* Controls Bar */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '20px', background: '#0b1120', padding: '14px 18px', borderRadius: '10px', border: '1px solid #1e293b' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={15} color="#94a3b8" />
              <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Precision:</span>
              <select
                value={filterPrecision}
                onChange={e => setFilterPrecision(e.target.value)}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
              >
                <option value="ALL">All Precisions</option>
                <option value="SECOND">Second / Exact</option>
                <option value="DAY">Day</option>
                <option value="MONTH">Month</option>
                <option value="YEAR">Year (Bounded Range)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status:</span>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
              >
                <option value="ALL">All Records</option>
                <option value="VALID">Verified Valid Only</option>
                <option value="REVIEW">Flagged for Review</option>
              </select>
            </div>

            <button
              className="tag-btn"
              onClick={() => setSortAsc(!sortAsc)}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <ArrowUpDown size={13} />
              {sortAsc ? 'Chronological (Oldest First)' : 'Reverse Chronological (Newest First)'}
            </button>

            <input
              type="text"
              placeholder="Search record ID or kind..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ flex: 1, minWidth: '180px', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', padding: '6px 12px', borderRadius: '6px', fontSize: '12px' }}
            />

            <button
              className="tag-btn"
              onClick={loadSampleRecords}
              disabled={loading}
              title="Refresh timeline records"
              style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>

          {/* Timeline Stream */}
          {displayRecords.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b', background: '#0b1120', borderRadius: '12px', border: '1px dashed #1e293b' }}>
              <Clock size={32} style={{ margin: '0 auto 12px auto', opacity: 0.5 }} />
              <p>No records match the active temporal filter criteria.</p>
            </div>
          ) : (
            <div style={{ position: 'relative', paddingLeft: '28px', borderLeft: '2px solid #1e293b', marginLeft: '12px' }}>
              {displayRecords.map((rec, idx) => {
                const temp = rec.temporal || {}
                const isYearOnly = temp.timestamp_precision === 'year'
                const precColor = getPrecisionColor(temp.timestamp_precision)

                return (
                  <div
                    key={rec.id || idx}
                    style={{
                      position: 'relative',
                      marginBottom: '20px',
                      background: '#090d16',
                      border: `1px solid ${temp.requires_review ? '#ef4444' : '#1e293b'}`,
                      borderRadius: '10px',
                      padding: '16px 20px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                    }}
                  >
                    {/* Circle Node on Timeline line */}
                    <div
                      style={{
                        position: 'absolute',
                        left: '-37px',
                        top: '18px',
                        width: '16px',
                        height: '16px',
                        borderRadius: '50%',
                        background: temp.requires_review ? '#ef4444' : precColor,
                        border: '3px solid #090d16',
                        boxShadow: `0 0 10px ${precColor}`,
                      }}
                    />

                    {/* Top Row: Record ID, Type & Precision Badge */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: '#f8fafc', fontFamily: "'JetBrains Mono', monospace" }}>
                          {rec.id}
                        </span>
                        <span style={{ fontSize: '11px', background: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
                          {rec.record_type || 'Record'}
                        </span>
                        {temp.is_estimate ? (
                          <span style={{ fontSize: '10px', background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                            ESTIMATE (±{temp.uncertainty_seconds || 0}s)
                          </span>
                        ) : (
                          <span style={{ fontSize: '10px', background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.25)', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                            OBSERVED
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: precColor, border: `1px solid ${precColor}40`, background: `${precColor}15`, padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                          Precision: {temp.timestamp_precision || 'unknown'}
                        </span>
                        {temp.requires_review && (
                          <span style={{ fontSize: '11px', background: '#ef444420', color: '#ef4444', border: '1px solid #ef4444', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <AlertTriangle size={12} /> REVIEW NEEDED
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Temporal Breakdown Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', background: '#020617', padding: '12px 14px', borderRadius: '8px', border: '1px solid #1e293b', fontSize: '12px', fontFamily: "'JetBrains Mono', monospace" }}>
                      <div>
                        <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase' }}>Normalized UTC Event Time</div>
                        <div style={{ color: temp.event_time ? '#38bdf8' : '#e2e8f0', fontWeight: 600, marginTop: '2px' }}>
                          {temp.event_time ? temp.event_time : <span style={{ color: '#f59e0b' }}>None (Year-only statistic)</span>}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase' }}>Original Raw String & TZ</div>
                        <div style={{ color: '#cbd5e1', marginTop: '2px' }}>
                          {temp.original_event_time || 'None'} ({temp.timezone || 'UTC'})
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase' }}>Source Created At</div>
                        <div style={{ color: '#94a3b8', marginTop: '2px' }}>
                          {temp.source_created_at || 'Not Provided'}
                        </div>
                      </div>

                      <div>
                        <div style={{ color: '#64748b', fontSize: '10px', textTransform: 'uppercase' }}>Ingested At</div>
                        <div style={{ color: '#94a3b8', marginTop: '2px' }}>
                          {temp.ingested_at || 'Recorded'}
                        </div>
                      </div>
                    </div>

                    {/* Strict Rule 10: Year-only Bounded Time Range Display */}
                    {isYearOnly && temp.time_range && (
                      <div style={{ marginTop: '10px', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '6px', padding: '8px 12px', fontSize: '12px' }}>
                        <div style={{ color: '#f59e0b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Info size={13} /> Strict Rule 10 Non-Fabrication Constraint:
                        </div>
                        <div style={{ color: '#cbd5e1', marginTop: '4px', fontSize: '11px', fontFamily: "'JetBrains Mono', monospace" }}>
                          Bounded Range: {temp.time_range.start} → {temp.time_range.end}
                        </div>
                        <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '2px' }}>
                          Limitation: {temp.time_range.limitation_note}
                        </div>
                      </div>
                    )}

                    {/* Review Flags Warnings */}
                    {temp.validation_flags && temp.validation_flags.length > 0 && (
                      <div style={{ marginTop: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', padding: '8px 12px', fontSize: '12px' }}>
                        <div style={{ color: '#ef4444', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <AlertTriangle size={13} /> Temporal Flags:
                        </div>
                        <ul style={{ margin: '4px 0 0 16px', color: '#fca5a5', fontSize: '11px' }}>
                          {temp.validation_flags.map((flag, fidx) => (
                            <li key={fidx}>{flag}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Record payload snippet */}
                    {rec.data && Object.keys(rec.data).length > 0 && (
                      <div style={{ marginTop: '10px', fontSize: '11px', color: '#64748b' }}>
                        Data: {JSON.stringify(rec.data).slice(0, 160)}...
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* 2. UNIVERSAL TIMESTAMP INSPECTOR                               */}
      {/* ============================================================== */}
      {activeSubTab === 'inspector' && (
        <div style={{ background: '#0b1120', padding: '24px', borderRadius: '12px', border: '1px solid #1e293b' }}>
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '16px', margin: '0 0 6px 0', color: '#f8fafc' }}>
              Universal Timestamp Parser & Normalizer
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
              Test any date format, RFC 2822, UNIX epoch, Apache CLF, Syslog, or year-only string.
              Validates internal UTC normalization while preserving source provenance and detecting conflicts.
            </p>
          </div>

          {/* Quick Preset Buttons */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '18px' }}>
            <span style={{ fontSize: '11px', color: '#64748b', alignSelf: 'center', marginRight: '4px' }}>Quick Tests:</span>
            {[
              { label: 'ISO Offset (-04:00)', val: '2024-05-18T10:30:00-04:00', created: '' },
              { label: 'RFC 2822 (EDT)', val: 'Mon, 18 May 2024 10:30:00 -0400', created: '' },
              { label: 'Unix Epoch (ms)', val: '1716028200000', created: '' },
              { label: 'Apache CLF', val: '[18/May/2024:14:30:00 +0000]', created: '' },
              { label: 'Year Only (Rule 10)', val: '2023', created: '' },
              { label: 'Conflicting Dates', val: '2024-01-01T00:00:00Z', created: '2021-01-01T00:00:00Z' },
              { label: 'Implausible (Feb 31)', val: '2024-02-31T12:00:00Z', created: '' },
              { label: 'Missing Date', val: '', created: '' },
            ].map((p, pidx) => (
              <button
                key={pidx}
                className="tag-btn"
                style={{ fontSize: '11px' }}
                onClick={() => {
                  setInspectRaw(p.val)
                  setInspectSourceCreated(p.created)
                }}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', marginBottom: '18px' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              Raw Event Timestamp Input *
              <input
                type="text"
                value={inspectRaw}
                onChange={e => setInspectRaw(e.target.value)}
                placeholder="e.g. 2024-05-18T14:30:00-04:00, 2023, 1716028200"
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '9px 12px', borderRadius: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px' }}
              />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              Source Created At (Optional for Conflict Detection)
              <input
                type="text"
                value={inspectSourceCreated}
                onChange={e => setInspectSourceCreated(e.target.value)}
                placeholder="e.g. 2024-05-18T10:00:00Z"
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '9px 12px', borderRadius: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px' }}
              />
            </label>

            <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: '#cbd5e1' }}>
              Verification Timestamp (Optional)
              <input
                type="text"
                value={inspectVerified}
                onChange={e => setInspectVerified(e.target.value)}
                placeholder="e.g. 2024-05-18T15:00:00Z"
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '9px 12px', borderRadius: '6px', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px' }}
              />
            </label>
          </div>

          <button
            className="primary-button"
            onClick={handleParseInspect}
            disabled={inspecting}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            {inspecting ? 'Parsing & Normalizing...' : 'Parse & Validate Timestamp'} <ArrowRight size={15} />
          </button>

          {/* Inspection Result Display */}
          {inspectResult && (
            <div style={{ marginTop: '24px', background: '#020617', border: '1px solid #1e293b', borderRadius: '10px', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <strong style={{ fontSize: '14px', color: inspectResult.requires_review ? '#ef4444' : '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {inspectResult.requires_review ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
                  Status: {inspectResult.validation_status?.toUpperCase() || 'RESULT'}
                </strong>
                <span style={{ fontSize: '11px', color: '#64748b' }}>
                  Ingested At: {inspectResult.ingested_at}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', fontFamily: "'JetBrains Mono', monospace", fontSize: '12px' }}>
                <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>Normalized UTC Event Time</div>
                  <div style={{ color: inspectResult.event_time ? '#38bdf8' : '#f59e0b', fontWeight: 600, marginTop: '3px' }}>
                    {inspectResult.event_time ? inspectResult.event_time : 'None (Year-only)'}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>Original Input & Timezone</div>
                  <div style={{ color: '#cbd5e1', marginTop: '3px' }}>
                    {inspectResult.original_event_time || 'None'} ({inspectResult.timezone || 'UTC'})
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>Precision Tier</div>
                  <div style={{ color: getPrecisionColor(inspectResult.timestamp_precision), fontWeight: 600, marginTop: '3px' }}>
                    {inspectResult.timestamp_precision || 'unknown'}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '10px 14px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b', fontSize: '11px' }}>Requires Human Review</div>
                  <div style={{ color: inspectResult.requires_review ? '#ef4444' : '#34d399', fontWeight: 600, marginTop: '3px' }}>
                    {inspectResult.requires_review ? 'YES (Flagged)' : 'NO (Valid)'}
                  </div>
                </div>
              </div>

              {/* Time Range Details (Strict Rule 10) */}
              {inspectResult.time_range && (
                <div style={{ marginTop: '14px', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px', padding: '10px 14px', fontSize: '12px' }}>
                  <div style={{ color: '#f59e0b', fontWeight: 600 }}>Bounded Range & Limitation Note (Strict Rule 10):</div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", color: '#e2e8f0', marginTop: '4px' }}>
                    Range: {inspectResult.time_range.start} → {inspectResult.time_range.end}
                  </div>
                  <div style={{ color: '#94a3b8', marginTop: '3px' }}>
                    Note: {inspectResult.time_range.limitation_note}
                  </div>
                </div>
              )}

              {/* Validation Flags list */}
              {inspectResult.validation_flags && inspectResult.validation_flags.length > 0 && (
                <div style={{ marginTop: '14px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.35)', borderRadius: '6px', padding: '10px 14px', fontSize: '12px' }}>
                  <div style={{ color: '#ef4444', fontWeight: 600 }}>Validation Flags:</div>
                  <ul style={{ margin: '6px 0 0 16px', color: '#fca5a5' }}>
                    {inspectResult.validation_flags.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* 3. MODULAR DATA INGESTION TAB                                  */}
      {/* ============================================================== */}
      {activeSubTab === 'ingest' && (
        <div style={{ background: '#0b1120', padding: '24px', borderRadius: '12px', border: '1px solid #1e293b' }}>
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '16px', margin: '0 0 6px 0', color: '#f8fafc' }}>
              Modular Temporal Ingestion Engine
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
              Ingest structured records, CSV datasets, application logs (Apache, Nginx, Syslog), or JSON payloads.
              Extracts timestamps, detects missing/conflicting entries, and populates the temporal registry.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            {['CSV', 'LOG', 'JSON'].map(fmt => (
              <button
                key={fmt}
                className={`tag-btn ${ingestType === fmt ? 'active' : ''}`}
                onClick={() => {
                  setIngestType(fmt)
                  if (fmt === 'CSV') {
                    setIngestContent(`id,event_time,kind,detail\ntx_101,2024-06-15T09:30:00+02:00,Transaction,Core ledger transfer\nstat_102,2023,Statistic,World Bank GDP observation\nlog_103,2024-02-31T12:00:00Z,LogEntry,Implausible calendar date`)
                  } else if (fmt === 'LOG') {
                    setIngestContent(`192.168.1.1 - - [18/May/2024:10:30:00 -0400] "GET /api/v1/health HTTP/1.1" 200 452\n2024-05-18T14:32:00.123Z [INFO] Service cluster started\ntime="2024-05-18T14:35:00Z" level=warn msg="Latency peak detected"`)
                  } else {
                    setIngestContent(JSON.stringify([
                      { id: 'node_1', kind: 'Deployment', event_time: '2024-05-18T10:30:00Z' },
                      { id: 'node_2', kind: 'Observation', year: 2023 },
                      { id: 'node_3', kind: 'Alert', timestamp: 'malformed_date_text' }
                    ], null, 2))
                  }
                }}
              >
                {fmt} Format
              </button>
            ))}
          </div>

          <textarea
            rows="8"
            value={ingestContent}
            onChange={e => setIngestContent(e.target.value)}
            style={{ width: '100%', background: '#020617', border: '1px solid #1e293b', color: '#f8fafc', padding: '12px 14px', borderRadius: '8px', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px', marginBottom: '16px' }}
          />

          <button
            className="primary-button"
            onClick={handleIngestSubmit}
            disabled={ingestingData}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            {ingestingData ? 'Ingesting & Validating...' : `Ingest ${ingestType} Data`} <ArrowRight size={15} />
          </button>

          {ingestStatus && (
            <div style={{ marginTop: '18px', padding: '14px 18px', background: ingestStatus.success ? '#020617' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${ingestStatus.success ? '#1e293b' : '#ef4444'}`, borderRadius: '8px', fontSize: '13px' }}>
              {ingestStatus.success ? (
                <div>
                  <strong style={{ color: '#34d399' }}>✓ Successfully Ingested {ingestStatus.total} Records</strong>
                  <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>
                    Valid records: {ingestStatus.valid} · Flagged for review: {ingestStatus.reviewNeeded}
                  </div>
                </div>
              ) : (
                <div style={{ color: '#ef4444' }}>
                  <strong>Error:</strong> {ingestStatus.error}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* 4. HISTORICAL WINDOW COMPARISON                                */}
      {/* ============================================================== */}
      {activeSubTab === 'compare' && (
        <div style={{ background: '#0b1120', padding: '24px', borderRadius: '12px', border: '1px solid #1e293b' }}>
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '16px', margin: '0 0 6px 0', color: '#f8fafc' }}>
              Historical Window Comparison
            </h4>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
              Compare record density, temporal coverage, and precision distributions between two historical time periods.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{ background: '#020617', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
              <strong style={{ color: '#38bdf8', fontSize: '13px', display: 'block', marginBottom: '10px' }}>
                Historical Window A (Baseline)
              </strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <label>
                  Start UTC:
                  <input
                    type="text"
                    value={windowAStart}
                    onChange={e => setWindowAStart(e.target.value)}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '6px 10px', borderRadius: '4px', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}
                  />
                </label>
                <label>
                  End UTC:
                  <input
                    type="text"
                    value={windowAEnd}
                    onChange={e => setWindowAEnd(e.target.value)}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '6px 10px', borderRadius: '4px', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}
                  />
                </label>
              </div>
            </div>

            <div style={{ background: '#020617', padding: '16px', borderRadius: '8px', border: '1px solid #1e293b' }}>
              <strong style={{ color: '#a78bfa', fontSize: '13px', display: 'block', marginBottom: '10px' }}>
                Historical Window B (Comparison)
              </strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                <label>
                  Start UTC:
                  <input
                    type="text"
                    value={windowBStart}
                    onChange={e => setWindowBStart(e.target.value)}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '6px 10px', borderRadius: '4px', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}
                  />
                </label>
                <label>
                  End UTC:
                  <input
                    type="text"
                    value={windowBEnd}
                    onChange={e => setWindowBEnd(e.target.value)}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f8fafc', padding: '6px 10px', borderRadius: '4px', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}
                  />
                </label>
              </div>
            </div>
          </div>

          <button
            className="primary-button"
            onClick={handleCompareWindows}
            disabled={comparing}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            {comparing ? 'Computing Historical Comparison...' : 'Compare Temporal Windows'} <ArrowRight size={15} />
          </button>

          {compareResult && !compareResult.error && (
            <div style={{ marginTop: '20px', background: '#020617', border: '1px solid #1e293b', borderRadius: '8px', padding: '18px' }}>
              <strong style={{ color: '#38bdf8', fontSize: '14px', display: 'block', marginBottom: '12px' }}>
                Window Comparison Results
              </strong>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', fontSize: '12px' }}>
                <div style={{ background: '#090d16', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b' }}>Window A Records</div>
                  <div style={{ color: '#38bdf8', fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {compareResult.window_a?.record_count ?? 0}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b' }}>Window B Records</div>
                  <div style={{ color: '#a78bfa', fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {compareResult.window_b?.record_count ?? 0}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b' }}>Record Delta</div>
                  <div style={{ color: '#f8fafc', fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {compareResult.comparison?.record_count_delta > 0 ? `+${compareResult.comparison?.record_count_delta}` : compareResult.comparison?.record_count_delta}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <div style={{ color: '#64748b' }}>Growth Rate</div>
                  <div style={{ color: '#34d399', fontSize: '18px', fontWeight: 700, marginTop: '4px' }}>
                    {compareResult.comparison?.growth_rate_pct != null ? `${compareResult.comparison.growth_rate_pct}%` : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* 5. REVIEW QUEUE FOR FLAGGED TIMESTAMPS                          */}
      {/* ============================================================== */}
      {activeSubTab === 'review' && (
        <div style={{ background: '#0b1120', padding: '24px', borderRadius: '12px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h4 style={{ fontSize: '16px', margin: '0 0 6px 0', color: '#f8fafc' }}>
                Temporal Data Quality & Flag Review Queue
              </h4>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
                Records with missing, malformed, conflicting, or implausible timestamps flagged for human review.
                Zero values are invented.
              </p>
            </div>
            <button
              className="tag-btn"
              onClick={fetchReviewFlags}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <RefreshCw size={13} /> Refresh Queue
            </button>
          </div>

          {reviewFlags.length === 0 ? (
            <div style={{ padding: '36px', textAlign: 'center', color: '#34d399', background: 'rgba(52, 211, 153, 0.05)', borderRadius: '10px', border: '1px solid rgba(52, 211, 153, 0.2)' }}>
              <CheckCircle2 size={32} style={{ margin: '0 auto 10px auto' }} />
              <strong style={{ display: 'block', fontSize: '14px' }}>No Flagged Timestamps in Review Queue</strong>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                All ingested records satisfy validation checks with zero conflicting or implausible dates.
              </span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {reviewFlags.map((flagged, fidx) => {
                const temp = flagged.temporal || {}
                return (
                  <div
                    key={fidx}
                    style={{
                      background: '#020617',
                      border: '1px solid #ef4444',
                      borderRadius: '8px',
                      padding: '14px 18px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ color: '#ef4444', fontWeight: 700, fontSize: '13px', fontFamily: "'JetBrains Mono', monospace" }}>
                          {flagged.id || `Flagged Record #${fidx + 1}`}
                        </span>
                        <span style={{ fontSize: '11px', background: '#ef444420', color: '#ef4444', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                          {temp.validation_status || 'FLAGGED'}
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        Source: {temp.source_provenance?.source_name || 'System Ingest'}
                      </span>
                    </div>

                    <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '8px', fontFamily: "'JetBrains Mono', monospace" }}>
                      Raw input: <code style={{ color: '#f59e0b' }}>{temp.original_event_time || 'None (Missing)'}</code>
                    </div>

                    {temp.validation_flags && temp.validation_flags.length > 0 && (
                      <div style={{ background: '#090d16', padding: '8px 12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                        <div style={{ color: '#ef4444', fontSize: '11px', fontWeight: 600 }}>Reasons for Review Flag:</div>
                        <ul style={{ margin: '4px 0 0 16px', color: '#fca5a5', fontSize: '11px' }}>
                          {temp.validation_flags.map((flag, i) => (
                            <li key={i}>{flag}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
