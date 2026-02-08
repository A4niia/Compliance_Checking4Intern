import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Code, Shield, CheckCircle, Brain, Workflow, BarChart3, ArrowRight, Zap } from 'lucide-react'
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
                <div className="processing-spinner w-8 h-8 border-blue-600"></div>
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Hero */}
            <div className="card bg-gradient-to-br from-blue-50 via-white to-blue-50 border-2 border-blue-100">
                <div className="text-center py-8">
                    <h1 className="text-5xl font-bold text-gray-800 mb-3">
                        Automated Policy Formalization Pipeline
                    </h1>
                    <p className="text-xl text-gray-600 mb-6">
                        From Natural Language to Semantic Web Constraints
                    </p>
                    <div className="flex items-center justify-center gap-4">
                        <Link to="/methodology" className="btn btn-primary">
                            <Workflow className="w-5 h-5" />
                            View 5-Phase Methodology
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                        <Link to="/results" className="btn btn-secondary">
                            <BarChart3 className="w-5 h-5" />
                            See Research Results
                        </Link>
                    </div>
                </div>
            </div>

            {/* Research Questions */}
            <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                    Research Questions Answered
                </h2>
                <div className="grid grid-cols-3 gap-6">
                    <div className="card bg-gradient-to-br from-purple-50 to-white border-l-4 border-purple-500">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                <Brain className="w-5 h-5 text-purple-700" />
                            </div>
                            <span className="text-sm font-bold px-2 py-1 rounded bg-purple-100 text-purple-700">RQ1</span>
                        </div>
                        <h3 className="font-semibold text-gray-700 text-sm mb-3">Can LLMs identify policy rules?</h3>
                        <div className="text-3xl font-bold text-purple-700 mb-1">95.88%</div>
                        <p className="text-sm text-gray-600">Mistral-7B, κ=0.8503</p>
                    </div>

                    <div className="card bg-gradient-to-br from-green-50 to-white border-l-4 border-green-500">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                                <Code className="w-5 h-5 text-green-700" />
                            </div>
                            <span className="text-sm font-bold px-2 py-1 rounded bg-green-100 text-green-700">RQ2</span>
                        </div>
                        <h3 className="font-semibold text-gray-700 text-sm mb-3">Is FOL sufficient?</h3>
                        <div className="text-3xl font-bold text-green-700 mb-1">100%</div>
                        <p className="text-sm text-gray-600">All rules formalized</p>
                    </div>

                    <div className="card bg-gradient-to-br from-orange-50 to-white border-l-4 border-orange-500">
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                                <Shield className="w-5 h-5 text-orange-700" />
                            </div>
                            <span className="text-sm font-bold px-2 py-1 rounded bg-orange-100 text-orange-700">RQ3</span>
                        </div>
                        <h3 className="font-semibold text-gray-700 text-sm mb-3">FOL → SHACL translation?</h3>
                        <div className="text-3xl font-bold text-orange-700 mb-1">1,309</div>
                        <p className="text-sm text-gray-600">W3C triples</p>
                    </div>
                </div>
            </div>

            {/* Pipeline Stats */}
            <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <Zap className="w-7 h-7 text-blue-600" />
                    Pipeline Performance
                </h2>
                <div className="grid grid-cols-4 gap-4">
                    <div className="card text-center hover:transform hover:scale-105 transition-transform">
                        <div className="text-4xl font-bold text-blue-600 mb-2">{stats?.total_rules || 97}</div>
                        <div className="text-sm text-gray-600 font-medium uppercase tracking-wide">Candidates</div>
                        <div className="text-xs text-gray-500 mt-1">83 validated as rules</div>
                    </div>
                    <div className="card text-center hover:transform hover:scale-105 transition-transform">
                        <div className="text-4xl font-bold text-purple-600 mb-2">95.88%</div>
                        <div className="text-sm text-gray-600 font-medium uppercase tracking-wide">Classification</div>
                        <div className="text-xs text-gray-500 mt-1">Validated accuracy (v4)</div>
                    </div>
                    <div className="card text-center hover:transform hover:scale-105 transition-transform">
                        <div className="text-4xl font-bold text-green-600 mb-2">{stats?.formalized || 81}</div>
                        <div className="text-sm text-gray-600 font-medium uppercase tracking-wide">LLM Classified</div>
                        <div className="text-xs text-gray-500 mt-1">v4 annotations</div>
                    </div>
                    <div className="card text-center hover:transform hover:scale-105 transition-transform">
                        <div className="text-4xl font-bold text-orange-600 mb-2">{stats?.shacl_triples || 1309}</div>
                        <div className="text-sm text-gray-600 font-medium uppercase tracking-wide">SHACL Triples</div>
                        <div className="text-xs text-gray-500 mt-1">W3C validated</div>
                    </div>
                </div>
            </div>

            {/* 5-Phase Overview */}
            <div className="card">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <Workflow className="w-7 h-7 text-gray-700" />
                    5-Phase Methodology
                </h2>
                <div className="grid grid-cols-5 gap-4 mb-6">
                    <div className="text-center p-4 rounded-xl bg-blue-50 border border-blue-200">
                        <div className="w-12 h-12 rounded-full bg-blue-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">1</div>
                        <h3 className="font-semibold text-gray-800 mb-2">Text Simplification</h3>
                        <p className="text-sm text-gray-600">OCR cleanup</p>
                        <div className="mt-3 text-xs font-semibold text-blue-700">+15pp accuracy</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-purple-50 border border-purple-200">
                        <div className="w-12 h-12 rounded-full bg-purple-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">2</div>
                        <h3 className="font-semibold text-gray-800 mb-2">LLM Classification</h3>
                        <p className="text-sm text-gray-600">Deontic types</p>
                        <div className="mt-3 text-xs font-semibold text-purple-700">0% → 50% permissions</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-green-50 border border-green-200">
                        <div className="w-12 h-12 rounded-full bg-green-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">3</div>
                        <h3 className="font-semibold text-gray-800 mb-2">FOL Formalization</h3>
                        <p className="text-sm text-gray-600">First-order logic</p>
                        <div className="mt-3 text-xs font-semibold text-green-700">100% success</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-orange-50 border border-orange-200">
                        <div className="w-12 h-12 rounded-full bg-orange-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">4</div>
                        <h3 className="font-semibold text-gray-800 mb-2">SHACL Translation</h3>
                        <p className="text-sm text-gray-600">Semantic web</p>
                        <div className="mt-3 text-xs font-semibold text-orange-700">1,309 triples</div>
                    </div>
                    <div className="text-center p-4 rounded-xl bg-red-50 border border-red-200">
                        <div className="w-12 h-12 rounded-full bg-red-500 text-white font-bold text-xl flex items-center justify-center mx-auto mb-3">5</div>
                        <h3 className="font-semibold text-gray-800 mb-2">Rule Validation</h3>
                        <p className="text-sm text-gray-600">SHACL checking</p>
                        <div className="mt-3 text-xs font-semibold text-red-700">Automated + LLM</div>
                    </div>
                </div>
                <div className="text-center">
                    <Link to="/methodology" className="btn btn-primary">
                        View Live Pipeline Execution
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>
            </div>

            {/* Rule Distribution */}
            <div className="card">
                <h2 className="text-xl font-semibold text-gray-800 mb-6">Deontic Type Distribution</h2>
                <div className="grid grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="text-4xl font-bold text-red-600 mb-2">{stats?.obligations || 48}</div>
                        <div className="text-gray-600 font-medium">Obligations</div>
                        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-red-500 rounded-full" style={{ width: `${((stats?.obligations || 48) / (stats?.formalized || 81)) * 100}%` }}></div>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">{Math.round(((stats?.obligations || 48) / (stats?.formalized || 81)) * 100)}%</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-green-600 mb-2">{stats?.permissions || 15}</div>
                        <div className="text-gray-600 font-medium">Permissions</div>
                        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-green-500 rounded-full" style={{ width: `${((stats?.permissions || 15) / (stats?.formalized || 81)) * 100}%` }}></div>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">{Math.round(((stats?.permissions || 15) / (stats?.formalized || 81)) * 100)}%</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-orange-600 mb-2">{stats?.prohibitions || 18}</div>
                        <div className="text-gray-600 font-medium">Prohibitions</div>
                        <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-orange-500 rounded-full" style={{ width: `${((stats?.prohibitions || 18) / (stats?.formalized || 81)) * 100}%` }}></div>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">{Math.round(((stats?.prohibitions || 18) / (stats?.formalized || 81)) * 100)}%</div>
                    </div>
                </div>
            </div>
        </div>
    )
}
