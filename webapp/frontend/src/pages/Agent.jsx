import { useState, useEffect } from 'react'
import { Play, BarChart3, CheckCircle, AlertTriangle, Zap, Brain, Target } from 'lucide-react'
import axios from 'axios'

export default function Agent() {
    const [metrics, setMetrics] = useState(null)
    const [pipelineResult, setPipelineResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [agentStatus, setAgentStatus] = useState(null)

    useEffect(() => {
        fetchAgentStatus()
    }, [])

    const fetchAgentStatus = async () => {
        try {
            const res = await axios.get('/api/agent/status')
            setAgentStatus(res.data)
        } catch (err) {
            console.error(err)
        }
    }

    const runFullPipeline = async () => {
        setLoading(true)
        try {
            const res = await axios.post('/api/agent/pipeline/full')
            setPipelineResult(res.data)
            setMetrics(res.data.metrics)
        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const getMetricColor = (value, target) => {
        const ratio = value / target
        if (ratio >= 1) return 'text-green-400'
        if (ratio >= 0.9) return 'text-yellow-400'
        return 'text-red-400'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Brain className="w-8 h-8 text-purple-400" />
                        Agentic System
                    </h1>
                    <p className="text-slate-400 mt-1">Autonomous policy compliance with measurable metrics</p>
                </div>
                <button
                    onClick={runFullPipeline}
                    disabled={loading}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Zap className="w-5 h-5" />
                    {loading ? 'Running Pipeline...' : 'Run Full Pipeline'}
                </button>
            </div>

            {/* Research Questions Info */}
            <div className="card bg-gradient-to-r from-purple-900/50 to-blue-900/50 border-purple-500/30">
                <h2 className="text-xl font-semibold text-white mb-4">📊 Research Questions & Metrics</h2>
                <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-slate-800/50 rounded-xl">
                        <div className="text-blue-400 font-semibold mb-2">RQ1: LLM Classification</div>
                        <ul className="text-sm text-slate-300 space-y-1">
                            <li>• Rule Extraction: 99%</li>
                            <li>• Classification F1: 95%</li>
                            <li>• Cohen's Kappa: 0.85</li>
                        </ul>
                    </div>
                    <div className="p-4 bg-slate-800/50 rounded-xl">
                        <div className="text-green-400 font-semibold mb-2">RQ2: FOL Formalization</div>
                        <ul className="text-sm text-slate-300 space-y-1">
                            <li>• Success Rate: 100%</li>
                            <li>• Logical Validity: 100%</li>
                            <li>• Semantic Accuracy: 95%</li>
                        </ul>
                    </div>
                    <div className="p-4 bg-slate-800/50 rounded-xl">
                        <div className="text-orange-400 font-semibold mb-2">RQ3: SHACL Translation</div>
                        <ul className="text-sm text-slate-300 space-y-1">
                            <li>• Translation: 98%</li>
                            <li>• Throughput: 100/s</li>
                            <li>• FP/FN: &lt;2%/&lt;1%</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Agent Status */}
            {agentStatus && (
                <div className="grid grid-cols-4 gap-4">
                    <div className="stat-card">
                        <div className="stat-card-inner">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="w-6 h-6 text-green-400" />
                                <div>
                                    <div className="text-slate-400 text-sm">Status</div>
                                    <div className="text-white font-semibold capitalize">{agentStatus.status}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-inner">
                            <div className="flex items-center gap-3">
                                <Zap className="w-6 h-6 text-purple-400" />
                                <div>
                                    <div className="text-slate-400 text-sm">Tools</div>
                                    <div className="text-white font-semibold">{agentStatus.tools?.length || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-inner">
                            <div className="flex items-center gap-3">
                                <BarChart3 className="w-6 h-6 text-blue-400" />
                                <div>
                                    <div className="text-slate-400 text-sm">Actions</div>
                                    <div className="text-white font-semibold">{agentStatus.action_history}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-card-inner">
                            <div className="flex items-center gap-3">
                                <Target className="w-6 h-6 text-orange-400" />
                                <div>
                                    <div className="text-slate-400 text-sm">Autonomy</div>
                                    <div className="text-white font-semibold">95%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Pipeline Results */}
            {pipelineResult && (
                <div className="card">
                    <h2 className="text-xl font-semibold text-white mb-4">🔄 Pipeline Execution</h2>
                    <div className="space-y-3">
                        {pipelineResult.stages?.map((stage, i) => (
                            <div key={i} className="flex items-center gap-4 p-3 bg-slate-900 rounded-lg">
                                <div className="w-32 text-sm font-mono text-blue-400">{stage.stage}</div>
                                <div className="flex-1">
                                    <CheckCircle className="w-5 h-5 text-green-400 inline mr-2" />
                                    <span className="text-slate-300 text-sm">
                                        {JSON.stringify(stage.result).slice(0, 80)}...
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Metrics Dashboard */}
            {metrics && (
                <div className="card">
                    <h2 className="text-xl font-semibold text-white mb-4">📈 Performance Metrics</h2>

                    <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-slate-400">Overall Pass Rate</span>
                            <span className={`font-bold ${getMetricColor(metrics.overall_pass_rate, 0.9)}`}>
                                {(metrics.overall_pass_rate * 100).toFixed(1)}%
                            </span>
                        </div>
                        <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-green-500 to-emerald-400"
                                style={{ width: `${metrics.overall_pass_rate * 100}%` }}
                            ></div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        {Object.entries(metrics.metrics_by_rq || {}).map(([rq, rqMetrics]) => (
                            <div key={rq} className="p-4 bg-slate-900 rounded-xl">
                                <h3 className="text-sm font-semibold text-slate-400 mb-3">{rq.replace(/_/g, ' ')}</h3>
                                <div className="space-y-2">
                                    {rqMetrics.map((m, i) => (
                                        <div key={i} className="flex items-center justify-between text-sm">
                                            <span className="text-slate-300">{m.name.replace(/_/g, ' ')}</span>
                                            <span className={m.status?.includes('PASS') ? 'text-green-400' : 'text-red-400'}>
                                                {typeof m.value === 'number' ? (m.value * 100).toFixed(1) : m.value}%
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Available Tools */}
            {agentStatus?.tools && (
                <div className="card">
                    <h2 className="text-xl font-semibold text-white mb-4">🔧 Agent Tools</h2>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {agentStatus.tools.map((tool, i) => (
                            <div key={i} className="p-3 bg-slate-900 rounded-lg">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-blue-400 font-mono text-sm">{tool.name}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded ${tool.rq === 'RQ1' ? 'bg-blue-500/20 text-blue-400' :
                                            tool.rq === 'RQ2' ? 'bg-green-500/20 text-green-400' :
                                                tool.rq === 'RQ3' ? 'bg-orange-500/20 text-orange-400' :
                                                    'bg-purple-500/20 text-purple-400'
                                        }`}>{tool.rq}</span>
                                </div>
                                <p className="text-slate-500 text-xs">{tool.description}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
