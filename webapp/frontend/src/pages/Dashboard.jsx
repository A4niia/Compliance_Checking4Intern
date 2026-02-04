import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    FileText, Code, Shield, CheckCircle, Brain,
    Workflow, BarChart3, ArrowRight, Zap
} from 'lucide-react'
import axios from 'axios'

export default function Dashboard() {
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchStats()
    }, [])

    const fetchStats = async () => {
        try {
            const res = await axios.get('/api/stats')
            setStats(res.data)
        } catch (err) {
            console.error('Failed to fetch stats:', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="processing-spinner w-8 h-8 border-primary-600"></div>
            </div>
        )
    }

    const researchQuestions = [
        {
            id: 'RQ1',
            question: 'Can LLMs effectively identify policy rules?',
            answer: '99% Accuracy',
            detail: 'Mistral-7B, Cohen\'s κ = 0.85',
            color: 'purple',
            icon: Brain
        },
        {
            id: 'RQ2',
            question: 'Is First-Order Logic sufficient for policy formalization?',
            answer: '100% Success',
            detail: '97 rules formalized, no HOL needed',
            color: 'success',
            icon: Code
        },
        {
            id: 'RQ3',
            question: 'Can FOL be automatically translated to SHACL?',
            answer: '1,309 Triples',
            detail: 'W3C-compliant SHACL shapes',
            color: 'warning',
            icon: Shield
        }
    ]

    return (
        <div className="space-y-8">
            {/* Hero Section */}
            <div className="card bg-gradient-to-br from-primary-50 via-white to-primary-50 border-2 border-primary-100">
                <div className="text-center py-8">
                    <h1 className="text-5xl font-bold text-neutral-800 mb-3">
                        Automated Policy Formalization Pipeline
                    </h1>
                    <p className="text-xl text-neutral-600 mb-6">
                        From Natural Language to Semantic Web Constraints
                    </p>
                    <div className="flex items-center justify-center gap-4 flex-wrap">
                        <Link to="/methodology" className="btn btn-primary flex items-center gap-2">
                            <Workflow className="w-5 h-5" />
                            View 4-Phase Methodology
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                        <Link to="/results" className="btn btn-secondary flex items-center gap-2">
                            <BarChart3 className="w-5 h-5" />
                            See Research Results
                        </Link>
                    </div>
                </div>
            </div>

            {/* Research Questions - Answered */}
            <div>
                <h2 className="text-2xl font-bold text-neutral-800 mb-6 flex items-center gap-3">
                    <CheckCircle className="w-8 h-8 text-success-600" />
                    Research Questions Answered
                </h2>
                <div className="grid grid-cols-3 gap-6">
                    {researchQuestions.map((rq) => (
                        <div key={rq.id} className={`card bg-gradient-to-br from-${rq.color}-50 to-white border-l-4 border-${rq.color}-500`}>
                            <div className="flex items-center gap-2 mb-3">
                                <div className={`w-10 h-10 rounded-lg bg-${rq.color}-100 flex items-center justify-center`}>
                                    <rq.icon className={`w-5 h-5 text-${rq.color}-700`} />
                                </div>
                                <span className={`text-sm font-bold px-2 py-1 rounded bg-${rq.color}-100 text-${rq.color}-700`}>
                                    {rq.id}
                                </span>
                            </div>
                            <h3 className="font-semibold text-neutral-700 text-sm mb-3 leading-tight">
                                {rq.question}
                            </h3>
                            <div className={`text-3xl font-bold text-${rq.color}-700 mb-1`}>
                                {rq.answer}
                            </div>
                            <p className="text-sm text-neutral-600">
                                {rq.detail}
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Pipeline Statistics */}
            <div>
                <h2 className="text-2xl font-bold text-neutral-800 mb-6 flex items-center gap-3">
                    <Zap className="w-7 h-7 text-primary-600" />
                    Pipeline Performance
                </h2>
                <div className="grid grid-cols-4 gap-4">
                    <div className="stat-card">
                        <div className="stat-value text-primary-600">{stats?.total_rules || 0}</div>
                        <div className="stat-label">Total Rules</div>
                        <div className="text-xs text-neutral-500 mt-2">Gold standard corpus</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value text-purple-600">99%</div>
                        <div className="stat-label">Classification</div>
                        <div className="text-xs text-neutral-500 mt-2">LLM accuracy</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value text-success-600">{stats?.formalized || 0}</div>
                        <div className="stat-label">FOL Formalized</div>
                        <div className="text-xs text-neutral-500 mt-2">100% success rate</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value text-warning-600">{stats?.shacl_triples || 0}</div>
                        <div className="stat-label">SHACL Triples</div>
                        <div className="text-xs text-neutral-500 mt-2">W3C validated</div>
                    </div>
                </div>
            </div>

            {/* 4-Phase Overview */}
            <div className="card">
                <h2 className="text-2xl font-bold text-neutral-800 mb-6 flex items-center gap-3">
                    <Workflow className="w-7 h-7 text-neutral-700" />
                    4-Phase Methodology
                </h2>
                <div className="grid grid-cols-4 gap-4">
                    <div className="text-center p-4 rounded-xl bg-primary-50 border border-primary-200">
                        <div className="w-12 h-12 rounded-full bg-primary-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">
                            1
                        </div>
                        <h3 className="font-semibold text-neutral-800 mb-2">Text Simplification</h3>
                        <p className="text-sm text-neutral-600">OCR cleanup & normalization</p>
                        <div className="mt-3 text-xs font-semibold text-primary-700">+15pp accuracy</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-purple-50 border border-purple-200">
                        <div className="w-12 h-12 rounded-full bg-purple-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">
                            2
                        </div>
                        <h3 className="font-semibold text-neutral-800 mb-2">LLM Classification</h3>
                        <p className="text-sm text-neutral-600">Deontic type identification</p>
                        <div className="mt-3 text-xs font-semibold text-purple-700">0% → 70% permissions</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-success-50 border border-success-200">
                        <div className="w-12 h-12 rounded-full bg-success-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">
                            3
                        </div>
                        <h3 className="font-semibold text-neutral-800 mb-2">FOL Formalization</h3>
                        <p className="text-sm text-neutral-600">First-order logic generation</p>
                        <div className="mt-3 text-xs font-semibold text-success-700">100% success</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-warning-50 border border-warning-200">
                        <div className="w-12 h-12 rounded-full bg-warning-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">
                            4
                        </div>
                        <h3 className="font-semibold text-neutral-800 mb-2">SHACL Translation</h3>
                        <p className="text-sm text-neutral-600">Semantic web constraints</p>
                        <div className="mt-3 text-xs font-semibold text-warning-700">1,309 triples</div>
                    </div>
                </div>
                <div className="mt-6 text-center">
                    <Link to="/methodology" className="btn btn-primary inline-flex items-center gap-2">
                        View Live Pipeline Execution
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>
            </div>

            {/* Rule Distribution */}
            <div className="card">
                <h2 className="text-xl font-semibold text-neutral-800 mb-6">Deontic Type Distribution</h2>
                <div className="grid grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="text-4xl font-bold text-error-600">{stats?.obligations || 0}</div>
                        <div className="text-neutral-600 mt-1 font-medium">Obligations</div>
                        <div className="mt-3 h-2 bg-neutral-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-error-500 rounded-full"
                                style={{ width: `${((stats?.obligations || 0) / (stats?.formalized || 1)) * 100}%` }}
                            />
                        </div>
                        <div className="text-sm text-neutral-500 mt-1">
                            {Math.round(((stats?.obligations || 0) / (stats?.formalized || 1)) * 100)}%
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-success-600">{stats?.permissions || 0}</div>
                        <div className="text-neutral-600 mt-1 font-medium">Permissions</div>
                        <div className="mt-3 h-2 bg-neutral-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-success-500 rounded-full"
                                style={{ width: `${((stats?.permissions || 0) / (stats?.formalized || 1)) * 100}%` }}
                            />
                        </div>
                        <div className="text-sm text-neutral-500 mt-1">
                            {Math.round(((stats?.permissions || 0) / (stats?.formalized || 1)) * 100)}%
                        </div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-warning-600">{stats?.prohibitions || 0}</div>
                        <div className="text-neutral-600 mt-1 font-medium">Prohibitions</div>
                        <div className="mt-3 h-2 bg-neutral-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-warning-500 rounded-full"
                                style={{ width: `${((stats?.prohibitions || 0) / (stats?.formalized || 1)) * 100}%` }}
                            />
                        </div>
                        <div className="text-sm text-neutral-500 mt-1">
                            {Math.round(((stats?.prohibitions || 0) / (stats?.formalized || 1)) * 100)}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
