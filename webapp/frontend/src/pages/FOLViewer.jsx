import { useState, useEffect } from 'react'
import { Code, Search, Copy, Check } from 'lucide-react'
import axios from 'axios'

export default function FOLViewer() {
    const [fol, setFol] = useState(null)
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [copied, setCopied] = useState(null)

    useEffect(() => {
        fetchFOL()
    }, [])

    const fetchFOL = async () => {
        try {
            const res = await axios.get('/api/fol')
            setFol(res.data)
        } catch (err) {
            console.error('Failed to fetch FOL:', err)
        } finally {
            setLoading(false)
        }
    }

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text)
        setCopied(id)
        setTimeout(() => setCopied(null), 2000)
    }

    const filteredRules = fol?.formalized_rules?.filter(rule =>
        rule.id?.toLowerCase().includes(search.toLowerCase()) ||
        rule.fol_formalization?.deontic_formula?.toLowerCase().includes(search.toLowerCase())
    ) || []

    const getBadgeClass = (type) => {
        switch (type) {
            case 'obligation': return 'badge-obligation'
            case 'permission': return 'badge-permission'
            case 'prohibition': return 'badge-prohibition'
            default: return 'bg-slate-700 text-slate-300'
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">FOL Viewer</h1>
                    <p className="text-slate-400 mt-1">First-Order Logic formalizations</p>
                </div>
                <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2">
                    <Search className="w-5 h-5 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search formulas..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="bg-transparent text-white focus:outline-none w-64"
                    />
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
                <div className="card text-center">
                    <div className="text-3xl font-bold text-white">{fol?.formalized_rules?.length || 0}</div>
                    <div className="text-slate-400 text-sm">Total Formalized</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-red-400">
                        {fol?.formalized_rules?.filter(r => r.fol_formalization?.deontic_type === 'obligation').length || 0}
                    </div>
                    <div className="text-slate-400 text-sm">Obligations</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-green-400">
                        {fol?.formalized_rules?.filter(r => r.fol_formalization?.deontic_type === 'permission').length || 0}
                    </div>
                    <div className="text-slate-400 text-sm">Permissions</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-orange-400">
                        {fol?.formalized_rules?.filter(r => r.fol_formalization?.deontic_type === 'prohibition').length || 0}
                    </div>
                    <div className="text-slate-400 text-sm">Prohibitions</div>
                </div>
            </div>

            {/* Formulas List */}
            <div className="space-y-4">
                {filteredRules.map((rule, i) => (
                    <div key={i} className="card card-hover">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-3">
                                    <span className="text-blue-400 font-mono text-sm">{rule.id}</span>
                                    {rule.fol_formalization?.deontic_type && (
                                        <span className={`badge ${getBadgeClass(rule.fol_formalization.deontic_type)}`}>
                                            {rule.fol_formalization.deontic_type}
                                        </span>
                                    )}
                                </div>

                                {/* Deontic Formula */}
                                <div className="bg-slate-900 rounded-lg p-4 mb-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-slate-500 uppercase tracking-wider">Deontic Formula</span>
                                        <button
                                            onClick={() => copyToClipboard(rule.fol_formalization?.deontic_formula || '', `df-${i}`)}
                                            className="text-slate-400 hover:text-white"
                                        >
                                            {copied === `df-${i}` ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    <code className="text-green-400 font-mono text-sm">
                                        {rule.fol_formalization?.deontic_formula || 'N/A'}
                                    </code>
                                </div>

                                {/* FOL Expansion */}
                                {rule.fol_formalization?.fol_expansion && (
                                    <div className="bg-slate-900 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs text-slate-500 uppercase tracking-wider">FOL Expansion</span>
                                            <button
                                                onClick={() => copyToClipboard(rule.fol_formalization?.fol_expansion || '', `fe-${i}`)}
                                                className="text-slate-400 hover:text-white"
                                            >
                                                {copied === `fe-${i}` ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                                            </button>
                                        </div>
                                        <code className="text-purple-400 font-mono text-sm break-all">
                                            {rule.fol_formalization.fol_expansion}
                                        </code>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {filteredRules.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                    No formulas found matching your search.
                </div>
            )}
        </div>
    )
}
