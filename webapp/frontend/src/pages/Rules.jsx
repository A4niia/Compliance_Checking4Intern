import { useState, useEffect } from 'react'
import { Search, Filter, ChevronLeft, ChevronRight, Check, X } from 'lucide-react'
import axios from 'axios'

export default function Rules() {
    const [rules, setRules] = useState([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [filter, setFilter] = useState('')
    const [selectedRule, setSelectedRule] = useState(null)
    const [annotating, setAnnotating] = useState(false)

    useEffect(() => {
        fetchRules()
    }, [page, filter])

    const fetchRules = async () => {
        setLoading(true)
        try {
            const params = { page, per_page: 10 }
            if (filter) params.type = filter
            const res = await axios.get('/api/rules', { params })
            setRules(res.data.rules)
            setTotalPages(res.data.pages)
        } catch (err) {
            console.error('Failed to fetch rules:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleAnnotate = async (ruleId, annotation) => {
        setAnnotating(true)
        try {
            await axios.put(`/api/rules/${ruleId}/annotate`, annotation)
            fetchRules()
            setSelectedRule(null)
        } catch (err) {
            console.error('Failed to annotate:', err)
        } finally {
            setAnnotating(false)
        }
    }

    const getBadgeClass = (type) => {
        switch (type) {
            case 'obligation': return 'badge-obligation'
            case 'permission': return 'badge-permission'
            case 'prohibition': return 'badge-prohibition'
            default: return 'bg-slate-700 text-slate-300'
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Policy Rules</h1>
                    <p className="text-slate-400 mt-1">View and annotate extracted rules</p>
                </div>
                <div className="flex items-center gap-4">
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                        <option value="">All Types</option>
                        <option value="obligation">Obligations</option>
                        <option value="permission">Permissions</option>
                        <option value="prohibition">Prohibitions</option>
                    </select>
                </div>
            </div>

            {/* Rules List */}
            <div className="space-y-4">
                {loading ? (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    </div>
                ) : (
                    rules.map((rule) => (
                        <div
                            key={rule.id}
                            className="card card-hover cursor-pointer"
                            onClick={() => setSelectedRule(rule)}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-blue-400 font-mono text-sm">{rule.id}</span>
                                        {rule.fol?.deontic_type && (
                                            <span className={`badge ${getBadgeClass(rule.fol.deontic_type)}`}>
                                                {rule.fol.deontic_type}
                                            </span>
                                        )}
                                        {rule.human_annotation?.is_rule !== null && (
                                            <span className="badge bg-green-500/20 text-green-400 border border-green-500/30">
                                                ✓ Annotated
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-slate-300 text-sm line-clamp-2">{rule.original_text}</p>
                                    <p className="text-slate-500 text-xs mt-2">{rule.source_document}</p>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-center gap-4">
                <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn btn-secondary disabled:opacity-50"
                >
                    <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-slate-400">
                    Page {page} of {totalPages}
                </span>
                <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn btn-secondary disabled:opacity-50"
                >
                    <ChevronRight className="w-5 h-5" />
                </button>
            </div>

            {/* Annotation Modal */}
            {selectedRule && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-auto">
                        <div className="p-6 border-b border-slate-700">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-semibold text-white">Annotate Rule</h2>
                                <button onClick={() => setSelectedRule(null)} className="text-slate-400 hover:text-white">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                        </div>

                        <div className="p-6 space-y-6">
                            <div>
                                <label className="text-sm text-slate-400">Rule ID</label>
                                <p className="text-blue-400 font-mono">{selectedRule.id}</p>
                            </div>

                            <div>
                                <label className="text-sm text-slate-400">Original Text</label>
                                <p className="text-white mt-1 p-4 bg-slate-800 rounded-lg">{selectedRule.original_text}</p>
                            </div>

                            {selectedRule.fol?.deontic_formula && (
                                <div>
                                    <label className="text-sm text-slate-400">FOL Formula</label>
                                    <code className="block text-green-400 mt-1 p-4 bg-slate-800 rounded-lg font-mono text-sm">
                                        {selectedRule.fol.deontic_formula}
                                    </code>
                                </div>
                            )}

                            <div className="grid grid-cols-3 gap-4">
                                {['obligation', 'permission', 'prohibition'].map(type => (
                                    <button
                                        key={type}
                                        onClick={() => handleAnnotate(selectedRule.id, { is_rule: true, rule_type: type, confidence: 5 })}
                                        disabled={annotating}
                                        className={`p-4 rounded-xl border-2 transition-all ${type === 'obligation' ? 'border-red-500/50 hover:bg-red-500/20' :
                                                type === 'permission' ? 'border-green-500/50 hover:bg-green-500/20' :
                                                    'border-orange-500/50 hover:bg-orange-500/20'
                                            }`}
                                    >
                                        <span className={`font-semibold ${type === 'obligation' ? 'text-red-400' :
                                                type === 'permission' ? 'text-green-400' :
                                                    'text-orange-400'
                                            }`}>
                                            {type.charAt(0).toUpperCase() + type.slice(1)}
                                        </span>
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => handleAnnotate(selectedRule.id, { is_rule: false, rule_type: null, confidence: 5 })}
                                disabled={annotating}
                                className="w-full btn btn-secondary"
                            >
                                Not a Rule
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
