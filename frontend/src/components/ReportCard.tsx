/**
 * Report Card Component
 * Display evaluation sections in card format
 */
interface ReportCardProps {
  title: string
  children: React.ReactNode
  className?: string
}

export default function ReportCard({ title, children, className = '' }: ReportCardProps) {
  return (
    <div className={`bg-meet-darker rounded-lg p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      <div className="text-meet-light-gray">{children}</div>
    </div>
  )
}

interface VerdictBadgeProps {
  verdict: string
  score: number
}

export function VerdictBadge({ verdict, score }: VerdictBadgeProps) {
  const getVerdictColor = () => {
    if (verdict === 'Hire') return 'bg-meet-green'
    if (verdict === 'Borderline') return 'bg-yellow-500'
    return 'bg-meet-red'
  }

  return (
    <div className="flex items-center space-x-4">
      <div className={`${getVerdictColor()} text-white px-6 py-3 rounded-full font-bold text-lg`}>
        {verdict}
      </div>
      <div className="text-white text-2xl font-semibold">
        {score.toFixed(1)}<span className="text-meet-light-gray text-lg">/10</span>
      </div>
    </div>
  )
}

interface MetricScoreProps {
  metric: string
  score: number
}

export function MetricScore({ metric, score }: MetricScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-meet-green'
    if (score >= 6.5) return 'text-yellow-500'
    if (score >= 5) return 'text-meet-light-gray'
    return 'text-meet-red'
  }

  const percentage = (score / 10) * 100

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-white capitalize">{metric.replace('_', ' ')}</span>
        <span className={`font-semibold ${getScoreColor(score)}`}>{score.toFixed(1)}/10</span>
      </div>
      <div className="w-full bg-meet-gray rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${
            score >= 8
              ? 'bg-meet-green'
              : score >= 6.5
              ? 'bg-yellow-500'
              : score >= 5
              ? 'bg-meet-blue'
              : 'bg-meet-red'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
