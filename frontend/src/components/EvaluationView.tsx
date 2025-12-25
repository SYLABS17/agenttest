import { EvaluationReport } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'

interface EvaluationViewProps {
  evaluation: EvaluationReport
}

export default function EvaluationView({ evaluation }: EvaluationViewProps) {
  // Prepare data for bar chart
  const agentScoresData = evaluation.agent_evaluations.map(eval => ({
    agent: eval.agent_name.replace('Agent', ''),
    overall: eval.overall_score,
    accuracy: eval.scores.accuracy,
    relevance: eval.scores.relevance,
    completeness: eval.scores.completeness,
    latency: eval.scores.latency,
  }))

  // Prepare data for radar chart
  const metricsData = Object.keys(evaluation.agent_evaluations[0]?.scores || {}).map(metric => {
    const dataPoint: any = { metric: metric.charAt(0).toUpperCase() + metric.slice(1) }
    evaluation.agent_evaluations.forEach(eval => {
      dataPoint[eval.agent_name.replace('Agent', '')] = eval.scores[metric as keyof typeof eval.scores]
    })
    return dataPoint
  })

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400'
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1) + '%'
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Overall Performance
          </h3>
          <p className={`text-2xl font-bold ${getScoreColor(evaluation.summary.overall.mean)}`}>
            {formatScore(evaluation.summary.overall.mean)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Best: {evaluation.summary.overall.best_agent}
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Agent Agreement
          </h3>
          <p className={`text-2xl font-bold ${getScoreColor(evaluation.agreement_score)}`}>
            {formatScore(evaluation.agreement_score)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Consensus level
          </p>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
            Total Latency
          </h3>
          <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">
            {evaluation.summary.latency.total_ms.toFixed(0)}ms
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Avg: {evaluation.summary.latency.mean_ms.toFixed(0)}ms
          </p>
        </div>
      </div>

      {/* Agent Performance Comparison */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Agent Performance Comparison
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={agentScoresData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="agent" />
            <YAxis domain={[0, 1]} />
            <Tooltip formatter={(value: number) => formatScore(value)} />
            <Legend />
            <Bar dataKey="overall" fill="#3b82f6" name="Overall" />
            <Bar dataKey="accuracy" fill="#10b981" name="Accuracy" />
            <Bar dataKey="relevance" fill="#f59e0b" name="Relevance" />
            <Bar dataKey="completeness" fill="#8b5cf6" name="Completeness" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Radar Chart */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Metrics Distribution
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={metricsData}>
            <PolarGrid className="opacity-30" />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis domain={[0, 1]} />
            {evaluation.agent_evaluations.map((eval, index) => (
              <Radar
                key={eval.agent_name}
                name={eval.agent_name.replace('Agent', '')}
                dataKey={eval.agent_name.replace('Agent', '')}
                stroke={index === 0 ? '#3b82f6' : '#10b981'}
                fill={index === 0 ? '#3b82f6' : '#10b981'}
                fillOpacity={0.3}
              />
            ))}
            <Tooltip formatter={(value: number) => formatScore(value)} />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Agent Evaluations */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Detailed Agent Evaluations
        </h3>
        <div className="space-y-4">
          {evaluation.agent_evaluations.map(eval => (
            <div key={eval.agent_name} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {eval.agent_name}
                </h4>
                <span className={`font-bold ${getScoreColor(eval.overall_score)}`}>
                  {formatScore(eval.overall_score)}
                </span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.entries(eval.scores).map(([metric, score]) => (
                  <div key={metric} className="text-sm">
                    <span className="text-gray-600 dark:text-gray-400 capitalize">
                      {metric}:
                    </span>
                    <span className={`ml-2 font-medium ${getScoreColor(score)}`}>
                      {formatScore(score)}
                    </span>
                  </div>
                ))}
              </div>
              
              <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                Latency: {eval.latency_ms.toFixed(0)}ms
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {evaluation.recommendations && evaluation.recommendations.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-300 mb-3">
            Recommendations
          </h3>
          <ul className="list-disc list-inside space-y-2">
            {evaluation.recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-yellow-700 dark:text-yellow-400">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}