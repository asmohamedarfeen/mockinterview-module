/**
 * Score Chart Components
 * Visualizations for evaluation metrics
 */
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'

interface ScoreChartProps {
  radarData: Array<{ metric: string; score: number }>
  barData: Array<{ metric: string; score: number }>
  lineData: Array<{ question: number; score: number }>
}

export default function ScoreChart({ radarData, barData, lineData }: ScoreChartProps) {
  return (
    <div className="space-y-8">
      {/* Radar Chart */}
      <div className="bg-meet-darker rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Overall Performance</h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" tick={{ fill: '#ffffff', fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 10]} tick={{ fill: '#ffffff', fontSize: 10 }} />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#1a73e8"
              fill="#1a73e8"
              fillOpacity={0.6}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart */}
      <div className="bg-meet-darker rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Metric Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3c4043" />
            <XAxis dataKey="metric" tick={{ fill: '#ffffff', fontSize: 12 }} />
            <YAxis domain={[0, 10]} tick={{ fill: '#ffffff', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#202124',
                border: '1px solid #3c4043',
                color: '#ffffff',
              }}
            />
            <Bar dataKey="score" fill="#1a73e8" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Line Chart - Score Progression */}
      {lineData.length > 0 && (
        <div className="bg-meet-darker rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Score Progression</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3c4043" />
              <XAxis dataKey="question" tick={{ fill: '#ffffff', fontSize: 12 }} />
              <YAxis domain={[0, 10]} tick={{ fill: '#ffffff', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#202124',
                  border: '1px solid #3c4043',
                  color: '#ffffff',
                }}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#34a853"
                strokeWidth={3}
                dot={{ fill: '#34a853', r: 5 }}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
