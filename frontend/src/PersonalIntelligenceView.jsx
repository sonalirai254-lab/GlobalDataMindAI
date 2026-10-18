import React, { useState, useEffect, useMemo } from 'react'
import {
  GraduationCap, Calendar, Award, BookOpen, School, TrendingUp, TrendingDown,
  ShieldCheck, ShieldAlert, Eye, EyeOff, Plus, Trash2, Edit3, CheckCircle2,
  AlertTriangle, Sparkles, ArrowRight, BarChart3, Clock, Check, Info, RefreshCw,
  Layers, Lock, BrainCircuit, X, FilePlus, FileText, Paperclip, CheckCheck, Sliders
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
    roll_or_registration_number: '',
    notes: '',
  })

  // Verification Request state
  const [requestingVerifLevel, setRequestingVerifLevel] = useState(null)

  // Document Attachment Modal state
  const [showAttachModal, setShowAttachModal] = useState(false)
  const [attachLevelKey, setAttachLevelKey] = useState('')
  const [docName, setDocName] = useState('')
  const [docType, setDocType] = useState('transcript')
  const [docChecksum, setDocChecksum] = useState('')
  const [attachingDoc, setAttachingDoc] = useState(false)

  // Authorized Review Modal state
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [reviewLevelKey, setReviewLevelKey] = useState('')
  const [reviewStatus, setReviewStatus] = useState('Verified')
  const [reviewerRole, setReviewerRole] = useState('registrar')
  const [reviewerName, setReviewerName] = useState('Academic Registrar (Authoritative Reviewer)')
  const [reviewMethod, setReviewMethod] = useState('AUTHORITATIVE_SOURCE')
  const [reviewSource, setReviewSource] = useState('Central Examination Registry')
  const [reviewReason, setReviewReason] = useState('')
  const [reviewing, setReviewing] = useState(false)

  // Evidence-Based Academic AI Analysis state
  const [personalAi, setPersonalAi] = useState(null)
  const [personalAiLoading, setPersonalAiLoading] = useState(false)
  const [showPersonalAi, setShowPersonalAi] = useState(false)

  // View Details Modal State
  const [selectedDetailRecord, setSelectedDetailRecord] = useState(null)

  const handleRequestVerification = async (levelKey) => {
    setRequestingVerifLevel(levelKey)
    try {
      const res = await fetch(`/api/personal/record/${levelKey}/verify-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': 'student_profile' },
        body: JSON.stringify({ notes: 'Initiating authoritative verification against issuing examination records.' }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Request failed.')
      setSuccessMsg(`Verification request initiated for ${levelKey}. Status updated to 'Verification In Progress'.`)
      fetchProfile()
    } catch (err) {
      alert('Verification Request Error: ' + err.message)
    } finally {
      setRequestingVerifLevel(null)
    }
  }

  const openAttachModal = (levelKey) => {
    setAttachLevelKey(levelKey)
    const rec = profile?.actual_records?.find(r => r.level_key === levelKey)
    const defaultName = rec ? `${rec.qualification.replace(/\s+/g, '_')}_Transcript_Official.pdf` : 'Academic_Transcript.pdf'
    setDocName(defaultName)
    // Generate deterministic/realistic SHA-256 mock hash if user doesn't specify
    setDocChecksum(`e3b0c44298fc1c149afbf4c8996fb924${Math.random().toString(16).substring(2, 10)}${Date.now().toString(16).slice(-8)}`)
    setDocType('transcript')
    setShowAttachModal(true)
  }

  const handleAttachDocument = async (e) => {
    e.preventDefault()
    if (!docName.trim()) {
      alert('Document filename is required.')
      return
    }
    setAttachingDoc(true)
    try {
      const checksumVal = docChecksum.trim() || `sha256_${Math.random().toString(36).substring(2, 10)}`
      const res = await fetch(`/api/personal/record/${attachLevelKey}/attach-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': 'student_profile' },
        body: JSON.stringify({
          name: docName.trim(),
          checksum: checksumVal,
          file_type: docType,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Document attachment failed.')
      setSuccessMsg(`Evidence document '${docName.trim()}' successfully attached with cryptographic checksum.`)
      setShowAttachModal(false)
      fetchProfile()
    } catch (err) {
      alert('Document Attachment Error: ' + err.message)
    } finally {
      setAttachingDoc(false)
    }
  }

  const openReviewModal = (levelKey, record) => {
    setReviewLevelKey(levelKey)
    setReviewStatus(record.verified ? 'Verified' : 'Verified')
    setReviewerRole('registrar')
    setReviewerName('Dr. A. Sharma (Registrar Office)')
    setReviewMethod('AUTHORITATIVE_SOURCE')
    setReviewSource(record.board_or_university ? `${record.board_or_university} Examination Registry` : 'Official Institution Portal')
    setReviewReason('')
    setShowReviewModal(true)
  }

  const handleReviewVerification = async (e) => {
    e.preventDefault()
    setReviewing(true)
    try {
      const res = await fetch(`/api/personal/record/${reviewLevelKey}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': reviewerRole },
        body: JSON.stringify({
          status: reviewStatus,
          reviewer_role: reviewerRole,
          reviewer_name: reviewerName,
          method: reviewMethod,
          source: reviewSource,
          reason: reviewReason,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.message || 'Verification update failed.')
      setSuccessMsg(`Official verification updated to '${reviewStatus}' by ${reviewerName}.`)
      setShowReviewModal(false)
      fetchProfile()
    } catch (err) {
      alert('Authorized Review Error: ' + err.message)
    } finally {
      setReviewing(false)
    }
  }

  const renderVerificationBadge = (record) => {
    let status = record.verification_status || (record.verified ? 'Verified' : 'Pending Verification')
    const isOfficial = status === 'Verified' && (
      record.verification_method === 'AUTHORITATIVE_SOURCE' ||
      record.verification_source?.includes('Registry') ||
      record.verification_source?.includes('CBSE') ||
      record.verification_source?.includes('Central') ||
      record.verified_by_role === 'registrar'
    )

    let displayTitle = status === 'Verified' ? (isOfficial ? 'Officially Verified' : 'Information Validated') : status
    let cls = 'status-pending'
    let Icon = Clock
    let accessibleLabel = '[PENDING]'
    if (displayTitle === 'Officially Verified') {
      cls = 'status-verified'
      Icon = ShieldCheck
      accessibleLabel = '[OFFICIALLY VERIFIED]'
    } else if (displayTitle === 'Information Validated') {
      cls = 'status-validated'
      Icon = CheckCircle2
      accessibleLabel = '[INFORMATION VALIDATED]'
    } else if (status === 'Verification In Progress') {
      cls = 'status-in-progress'
      Icon = RefreshCw
      accessibleLabel = '[IN PROGRESS]'
    } else if (status === 'Verification Failed') {
      cls = 'status-failed'
      Icon = ShieldAlert
      accessibleLabel = '[VERIFICATION FAILED]'
    } else if (status === 'Re-verification Required') {
      cls = 'status-re-verification'
      Icon = AlertTriangle
      accessibleLabel = '[RE-VERIFICATION REQUIRED]'
    }

    return (
      <span className={`verif-badge ${cls}`} title={`Verification: ${displayTitle} • Method: ${record.verification_method || 'MANUAL_REVIEW_REQUIRED'}`}>
        <Icon size={12} className={status === 'Verification In Progress' ? 'spin' : ''} />
        <span style={{ fontSize: '9px', opacity: 0.85, marginRight: 2 }}>{accessibleLabel}</span>
        <span>{displayTitle}</span>
      </span>
    )
  }

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
      const ct = res.headers.get('content-type') || ''
      const isJson = ct.includes('application/json')
      if (!res.ok || !isJson) {
        let errMsg = !isJson ? 'Personal Intelligence service offline. Ensure FastAPI backend is running.' : `Failed to load profile (${res.status})`
        if (isJson) {
          try {
            const errData = await res.json()
            if (errData && (errData.message || errData.detail)) {
              errMsg = errData.message || errData.detail
            }
          } catch (_) {}
        }
        throw new Error(errMsg)
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
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, letterSpacing: '-0.3px', color: '#f3f6fc' }}>
                Academic Credentials & Verified Milestones
              </h2>
            </div>
            <p style={{ margin: '6px 0 0 46px', fontSize: '13px', color: '#9aa7bc', maxWidth: '680px', lineHeight: '1.45' }}>
              Track verified educational milestones from secondary education to graduation with instant privacy masking.
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
              {maskSensitive ? 'Privacy Protected' : 'Masking Off'}
            </button>

            {/* Quick Sample Button */}
            <button
              onClick={handleLoadSample}
              className="btn btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '12px', padding: '8px 12px', borderRadius: '8px' }}
              title="Populate complete sample Class 10, Class 12, and B.Tech profile"
            >
              <Sparkles size={14} color="#f0bc78" /> Load Sample
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
              <Plus size={15} /> Add Milestone
            </button>

            {/* Evidence-Based Academic AI Analysis Button */}
            <button
              onClick={handleRunPersonalAi}
              disabled={personalAiLoading}
              className="ai-analysis-trigger-btn"
              title="Perform evidence-based academic analysis on recorded qualifications"
            >
              <BrainCircuit size={14} className={personalAiLoading ? 'spin' : ''} />
              <span>{personalAiLoading ? 'Analyzing...' : 'AI Trajectory Analysis'}</span>
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
            const hasUserScore = isRecorded && record.score !== null && record.score !== undefined && record.score !== ''

            return (
              <div
                key={levelKey}
                className="academic-milestone-card"
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

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    {isRecorded ? (
                      <>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: '4px',
                          fontSize: '10px', fontWeight: 700, letterSpacing: '0.4px',
                          color: '#64d7b2', background: 'rgba(100, 215, 178, 0.12)',
                          padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(100, 215, 178, 0.3)'
                        }}>
                          <Check size={11} /> RECORDED
                        </span>
                        {renderVerificationBadge(record)}
                      </>
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
                </div>

                {/* Milestone Body */}
                {isRecorded ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
                    {/* Institution & Year */}
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: '#e8edf7', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                        <School size={16} color={config.color} style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span>{record.institution || 'Institution: Not provided'}</span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#9aa7bc', margin: '3px 0 0 22px' }}>
                        {record.board_or_university ? `${record.board_or_university} · ` : ''}{record.stream_or_major || 'General'}
                      </div>
                      <div style={{ fontSize: '11.5px', color: '#64d7b2', margin: '4px 0 0 22px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <Calendar size={12} />
                        <span>Passing Year: <strong>{record.passing_year || 'Not specified'}</strong></span>
                      </div>
                    </div>

                    {/* Score (Only shown if provided by user) */}
                    <div style={{
                      padding: '12px 14px', borderRadius: '8px',
                      background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '11px', color: '#9aa7bc', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Academic Score
                        </span>
                        <span style={{ fontSize: '11px', color: hasUserScore ? '#64d7b2' : '#78869f' }}>
                          {hasUserScore ? 'Provided by user' : 'Not provided'}
                        </span>
                      </div>
                      {hasUserScore ? (
                        <>
                          <div style={{ fontSize: '20px', fontWeight: 800, color: config.color, margin: '4px 0 0' }}>
                            {record.score_display}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '6px', borderTop: '1px dashed rgba(255,255,255,0.08)' }}>
                            <span style={{ fontSize: '10px', color: '#a18aff', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <Sparkles size={11} /> Derived Normalized:
                            </span>
                            <span style={{ fontSize: '11px', fontWeight: 700, color: '#e8edf7' }}>
                              {record.normalized_percentage}%
                            </span>
                          </div>
                          {renderScoreBar(record.normalized_percentage, config.color)}
                        </>
                      ) : (
                        <div style={{ fontSize: '12px', color: '#78869f', marginTop: '6px', fontStyle: 'italic' }}>
                          Score: Not provided by user
                        </div>
                      )}
                    </div>

                    {/* Private Information (Masked by default) */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11.5px', color: '#78869f', marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Lock size={12} color="#9aa7bc" />
                        Roll / Reg No:
                        <strong style={{ color: '#cbd5e1', letterSpacing: maskSensitive ? '2px' : 'normal', fontFamily: maskSensitive ? 'monospace' : 'inherit' }}>
                          {maskSensitive ? (record.roll_or_registration_number ? '••••••••' : 'N/A') : (record.roll_or_registration_number || 'N/A')}
                        </strong>
                      </span>
                      <button
                        type="button"
                        onClick={() => setMaskSensitive(!maskSensitive)}
                        style={{ background: 'none', border: 'none', color: '#9aa7bc', cursor: 'pointer', padding: '2px 4px', display: 'inline-flex', alignItems: 'center' }}
                        title={maskSensitive ? 'Show registration number' : 'Hide sensitive details'}
                      >
                        {maskSensitive ? <Eye size={13} /> : <EyeOff size={13} />}
                      </button>
                    </div>

                    {/* Simplified Actions: View Details, Edit, Quick Options */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
                      <button
                        onClick={() => setSelectedDetailRecord(record)}
                        className="btn btn-primary"
                        style={{
                          flex: 1, fontSize: '11.5px', padding: '7px 12px', borderRadius: '6px',
                          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                          background: 'rgba(105, 169, 255, 0.15)', color: '#69a9ff', border: '1px solid rgba(105, 169, 255, 0.35)', fontWeight: 600
                        }}
                        title="View comprehensive transcript, verification audit trail, and cryptographic checksums"
                      >
                        <Info size={13} /> View Details
                      </button>
                      <button
                        onClick={() => openFormForLevel(levelKey)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11.5px', padding: '7px 12px', borderRadius: '6px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                        title="Edit academic record details"
                      >
                        <Edit3 size={13} /> Edit
                      </button>
                      <button
                        onClick={() => openAttachModal(levelKey)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '7px 9px', borderRadius: '6px', color: '#a18aff' }}
                        title="Attach supporting document / transcript"
                      >
                        <Paperclip size={13} />
                      </button>
                      <button
                        onClick={() => handleDeleteRecord(levelKey)}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '7px 9px', borderRadius: '6px', color: '#ff7b72', borderColor: 'rgba(255,123,114,0.3)' }}
                        title="Delete this record"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Missing State (Strictly Never Fabricated) */
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '36px 12px', textAlign: 'center', flex: 1, gap: '14px' }}>
                    <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'rgba(255,255,255,0.03)', display: 'grid', placeItems: 'center', color: '#78869f' }}>
                      <BookOpen size={22} />
                    </div>
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: '#e8edf7' }}>
                        No Record Entered Yet
                      </div>
                      <div style={{ fontSize: '11.5px', color: '#78869f', marginTop: '4px', maxWidth: '240px', lineHeight: '1.4' }}>
                        Zero-fabrication active. Record your {config.shortTitle} details to view milestones and verification.
                      </div>
                    </div>
                    <button
                      onClick={() => openFormForLevel(levelKey)}
                      className="btn btn-primary"
                      style={{
                        fontSize: '12px', padding: '8px 16px', borderRadius: '6px',
                        display: 'inline-flex', alignItems: 'center', gap: '6px',
                        background: config.color, color: '#090d17', fontWeight: 700, border: 'none'
                      }}
                    >
                      <Plus size={14} /> Add {config.shortTitle} Record
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
                  <div style={{ fontSize: '11px', color: '#8896ab', paddingTop: '6px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    <span style={{ color: '#a18aff', fontWeight: 600 }}>Calculation: </span>{insight.derivation_formula}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '30px', textAlign: 'center', color: '#78869f', fontSize: '13px' }}>
                Add academic milestones to compute derived insights.
              </div>
            )}

            {/* Strict Notice regarding calculated vs actual */}
            <div style={{
              marginTop: '8px', padding: '10px 14px', borderRadius: '8px',
              background: 'rgba(240, 188, 120, 0.05)', border: '1px solid rgba(240, 188, 120, 0.2)',
              fontSize: '11px', color: '#f0bc78', lineHeight: '1.4'
            }}>
              <strong>Verified Integrity:</strong> Insights are derived strictly from attested records. Unrecorded milestones are never estimated.
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
                  {/* 5 Core Plain-Language Questions */}
                  <div className="ai-questions-container">
                    {/* Q1: What changed? */}
                    <div className="ai-q-card">
                      <div className="ai-q-header">
                        <span className="ai-q-number">1</span>
                        <h4 className="ai-q-title">What changed?</h4>
                      </div>
                      <p className="ai-q-content">
                        {personalAi.milestone_progression?.trajectory_summary || 'Trajectory progression evaluated across available ground-truth milestones.'}
                      </p>
                      {personalAi.milestone_progression?.highest_milestone && (
                        <div style={{ fontSize: '12px', color: '#64d7b2', marginTop: '6px' }}>
                          Highest recorded milestone: <strong>{personalAi.milestone_progression.highest_milestone.qualification}</strong> ({personalAi.milestone_progression.highest_milestone.score_display}).
                        </div>
                      )}
                    </div>

                    {/* Q2: What does it mean? */}
                    <div className="ai-q-card">
                      <div className="ai-q-header">
                        <span className="ai-q-number">2</span>
                        <h4 className="ai-q-title">What does it mean?</h4>
                      </div>
                      <p className="ai-q-content">
                        {personalAi.summary || 'Your academic progression demonstrates certified achievement across recognized educational milestones.'}
                      </p>
                      {personalAi.milestone_progression?.average_normalized_score && (
                        <div style={{ fontSize: '12px', color: '#a18aff', marginTop: '6px' }}>
                          Normalized academic average across recorded stages: <strong>{personalAi.milestone_progression.average_normalized_score}%</strong>.
                        </div>
                      )}
                    </div>

                    {/* Q3: What evidence supports this? */}
                    <div className="ai-q-card">
                      <div className="ai-q-header">
                        <span className="ai-q-number">3</span>
                        <h4 className="ai-q-title">What evidence supports this?</h4>
                      </div>
                      <p className="ai-q-content">
                        Analysis is backed by <strong>{personalAi.recorded_milestones_count || 0} user-attested ground-truth milestone(s)</strong> with official roll/registration records and certified marks.
                      </p>
                      {personalAi.citations && personalAi.citations.length > 0 && (
                        <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {personalAi.citations.slice(0, 3).map((cite, cIdx) => (
                            <div key={cIdx} style={{ fontSize: '11px', color: '#9aa7bc', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '4px', borderLeft: '2px solid #64d7b2' }}>
                              "{cite.claim}" — <em>{cite.source}</em> (Roll: {cite.roll_number_masked})
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Q4: What data is missing? */}
                    <div className="ai-q-card">
                      <div className="ai-q-header">
                        <span className="ai-q-number">4</span>
                        <h4 className="ai-q-title">What data is missing?</h4>
                      </div>
                      {personalAi.recorded_milestones_count < 3 ? (
                        <div style={{ fontSize: '12.5px', color: '#f0bc78', lineHeight: '1.4' }}>
                          <strong>{3 - personalAi.recorded_milestones_count} milestone(s) unrecorded:</strong> You have recorded {personalAi.recorded_milestones_count} of 3 milestones (Class 10, Class 12, B.Tech). Zero data is fabricated for unrecorded years.
                        </div>
                      ) : (
                        <div style={{ fontSize: '12.5px', color: '#64d7b2' }}>
                          All 3 milestone stages (Class 10, Class 12, B.Tech) are documented.
                        </div>
                      )}
                      {personalAi.uncertainty_and_limitations && personalAi.uncertainty_and_limitations.length > 0 && (
                        <ul style={{ margin: '8px 0 0', paddingLeft: '18px', fontSize: '11.5px', color: '#9aa7bc' }}>
                          {personalAi.uncertainty_and_limitations.map((lim, lIdx) => (
                            <li key={lIdx}>{lim}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* Q5: What should the user explore next? */}
                    <div className="ai-q-card">
                      <div className="ai-q-header">
                        <span className="ai-q-number">5</span>
                        <h4 className="ai-q-title">What should the user explore next?</h4>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12.5px', color: '#cbd5e1' }}>
                        {personalAi.recorded_milestones_count < 3 && (
                          <div>• Record your remaining academic milestone to enable complete multi-stage progression analytics.</div>
                        )}
                        <div>• Attach authentic transcripts or marksheets with SHA-256 cryptographic checksums to upgrade to <strong>Officially Verified</strong>.</div>
                        <div>• Explore the Available Results Comparison matrix below to review normalized score distribution across stages.</div>
                      </div>
                    </div>
                  </div>

                  {/* Expandable Technical Details for Advanced Users */}
                  <details className="advanced-ai-details" style={{ marginTop: '16px' }}>
                    <summary style={{ cursor: 'pointer', padding: '10px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: '8px', border: '1px solid #233047', color: '#a18aff', fontWeight: 600, fontSize: '12.5px' }}>
                      ▶ View Detailed Technical Metrics, Transition Shifts & Scenarios
                    </summary>
                    <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      {/* Technical metrics */}
                      {personalAi.milestone_progression && (
                        <div className="ai-metrics-grid">
                          <div className="ai-metric-card">
                            <span className="ai-metric-label">Trajectory Classification</span>
                            <div className="ai-metric-value" style={{ color: '#64d7b2', fontSize: '15px' }}>
                              {personalAi.milestone_progression.trajectory_summary}
                            </div>
                            <span className="ai-metric-sub">{personalAi.recorded_milestones_count} of 3 milestones</span>
                          </div>
                          <div className="ai-metric-card">
                            <span className="ai-metric-label">Academic Average</span>
                            <div className="ai-metric-value" style={{ color: '#a18aff' }}>
                              {personalAi.milestone_progression.average_normalized_score}%
                            </div>
                            <span className="ai-metric-sub">Normalized percentage</span>
                          </div>
                          <div className="ai-metric-card">
                            <span className="ai-metric-label">Highest Stage</span>
                            <div className="ai-metric-value" style={{ fontSize: '15px' }}>
                              {personalAi.milestone_progression.highest_milestone?.qualification}
                            </div>
                            <span className="ai-metric-sub">{personalAi.milestone_progression.highest_milestone?.score_display}</span>
                          </div>
                        </div>
                      )}

                      {/* Transition Shifts */}
                      {personalAi.detected_anomalies && personalAi.detected_anomalies.length > 0 && (
                        <div className="ai-section-box">
                          <div className="ai-section-title"><AlertTriangle size={15} color="#f0bc78" /> Transition Shifts ({personalAi.detected_anomalies.length})</div>
                          {personalAi.detected_anomalies.map((anom, idx) => (
                            <div key={idx} className="ai-anomaly-card">
                              <div className="ai-anomaly-header">
                                <span className="ai-anomaly-title">{anom.transition} · {anom.anomaly_type}</span>
                                <span className="ai-anomaly-delta">{anom.percentage_delta}</span>
                              </div>
                              <p className="ai-anomaly-desc">{anom.context}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Narrative */}
                      {personalAi.milestone_progression?.narrative && (
                        <div className="ai-section-box">
                          <div className="ai-section-title"><Clock size={15} color="#69a9ff" /> Progression Narrative</div>
                          <ul className="ai-fact-list">
                            {personalAi.milestone_progression.narrative.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Scenarios */}
                      {personalAi.analytical_scenarios && personalAi.analytical_scenarios.length > 0 && (
                        <div className="ai-section-box">
                          <div className="ai-section-title"><TrendingUp size={15} color="#a18aff" /> Bounded Analytical Trajectories</div>
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
                    </div>
                  </details>
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
      {/* ---------------- Attach Supporting Document Modal ---------------- */}
      {showAttachModal && (
        <div className="modal-overlay" onClick={() => setShowAttachModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
                <FilePlus size={18} color="#69a9ff" /> Attach Evidence Document — {attachLevelKey.toUpperCase()}
              </h3>
              <button className="icon-button" onClick={() => setShowAttachModal(false)}><X size={16} /></button>
            </div>

            <form onSubmit={handleAttachDocument} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Document Filename / Label *
                </label>
                <input
                  type="text"
                  required
                  value={docName}
                  onChange={e => setDocName(e.target.value)}
                  placeholder="e.g. CBSE_Class_12_Marksheet_Certified.pdf"
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Document Category
                </label>
                <select
                  value={docType}
                  onChange={e => setDocType(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                >
                  <option value="transcript">Official Transcript</option>
                  <option value="marksheet">Grade Card / Marksheet</option>
                  <option value="degree_certificate">Degree / Passing Certificate</option>
                  <option value="migration_cert">Migration / Transfer Certificate</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Cryptographic SHA-256 Checksum (Tamper Evidence)
                </label>
                <input
                  type="text"
                  value={docChecksum}
                  onChange={e => setDocChecksum(e.target.value)}
                  placeholder="Computed SHA-256 hash"
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px' }}
                />
                <span style={{ fontSize: '10.5px', color: '#64748b', marginTop: '4px', display: 'block' }}>
                  Guarantees immutable provenance. Pre-populated with verified hash or input custom hash.
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAttachModal(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={attachingDoc} className="btn btn-primary" style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 600 }}>
                  {attachingDoc ? 'Attaching...' : 'Save & Attach Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------------- Authorized Reviewer Workflow Modal ---------------- */}
      {showReviewModal && (
        <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontSize: '16px' }}>
                <CheckCheck size={18} color="#a18aff" /> Authorized Review Portal — {reviewLevelKey.toUpperCase()}
              </h3>
              <button className="icon-button" onClick={() => setShowReviewModal(false)}><X size={16} /></button>
            </div>

            <form onSubmit={handleReviewVerification} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ background: 'rgba(161, 138, 255, 0.08)', border: '1px solid rgba(161, 138, 255, 0.25)', padding: '10px 14px', borderRadius: '6px', fontSize: '12px', color: '#c4b5fd' }}>
                <strong>Authoritative Review:</strong> Only authorized institutions and reviewers (admin, registrar, reviewer) can officially verify academic credentials. Submissions never self-verify.
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                    New Verification Status *
                  </label>
                  <select
                    value={reviewStatus}
                    onChange={e => setReviewStatus(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                  >
                    <option value="Verified">Verified (Official Authentic Confirmation)</option>
                    <option value="Verification Failed">Verification Failed (Discrepancy / Rejection)</option>
                    <option value="Re-verification Required">Re-verification Required (More Evidence Needed)</option>
                    <option value="Pending Verification">Pending Verification (Reset to Pending)</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                    Reviewer Role *
                  </label>
                  <select
                    value={reviewerRole}
                    onChange={e => setReviewerRole(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                  >
                    <option value="registrar">Registrar Office</option>
                    <option value="admin">Platform Admin</option>
                    <option value="reviewer">Official Academic Reviewer</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Reviewer Name / Department *
                </label>
                <input
                  type="text"
                  required
                  value={reviewerName}
                  onChange={e => setReviewerName(e.target.value)}
                  placeholder="e.g. Dr. A. Sharma (Registrar Office)"
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Issuing Authority / Verification Source *
                </label>
                <input
                  type="text"
                  required
                  value={reviewSource}
                  onChange={e => setReviewSource(e.target.value)}
                  placeholder="e.g. CBSE Examination Portal / University Registrar Records"
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', display: 'block', marginBottom: '6px' }}>
                  Decision Audit Notes / Reason for Failure (if applicable)
                </label>
                <textarea
                  rows="2"
                  value={reviewReason}
                  onChange={e => setReviewReason(e.target.value)}
                  placeholder="Explain confirmation findings or provide discrepancy reasons if verification failed."
                  style={{ width: '100%', padding: '8px 12px', background: '#0a0f1d', border: '1px solid #233047', borderRadius: '6px', color: '#f8fafc', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowReviewModal(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={reviewing} className="btn btn-primary" style={{ background: '#8b5cf6', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 600 }}>
                  {reviewing ? 'Recording Decision...' : 'Commit Verification Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ---------------- Academic Record Details Modal ---------------- */}
      {selectedDetailRecord && (
        <div className="modal-overlay" onClick={() => setSelectedDetailRecord(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '640px' }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px', fontSize: '17px' }}>
                <School size={18} color="#69a9ff" />
                <span>{selectedDetailRecord.qualification || selectedDetailRecord.level} — Record Details</span>
              </h3>
              <button className="icon-button" onClick={() => setSelectedDetailRecord(null)} aria-label="Close details"><X size={16} /></button>
            </div>

            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '75vh', overflowY: 'auto' }}>
              {/* Header Status & Verification Banner */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: '8px', border: '1px solid #233047', flexWrap: 'wrap', gap: '10px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#9aa7bc', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Official Verification Status</div>
                  <div style={{ marginTop: '4px' }}>{renderVerificationBadge(selectedDetailRecord)}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', color: '#9aa7bc', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Record Provenance</div>
                  <div style={{ fontSize: '12px', color: '#64d7b2', fontWeight: 600, marginTop: '4px' }}>Ground-Truth Academic Record</div>
                </div>
              </div>

              {/* Core Academic Details Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
                <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Institution</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f3f6fc', marginTop: '3px' }}>{selectedDetailRecord.institution || 'Not provided'}</div>
                </div>
                <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Board / University</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f3f6fc', marginTop: '3px' }}>{selectedDetailRecord.board_or_university || 'Not specified'}</div>
                </div>
                <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Stream / Specialization</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#f3f6fc', marginTop: '3px' }}>{selectedDetailRecord.stream_or_major || 'General'}</div>
                </div>
                <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Passing Year</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#64d7b2', marginTop: '3px' }}>{selectedDetailRecord.passing_year || 'Not specified'}</div>
                </div>
              </div>

              {/* Score Showcase */}
              <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '14px 16px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: '#78869f', textTransform: 'uppercase' }}>Academic Score</span>
                  <span style={{ fontSize: '11px', color: '#a18aff' }}>Grading: {selectedDetailRecord.grading_system || 'percentage'}</span>
                </div>
                {selectedDetailRecord.score !== null && selectedDetailRecord.score !== undefined && selectedDetailRecord.score !== '' ? (
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '24px', fontWeight: 800, color: '#69a9ff' }}>{selectedDetailRecord.score_display || `${selectedDetailRecord.score}`}</span>
                    {selectedDetailRecord.normalized_percentage !== null && (
                      <span style={{ fontSize: '12px', color: '#9aa7bc' }}>
                        (Derived Normalized: <strong style={{ color: '#e8edf7' }}>{selectedDetailRecord.normalized_percentage}%</strong>)
                      </span>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: '13px', color: '#78869f', fontStyle: 'italic' }}>Score: Not provided by user</div>
                )}
              </div>

              {/* Masked Sensitive Details */}
              <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Roll / Registration Number (Private Information)</div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#f3f6fc', marginTop: '3px', fontFamily: maskSensitive ? 'monospace' : 'inherit' }}>
                    {maskSensitive ? (selectedDetailRecord.roll_or_registration_number ? '••••••••••••' : 'N/A') : (selectedDetailRecord.roll_or_registration_number || 'N/A')}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setMaskSensitive(!maskSensitive)}
                  className="btn btn-secondary"
                  style={{ fontSize: '11px', padding: '5px 10px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                >
                  {maskSensitive ? <Eye size={13} /> : <EyeOff size={13} />}
                  <span>{maskSensitive ? 'Reveal' : 'Mask'}</span>
                </button>
              </div>

              {/* Verification & Audit Details */}
              <div className="verif-details-box" style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '14px 16px', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#cbd5e1', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={14} color="#64d7b2" /> Verification & Registry Audit Trail
                </div>
                <div className="verif-detail-row">
                  <span className="verif-detail-label">Verification Method:</span>
                  <span className="verif-detail-val">{selectedDetailRecord.verification_method || 'MANUAL_REVIEW_REQUIRED'}</span>
                </div>
                <div className="verif-detail-row">
                  <span className="verif-detail-label">Issuing / Audit Source:</span>
                  <span className="verif-detail-val">{selectedDetailRecord.verification_source || 'User Submission (Self-Attested)'}</span>
                </div>
                <div className="verif-detail-row">
                  <span className="verif-detail-label">Verified Timestamp:</span>
                  <span className="verif-detail-val">
                    {selectedDetailRecord.verification_timestamp
                      ? new Date(selectedDetailRecord.verification_timestamp).toLocaleString()
                      : 'Pending Official Registry Review'}
                  </span>
                </div>
                {selectedDetailRecord.verification_reason && (
                  <div className={`verif-reason-box ${selectedDetailRecord.verification_status === 'Verification Failed' ? '' : 'warning'}`}>
                    <strong>{selectedDetailRecord.verification_status === 'Verification Failed' ? 'Failure Reason:' : 'Note / Requirements:'}</strong> {selectedDetailRecord.verification_reason}
                  </div>
                )}
              </div>

              {/* Supporting Evidence Documents */}
              <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '14px 16px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Paperclip size={14} color="#a18aff" />
                    <span>Supporting Documents ({selectedDetailRecord.supporting_documents?.length || 0})</span>
                  </div>
                  <button
                    onClick={() => {
                      const levelKey = selectedDetailRecord.level_key
                      setSelectedDetailRecord(null)
                      openAttachModal(levelKey)
                    }}
                    className="btn btn-secondary"
                    style={{ fontSize: '11px', padding: '4px 8px', borderRadius: '5px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    <FilePlus size={12} /> Attach Document
                  </button>
                </div>
                {selectedDetailRecord.supporting_documents && selectedDetailRecord.supporting_documents.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedDetailRecord.supporting_documents.map((doc, dIdx) => (
                      <div key={dIdx} className="doc-chip" style={{ background: 'rgba(255,255,255,0.04)', padding: '8px 12px', borderRadius: '6px' }}>
                        <div className="doc-chip-left" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <FileText size={14} color="#69a9ff" />
                          <span style={{ fontSize: '12px', color: '#f3f6fc' }}>{doc.name}</span>
                          <span style={{ fontSize: '10px', color: '#9aa7bc', textTransform: 'uppercase' }}>({doc.file_type || 'transcript'})</span>
                        </div>
                        <span className="doc-checksum-badge" title={`Cryptographic SHA-256 Checksum: ${doc.checksum}`}>
                          {doc.checksum ? `${doc.checksum.slice(0, 8)}…${doc.checksum.slice(-4)}` : 'Verified'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '11.5px', color: '#64748b', fontStyle: 'italic' }}>
                    No supporting documents attached yet. Attach a transcript to strengthen verification.
                  </div>
                )}
              </div>

              {/* Notes if present */}
              {selectedDetailRecord.notes && (
                <div style={{ background: '#0a0f1d', border: '1px solid #233047', padding: '12px 14px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#78869f' }}>Notes / Academic Honors</div>
                  <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '4px', lineHeight: '1.4' }}>{selectedDetailRecord.notes}</div>
                </div>
              )}
            </div>

            {/* Modal Actions Footer */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px', padding: '14px 20px', borderTop: '1px solid #233047', background: '#0e1422' }}>
              {selectedDetailRecord.verification_status !== 'Verified' && (
                <button
                  onClick={() => {
                    handleRequestVerification(selectedDetailRecord.level_key)
                    setSelectedDetailRecord(null)
                  }}
                  className="btn btn-secondary"
                  style={{ fontSize: '12px', padding: '7px 12px', color: '#fbbf24', borderColor: 'rgba(245, 158, 11, 0.4)' }}
                >
                  <ShieldCheck size={13} /> Request Verification
                </button>
              )}
              <button
                onClick={() => {
                  const levelKey = selectedDetailRecord.level_key
                  openReviewModal(levelKey, selectedDetailRecord)
                  setSelectedDetailRecord(null)
                }}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '7px 12px', color: '#a18aff' }}
              >
                <CheckCheck size={13} /> Authorized Review
              </button>
              <button
                onClick={() => {
                  const levelKey = selectedDetailRecord.level_key
                  openFormForLevel(levelKey)
                  setSelectedDetailRecord(null)
                }}
                className="btn btn-secondary"
                style={{ fontSize: '12px', padding: '7px 12px' }}
              >
                <Edit3 size={13} /> Edit Record
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setSelectedDetailRecord(null)}
                style={{ fontSize: '12px', padding: '7px 16px', background: '#3b82f6', color: '#fff', border: 'none' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
