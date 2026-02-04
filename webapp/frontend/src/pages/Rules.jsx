import { useState, useEffect } from 'react'
import { Search, FileText, Filter } from 'lucide-react'
import axios from 'axios'

export default function Rules() {
    const [rulesData, setRulesData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')
    const [filterType, setFilterType] = useState('All')

    useEffect(() => {
        fetchRules()
    }, [])

    const fetchRules = async () => {
        try {
            const res = await axios.get('/api/rules?per_page=100')
            console.log('Rules API response:', res.data)
            setRulesData(res.data)
        } catch (err) {
            console.error('Failed to fetch rules:', err)
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

    const rules = rulesData?.rules || []

    const filteredRules = rules.filter(rule => {
        const ruleText = rule.text || rule.original_text || ''
        const ruleId = rule.id || rule.rule_id || ''
        const matchesSearch = ruleText.toLowerCase().includes(searchTerm.toLowerCase()) ||
            ruleId.toLowerCase().includes(searchTerm.toLowerCase())

        // Get deontic type from either direct field or nested in fol
        const deonticType = rule.deontic_type || rule.fol?.deontic_type || rule.llm_classification
        const matchesFilter = filterType === 'All' || deonticType === filterType

        return matchesSearch && matchesFilter
    })

    // Count by type
    const typeCounts = {
        All: rules.length,
        Obligation: rules.filter(r => {
            const type = r.deontic_type || r.fol?.deontic_type || r.llm_classification
            return type === 'Obligation'
        }).length,
        Permission: rules.filter(r => {
            const type = r.deontic_type || r.fol?.deontic_type || r.llm_classification
            return type === 'Permission'
        }).length,
        Prohibition: rules.filter(r => {
            const type = r.deontic_type || r.fol?.deontic_type || r.llm_classification
            return type === 'Prohibition'
        }).length
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <FileText className="w-10 h-10 text-blue-600" />
                    Rules Browser
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    {rules.length} annotated policy rules from AIT Student Handbook
                </p>
            </div>

            {/* Filters */}
            <div className="card">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <Search className="w-4 h-4 inline mr-1" />
                            Search Rules
                        </label>
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search by rule ID or text..."
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            <Filter className="w-4 h-4 inline mr-1" />
                            Filter by Type
                        </label>
                        <div className="flex gap-2">
                            {['All', 'Obligation', 'Permission', 'Prohibition'].map(type => (
                                <button
                                    key={type}
                                    onClick={() => setFilterType(type)}
                                    className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${filterType === type
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        }`}
                                >
                                    {type} ({typeCounts[type]})
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4">
                <div className="card text-center bg-gray-50">
                    <div className="text-3xl font-bold text-gray-700">{filteredRules.length}</div>
                    <div className="text-sm text-gray-600 mt-1">Showing</div>
                </div>
                <div className="card text-center bg-red-50">
                    <div className="text-3xl font-bold text-red-600">{typeCounts.Obligation}</div>
                    <div className="text-sm text-red-600 mt-1 font-medium">Obligations</div>
                </div>
                <div className="card text-center bg-green-50">
                    <div className="text-3xl font-bold text-green-600">{typeCounts.Permission}</div>
                    <div className="text-sm text-green-600 mt-1 font-medium">Permissions</div>
                </div>
                <div className="card text-center bg-orange-50">
                    <div className="text-3xl font-bold text-orange-600">{typeCounts.Prohibition}</div>
                    <div className="text-sm text-orange-600 mt-1 font-medium">Prohibitions</div>
                </div>
            </div>

            {/* Rules List */}
            <div className="space-y-3">
                {filteredRules.map((rule, idx) => {
                    const deonticType = rule.deontic_type || rule.fol?.deontic_type || rule.llm_classification || 'Unknown'
                    const ruleId = rule.id || rule.rule_id || `R${idx + 1}`
                    const ruleText = rule.text || rule.original_text || 'No text available'
                    const folFormula = rule.fol?.fol_formula || rule.fol_formula || rule.fol?.formula

                    return (
                        <div key={idx} className="card hover:shadow-lg transition-shadow">
                            <div className="flex items-start gap-4">
                                <div className="flex-shrink-0">
                                    <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center font-bold text-blue-700 text-sm">
                                        {ruleId}
                                    </div>
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${deonticType === 'Obligation' ? 'bg-red-100 text-red-700' :
                                                deonticType === 'Permission' ? 'bg-green-100 text-green-700' :
                                                    deonticType === 'Prohibition' ? 'bg-orange-100 text-orange-700' :
                                                        'bg-gray-100 text-gray-700'
                                            }`}>
                                            {deonticType}
                                        </span>
                                        {rule.llm_classification && (
                                            <span className="px-3 py-1 rounded-full text-xs bg-purple-100 text-purple-700 font-semibold">
                                                LLM: {rule.llm_classification}
                                            </span>
                                        )}
                                        {rule.human_annotation && (
                                            <span className="px-3 py-1 rounded-full text-xs bg-blue-100 text-blue-700 font-semibold">
                                                Human: {rule.human_annotation}
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-gray-800 leading-relaxed mb-2">{ruleText}</p>
                                    {folFormula && (
                                        <div className="mt-3 p-3 bg-gray-900 text-gray-100 rounded-lg font-mono text-sm overflow-x-auto">
                                            {folFormula}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {filteredRules.length === 0 && (
                <div className="card text-center py-12">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">
                        {rules.length === 0
                            ? 'No rules loaded from the backend'
                            : 'No rules found matching your criteria'}
                    </p>
                    {rules.length === 0 && (
                        <p className="text-sm text-gray-400 mt-2">
                            Check that the backend is running and the API endpoint is accessible
                        </p>
                    )}
                </div>
            )}
        </div>
    )
}
