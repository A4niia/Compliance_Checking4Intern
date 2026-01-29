import { useState, useEffect } from 'react'
import { FileText, Code, Shield, CheckCircle, AlertCircle, Clock } from 'lucide-react'
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
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    const statCards = [
        { label: 'Total Rules', value: stats?.total_rules || 0, icon: FileText, color: 'blue' },
        { label: 'Formalized', value: stats?.formalized || 0, icon: Code, color: 'purple' },
        { label: 'SHACL Triples', value: stats?.shacl_triples || 0, icon: Shield, color: 'green' },
        { label: 'Annotated', value: stats?.annotated || 0, icon: CheckCircle, color: 'emerald' },
    ]

    const ruleTypes = [
        { type: 'Obligations', count: stats?.obligations || 0, color: 'red' },
        { type: 'Permissions', count: stats?.permissions || 0, color: 'green' },
        { type: 'Prohibitions', count: stats?.prohibitions || 0, color: 'orange' },
    ]

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                <p className="text-slate-400 mt-2">Overview of your policy formalization pipeline</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {statCards.map((stat, i) => (
                    <div key={i} className="stat-card">
                        <div className="stat-card-inner">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-slate-400 text-sm">{stat.label}</p>
                                    <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                                </div>
                                <div className={`w-12 h-12 rounded-xl bg-${stat.color}-500/20 flex items-center justify-center`}>
                                    <stat.icon className={`w-6 h-6 text-${stat.color}-400`} />
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Rule Types */}
            <div className="card">
                <h2 className="text-xl font-semibold text-white mb-6">Rule Distribution</h2>
                <div className="grid grid-cols-3 gap-6">
                    {ruleTypes.map((item, i) => (
                        <div key={i} className="text-center">
                            <div className={`text-4xl font-bold text-${item.color}-400`}>{item.count}</div>
                            <div className="text-slate-400 mt-1">{item.type}</div>
                            <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full bg-${item.color}-500`}
                                    style={{ width: `${(item.count / (stats?.formalized || 1)) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Progress */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card">
                    <h2 className="text-xl font-semibold text-white mb-4">Annotation Progress</h2>
                    <div className="flex items-center gap-4">
                        <div className="flex-1">
                            <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                    style={{ width: `${((stats?.annotated || 0) / (stats?.total_rules || 1)) * 100}%` }}
                                ></div>
                            </div>
                        </div>
                        <span className="text-white font-semibold">
                            {Math.round(((stats?.annotated || 0) / (stats?.total_rules || 1)) * 100)}%
                        </span>
                    </div>
                    <p className="text-slate-400 text-sm mt-2">
                        {stats?.annotated} of {stats?.total_rules} rules annotated
                    </p>
                </div>

                <div className="card">
                    <h2 className="text-xl font-semibold text-white mb-4">Pipeline Status</h2>
                    <div className="space-y-3">
                        {[
                            { step: 'PDF Extraction', status: 'complete' },
                            { step: 'LLM Classification', status: 'complete' },
                            { step: 'FOL Formalization', status: 'complete' },
                            { step: 'SHACL Translation', status: 'complete' },
                        ].map((item, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-green-400" />
                                <span className="text-slate-300">{item.step}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
