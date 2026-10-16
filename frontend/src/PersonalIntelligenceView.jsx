import React, { useState, useEffect, useMemo } from 'react'
import {
  GraduationCap, Calendar, Award, BookOpen, School, TrendingUp, TrendingDown,
  ShieldCheck, ShieldAlert, Eye, EyeOff, Plus, Trash2, Edit3, CheckCircle2,
  AlertTriangle, Sparkles, ArrowRight, BarChart3, Clock, Check, Info, RefreshCw,
  Layers, Lock, BrainCircuit, X
} from 'lucide-react'

// Milestone level definitions with themes and canonical icons
const MILESTONE_CONFIG = {
  class_10: {
    title: 'Class 10 (Secondary)',
    shortTitle: 'Class 10',
    color: '#69a9ff', // Blue
    bgLight: 'rgba(105, 169, 255, 0.12)',
    border: 'rgba(105, 169, 255, 0.35)',
    defaultStream: 'General',
    expectedGap: null,
  },
  class_12: {
    title: 'Class 12 (Higher Secondary)',
    shortTitle: 'Class 12',
    color: '#64d7b2', // Mint
    bgLight: 'rgba(100, 215, 178, 0.12)',
    border: 'rgba(100, 215, 178, 0.35)',
    defaultStream: 'Science / Commerce / Arts',
    expectedGap: '2 Years typical',
  },
  btech: {
    title: 'B.Tech (Undergraduate)',
    shortTitle: 'B.Tech',
    color: '#a18aff', // Violet
    bgLight: 'rgba(161, 138, 255, 0.12)',
    border: 'rgba(161, 138, 255, 0.35)',
    defaultStream: 'Computer Science / Engineering',
    expectedGap: '4 Years typical',
  },
}

// Sample authentic academic data for quick verification
const SAMPLE_PROFILE = [
  {
    level: 'Class 10',
    institution: 'Delhi Public School, R.K. Puram',
    board_or_university: 'CBSE',
    passing_year: 2018,
    stream_or_major: 'General',
    grading_system: 'percentage',
    score: 92.4,
    max_score: 100.0,
    roll_or_registration_number: 'CBSE-10-847291',
    notes: 'Awarded School Scholar Certificate for academic excellence in Science and Mathematics.',
  },
  {
    level: 'Class 12',
    institution: 'Delhi Public School, R.K. Puram',
    board_or_university: 'CBSE',
    passing_year: 2020,
    stream_or_major: 'Science (PCM with Computer Science)',
    grading_system: 'percentage',
    score: 89.8,
    max_score: 100.0,
    roll_or_registration_number: 'CBSE-12-918230',
    notes: 'Subject topper in Computer Science (Python/SQL) with 98/100.',
  },
  {
    level: 'B.Tech',
    institution: 'Indian Institute of Technology (BHU) Varanasi',
    board_or_university: 'IIT (Autonomous)',
    passing_year: 2024,
    stream_or_major: 'Computer Science and Engineering',
    grading_system: 'cgpa',
    score: 8.85,
    max_score: 10.0,
    roll_or_registration_number: 'IITBHU-CSE-2020-048',
    notes: 'Graduated with First Class Honours. Capstone project on distributed graph neural networks.',
  },
]

export default function PersonalIntelligenceView() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMsg, setSuccessMsg] = useState(null)
  const [maskSensitive, setMaskSensitive] = useState(true)

  // Record Form Modal / State
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const [formData, setFormData] = useState({
    level: 'Class 10',
    institution: '',
    board_or_university: '',
    passing_year: 2018,
    stream_or_major: '',
    grading_system: 'percentage',
    score: '',
    max_score: 100.0,
    roll_or_registration_number: '',
    notes: '',
  })

  // Evidence-Based Academic AI Analysis state
  const [personalAi, setPersonalAi] = useState(null)
  const [personalAiLoading, setPersonalAiLoading] = useState(false)
  const [showPersonalAi, setShowPersonalAi] = useState(false)

  const handleRunPersonalAi = async () => {
    setPersonalAiLoading(true)
    try {
      const res = await fetch(`/api/ai/analyze/personal?mask_sensitive=${maskSensitive}`)
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Academic AI analysis failed.')
      }
      setPersonalAi(data)
      setShowPersonalAi(true)
    } catch (err) {
      alert('Academic AI Analysis Error: ' + err.message)
    } finally {
      setPersonalAiLoading(false)
    }
  }

  // Load Personal Profile on mount or when privacy toggle changes
  const fetchProfile = async (mask = maskSensitive) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/personal/profile?mask=${mask}`)
      if (!res.ok) {
        throw new Error(`Failed to load profile (${res.status})`)
      }
      const data = await res.json()
      setProfile(data)
    } catch (err) {
      console.error('Failed to fetch personal profile:', err)
      setError(err.message || 'Unable to connect to Personal Intelligence backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile(maskSensitive)
  }, [maskSensitive])

  // Handle Form Input Changes
  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => {
      const updated = { ...prev, [name]: value }
      // Auto-set max score based on grading system
      if (name === 'grading_system') {
        updated.max_score = value === 'percentage' ? 100.0 : 10.0
      }
      if (name === 'level') {
        if (value === 'Class 10') updated.stream_or_major = 'General'
        if (value === 'Class 12' && (!prev.stream_or_major || prev.stream_or_major === 'General')) {
          updated.stream_or_major = 'Science (PCM)'
        }
        if (value === 'B.Tech' && (!prev.stream_or_major || prev.stream_or_major === 'Science (PCM)')) {
          updated.stream_or_major = 'Computer Science & Engineering'
        }
      }
      return updated
    })
  }

  // Pre-fill form for specific level
  const openFormForLevel = (levelKey) => {
    const existingRec = profile?.actual_records?.find(r => r.level_key === levelKey)
    if (existingRec) {
      setFormData({
        level: existingRec.qualification,
        institution: existingRec.institution,
        board_or_university: existingRec.board_or_university,
        passing_year: existingRec.passing_year,
        stream_or_major: existingRec.stream_or_major,
        grading_system: existingRec.grading_system,
        score: existingRec.score,
        max_score: existingRec.max_score,
        roll_or_registration_number: existingRec.roll_or_registration_number || '',
        notes: existingRec.notes || '',
      })
    } else {
      const lvlMap = { class_10: 'Class 10', class_12: 'Class 12', btech: 'B.Tech' }
      const yrMap = { class_10: 2018, class_12: 2020, btech: 2024 }
      const streamMap = { class_10: 'General', class_12: 'Science (PCM)', btech: 'Computer Science and Engineering' }
      const lvl = lvlMap[levelKey] || 'Class 10'
      setFormData({
        level: lvl,
        institution: '',
        board_or_university: levelKey === 'btech' ? 'Autonomous / Central University' : 'CBSE',
        passing_year: yrMap[levelKey] || 2020,
        stream_or_major: streamMap[levelKey] || '',
        grading_system: levelKey === 'btech' ? 'cgpa' : 'percentage',
        score: '',
        max_score: levelKey === 'btech' ? 10.0 : 100.0,
        roll_or_registration_number: '',
        notes: '',
      })
    }
    setFormError(null)
    setShowForm(true)
  }

  // Submit Academic Record
  const handleSubmitRecord = async (e) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)

    try {
      const payload = {
        level: formData.level,
        institution: formData.institution.trim(),
        board_or_university: formData.board_or_university.trim(),
        passing_year: parseInt(formData.passing_year, 10),
        stream_or_major: formData.stream_or_major.trim(),
        grading_system: formData.grading_system,
        score: parseFloat(formData.score),
        max_score: parseFloat(formData.max_score),
        roll_or_registration_number: formData.roll_or_registration_number.trim(),
        notes: formData.notes.trim(),
      }

      if (!payload.institution) throw new Error('Please enter an institution name.')
      if (isNaN(payload.score)) throw new Error('Please enter a valid numeric score.')

      const res = await fetch('/api/personal/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const result = await res.json()
      if (!res.ok) {
        throw new Error(result.detail || 'Validation error while saving record.')
      }

      setProfile(result)
      setShowForm(false)
      setSuccessMsg(`Successfully recorded ground truth for ${formData.level}!`)
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  // Delete Record
  const handleDeleteRecord = async (levelKey) => {
    if (!window.confirm(`Are you sure you want to delete the ${levelKey} record? This action cannot be undone.`)) {
      return
    }
    try {
      const res = await fetch(`/api/personal/record/${levelKey}`, { method: 'DELETE' })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to delete record.')
      }
      const data = await res.json()
      setProfile(data.profile)
      setSuccessMsg(`Removed record for ${levelKey}.`)
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err) {
      alert(err.message)
    }
  }

  // Load Sample Profile
  const handleLoadSample = async () => {
    setLoading(true)
    setError(null)
    try {
      for (const rec of SAMPLE_PROFILE) {
        const res = await fetch('/api/personal/record', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(rec),
        })
        if (!res.ok) {
          const err = await res.json()
          throw new Error(err.detail || 'Failed to load sample record.')
        }
      }
      await fetchProfile(maskSensitive)
      setSuccessMsg('Loaded sample academic profile with Class 10, Class 12, and B.Tech records!')
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Reset Profile
  const handleResetProfile = async () => {
    if (!window.confirm('Reset and clear all personal academic records? All personal intelligence entries will be erased.')) {
      return
    }
    try {
      await fetch('/api/personal/profile', { method: 'DELETE' })
      await fetchProfile(maskSensitive)
      setSuccessMsg('Personal profile reset. All records cleared.')
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err) {
      setError(err.message)
    }
  }

  // Render score bar
  const renderScoreBar = (normalizedPct, color) => {
    return (
      <div style={{ height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden', marginTop: '6px' }}>
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, Math.max(0, normalizedPct))}%`,
            background: `linear-gradient(90deg, ${color}, #8c79ff)`,
            borderRadius: '4px',
            transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>
    )
  }

  return (
    <div className="personal-intelligence-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Header & Privacy Control Toolbar */}
      <div className="panel" style={{ padding: '24px 28px', background: 'linear-gradient(135deg, #101725 0%, #151d30 100%)', border: '1px solid #233047' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '10px',
                background: 'linear-gradient(135deg, #a18aff 0%, #69a9ff 100%)',
                display: 'grid', placeItems: 'center', color: '#090d17', fontWeight: 800
              }}>
                <GraduationCap size={20} />
              </div>
              <h2 style={{ margin: 0, fontSize: '21px', fontWeight: 700, letterSpacing: '-0.4px', color: '#f3f6fc' }}>
                Personal Intelligence — Academic Provenance & Timeline
              </h2>
            </div>
            <p style={{ margin: '8px 0 0 46px', fontSize: '13px', color: '#9aa7bc', maxWidth: '720px', lineHeight: '1.5' }}>
              Documented chronological milestones for <strong>Class 10</strong>, <strong>Class 12</strong>, and <strong>B.Tech</strong>.
              Strictly preserves user ground truth, calculates isolated derived insights, and never fabricates missing records.
            </p>
          </div>

          {/* Privacy & Action Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            {/* Privacy Masking Toggle */}
            <button
              onClick={() => setMaskSensitive(prev => !prev)}
              className="btn btn-secondary"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: maskSensitive ? 'rgba(100, 215, 178, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                borderColor: maskSensitive ? '#64d7b2' : '#2c3a52',
                color: maskSensitive ? '#64d7b2' : '#c3cde3',
                fontSize: '12px', padding: '8px 14px', borderRadius: '8px', fontWeight: 600
              }}
              title="Toggle masking on sensitive roll numbers and registration details"
            >
              {maskSensitive ? <EyeOff size={15} /> : <Eye size={15} />}
              {maskSensitive ? 'Privacy Protected (Masked)' : 'Privacy Masking: Off'}
            </button>

            {/* Quick Sample Button */}
            <button
              onClick={handleLoadSample}
              className="btn btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', padding: '8px 12px', borderRadius: '8px' }}
              title="Populate complete sample Class 10, Class 12, and B.Tech profile"
            >
              <Sparkles size={14} color="#f0bc78" /> Load Sample Profile
            </button>

            {/* Add Record Button */}
            <button
              onClick={() => openFormForLevel('class_10')}
              className="btn btn-primary"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '6px',
                fontSize: '12px', padding: '8px 16px', borderRadius: '8px',
                background: 'linear-gradient(135deg, #7c68ee 0%, #5d48db 100%)',
                color: '#fff', fontWeight: 600, border: 'none'
              }}
            >
              <Plus size={15} /> Record Academic Milestone
            </button>

            {/* Evidence-Based Academic AI Analysis Button */}
            <button
              onClick={handleRunPersonalAi}
              disabled={personalAiLoading}
              className="ai-analysis-trigger-btn"
              title="Perform evidence-based academic analysis on recorded qualifications"
            >
              <BrainCircuit size={14} className={personalAiLoading ? 'spin' : ''} />
              <span>{personalAiLoading ? 'Synthesizing...' : 'Evidence-Based Academic Analysis'}</span>
            </button>

            {profile?.summary?.recorded_milestones_count > 0 && (
              <button
                onClick={handleResetProfile}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '8px 10px', borderRadius: '8px', color: '#ff7b72', borderColor: 'rgba(255, 123, 114, 0.3)' }}
                title="Erase all academic records"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Status Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#64d7b2', background: 'rgba(100, 215, 178, 0.1)', padding: '4px 10px', borderRadius: '20px', border: '1px solid rgba(100, 215, 178, 0.25)', fontWeight: 600 }}>
            <ShieldCheck size={13} /> ZERO DATA FABRICATION GUARANTEED
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#a18aff', background: 'rgba(161, 138, 255, 0.1)', padding: '4px 10px', borderRadius: '20px', border: '1px solid rgba(161, 138, 255, 0.25)', fontWeight: 600 }}>
            <Layers size={13} /> {profile?.summary?.recorded_milestones_count || 0} / 3 Milestones Recorded
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#f0bc78', background: 'rgba(240, 188, 120, 0.1)', padding: '4px 10px', borderRadius: '20px', border: '1px solid rgba(240, 188, 120, 0.25)', fontWeight: 600 }}>
            <Lock size={13} /> Local + FalkorDB Secure Storage
          </span>
        </div>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div style={{ padding: '12px 18px', background: 'rgba(100, 215, 178, 0.12)', border: '1px solid #64d7b2', borderRadius: '8px', color: '#64d7b2', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px' }}>
          <CheckCircle2 size={18} /> {successMsg}
        </div>
      )}

      {/* Global Error Banner */}
      {error && (
        <div style={{ padding: '12px 18px', background: 'rgba(255, 123, 114, 0.12)', border: '1px solid #ff7b72', borderRadius: '8px', color: '#ff7b72', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px' }}>
          <AlertTriangle size={18} /> {error}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !profile && (
        <div className="panel" style={{ padding: '40px', textAlign: 'center', color: '#9aa7bc' }}>
          <RefreshCw className="animate-spin" size={24} style={{ margin: '0 auto 12px', display: 'block', color: '#a18aff' }} />
          Loading personal intelligence academic records...
        </div>
      )}

      {/* 2. Chronological Timeline Progression Roadmap */}
      <div className="panel" style={{ padding: '24px 28px', background: '#101725', border: '1px solid #233047' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 700, color: '#f3f6fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={17} color="#a18aff" /> Chronological Academic Timeline
            </h3>
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#9aa7bc' }}>
              Chronological progression from Class 10 to Undergraduate degree with certified milestones.
            </p>
          </div>
          <div style={{ fontSize: '11px', color: '#78869f' }}>
            <span style={{ color: '#64d7b2', fontWeight: 600 }}>● ACTUAL RECORD</span> = Self-Attested Transcript | <span style={{ color: '#a18aff', fontWeight: 600 }}>★ DERIVED INSIGHT</span> = Calculated Metric
          </div>
        </div>

        {/* Milestone Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', position: 'relative' }}>
          {['class_10', 'class_12', 'btech'].map((levelKey, index) => {
            const config = MILESTONE_CONFIG[levelKey]
            const record = profile?.timeline?.find(t => t.level_key === levelKey)
            const isRecorded = Boolean(record)

            return (
              <div
                key={levelKey}
                style={{
                  background: isRecorded ? '#131b2c' : 'rgba(16, 23, 37, 0.4)',
                  border: isRecorded ? `1px solid ${config.border}` : '1px dashed #233047',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  boxShadow: isRecorded ? '0 4px 20px rgba(0,0,0,0.25)' : 'none',
                  transition: 'all 0.3s ease',
                }}
              >
                {/* Milestone Step Header */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '28px', height: '28px', borderRadius: '50%',
                      background: isRecorded ? config.color : '#233047',
                      color: isRecorded ? '#090d17' : '#9aa7bc',
                      display: 'grid', placeItems: 'center',
                      fontWeight: 700, fontSize: '12px',
                    }}>
                      {index + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: isRecorded ? '#f3f6fc' : '#78869f' }}>
                        {config.title}
                      </div>
                      <div style={{ fontSize: '11px', color: '#9aa7bc' }}>
                        {config.expectedGap ? `${config.expectedGap}` : 'Foundation Stage'}
                      </div>
                    </div>
                  </div>

                  {isRecorded ? (
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: '4px',
                      fontSize: '10px', fontWeight: 700, letterSpacing: '0.4px',
                      color: '#64d7b2', background: 'rgba(100, 215, 178, 0.12)',
                      padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(100, 215, 178, 0.3)'
                    }}>
                      <Check size={11} /> ACTUAL RECORD
                    </span>
                  ) : (
                    <span style={{
                      fontSize: '10px', fontWeight: 600, color: '#78869f',
                      background: 'rgba(255, 255, 255, 0.04)', padding: '3px 8px',
                      borderRadius: '6px', border: '1px dashed #233047'
                    }}>
                      NOT RECORDED
                    </span>
                  )}
                </div>

                {/* Milestone Body */}
                {isRecorded ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                    {/* Institution & Board */}
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: '#e8edf7', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                        <School size={16} color={config.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span>{record.institution}</span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#9aa7bc', margin: '3px 0 0 22px' }}>
                        Board / University: <strong style={{ color: '#c3cde3' }}>{record.board_or_university}</strong>
                      </div>
                      <div style={{ fontSize: '12px', color: '#9aa7bc', margin: '2px 0 0 22px' }}>
                        Stream / Specialization: <strong style={{ color: '#c3cde3' }}>{record.stream_or_major}</strong>
                      </div>
                    </div>

                    {/* Score Showcase & Normalized Conversion */}
                    <div style={{
                      padding: '12px 14px', borderRadius: '8px',
                      background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255, 255, 255, 0.05)',
                      marginTop: '4px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '11px', color: '#9aa7bc', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Official Ground-Truth Score
                        </span>
                        <span style={{ fontSize: '11px', color: '#64d7b2', fontWeight: 600 }}>
                          Passing Year: {record.passing_year}
                        </span>
                      </div>
                      <div style={{ fontSize: '22px', fontWeight: 800, color: config.color, margin: '4px 0 0' }}>
                        {record.score_display}
                      </div>

                      {/* Explicit Derived Calculation Tag */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px', paddingTop: '6px', borderTop: '1px dashed rgba(255,255,255,0.08)' }}>
                        <span style={{ fontSize: '10px', color: '#a18aff', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Sparkles size={11} /> Derived Normalized Equivalent:
                        </span>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#e8edf7' }}>
                          {record.normalized_percentage}%
                        </span>
                      </div>
                      {renderScoreBar(record.normalized_percentage, config.color)}
                    </div>

                    {/* Sensitive Details (Maskable) */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: '#78869f', marginTop: 'auto', paddingTop: '8px' }}>
                      <span>
                        Roll / Reg: <strong style={{ color: '#9aa7bc' }}>{record.roll_or_registration_number || 'N/A'}</strong>
                      </span>
                      {record.years_since_previous !== null && (
                        <span style={{ color: '#9aa7bc' }}>
                          +{record.years_since_previous} years after prior stage
                        </span>
                      )}
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <button
                        onClick={() => openFormForLevel(levelKey)}
                        className="btn btn-secondary"
                        style={{ flex: 1, fontSize: '11px', padding: '6px 10px', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
                      >
                        <Edit3 size={12} /> Edit Record
                      </button>
                      <button
                        onClick={() => handleDeleteRecord(levelKey)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '6px 10px', borderRadius: '6px', color: '#ff7b72', borderColor: 'rgba(255,123,114,0.3)' }}
                        title="Delete this record"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Missing State (Strictly Never Fabricated) */
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '28px 10px', textAlign: 'center', flex: 1, gap: '12px' }}>
                    <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'rgba(255,255,255,0.03)', display: 'grid', placeItems: 'center', color: '#78869f' }}>
                      <BookOpen size={20} />
                    </div>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: '#9aa7bc' }}>
                        No Record Entered Yet
                      </div>
                      <div style={{ fontSize: '11px', color: '#78869f', marginTop: '3px' }}>
                        Zero-fabrication rule active: missing data is strictly null.
                      </div>
                    </div>
                    <button
                      onClick={() => openFormForLevel(levelKey)}
                      className="btn btn-secondary"
                      style={{
                        fontSize: '11px', padding: '7px 14px', borderRadius: '6px',
                        display: 'inline-flex', alignItems: 'center', gap: '6px',
                        background: config.bgLight, color: config.color, borderColor: config.border
                      }}
                    >
                      <Plus size={13} /> Enter {config.shortTitle} Record
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 3. Comparison of Available Results & Calculated Insights */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px' }}>
        {/* Comparative Milestone Analysis */}
        <div className="panel" style={{ padding: '24px 28px', background: '#101725', border: '1px solid #233047' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#f3f6fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={17} color="#69a9ff" /> Available Results Comparison
            </h3>
            <span style={{ fontSize: '11px', color: '#9aa7bc' }}>
              {profile?.comparison?.available_milestones?.length || 0} of 3 Stages Compared
            </span>
          </div>

          {profile?.comparison?.available_milestones?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Comparative Matrix Table */}
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #233047', color: '#78869f' }}>
                      <th style={{ padding: '8px 6px' }}>Milestone</th>
                      <th style={{ padding: '8px 6px' }}>Year</th>
                      <th style={{ padding: '8px 6px' }}>Raw Score</th>
                      <th style={{ padding: '8px 6px' }}>Normalized</th>
                      <th style={{ padding: '8px 6px' }}>Stream / Major</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.comparison.comparison_matrix.map(row => (
                      <tr key={row.qualification} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '10px 6px', fontWeight: 700, color: '#f3f6fc' }}>
                          {row.qualification}
                        </td>
                        <td style={{ padding: '10px 6px', color: '#9aa7bc' }}>
                          {row.passing_year}
                        </td>
                        <td style={{ padding: '10px 6px', fontWeight: 600, color: '#64d7b2' }}>
                          {row.raw_score}
                        </td>
                        <td style={{ padding: '10px 6px', fontWeight: 700, color: '#a18aff' }}>
                          {row.normalized_percentage}%
                        </td>
                        <td style={{ padding: '10px 6px', color: '#c3cde3' }}>
                          {row.stream}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Step-by-Step Score Progression Deltas */}
              {profile.comparison.score_deltas?.length > 0 ? (
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.6px', color: '#78869f', marginBottom: '8px', fontWeight: 600 }}>
                    Step-by-Step Transition Trajectory
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {profile.comparison.score_deltas.map((delta, i) => (
                      <div
                        key={i}
                        style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '10px 14px', background: 'rgba(255,255,255,0.02)',
                          border: '1px solid #233047', borderRadius: '8px', fontSize: '12px'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontWeight: 600, color: '#e8edf7' }}>{delta.from_qualification}</span>
                          <ArrowRight size={13} color="#78869f" />
                          <span style={{ fontWeight: 600, color: '#e8edf7' }}>{delta.to_qualification}</span>
                          <span style={{ fontSize: '11px', color: '#78869f' }}>({delta.years_gap} yrs interval)</span>
                        </div>
                        <span style={{
                          fontWeight: 700,
                          color: delta.percentage_change >= 0 ? '#64d7b2' : '#f0bc78',
                          display: 'inline-flex', alignItems: 'center', gap: '4px'
                        }}>
                          {delta.percentage_change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                          {delta.percentage_change >= 0 ? `+${delta.percentage_change}%` : `${delta.percentage_change}%`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ padding: '14px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', fontSize: '12px', color: '#78869f', textAlign: 'center' }}>
                  <Info size={14} style={{ display: 'inline', marginRight: '6px' }} />
                  Record at least 2 milestones to activate transition progression and growth deltas.
                </div>
              )}
            </div>
          ) : (
            <div style={{ padding: '30px', textAlign: 'center', color: '#78869f', fontSize: '13px' }}>
              No academic milestones recorded yet. Add records above to compare performance.
            </div>
          )}
        </div>

        {/* Calculated Insights Engine (Clearly Isolated) */}
        <div className="panel" style={{ padding: '24px 28px', background: '#101725', border: '1px solid #233047' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#f3f6fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={17} color="#a18aff" /> Calculated Insights
            </h3>
            <span style={{
              fontSize: '10px', color: '#a18aff', background: 'rgba(161, 138, 255, 0.1)',
              padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(161, 138, 255, 0.25)', fontWeight: 600
            }}>
              DERIVED ANALYTICS
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {profile?.calculated_insights?.length > 0 ? (
              profile.calculated_insights.map(insight => (
                <div
                  key={insight.insight_key}
                  style={{
                    padding: '14px 16px', borderRadius: '10px',
                    background: 'rgba(161, 138, 255, 0.04)', border: '1px solid rgba(161, 138, 255, 0.18)',
                    display: 'flex', flexDirection: 'column', gap: '6px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#c3cde3' }}>
                      {insight.title}
                    </span>
                    <span style={{ fontSize: '15px', fontWeight: 800, color: '#a18aff' }}>
                      {insight.value}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#9aa7bc' }}>
                    {insight.interpretation}
                  </div>
                  <div style={{ fontSize: '10px', color: '#78869f', fontFamily: 'monospace', paddingTop: '4px', borderTop: '1px dashed rgba(255,255,255,0.06)' }}>
                    Formula: {insight.derivation_formula}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '30px', textAlign: 'center', color: '#78869f', fontSize: '13px' }}>
                Record academic milestones to compute derived insights.
              </div>
            )}

            {/* Strict Notice regarding calculated vs actual */}
            <div style={{
              marginTop: '8px', padding: '10px 14px', borderRadius: '8px',
              background: 'rgba(240, 188, 120, 0.05)', border: '1px solid rgba(240, 188, 120, 0.2)',
              fontSize: '11px', color: '#f0bc78', lineHeight: '1.4'
            }}>
              <strong>Zero-Fabrication Notice:</strong> Calculated insights are mathematical projections derived solely from verified records. Missing milestones are never guessed or filled with default estimates.
            </div>
          </div>
        </div>
      </div>

      {/* 4. Modal Record Entry / Edit Form */}
      {showForm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0, 0, 0, 0.75)', backdropFilter: 'blur(6px)',
          display: 'grid', placeItems: 'center', padding: '20px'
        }}>
          <div
            className="panel"
            style={{
              width: '100%', maxWidth: '580px', maxHeight: '90vh', overflowY: 'auto',
              padding: '28px', background: '#121a2a', border: '1px solid #2f3e58',
              borderRadius: '14px', boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#f3f6fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <GraduationCap size={20} color="#a18aff" />
                Record Academic Milestone
              </h3>
              <button
                onClick={() => setShowForm(false)}
                style={{ background: 'none', border: 'none', color: '#9aa7bc', cursor: 'pointer', padding: '4px' }}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div style={{ padding: '10px 14px', background: 'rgba(255, 123, 114, 0.15)', border: '1px solid #ff7b72', borderRadius: '8px', color: '#ff7b72', marginBottom: '16px', fontSize: '12px' }}>
                <AlertTriangle size={15} style={{ display: 'inline', marginRight: '6px' }} />
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmitRecord} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Level Selector */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                  Qualification Level *
                </label>
                <select
                  name="level"
                  value={formData.level}
                  onChange={handleInputChange}
                  style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                >
                  <option value="Class 10">Class 10 (Secondary / Matriculation)</option>
                  <option value="Class 12">Class 12 (Higher Secondary / Intermediate)</option>
                  <option value="B.Tech">B.Tech (Bachelor of Technology / Undergraduate)</option>
                </select>
              </div>

              {/* Institution */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                  School / College / University Name *
                </label>
                <input
                  type="text"
                  name="institution"
                  value={formData.institution}
                  onChange={handleInputChange}
                  placeholder="e.g. Delhi Public School / IIT Bombay"
                  required
                  style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                />
              </div>

              {/* Board / University & Passing Year */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                    Affiliated Board / University *
                  </label>
                  <input
                    type="text"
                    name="board_or_university"
                    value={formData.board_or_university}
                    onChange={handleInputChange}
                    placeholder="e.g. CBSE, ICSE, State Board, Autonomous"
                    required
                    style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                    Passing Year *
                  </label>
                  <input
                    type="number"
                    name="passing_year"
                    value={formData.passing_year}
                    onChange={handleInputChange}
                    min="1970"
                    max="2035"
                    required
                    style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                  />
                </div>
              </div>

              {/* Stream / Major */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                  Stream / Academic Branch
                </label>
                <input
                  type="text"
                  name="stream_or_major"
                  value={formData.stream_or_major}
                  onChange={handleInputChange}
                  placeholder={formData.level === 'Class 10' ? 'General' : formData.level === 'Class 12' ? 'e.g. Science (PCM)' : 'e.g. Computer Science and Engineering'}
                  style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                />
              </div>

              {/* Grading System & Score */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                    Grading Scale
                  </label>
                  <select
                    name="grading_system"
                    value={formData.grading_system}
                    onChange={handleInputChange}
                    style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="cgpa">CGPA (Scale 10.0)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                    Score Obtained *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="score"
                    value={formData.score}
                    onChange={handleInputChange}
                    placeholder={formData.grading_system === 'percentage' ? 'e.g. 91.5' : 'e.g. 8.75'}
                    required
                    style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                    Max Possible
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    name="max_score"
                    value={formData.max_score}
                    onChange={handleInputChange}
                    required
                    style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                  />
                </div>
              </div>

              {/* Roll / Registration Number (Optional & Maskable) */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                  Roll / Registration Number <span style={{ color: '#78869f' }}>(Optional · Protected Personal Data)</span>
                </label>
                <input
                  type="text"
                  name="roll_or_registration_number"
                  value={formData.roll_or_registration_number}
                  onChange={handleInputChange}
                  placeholder="e.g. CBSE-10-847291"
                  style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px' }}
                />
              </div>

              {/* Notes */}
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#c3cde3', marginBottom: '6px' }}>
                  Honours, Subject Scores, or Notes
                </label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  rows={2}
                  placeholder="e.g. Distinction in Science & Math, Capstone Honours"
                  style={{ width: '100%', padding: '10px 12px', background: '#0c111d', border: '1px solid #233047', borderRadius: '8px', color: '#e8edf7', fontSize: '13px', resize: 'vertical' }}
                />
              </div>

              {/* Form Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="btn btn-secondary"
                  style={{ padding: '9px 18px', borderRadius: '8px', fontSize: '13px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn btn-primary"
                  style={{
                    padding: '9px 22px', borderRadius: '8px', fontSize: '13px',
                    background: 'linear-gradient(135deg, #7c68ee 0%, #5d48db 100%)',
                    color: '#fff', border: 'none', fontWeight: 600
                  }}
                >
                  {submitting ? 'Validating & Saving...' : 'Save Academic Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Evidence-Based Academic AI Analysis Modal */}
      {showPersonalAi && personalAi && (
        <div className="ai-modal-overlay" onClick={() => setShowPersonalAi(false)}>
          <div className="ai-modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="ai-modal-header">
              <div className="ai-modal-header-left">
                <div className="ai-modal-icon" style={{ background: 'linear-gradient(135deg, #64d7b2 0%, #a18aff 100%)' }}>
                  <BrainCircuit size={20} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 className="ai-modal-title">Evidence-Based Academic Analysis</h3>
                    <span className="ai-scope-badge personal">
                      {personalAi.analysis_scope}
                    </span>
                  </div>
                  <p className="ai-modal-subtitle">
                    Isolated evaluation of user-attested transcripts with zero data fabrication
                  </p>
                </div>
              </div>
              <button
                className="ai-modal-close-btn"
                onClick={() => setShowPersonalAi(false)}
                aria-label="Close modal"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="ai-modal-scrollable">
              {/* Executive Summary */}
              <div className="ai-synthesis-box">
                <div className="ai-synthesis-label">
                  <Sparkles size={14} /> Academic Synthesis Narrative
                </div>
                <p className="ai-synthesis-text">{personalAi.summary}</p>
              </div>

              {!personalAi.has_records ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#9aa7bc' }}>
                  <Info size={24} style={{ margin: '0 auto 8px', display: 'block', color: '#f0bc78' }} />
                  Please record your Class 10, Class 12, or B.Tech milestones above or load sample records to generate evidence-based academic analytics.
                </div>
              ) : (
                <>
                  {/* Key Progression Metrics */}
                  {personalAi.milestone_progression && (
                    <div className="ai-metrics-grid">
                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Trajectory Classification</span>
                        <div className="ai-metric-value" style={{ color: '#64d7b2', fontSize: '15px' }}>
                          {personalAi.milestone_progression.trajectory_summary}
                        </div>
                        <span className="ai-metric-sub">
                          {personalAi.recorded_milestones_count} of 3 milestones recorded
                        </span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Academic Average</span>
                        <div className="ai-metric-value" style={{ color: '#a18aff' }}>
                          {personalAi.milestone_progression.average_normalized_score}%
                        </div>
                        <span className="ai-metric-sub">Normalized percentage average</span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Highest Milestone</span>
                        <div className="ai-metric-value" style={{ fontSize: '15px' }}>
                          {personalAi.milestone_progression.highest_milestone?.qualification}
                        </div>
                        <span className="ai-metric-sub">
                          {personalAi.milestone_progression.highest_milestone?.score_display} ({personalAi.milestone_progression.highest_milestone?.normalized_percentage}%)
                        </span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Earliest Milestone</span>
                        <div className="ai-metric-value" style={{ fontSize: '15px' }}>
                          {personalAi.milestone_progression.lowest_milestone?.qualification}
                        </div>
                        <span className="ai-metric-sub">
                          {personalAi.milestone_progression.lowest_milestone?.score_display} ({personalAi.milestone_progression.lowest_milestone?.normalized_percentage}%)
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Chronological Narrative */}
                  {personalAi.milestone_progression?.narrative && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <Clock size={15} color="#69a9ff" /> Documented Milestone Progression
                      </div>
                      <ul className="ai-fact-list">
                        {personalAi.milestone_progression.narrative.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Transition Anomalies */}
                  {personalAi.detected_anomalies && personalAi.detected_anomalies.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <AlertTriangle size={15} color="#f0bc78" /> Transition Shifts & Adjustments ({personalAi.detected_anomalies.length})
                      </div>
                      {personalAi.detected_anomalies.map((anom, idx) => (
                        <div key={idx} className="ai-anomaly-card">
                          <div className="ai-anomaly-header">
                            <span className="ai-anomaly-title">
                              {anom.transition} · {anom.anomaly_type}
                            </span>
                            <span className="ai-anomaly-delta">{anom.percentage_delta}</span>
                          </div>
                          <p className="ai-anomaly-desc">{anom.context}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* User-Attested Citations */}
                  {personalAi.citations && personalAi.citations.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <ShieldCheck size={15} color="#64d7b2" /> Verified Citations (User Ground Truth)
                      </div>
                      {personalAi.citations.map((cite, idx) => (
                        <div key={idx} className="ai-citation-card">
                          <div className="ai-citation-claim">"{cite.claim}"</div>
                          <div className="ai-citation-meta">
                            <span>Source: <strong className="ai-citation-badge">{cite.source}</strong></span>
                            <span>Registration / Roll No: <code style={{ color: '#64d7b2' }}>{cite.roll_number_masked}</code></span>
                            <span>Type: {cite.attestation_type}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Verified Facts */}
                  {personalAi.verified_facts && personalAi.verified_facts.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <CheckCircle2 size={15} color="#64d7b2" /> Ground Truth Empirical Facts
                      </div>
                      <ul className="ai-fact-list">
                        {personalAi.verified_facts.map((fact, idx) => (
                          <li key={idx}>{fact}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Uncertainty & Limitations */}
                  {personalAi.uncertainty_and_limitations && personalAi.uncertainty_and_limitations.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <Info size={15} color="#f0bc78" /> Empirical Limitations & Data Boundaries
                      </div>
                      <ul className="ai-limitations-list">
                        {personalAi.uncertainty_and_limitations.map((lim, idx) => (
                          <li key={idx}>{lim}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Bounded Analytical Scenarios */}
                  {personalAi.analytical_scenarios && personalAi.analytical_scenarios.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <TrendingUp size={15} color="#a18aff" /> Bounded Analytical Trajectories (Conditional)
                      </div>
                      <div className="ai-scenarios-grid">
                        {personalAi.analytical_scenarios.map((scen, idx) => (
                          <div key={idx} className="ai-scenario-card">
                            <div className="ai-scenario-name">{scen.scenario_name}</div>
                            <div className="ai-scenario-val">{scen.estimated_score_range}</div>
                            <div className="ai-scenario-meta">{scen.trajectory_horizon}</div>
                            <div className="ai-scenario-meta" style={{ color: '#cbd5e1' }}>{scen.assumptions}</div>
                            <span className="ai-scenario-confidence">{scen.confidence}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Mandatory Statistical Disclaimer */}
              {personalAi.disclaimer && (
                <div className="ai-disclaimer-banner">
                  <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <strong>NO PREDICTION GUARANTEE:</strong> {personalAi.disclaimer}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="ai-modal-footer">
              <div>
                {personalAi.trust_ledger_id ? (
                  <span>
                    Audited in Trust Ledger: <strong style={{ color: '#a18aff' }}>#{personalAi.trust_ledger_id.slice(-6)}</strong>
                  </span>
                ) : (
                  <span>Academic Ground Truth Integrity Maintained</span>
                )}
              </div>
              <div>Privacy Protection: {maskSensitive ? 'Masked' : 'Unmasked'} · Never Fabricated</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
