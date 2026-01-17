/**
 * Report Dashboard Page
 * Display comprehensive interview evaluation with charts and insights
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ScoreChart from '../components/ScoreChart'
import ReportCard, { VerdictBadge, MetricScore } from '../components/ReportCard'

interface DashboardData {
  session_id: string
  job_role: string
  created_at: string
  final_evaluation: {
    overall_score: number
    verdict: string
    metrics: {
      technical_depth: number
      communication: number
      confidence: number
      logical_thinking: number
      problem_solving: number
      culture_fit: number
    }
    insights: {
      strongest_metric?: string
      weakest_metric?: string
      common_strengths?: string[]
      common_weaknesses?: string[]
    }
  }
  improvement_suggestions: Array<{
    area: string
    suggestion: string
  }>
  chart_data: {
    radar_data: Array<{ metric: string; score: number }>
    bar_data: Array<{ metric: string; score: number }>
    line_data: Array<{ question: number; score: number }>
  }
}

export default function Report() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setError('Session ID not provided')
      setLoading(false)
      return
    }

    fetch(`http://localhost:8000/api/reports/${sessionId}/dashboard`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch dashboard data')
        return res.json()
      })
      .then((data) => {
        setData(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [sessionId])

  const handleDownloadPDF = () => {
    if (!sessionId) return
    window.open(`http://localhost:8000/api/reports/${sessionId}/pdf`, '_blank')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-meet-dark flex items-center justify-center">
        <div className="text-white text-xl">Loading report...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-meet-dark flex items-center justify-center">
        <div className="text-center">
          <div className="text-meet-red text-xl mb-4">Error loading report</div>
          <div className="text-meet-light-gray mb-4">{error || 'Report not found'}</div>
          <button
            onClick={() => navigate('/')}
            className="bg-meet-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600"
          >
            Back to Interview
          </button>
        </div>
      </div>
    )
  }

  const evaluation = data.final_evaluation

  return (
    <div className="min-h-screen bg-meet-dark p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Interview Report</h1>
            <p className="text-meet-light-gray">
              {data.job_role} • {new Date(data.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex space-x-4">
            <button
              onClick={handleDownloadPDF}
              className="bg-meet-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            >
              Download PDF
            </button>
            <button
              onClick={() => navigate('/')}
              className="bg-meet-gray text-white px-6 py-2 rounded-lg hover:bg-meet-light-gray transition-colors"
            >
              New Interview
            </button>
          </div>
        </div>

        {/* Verdict Card */}
        <div className="bg-meet-darker rounded-lg p-8 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Executive Summary</h2>
          <VerdictBadge verdict={evaluation.verdict} score={evaluation.overall_score} />
          {evaluation.insights && (
            <div className="mt-6 text-meet-light-gray">
              <p>
                <strong className="text-white">Strongest Area:</strong>{' '}
                {evaluation.insights.strongest_metric?.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase()) || 'N/A'}
              </p>
              <p className="mt-2">
                <strong className="text-white">Weakest Area:</strong>{' '}
                {evaluation.insights.weakest_metric?.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase()) || 'N/A'}
              </p>
            </div>
          )}
        </div>

        {/* Charts */}
        <div className="mb-6">
          <ScoreChart
            radarData={data.chart_data.radar_data}
            barData={data.chart_data.bar_data}
            lineData={data.chart_data.line_data}
          />
        </div>

        {/* Metrics Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <ReportCard title="Evaluation Metrics">
            <MetricScore metric="Technical Depth" score={evaluation.metrics.technical_depth} />
            <MetricScore metric="Communication" score={evaluation.metrics.communication} />
            <MetricScore metric="Confidence" score={evaluation.metrics.confidence} />
            <MetricScore metric="Logical Thinking" score={evaluation.metrics.logical_thinking} />
            <MetricScore metric="Problem Solving" score={evaluation.metrics.problem_solving} />
            <MetricScore metric="Culture Fit" score={evaluation.metrics.culture_fit} />
          </ReportCard>

          {/* Strengths & Weaknesses */}
          <div className="space-y-6">
            <ReportCard title="Strengths">
              {evaluation.insights?.common_strengths && evaluation.insights.common_strengths.length > 0 ? (
                <ul className="list-disc list-inside space-y-2">
                  {evaluation.insights.common_strengths.map((strength, i) => (
                    <li key={i} className="text-white">
                      {strength}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-meet-light-gray">No specific strengths identified.</p>
              )}
            </ReportCard>

            <ReportCard title="Areas for Improvement">
              {evaluation.insights?.common_weaknesses && evaluation.insights.common_weaknesses.length > 0 ? (
                <ul className="list-disc list-inside space-y-2">
                  {evaluation.insights.common_weaknesses.map((weakness, i) => (
                    <li key={i} className="text-white">
                      {weakness}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-meet-light-gray">No specific weaknesses identified.</p>
              )}
            </ReportCard>
          </div>
        </div>

        {/* Improvement Suggestions */}
        {data.improvement_suggestions && data.improvement_suggestions.length > 0 && (
          <ReportCard title="Improvement Suggestions" className="mb-6">
            <div className="space-y-4">
              {data.improvement_suggestions.map((suggestion, i) => (
                <div key={i} className="border-l-4 border-meet-blue pl-4">
                  <h4 className="text-white font-semibold mb-1">{suggestion.area}</h4>
                  <p className="text-meet-light-gray">{suggestion.suggestion}</p>
                </div>
              ))}
            </div>
          </ReportCard>
        )}
      </div>
    </div>
  )
}
