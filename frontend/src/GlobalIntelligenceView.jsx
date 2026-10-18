import React, { useState, useEffect, useMemo, useRef } from 'react'
import {
  Globe, TrendingUp, BarChart3, Calendar, ArrowRight, RefreshCw, AlertCircle,
  CheckCircle2, Download, Layers, ShieldCheck, Database, Info, Sparkles, Filter,
  TrendingDown, Minus, ExternalLink, Search, X, Check, Network, BrainCircuit, AlertTriangle
} from 'lucide-react'

// Curated harmonious color palette for multi-country charts
const COUNTRY_COLORS = [
  '#69a9ff', // Blue
  '#64d7b2', // Mint
  '#f0bc78', // Amber
  '#a18aff', // Purple
  '#f472b6', // Pink
  '#38bdf8', // Sky
  '#fb923c', // Orange
  '#a3e635', // Lime
]

// Available indicator categories for filter pills
const INDICATOR_CATEGORIES = [
  'All',
  'Economy',
  'Demographics',
  'Healthcare',
  'Education',
  'Employment',
  'Climate & Environment',
  'Trade & Finance',
  'Technology',
  'Society & Development',
]

// Popular preset countries for quick selection
const POPULAR_COUNTRIES = ['IND', 'USA', 'CHN', 'DEU', 'GBR', 'JPN', 'FRA', 'BRA', 'ZAF', 'AUS']

// Helper function to format large numbers cleanly and accurately
function formatNumber(val, unit = '') {
  if (val === null || val === undefined) return 'N/A'
  if (val === 0) return '0.0'

  const absVal = Math.abs(val)
  let formatted = ''

  if (unit === '%' || unit.includes('%')) {
    formatted = val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + '%'
    return formatted
  }

  if (absVal >= 1e12) {
    formatted = (val / 1e12).toFixed(2) + ' Trillion'
  } else if (absVal >= 1e9) {
    formatted = (val / 1e9).toFixed(2) + ' Billion'
  } else if (absVal >= 1e6) {
    formatted = (val / 1e6).toFixed(2) + ' Million'
  } else if (absVal >= 1e3) {
    formatted = val.toLocaleString(undefined, { maximumFractionDigits: 2 })
  } else {
    formatted = val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 3 })
  }

  if (unit && !unit.includes('%')) {
    if (unit.includes('USD') || unit.includes('$')) {
      formatted = '$' + formatted
    } else {
      formatted = formatted + ' ' + unit
    }
  }

  return formatted
}

export default function GlobalIntelligenceView({ onSelectCountryNode }) {
  // Navigation Mode
  const [mode, setMode] = useState('single') // 'single' | 'compare'

  // Catalogs loaded from backend
  const [indicators, setIndicators] = useState([])
  const [countries, setCountries] = useState([])
  const [catalogsLoading, setCatalogsLoading] = useState(true)

  // Search & Filter controls
  const [countrySearch, setCountrySearch] = useState('')
  const [indicatorSearch, setIndicatorSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')

  // Single Country Selection
  const [selectedCountry, setSelectedCountry] = useState('IND')
  const [selectedIndicator, setSelectedIndicator] = useState('NY.GDP.MKTP.CD')
  const [startYear, setStartYear] = useState(2000)
  const [endYear, setEndYear] = useState(2024)

  // Multi-Country Comparison Selection (up to 8)
  const [compareCountries, setCompareCountries] = useState(['IND', 'USA', 'CHN', 'DEU'])

  // Data state
  const [singleData, setSingleData] = useState(null)
  const [compareData, setCompareData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Table & Interactive filter state
  const [tableFilter, setTableFilter] = useState('all') // 'all' | 'valid' | 'missing'
  const [activeTooltip, setActiveTooltip] = useState(null)

  // Evidence-Based AI Analysis state
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState(null)
  const [showAiModal, setShowAiModal] = useState(false)

  const handleRunAiAnalysis = async () => {
    setAiLoading(true)
    setAiError(null)
    try {
      let res
      if (mode === 'single') {
        res = await fetch('/api/ai/analyze/global', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            country: selectedCountry,
            indicator: selectedIndicator,
            start_year: startYear,
            end_year: endYear,
          }),
        })
      } else {
        res = await fetch('/api/ai/analyze/global/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            country_codes: compareCountries,
            indicator: selectedIndicator,
            start_year: startYear,
            end_year: endYear,
          }),
        })
      }
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Evidence-based analysis could not be completed.')
      }
      setAiAnalysis(data)
      setShowAiModal(true)
    } catch (err) {
      setAiError(err.message)
      alert('AI Analysis error: ' + err.message)
    } finally {
      setAiLoading(false)
    }
  }

  // Load verified catalogs on initial component mount
  useEffect(() => {
    let isMounted = true
    async function loadCatalogs() {
      try {
        const [indRes, cRes] = await Promise.all([
          fetch('/api/global/indicators'),
          fetch('/api/global/countries'),
        ])
        if (!indRes.ok || !cRes.ok) {
          throw new Error('Failed to load global intelligence catalogs from backend.')
        }
        const indData = await indRes.json()
        const cData = await cRes.json()
        if (isMounted) {
          setIndicators(indData)
          setCountries(cData)
          setCatalogsLoading(false)
        }
      } catch (err) {
        if (isMounted) {
          setError('Could not connect to Global Intelligence service: ' + err.message)
          setCatalogsLoading(false)
        }
      }
    }
    loadCatalogs()
    return () => { isMounted = false }
  }, [])

  // Fetch single country data from real backend endpoint
  const fetchSingleData = async (forceRefresh = false) => {
    if (!selectedCountry || !selectedIndicator) return
    setLoading(true)
    setError(null)
    setActiveTooltip(null)
    try {
      const url = `/api/global/observations?country=${encodeURIComponent(selectedCountry)}&indicator=${encodeURIComponent(selectedIndicator)}&start_year=${startYear}&end_year=${endYear}${forceRefresh ? '&refresh=true' : ''}`
      const res = await fetch(url)
      const data = await res.json()
      if (!res.ok) {
        if (res.status === 504) {
          throw new Error('World Bank API request timed out. Please try refreshing or using a narrower year range.')
        }
        if (res.status === 502) {
          throw new Error('World Bank API communication error. Check your internet connection or try again.')
        }
        if (res.status === 503) {
          throw new Error(data.message || data.detail || 'GlobalDataMind AI backend is offline. Ensure uvicorn is running on port 8000.')
        }
        throw new Error(data.detail || data.message || 'Failed to fetch observations.')
      }
      setSingleData(data)
    } catch (err) {
      setError(err.message)
      setSingleData(null)
    } finally {
      setLoading(false)
    }
  }

  // Fetch comparison data from real backend comparison endpoint
  const fetchCompareData = async () => {
    if (!compareCountries.length || !selectedIndicator) return
    setLoading(true)
    setError(null)
    setActiveTooltip(null)
    try {
      const res = await fetch('/api/global/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_codes: compareCountries,
          indicator: selectedIndicator,
          start_year: startYear,
          end_year: endYear,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        if (res.status === 504) {
          throw new Error('World Bank comparison query timed out. Please try with fewer countries or a narrower year range.')
        }
        if (res.status === 502) {
          throw new Error('World Bank comparison service unavailable. Check network connectivity.')
        }
        if (res.status === 503) {
          throw new Error(data.message || data.detail || 'GlobalDataMind AI backend is offline. Ensure uvicorn is running on port 8000.')
        }
        throw new Error(data.detail || data.message || 'Comparison query failed.')
      }
      setCompareData(data)
    } catch (err) {
      setError(err.message)
      setCompareData(null)
    } finally {
      setLoading(false)
    }
  }

  // Auto-fetch observations once catalogs are ready or when primary selections change
  useEffect(() => {
    if (catalogsLoading) return
    if (mode === 'single') {
      fetchSingleData()
    } else {
      fetchCompareData()
    }
  }, [catalogsLoading, mode, selectedCountry, selectedIndicator, startYear, endYear, compareCountries.join(',')])

  // Quick range preset handlers
  const setRangePreset = (yearsBack) => {
    const currentMax = 2024
    setEndYear(currentMax)
    setStartYear(Math.max(1960, currentMax - yearsBack))
  }

  // Toggle country in comparison set
  const toggleCompareCountry = (code) => {
    if (compareCountries.includes(code)) {
      if (compareCountries.length <= 1) return // Keep at least one country
      setCompareCountries(compareCountries.filter(c => c !== code))
    } else {
      if (compareCountries.length >= 8) return // Limit to max 8 countries
      setCompareCountries([...compareCountries, code])
    }
  }

  // Filter countries by search query
  const filteredCountries = useMemo(() => {
    if (!countrySearch.trim()) return countries
    const q = countrySearch.toLowerCase().trim()
    return countries.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.code.toLowerCase().includes(q) ||
      (c.iso2 && c.iso2.toLowerCase().includes(q)) ||
      (c.region && c.region.toLowerCase().includes(q)) ||
      (c.capital && c.capital.toLowerCase().includes(q))
    )
  }, [countries, countrySearch])

  // Filter indicators by category and search keyword
  const filteredIndicators = useMemo(() => {
    return indicators.filter(ind => {
      const matchCat = selectedCategory === 'All' || ind.category === selectedCategory
      if (!matchCat) return false
      if (!indicatorSearch.trim()) return true
      const q = indicatorSearch.toLowerCase().trim()
      return (
        ind.name.toLowerCase().includes(q) ||
        ind.id.toLowerCase().includes(q) ||
        (ind.description && ind.description.toLowerCase().includes(q)) ||
        (ind.unit && ind.unit.toLowerCase().includes(q))
      )
    })
  }, [indicators, selectedCategory, indicatorSearch])

  // Filter observations for the tabular view
  const filteredObservations = useMemo(() => {
    if (!singleData?.observations) return []
    if (tableFilter === 'valid') return singleData.observations.filter(o => !o.is_missing)
    if (tableFilter === 'missing') return singleData.observations.filter(o => o.is_missing)
    return singleData.observations
  }, [singleData, tableFilter])

  // Export current series as CSV file
  const exportCSV = () => {
    if (!singleData?.observations) return
    const headers = ['Year', 'Country_Code', 'Country_Name', 'Indicator_Code', 'Indicator_Name', 'Value', 'Status', 'Unit', 'Source', 'Last_Updated']
    const rows = singleData.observations.map(o => [
      o.year,
      `"${o.country_code}"`,
      `"${o.country_name}"`,
      `"${o.indicator_code}"`,
      `"${o.indicator_name}"`,
      o.is_missing ? '' : o.value,
      o.is_missing ? 'MISSING' : (o.value === 0 ? 'ZERO' : 'VERIFIED'),
      `"${o.unit || ''}"`,
      `"${o.source}"`,
      `"${o.last_updated}"`,
    ])
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `${singleData.country.code}_${singleData.indicator.code}_${startYear}_${endYear}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Render SVG Line Chart for Single Country
  const renderSingleChart = () => {
    if (!singleData || !singleData.observations || singleData.observations.length === 0) return null

    const observations = singleData.observations
    const validPoints = observations.filter(o => !o.is_missing)

    if (validPoints.length === 0) {
      return (
        <div className="chart-empty-state">
          <AlertCircle size={28} className="text-amber" />
          <p>No verified observations available from World Bank for {singleData.country.name} during {startYear}–{endYear}.</p>
          <small>The World Bank repository does not publish records for this indicator during this timeframe. No estimates were fabricated.</small>
        </div>
      )
    }

    const width = 850
    const height = 300
    const padding = { top: 30, right: 30, bottom: 40, left: 75 }

    const plotWidth = width - padding.left - padding.right
    const plotHeight = height - padding.top - padding.bottom

    const minYear = observations[0].year
    const maxYear = observations[observations.length - 1].year
    const yearSpan = maxYear - minYear || 1

    const values = validPoints.map(p => p.value)
    let minVal = Math.min(...values)
    let maxVal = Math.max(...values)

    if (minVal === maxVal) {
      minVal = minVal > 0 ? minVal * 0.9 : minVal - 1
      maxVal = maxVal > 0 ? maxVal * 1.1 : maxVal + 1
    } else {
      const valSpan = maxVal - minVal
      if (minVal >= 0 && minVal / maxVal < 0.25) {
        minVal = 0
      } else {
        minVal -= valSpan * 0.05
      }
      maxVal += valSpan * 0.08
    }

    const getX = (year) => padding.left + ((year - minYear) / yearSpan) * plotWidth
    const getY = (val) => {
      if (val === null || val === undefined) return null
      return padding.top + plotHeight - ((val - minVal) / (maxVal - minVal)) * plotHeight
    }

    // Build SVG path segments for continuous lines, preserving explicit missing gaps
    const lineSegments = []
    let currentSegment = []

    for (let i = 0; i < observations.length; i++) {
      const obs = observations[i]
      if (!obs.is_missing) {
        currentSegment.push({ x: getX(obs.year), y: getY(obs.value), obs })
      } else {
        if (currentSegment.length > 0) {
          lineSegments.push(currentSegment)
          currentSegment = []
        }
      }
    }
    if (currentSegment.length > 0) {
      lineSegments.push(currentSegment)
    }

    const makePathD = (points) => {
      if (!points.length) return ''
      return points.map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')
    }

    const makeAreaD = (points) => {
      if (points.length < 2) return ''
      const lineD = makePathD(points)
      const lastX = points[points.length - 1].x
      const firstX = points[0].x
      const baselineY = padding.top + plotHeight
      return `${lineD} L ${lastX} ${baselineY} L ${firstX} ${baselineY} Z`
    }

    const yTicks = [0, 0.25, 0.5, 0.75, 1].map(fraction => minVal + fraction * (maxVal - minVal))

    const step = Math.max(1, Math.ceil(yearSpan / 8))
    const xTicks = []
    for (let y = minYear; y <= maxYear; y += step) {
      xTicks.push(y)
    }
    if (xTicks[xTicks.length - 1] !== maxYear) {
      xTicks.push(maxYear)
    }

    return (
      <div className="chart-wrapper">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="global-svg-chart"
          onMouseLeave={() => setActiveTooltip(null)}
        >
          <defs>
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#69a9ff" stopOpacity="0.32" />
              <stop offset="100%" stopColor="#69a9ff" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y tick labels */}
          {yTicks.map((val, idx) => {
            const y = getY(val)
            return (
              <g key={`ytick-${idx}`}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#1c2638"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="#718096"
                  fontSize="11"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {formatNumber(val)}
                </text>
              </g>
            )
          })}

          {/* X-axis tick labels */}
          {xTicks.map((yr) => {
            const x = getX(yr)
            return (
              <g key={`xtick-${yr}`}>
                <line
                  x1={x}
                  y1={padding.top + plotHeight}
                  x2={x}
                  y2={padding.top + plotHeight + 5}
                  stroke="#2d3748"
                />
                <text
                  x={x}
                  y={padding.top + plotHeight + 20}
                  textAnchor="middle"
                  fill="#718096"
                  fontSize="11"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {yr}
                </text>
              </g>
            )
          })}

          {/* Area gradient under continuous segments */}
          {lineSegments.map((segment, idx) => (
            <path
              key={`area-${idx}`}
              d={makeAreaD(segment)}
              fill="url(#chartGradient)"
            />
          ))}

          {/* Trend lines */}
          {lineSegments.map((segment, idx) => (
            <path
              key={`line-${idx}`}
              d={makePathD(segment)}
              fill="none"
              stroke="#69a9ff"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}

          {/* Dashed bridge lines across missing gap intervals */}
          {observations.map((obs, idx) => {
            if (obs.is_missing && idx > 0 && idx < observations.length - 1) {
              const prev = observations[idx - 1]
              const next = observations[idx + 1]
              if (!prev.is_missing && !next.is_missing) {
                return (
                  <line
                    key={`bridge-${obs.year}`}
                    x1={getX(prev.year)}
                    y1={getY(prev.value)}
                    x2={getX(next.year)}
                    y2={getY(next.value)}
                    stroke="#f0bc78"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    opacity="0.6"
                  />
                )
              }
            }
            return null
          })}

          {/* Observation Markers */}
          {observations.map((obs) => {
            const x = getX(obs.year)
            const y = obs.is_missing ? padding.top + plotHeight - 12 : getY(obs.value)
            const isHovered = activeTooltip?.obs?.year === obs.year

            if (obs.is_missing) {
              // Unpopulated data gap: Hollow amber dashed circle
              return (
                <g
                  key={`pt-${obs.year}`}
                  className="chart-point-group"
                  onMouseEnter={() => setActiveTooltip({ x, y, obs })}
                >
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? 6.5 : 4}
                    fill="#101725"
                    stroke="#f0bc78"
                    strokeWidth="2"
                    strokeDasharray="2 2"
                    style={{ cursor: 'pointer' }}
                  />
                </g>
              )
            }

            // Real Verified Observation
            return (
              <g
                key={`pt-${obs.year}`}
                className="chart-point-group"
                onMouseEnter={() => setActiveTooltip({ x, y, obs })}
              >
                {isHovered && (
                  <circle cx={x} cy={y} r={9} fill="#69a9ff" opacity="0.25" />
                )}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? 5.5 : 3.5}
                  fill={obs.value === 0 ? '#f0bc78' : '#69a9ff'}
                  stroke="#090d17"
                  strokeWidth="1.5"
                  style={{ cursor: 'pointer' }}
                />
              </g>
            )
          })}
        </svg>

        {/* Interactive Tooltip Overlay */}
        {activeTooltip && (
          <div
            className="chart-tooltip"
            style={{
              left: `${(activeTooltip.x / width) * 100}%`,
              top: `${(activeTooltip.y / height) * 100}%`,
            }}
          >
            <div className="tooltip-header">
              <strong>{activeTooltip.obs.year}</strong>
              {activeTooltip.obs.is_missing ? (
                <span className="tooltip-pill missing">Unreported Data Gap</span>
              ) : activeTooltip.obs.value === 0 ? (
                <span className="tooltip-pill zero">Reported Zero (0.0)</span>
              ) : (
                <span className="tooltip-pill verified">Verified Sourced</span>
              )}
            </div>
            <div className="tooltip-body">
              {activeTooltip.obs.is_missing ? (
                <p className="missing-text">No observation published by World Bank for this year. Not fabricated.</p>
              ) : (
                <div className="val-display">
                  <span className="val-num">{formatNumber(activeTooltip.obs.value, singleData.indicator.unit)}</span>
                  <small className="val-unit">{singleData.indicator.unit}</small>
                </div>
              )}
            </div>
            <div className="tooltip-footer">
              <span className="src-tag">World Bank WDI</span>
              {activeTooltip.obs.last_updated && <span>Rel: {activeTooltip.obs.last_updated}</span>}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Render SVG Multi-Line Chart for Cross-Country Comparison
  const renderCompareChart = () => {
    if (!compareData || !compareData.comparison_matrix || compareData.comparison_matrix.length === 0) return null

    const matrix = compareData.comparison_matrix
    const countriesInCompare = Object.keys(compareData.countries)

    const width = 850
    const height = 320
    const padding = { top: 30, right: 30, bottom: 40, left: 75 }

    const plotWidth = width - padding.left - padding.right
    const plotHeight = height - padding.top - padding.bottom

    const minYear = matrix[0].year
    const maxYear = matrix[matrix.length - 1].year
    const yearSpan = maxYear - minYear || 1

    const allValues = []
    countriesInCompare.forEach(c => {
      const cData = compareData.countries[c]
      cData.observations.forEach(o => {
        if (!o.is_missing && o.value !== null) allValues.push(o.value)
      })
    })

    if (allValues.length === 0) {
      return (
        <div className="chart-empty-state">
          <AlertCircle size={28} className="text-amber" />
          <p>No valid data points across selected countries in this period.</p>
        </div>
      )
    }

    let minVal = Math.min(...allValues)
    let maxVal = Math.max(...allValues)

    if (minVal === maxVal) {
      minVal = minVal > 0 ? minVal * 0.9 : minVal - 1
      maxVal = maxVal > 0 ? maxVal * 1.1 : maxVal + 1
    } else {
      const valSpan = maxVal - minVal
      if (minVal >= 0 && minVal / maxVal < 0.25) {
        minVal = 0
      } else {
        minVal -= valSpan * 0.05
      }
      maxVal += valSpan * 0.08
    }

    const getX = (year) => padding.left + ((year - minYear) / yearSpan) * plotWidth
    const getY = (val) => {
      if (val === null || val === undefined) return null
      return padding.top + plotHeight - ((val - minVal) / (maxVal - minVal)) * plotHeight
    }

    const yTicks = [0, 0.25, 0.5, 0.75, 1].map(fraction => minVal + fraction * (maxVal - minVal))

    const step = Math.max(1, Math.ceil(yearSpan / 8))
    const xTicks = []
    for (let y = minYear; y <= maxYear; y += step) xTicks.push(y)
    if (xTicks[xTicks.length - 1] !== maxYear) xTicks.push(maxYear)

    return (
      <div className="chart-wrapper">
        <svg viewBox={`0 0 ${width} ${height}`} className="global-svg-chart">
          {/* Grid lines */}
          {yTicks.map((val, idx) => {
            const y = getY(val)
            return (
              <g key={`ytick-${idx}`}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#1c2638"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="#718096"
                  fontSize="11"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  {formatNumber(val)}
                </text>
              </g>
            )
          })}

          {/* X ticks */}
          {xTicks.map((yr) => (
            <g key={`xtick-${yr}`}>
              <line
                x1={getX(yr)}
                y1={padding.top + plotHeight}
                x2={getX(yr)}
                y2={padding.top + plotHeight + 5}
                stroke="#2d3748"
              />
              <text
                x={getX(yr)}
                y={padding.top + plotHeight + 20}
                textAnchor="middle"
                fill="#718096"
                fontSize="11"
                fontFamily="'JetBrains Mono', monospace"
              >
                {yr}
              </text>
            </g>
          ))}

          {/* Render country series */}
          {countriesInCompare.map((cCode, cIdx) => {
            const cColor = COUNTRY_COLORS[cIdx % COUNTRY_COLORS.length]
            const observations = compareData.countries[cCode].observations

            const segments = []
            let current = []
            observations.forEach(o => {
              if (!o.is_missing && o.value !== null) {
                current.push({ x: getX(o.year), y: getY(o.value), obs: o })
              } else {
                if (current.length > 0) {
                  segments.push(current)
                  current = []
                }
              }
            })
            if (current.length > 0) segments.push(current)

            return (
              <g key={`series-${cCode}`}>
                {segments.map((seg, sIdx) => {
                  const d = seg.map((p, pIdx) => (pIdx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')
                  return (
                    <path
                      key={`line-${cCode}-${sIdx}`}
                      d={d}
                      fill="none"
                      stroke={cColor}
                      strokeWidth="2.2"
                      strokeLinecap="round"
                    />
                  )
                })}
                {observations.filter(o => !o.is_missing).map(o => (
                  <circle
                    key={`dot-${cCode}-${o.year}`}
                    cx={getX(o.year)}
                    cy={getY(o.value)}
                    r="3"
                    fill={cColor}
                    stroke="#090d17"
                    strokeWidth="1"
                  />
                ))}
              </g>
            )
          })}
        </svg>

        {/* Multi-Country Legend with Latest Values */}
        <div className="compare-chart-legend">
          {countriesInCompare.map((cCode, idx) => {
            const cInfo = compareData.countries[cCode]
            const cColor = COUNTRY_COLORS[idx % COUNTRY_COLORS.length]
            return (
              <div key={cCode} className="legend-chip">
                <span className="color-indicator" style={{ background: cColor }} />
                <strong>{cInfo.country.name} ({cCode})</strong>
                <span className="legend-latest">
                  {cInfo.analytics.latest_value !== null ? formatNumber(cInfo.analytics.latest_value, compareData.indicator.unit) : 'N/A'}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const currentIndicatorMeta = indicators.find(i => i.id === selectedIndicator)
  const currentCountryMeta = countries.find(c => c.code === selectedCountry)

  return (
    <div className="global-intelligence-container">
      {/* Top Header Banner */}
      <div className="global-header">
        <div className="global-header-left">
          <div className="global-badge" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
              <Globe size={15} className="text-blue" /> GLOBAL HISTORICAL INTELLIGENCE
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '10px', fontWeight: 700 }}>
              <ShieldCheck size={12} /> VERIFIED SOURCE: WORLD BANK (v2)
            </span>
          </div>
          <h2>Global Data Mind — World Bank Sourced Intelligence</h2>
          <p className="global-subtitle">
            Authoritative, multi-decade country indicators sourced live from the World Bank API.
            Includes country search, category filtering, chronological observations, and explicit missing-data integrity.
          </p>
        </div>

        <div className="global-header-right">
          <div className="mode-switch-group">
            <button
              className={`mode-btn ${mode === 'single' ? 'active' : ''}`}
              onClick={() => setMode('single')}
            >
              <TrendingUp size={15} />
              <span>Country Timeline</span>
            </button>
            <button
              className={`mode-btn ${mode === 'compare' ? 'active' : ''}`}
              onClick={() => setMode('compare')}
            >
              <BarChart3 size={15} />
              <span>Country Compare ({compareCountries.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* 5-Step Guided Workflow Navigation Banner */}
      <div className="workflow-steps-banner">
        <div className="workflow-step active">
          <span className="step-num">1</span>
          <div className="step-text">
            <strong>1. Select Country</strong>
            <small>{mode === 'single' ? (currentCountryMeta ? currentCountryMeta.name : selectedCountry) : `${compareCountries.length} Selected`}</small>
          </div>
        </div>
        <div className="workflow-step-arrow">→</div>
        <div className="workflow-step active">
          <span className="step-num">2</span>
          <div className="step-text">
            <strong>2. Select Indicator</strong>
            <small>{currentIndicatorMeta ? currentIndicatorMeta.name.slice(0, 20) + '…' : 'GDP / Population'}</small>
          </div>
        </div>
        <div className="workflow-step-arrow">→</div>
        <div className="workflow-step active">
          <span className="step-num">3</span>
          <div className="step-text">
            <strong>3. Select Year Range</strong>
            <small>{startYear} – {endYear}</small>
          </div>
        </div>
        <div className="workflow-step-arrow">→</div>
        <div className="workflow-step highlight">
          <span className="step-num">4</span>
          <div className="step-text">
            <strong>4. Click Analyze</strong>
            <small>World Bank API</small>
          </div>
        </div>
        <div className="workflow-step-arrow">→</div>
        <div className="workflow-step">
          <span className="step-num">5</span>
          <div className="step-text">
            <strong>5. View Chart & Findings</strong>
            <small>Evidence & Gaps</small>
          </div>
        </div>
      </div>

      {/* Main Interactive Controls Card */}
      <div className="global-controls-card">
        {/* Row 1: Search Inputs and Category Pills */}
        <div className="category-pills-row">
          <div className="category-pills-scroll">
            <span className="category-pill-label">Category:</span>
            {INDICATOR_CATEGORIES.map(cat => (
              <button
                key={cat}
                className={`category-pill ${selectedCategory === cat ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Row 2: Selectors & Filters */}
        <div className="controls-row">
          {/* Mode 1: Country Selector & Search */}
          {mode === 'single' && (
            <div className="control-group">
              <label>Country ({filteredCountries.length} available)</label>
              <div className="search-select-combo">
                <select
                  value={selectedCountry}
                  onChange={e => setSelectedCountry(e.target.value)}
                  className="control-select"
                  disabled={loading}
                >
                  {filteredCountries.map(c => (
                    <option key={c.code} value={c.code}>
                      {c.name} ({c.code}) {c.region ? `— ${c.region}` : ''}
                    </option>
                  ))}
                </select>
                <div className="search-filter-inline">
                  <Search size={13} className="search-icon" />
                  <input
                    type="text"
                    placeholder="Search country..."
                    value={countrySearch}
                    onChange={e => setCountrySearch(e.target.value)}
                    className="inline-search-input"
                  />
                  {countrySearch && (
                    <button className="clear-search-btn" onClick={() => setCountrySearch('')}>
                      <X size={12} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Indicator Selector & Search */}
          <div className="control-group indicator-group">
            <label>Indicator ({filteredIndicators.length} matching)</label>
            <div className="search-select-combo">
              <select
                value={selectedIndicator}
                onChange={e => setSelectedIndicator(e.target.value)}
                className="control-select"
                disabled={loading}
              >
                {filteredIndicators.map(ind => (
                  <option key={ind.id} value={ind.id}>
                    [{ind.category}] {ind.name} ({ind.unit})
                  </option>
                ))}
              </select>
              <div className="search-filter-inline">
                <Search size={13} className="search-icon" />
                <input
                  type="text"
                  placeholder="Filter indicators..."
                  value={indicatorSearch}
                  onChange={e => setIndicatorSearch(e.target.value)}
                  className="inline-search-input"
                />
                {indicatorSearch && (
                  <button className="clear-search-btn" onClick={() => setIndicatorSearch('')}>
                    <X size={12} />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Year Range Inputs */}
          <div className="control-group years-group">
            <label>Time Period (Years)</label>
            <div className="years-inputs">
              <input
                type="number"
                min="1960"
                max={endYear}
                value={startYear}
                onChange={e => setStartYear(Math.max(1960, Math.min(parseInt(e.target.value) || 1990, endYear)))}
                className="year-input"
                disabled={loading}
                title="Start Year (1960-2026)"
              />
              <span className="year-separator">to</span>
              <input
                type="number"
                min={startYear}
                max="2026"
                value={endYear}
                onChange={e => setEndYear(Math.min(2026, Math.max(parseInt(e.target.value) || 2024, startYear)))}
                className="year-input"
                disabled={loading}
                title="End Year (1960-2026)"
              />
            </div>
          </div>

          {/* Action Trigger Button */}
          <div className="control-group actions-group">
            <label>&nbsp;</label>
            <button
              className="primary-action-btn analyze-btn-prominent"
              onClick={() => (mode === 'single' ? fetchSingleData(true) : fetchCompareData())}
              disabled={loading}
              title="Query the World Bank API and compute evidence-based metrics"
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>{loading ? 'Analyzing World Bank Data...' : 'Analyze Data'}</span>
            </button>
          </div>
        </div>

        {/* Row 3: Quick Popular Country Pills (Single Mode) & Year Presets */}
        <div className="controls-footer">
          <div className="presets-row">
            <span className="preset-label">Quick Ranges:</span>
            <button className="preset-chip" onClick={() => setRangePreset(5)}>Last 5Y</button>
            <button className="preset-chip" onClick={() => setRangePreset(10)}>Last 10Y</button>
            <button className="preset-chip" onClick={() => setRangePreset(20)}>Last 20Y</button>
            <button className="preset-chip" onClick={() => { setStartYear(1990); setEndYear(2024); }}>1990–2024</button>
            <button className="preset-chip" onClick={() => { setStartYear(1960); setEndYear(2024); }}>Max Range</button>
          </div>

          {mode === 'single' && (
            <div className="popular-countries-row">
              <span className="preset-label">Quick Countries:</span>
              {POPULAR_COUNTRIES.map(code => (
                <button
                  key={code}
                  className={`preset-chip ${selectedCountry === code ? 'active' : ''}`}
                  onClick={() => setSelectedCountry(code)}
                >
                  {code}
                </button>
              ))}
            </div>
          )}

          {currentIndicatorMeta && (
            <div className="indicator-desc-chip" title={currentIndicatorMeta.description}>
              <Info size={13} />
              <span>{currentIndicatorMeta.description}</span>
            </div>
          )}
        </div>

        {/* Mode 2: Multi-Country Selector with Live Search */}
        {mode === 'compare' && (
          <div className="compare-countries-selector">
            <div className="compare-header">
              <div className="compare-header-left">
                <span className="compare-title">Select Countries to Compare (1 to 8):</span>
                <span className="compare-counter">{compareCountries.length} / 8 Selected</span>
              </div>
              <div className="compare-search-box">
                <Search size={13} className="search-icon" />
                <input
                  type="text"
                  placeholder="Filter country list..."
                  value={countrySearch}
                  onChange={e => setCountrySearch(e.target.value)}
                  className="compare-search-input"
                />
              </div>
            </div>

            {/* Selected Countries Active Badges */}
            <div className="selected-compare-chips">
              {compareCountries.map((code, idx) => {
                const cMeta = countries.find(c => c.code === code)
                const cColor = COUNTRY_COLORS[idx % COUNTRY_COLORS.length]
                return (
                  <div key={code} className="active-compare-badge" style={{ borderColor: cColor }}>
                    <span className="badge-dot" style={{ background: cColor }} />
                    <span>{cMeta ? cMeta.name : code} ({code})</span>
                    <button
                      className="remove-badge-btn"
                      onClick={() => toggleCompareCountry(code)}
                      title={`Remove ${code}`}
                      disabled={compareCountries.length <= 1}
                    >
                      <X size={12} />
                    </button>
                  </div>
                )
              })}
            </div>

            {/* Country Pills Available to Toggle */}
            <div className="country-pills-grid">
              {filteredCountries.map(c => {
                const isSelected = compareCountries.includes(c.code)
                return (
                  <button
                    key={c.code}
                    className={`country-pill ${isSelected ? 'selected' : ''}`}
                    onClick={() => toggleCompareCountry(c.code)}
                  >
                    <span>{c.name}</span>
                    <small>{c.code}</small>
                    {isSelected && <Check size={12} className="check-icon" />}
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div className="global-error-banner">
          <AlertCircle size={20} className="error-icon" />
          <div className="error-content">
            <strong>World Bank API Communication Notice</strong>
            <p>{error}</p>
          </div>
          <button
            className="retry-btn"
            onClick={() => (mode === 'single' ? fetchSingleData(true) : fetchCompareData())}
          >
            <RefreshCw size={13} />
            <span>Retry Request</span>
          </button>
        </div>
      )}

      {/* Loading state indicator */}
      {loading && !error && (
        <div className="global-loading-card">
          <RefreshCw size={26} className="spin text-blue" />
          <h4>Querying official World Bank Indicators API...</h4>
          <p>
            Retrieving authentic historical observations for{' '}
            <strong>{mode === 'single' ? (currentCountryMeta ? currentCountryMeta.name : selectedCountry) : `${compareCountries.length} countries`}</strong>{' '}
            across {startYear}–{endYear}.
          </p>
        </div>
      )}

      {/* ---------------- MODE 1: SINGLE COUNTRY TIMELINE ---------------- */}
      {!loading && !error && mode === 'single' && singleData && (
        <div className="global-results-container">
          {/* Provenance and Integrity Banner */}
          <div className="provenance-banner">
            <div className="prov-item">
              <Database size={15} className="text-blue" />
              <span><strong>Source:</strong> {singleData.meta.source}</span>
            </div>
            <div className="prov-item">
              <Calendar size={15} className="text-mint" />
              <span><strong>World Bank Release:</strong> {singleData.meta.last_updated || 'Published release'}</span>
            </div>
            <div className="prov-item">
              <ShieldCheck size={15} className="text-purple" />
              <span><strong>Audit Status:</strong> Verified in Trust Ledger</span>
            </div>
            {singleData.meta.from_cache && (
              <div className="prov-item cached">
                <CheckCircle2 size={14} className="text-amber" />
                <span>Loaded from Local Cache</span>
              </div>
            )}
            {onSelectCountryNode && (
              <button
                className="prov-action-btn"
                onClick={() => onSelectCountryNode(`country_${singleData.country.code.toLowerCase()}`)}
                title="View country entity in FalkorDB Knowledge Graph"
              >
                <Network size={14} />
                <span>Inspect in Knowledge Graph</span>
              </button>
            )}

            <button
              className="ai-analysis-trigger-btn"
              onClick={handleRunAiAnalysis}
              disabled={aiLoading}
              title="Run fact-grounded evidence analysis with historical trends, anomalies, and verified citations"
            >
              <BrainCircuit size={14} className={aiLoading ? 'spin' : ''} />
              <span>{aiLoading ? 'Synthesizing...' : 'Evidence-Based AI Analysis'}</span>
            </button>
          </div>

          {/* Statistical KPI Summary Cards */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Latest Verified Value ({singleData.analytics.latest_year || 'N/A'})</span>
                <Sparkles size={16} className="text-blue" />
              </div>
              <div className="kpi-val">
                {singleData.analytics.latest_value !== null ? formatNumber(singleData.analytics.latest_value, singleData.indicator.unit) : 'N/A'}
              </div>
              <div className="kpi-sub">
                Official observed value for {singleData.country.name}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Baseline ({singleData.analytics.oldest_year || 'N/A'})</span>
                <Calendar size={16} className="text-mint" />
              </div>
              <div className="kpi-val">
                {singleData.analytics.oldest_value !== null ? formatNumber(singleData.analytics.oldest_value, singleData.indicator.unit) : 'N/A'}
              </div>
              <div className="kpi-sub">
                Initial observation in selected timeframe
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Overall Change</span>
                {singleData.analytics.overall_change_pct !== null ? (
                  singleData.analytics.overall_change_pct >= 0 ? (
                    <TrendingUp size={16} className="text-mint" />
                  ) : (
                    <TrendingDown size={16} className="text-pink" />
                  )
                ) : (
                  <Minus size={16} className="text-muted" />
                )}
              </div>
              <div className="kpi-val">
                {singleData.analytics.overall_change_pct !== null ? (
                  <span className={singleData.analytics.overall_change_pct >= 0 ? 'text-mint' : 'text-pink'}>
                    {singleData.analytics.overall_change_pct > 0 ? '+' : ''}{singleData.analytics.overall_change_pct}%
                  </span>
                ) : 'N/A'}
              </div>
              <div className="kpi-sub">
                Net delta between baseline and latest record
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <span className="kpi-label">Observation Coverage</span>
                <Layers size={16} className="text-amber" />
              </div>
              <div className="kpi-val">
                {singleData.meta.valid_observations} / {singleData.meta.total_observations} Years
              </div>
              <div className="kpi-sub">
                {singleData.meta.missing_observations > 0 ? (
                  <span className="text-amber">{singleData.meta.missing_observations} data gaps strictly isolated</span>
                ) : (
                  <span className="text-mint">100% complete reporting</span>
                )}
              </div>
            </div>
          </div>

          {/* Missing data notification banner if any years have gaps */}
          {singleData.meta.missing_observations > 0 && (
            <div className="gap-alert-card">
              <AlertCircle size={16} className="text-amber" />
              <span>
                <strong>Zero Fabrication Notice:</strong> {singleData.meta.missing_observations} year(s) in this range have no reported data from the World Bank.
                These are strictly treated as <em>Missing / Unreported</em> rather than 0.0 to maintain empirical accuracy.
              </span>
            </div>
          )}

          {/* Historical Trend Chart Section */}
          <div className="section-card chart-section">
            <div className="section-header">
              <div>
                <h3>Historical Trend Chart — {singleData.country.name}</h3>
                <p>{singleData.indicator.name} ({startYear}–{endYear})</p>
              </div>
              <div className="chart-legend-simple">
                <span className="dot blue" /> Verified Fact
                <span className="dot amber-hollow" /> Data Gap (Missing)
              </div>
            </div>
            {renderSingleChart()}
          </div>

          {/* Observations Data Table Section */}
          <div className="section-card table-section">
            <div className="section-header table-header-row">
              <div>
                <h3>Empirical Observations Record ({filteredObservations.length} Rows)</h3>
                <p>Verified historical facts retrieved from World Bank API and stored in graph memory</p>
              </div>

              <div className="table-controls">
                <div className="filter-pill-group">
                  <button
                    className={`filter-btn ${tableFilter === 'all' ? 'active' : ''}`}
                    onClick={() => setTableFilter('all')}
                  >
                    All ({singleData.observations.length})
                  </button>
                  <button
                    className={`filter-btn ${tableFilter === 'valid' ? 'active' : ''}`}
                    onClick={() => setTableFilter('valid')}
                  >
                    Populated ({singleData.meta.valid_observations})
                  </button>
                  <button
                    className={`filter-btn ${tableFilter === 'missing' ? 'active' : ''}`}
                    onClick={() => setTableFilter('missing')}
                  >
                    Missing ({singleData.meta.missing_observations})
                  </button>
                </div>

                <button className="export-btn" onClick={exportCSV}>
                  <Download size={14} />
                  <span>Export CSV</span>
                </button>
              </div>
            </div>

            <div className="observations-table-wrapper">
              <table className="observations-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    <th>Country</th>
                    <th>Observed Value</th>
                    <th>Integrity Status</th>
                    <th>Source Release</th>
                    <th>Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredObservations.map((obs) => (
                    <tr key={obs.year} className={obs.is_missing ? 'row-missing' : ''}>
                      <td className="year-cell">
                        <strong>{obs.year}</strong>
                      </td>
                      <td>
                        <span className="country-code-pill">{obs.country_code}</span> {obs.country_name}
                      </td>
                      <td className="value-cell">
                        {obs.is_missing ? (
                          <span className="val-missing">—</span>
                        ) : (
                          <span className="val-verified">
                            {formatNumber(obs.value, singleData.indicator.unit)}
                          </span>
                        )}
                      </td>
                      <td>
                        {obs.is_missing ? (
                          <span className="status-badge missing" title="Isolated missing data gap — zero metric fabrication">
                            <AlertCircle size={11} style={{ marginRight: 3, verticalAlign: 'middle' }} /> Missing Gap
                          </span>
                        ) : obs.value === 0 ? (
                          <span className="status-badge zero" title="Empirical zero observation">
                            <CheckCircle2 size={11} style={{ marginRight: 3, verticalAlign: 'middle' }} /> Zero (0.0)
                          </span>
                        ) : (
                          <span className="status-badge verified" title="Authoritative Source: World Bank API (v2) • Status: Verified">
                            <ShieldCheck size={11} style={{ marginRight: 3, verticalAlign: 'middle' }} /> Verified
                          </span>
                        )}
                      </td>
                      <td className="source-cell">{obs.source}</td>
                      <td className="updated-cell">{obs.last_updated || 'Latest'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ---------------- MODE 2: MULTI-COUNTRY COMPARISON ---------------- */}
      {!loading && !error && mode === 'compare' && compareData && (
        <div className="global-results-container">
          <div className="provenance-banner">
            <div className="prov-item">
              <Globe size={15} className="text-blue" />
              <span><strong>Comparing:</strong> {Object.keys(compareData.countries).join(', ')}</span>
            </div>
            <div className="prov-item">
              <BarChart3 size={15} className="text-mint" />
              <span><strong>Indicator:</strong> {compareData.indicator.name} ({compareData.indicator.unit})</span>
            </div>
            <div className="prov-item">
              <ShieldCheck size={15} className="text-purple" />
              <span><strong>Provenance:</strong> World Bank WDI Certified Records</span>
            </div>

            <button
              className="ai-analysis-trigger-btn"
              onClick={handleRunAiAnalysis}
              disabled={aiLoading}
              style={{ marginLeft: 'auto' }}
              title="Run cross-country evidence analysis with disparity ratios, rankings, and citations"
            >
              <BrainCircuit size={14} className={aiLoading ? 'spin' : ''} />
              <span>{aiLoading ? 'Synthesizing...' : 'Comparative AI Analysis'}</span>
            </button>
          </div>

          {/* Latest Rankings Leaderboard Cards */}
          <div className="rankings-grid">
            {compareData.latest_rankings.map((rankItem) => (
              <div key={rankItem.country_code} className="ranking-card">
                <div className="rank-badge">#{rankItem.rank}</div>
                <div className="rank-details">
                  <strong>{rankItem.country_name} ({rankItem.country_code})</strong>
                  <div className="rank-value">
                    {formatNumber(rankItem.latest_value, compareData.indicator.unit)}
                  </div>
                  <small>As of year {rankItem.latest_year}</small>
                </div>
              </div>
            ))}
          </div>

          {/* Multi-Line Comparison Chart */}
          <div className="section-card chart-section">
            <div className="section-header">
              <div>
                <h3>Cross-Country Historical Comparison</h3>
                <p>{compareData.indicator.name} ({startYear}–{endYear})</p>
              </div>
            </div>
            {renderCompareChart()}
          </div>

          {/* Year-by-Year Comparison Matrix Table */}
          <div className="section-card table-section">
            <div className="section-header">
              <div>
                <h3>Comparative Annual Observations Matrix</h3>
                <p>Side-by-side annual comparison across selected nations sourced from World Bank</p>
              </div>
            </div>

            <div className="observations-table-wrapper">
              <table className="observations-table">
                <thead>
                  <tr>
                    <th>Year</th>
                    {Object.keys(compareData.countries).map(cCode => (
                      <th key={cCode}>{compareData.countries[cCode].country.name} ({cCode})</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {compareData.comparison_matrix.map((row) => (
                    <tr key={row.year}>
                      <td className="year-cell"><strong>{row.year}</strong></td>
                      {Object.keys(compareData.countries).map(cCode => {
                        const val = row[cCode]
                        return (
                          <td key={cCode} className="value-cell">
                            {val === null || val === undefined ? (
                              <span className="val-missing">—</span>
                            ) : (
                              <span className="val-verified">
                                {formatNumber(val, compareData.indicator.unit)}
                              </span>
                            )}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Evidence-Based AI Analysis Modal */}
      {showAiModal && aiAnalysis && (
        <div className="ai-modal-overlay" onClick={() => setShowAiModal(false)}>
          <div className="ai-modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="ai-modal-header">
              <div className="ai-modal-header-left">
                <div className="ai-modal-icon">
                  <BrainCircuit size={20} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h3 className="ai-modal-title">
                      {aiAnalysis.analysis_scope === 'GLOBAL_COUNTRY_INTELLIGENCE'
                        ? `Evidence-Based Analysis — ${aiAnalysis.country.name}`
                        : `Comparative AI Analysis — ${aiAnalysis.indicator.name}`}
                    </h3>
                    <span className="ai-scope-badge global">
                      {aiAnalysis.analysis_scope}
                    </span>
                  </div>
                  <p className="ai-modal-subtitle">
                    Fact-grounded, zero-fabrication analysis grounded in official World Bank historical data
                  </p>
                </div>
              </div>
              <button
                className="ai-modal-close-btn"
                onClick={() => setShowAiModal(false)}
                aria-label="Close modal"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="ai-modal-scrollable">
              {/* 5 Plain-Language Core Questions */}
              <div className="ai-questions-container" style={{ marginBottom: '20px' }}>
                {/* 1. What changed? */}
                <div className="ai-q-card">
                  <div className="ai-q-header">
                    <div className="ai-q-number">1</div>
                    <h4>What changed?</h4>
                  </div>
                  <p className="ai-q-content">
                    {aiAnalysis.analysis_scope === 'GLOBAL_COUNTRY_INTELLIGENCE'
                      ? `${aiAnalysis.country?.name} experienced ${aiAnalysis.historical_trend?.direction || 'movement'} in ${aiAnalysis.indicator?.name}. Value shifted from ${aiAnalysis.historical_trend?.start_value} (${aiAnalysis.timeframe?.start_year}) to ${aiAnalysis.historical_trend?.end_value} (${aiAnalysis.timeframe?.end_year}), representing a ${aiAnalysis.historical_trend?.percentage_change !== null ? `${aiAnalysis.historical_trend?.percentage_change}% net change` : 'recorded movement'}.`
                      : `Cross-country comparison of ${aiAnalysis.indicator?.name} revealed ${aiAnalysis.disparity_metrics?.top_country?.country_name} as top performer (${aiAnalysis.disparity_metrics?.top_country?.latest_value}) and ${aiAnalysis.disparity_metrics?.lowest_country?.country_name} at lowest (${aiAnalysis.disparity_metrics?.lowest_country?.latest_value}).`}
                  </p>
                </div>

                {/* 2. What does it mean? */}
                <div className="ai-q-card">
                  <div className="ai-q-header">
                    <div className="ai-q-number">2</div>
                    <h4>What does it mean?</h4>
                  </div>
                  <p className="ai-q-content">{aiAnalysis.summary}</p>
                </div>

                {/* 3. What evidence supports this? */}
                <div className="ai-q-card">
                  <div className="ai-q-header">
                    <div className="ai-q-number">3</div>
                    <h4>What evidence supports this?</h4>
                  </div>
                  <div className="ai-q-content">
                    <p style={{ margin: '0 0 6px' }}>Verified against official World Bank Development Indicators (API v2). Official Citations:</p>
                    <ul style={{ margin: 0, paddingLeft: '18px', color: '#cbd5e1', fontSize: '12px' }}>
                      {aiAnalysis.citations?.slice(0, 2).map((c, i) => (
                        <li key={i}><strong>{c.claim}</strong> (Source: {c.source})</li>
                      ))}
                      {aiAnalysis.verified_facts?.slice(0, 2).map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 4. What data is missing? */}
                <div className="ai-q-card">
                  <div className="ai-q-header">
                    <div className="ai-q-number">4</div>
                    <h4>What data is missing?</h4>
                  </div>
                  <div className="ai-q-content">
                    <ul style={{ margin: 0, paddingLeft: '18px', color: '#cbd5e1', fontSize: '12px' }}>
                      {aiAnalysis.uncertainty_and_limitations?.map((lim, i) => (
                        <li key={i}>{lim}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 5. What should the user explore next? */}
                <div className="ai-q-card">
                  <div className="ai-q-header">
                    <div className="ai-q-number">5</div>
                    <h4>What should the user explore next?</h4>
                  </div>
                  <p className="ai-q-content">
                    {aiAnalysis.analysis_scope === 'GLOBAL_COUNTRY_INTELLIGENCE'
                      ? `Compare ${aiAnalysis.country?.name} with peer nations using Country Compare mode, or explore related indicators such as Population (SP.POP.TOTL) or Life Expectancy (SP.DYN.LE00.IN).`
                      : `Drill into individual country series or inspect multi-hop macroeconomic relationships in the interactive Knowledge Graph.`}
                  </p>
                </div>
              </div>

              {/* Expandable Advanced Technical Details */}
              <details className="advanced-ai-details" style={{ marginBottom: '16px' }}>
                <summary>
                  <span>Advanced Mathematical & Empirical Details (CAGR, Anomalies, Citations)</span>
                  <ChevronDown size={14} className="details-chevron" />
                </summary>
                <div className="advanced-details-content" style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* 2. Key Historical Metrics (Series mode) */}
                  {aiAnalysis.analysis_scope === 'GLOBAL_COUNTRY_INTELLIGENCE' && aiAnalysis.historical_trend && (
                    <div className="ai-metrics-grid">
                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Trajectory Direction</span>
                        <div
                          className="ai-metric-value"
                          style={{
                            color:
                              aiAnalysis.historical_trend.direction === 'Growth'
                                ? '#64d7b2'
                                : aiAnalysis.historical_trend.direction === 'Decline'
                                ? '#f472b6'
                                : '#f0bc78',
                          }}
                        >
                          {aiAnalysis.historical_trend.direction}
                        </div>
                        <span className="ai-metric-sub">
                          {aiAnalysis.timeframe?.start_year} to {aiAnalysis.timeframe?.end_year}
                        </span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Total Net Delta</span>
                        <div className="ai-metric-value">
                          {aiAnalysis.historical_trend.net_change > 0 ? '+' : ''}
                          {aiAnalysis.historical_trend.net_change}
                        </div>
                        <span className="ai-metric-sub">{aiAnalysis.indicator?.unit}</span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Percentage Change</span>
                        <div
                          className="ai-metric-value"
                          style={{
                            color: aiAnalysis.historical_trend.percentage_change >= 0 ? '#64d7b2' : '#f0bc78',
                          }}
                        >
                          {aiAnalysis.historical_trend.percentage_change !== null
                            ? `${aiAnalysis.historical_trend.percentage_change}%`
                            : 'N/A'}
                        </div>
                        <span className="ai-metric-sub">Across verified span</span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Historical CAGR</span>
                        <div className="ai-metric-value">
                          {aiAnalysis.historical_trend.cagr_percentage !== null
                            ? `${aiAnalysis.historical_trend.cagr_percentage}%`
                            : 'N/A'}
                        </div>
                        <span className="ai-metric-sub">Annual compounded rate</span>
                      </div>
                    </div>
                  )}

                  {/* 2b. Disparity Metrics (Compare mode) */}
                  {aiAnalysis.analysis_scope === 'GLOBAL_CROSS_COUNTRY_COMPARISON' && aiAnalysis.disparity_metrics && (
                    <div className="ai-metrics-grid">
                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Top Ranked Country</span>
                        <div className="ai-metric-value" style={{ color: '#64d7b2' }}>
                          {aiAnalysis.disparity_metrics.top_country?.country_name}
                        </div>
                        <span className="ai-metric-sub">
                          {aiAnalysis.disparity_metrics.top_country?.latest_value !== undefined
                            ? aiAnalysis.disparity_metrics.top_country?.latest_value?.toLocaleString()
                            : 'N/A'}{' '}
                          ({aiAnalysis.disparity_metrics.top_country?.latest_year})
                        </span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Lowest Ranked Country</span>
                        <div className="ai-metric-value" style={{ color: '#f0bc78' }}>
                          {aiAnalysis.disparity_metrics.lowest_country?.country_name}
                        </div>
                        <span className="ai-metric-sub">
                          {aiAnalysis.disparity_metrics.lowest_country?.latest_value !== undefined
                            ? aiAnalysis.disparity_metrics.lowest_country?.latest_value?.toLocaleString()
                            : 'N/A'}{' '}
                          ({aiAnalysis.disparity_metrics.lowest_country?.latest_year})
                        </span>
                      </div>

                      <div className="ai-metric-card">
                        <span className="ai-metric-label">Disparity Ratio</span>
                        <div className="ai-metric-value" style={{ color: '#a18aff' }}>
                          {aiAnalysis.disparity_metrics.disparity_ratio
                            ? `${aiAnalysis.disparity_metrics.disparity_ratio}x`
                            : 'N/A'}
                        </div>
                        <span className="ai-metric-sub">Highest vs Lowest spread</span>
                      </div>
                    </div>
                  )}

                  {/* Detected Anomalies */}
                  {aiAnalysis.detected_anomalies && aiAnalysis.detected_anomalies.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <AlertCircle size={15} color="#f0bc78" /> Detected Statistical Anomalies ({aiAnalysis.detected_anomalies.length})
                      </div>
                      {aiAnalysis.detected_anomalies.map((anom, idx) => (
                        <div key={idx} className="ai-anomaly-card">
                          <div className="ai-anomaly-header">
                            <span className="ai-anomaly-title">
                              Year {anom.year} · {anom.direction} Volatility
                            </span>
                            <span className="ai-anomaly-delta">{anom.year_over_year_change_pct}</span>
                          </div>
                          <p className="ai-anomaly-desc">
                            Value shifted from {anom.previous_value} ({anom.previous_year}) to {anom.value} ({anom.year}). {anom.context}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Bounded Analytical Scenarios */}
                  {aiAnalysis.analytical_scenarios && aiAnalysis.analytical_scenarios.length > 0 && (
                    <div className="ai-section-box">
                      <div className="ai-section-title">
                        <TrendingUp size={15} color="#a18aff" /> Bounded Analytical Scenarios (Conditional Projections)
                      </div>
                      <div className="ai-scenarios-grid">
                        {aiAnalysis.analytical_scenarios.map((scen, idx) => (
                          <div key={idx} className="ai-scenario-card">
                            <div className="ai-scenario-name">{scen.scenario_name}</div>
                            <div className="ai-scenario-val">{scen.estimated_value}</div>
                            <div className="ai-scenario-meta">{scen.projection_horizon}</div>
                            <div className="ai-scenario-meta" style={{ color: '#cbd5e1' }}>{scen.growth_assumption}</div>
                            <span className="ai-scenario-confidence">{scen.confidence_level}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </details>

              {/* 8. Mandatory Statistical Disclaimer */}
              {aiAnalysis.disclaimer && (
                <div className="ai-disclaimer-banner">
                  <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
                  <div>
                    <strong>NO PREDICTION GUARANTEE:</strong> {aiAnalysis.disclaimer}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="ai-modal-footer">
              <div>
                {aiAnalysis.trust_ledger_id ? (
                  <span>
                    Audited in Trust Ledger: <strong style={{ color: '#a18aff' }}>#{aiAnalysis.trust_ledger_id.slice(-6)}</strong>
                  </span>
                ) : (
                  <span>Zero-fabrication audit complete</span>
                )}
              </div>
              <div>Evaluated: {aiAnalysis.evaluated_at || 'Just now'} · World Bank Indicators API</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
