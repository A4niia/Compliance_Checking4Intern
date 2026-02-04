import { useState, useEffect } from 'react'
import { Code, Search, Eye } from 'lucide-react'
import axios from 'axios'

export default function FOLViewer() {
    const [formulas, setFormulas] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedFormula, setSelectedFormula] = useState(null)

    useEffect(() => {
        fetchFormulas()
    }, [])

    const fetchFormulas = async () => {
        try {
            const res = await axios.get('/api/fol-results')
            setFormulas(res.data)
        } catch (err) {
            console.error('Failed to fetch FOL formulas:', err)
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
        <div className="space-y-6">
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <Code className="w-10 h-10 text-green-600" />
                    First-Order Logic Formulas
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    97 policy rules formalized in first-order logic (100% success rate)
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <div className="card bg-green-50 text-center">
                    <div className="text-4xl font-bold text-green-700">{formulas.length}</div>
                    <div className="text-sm text-green-600 mt-1 font-medium">Total Formulas</div>
                </div>
                <div className="card bg-blue-50 text-center">
                    <div className="text-4xl font-bold text-blue-700">100%</div>
                    <div className="text-sm text-blue-600 mt-1 font-medium">Success Rate</div>
                </div>
                <div className="card bg-purple-50 text-center">
                    <div className="text-4xl font-bold text-purple-700">0</div>
                    <div className="text-sm text-purple-600 mt-1 font-medium">HOL Needed</div>
                </div>
            </div>

            {/* Key Finding */}
            <div className="card bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-500">
                <h3 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
                    <Code className="w-5 h-5" />
                    Research Finding (RQ2)
                </h3>
                <p className="text-green-700">
                    <strong>FOL is sufficient</strong> for institutional policy formalization. No higher-order logic required.
                </p>
            </div>

            {/* Formula List */}
            <div className="grid grid-cols-2 gap-4">
                {formulas.slice(0, 20).map((formula, idx) => (
                    <div
                        key={idx}
                        className="card hover:shadow-lg transition-all cursor-pointer"
                        onClick={() => setSelectedFormula(formula)}
                    >
                        <div className="flex items-start gap-3 mb-3">
                            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center font-bold text-green-700">
                                {idx + 1}
                            </div>
                            <div className="flex-1">
                                <div className="text-sm text-gray-600 mb-1">{formula.rule_id || `Rule ${idx + 1}`}</div>
                                <div className={`inline-block px-2 py-1 rounded text-xs font-semibold ${formula.deontic_type === 'Obligation' ? 'bg-red-100 text-red-700' :
                                        formula.deontic_type === 'Permission' ? 'bg-green-100 text-green-700' :
                                            'bg-orange-100 text-orange-700'
                                    }`}>
                                    {formula.deontic_type}
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-900 text-gray-100 p-3 rounded-lg font-mono text-xs overflow-x-auto">
                            {formula.fol_formula || formula.formula || 'No formula available'}
                        </div>
                        <div className="mt-3 text-xs text-blue-600 flex items-center gap-1">
                            <Eye className="w-3 h-3" />
                            Click to view details
                        </div>
                    </div>
                ))}
            </div>

            {formulas.length === 0 && (
                <div className="card text-center py-12">
                    <Code className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No FOL formulas available</p>
                </div>
            )}

            {/* Modal */}
            {selectedFormula && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedFormula(null)}>
                    <div className="bg-white rounded-xl max-w-3xl w-full p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-2xl font-bold text-gray-800">Formula Details</h2>
                            <button onClick={() => setSelectedFormula(null)} className="text-gray-400 hover:text-gray-600">
                                ✕
                            </button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-semibold text-gray-700">Rule ID:</label>
                                <div className="text-gray-800">{selectedFormula.rule_id || 'N/A'}</div>
                            </div>
                            <div>
                                <label className="text-sm font-semibold text-gray-700">Deontic Type:</label>
                                <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mt-1 ${selectedFormula.deontic_type === 'Obligation' ? 'bg-red-100 text-red-700' :
                                        selectedFormula.deontic_type === 'Permission' ? 'bg-green-100 text-green-700' :
                                            'bg-orange-100 text-orange-700'
                                    }`}>
                                    {selectedFormula.deontic_type}
                                </div>
                            </div>
                            <div>
                                <label className="text-sm font-semibold text-gray-700">FOL Formula:</label>
                                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm mt-2 overflow-x-auto">
                                    {selectedFormula.fol_formula || selectedFormula.formula}
                                </div>
                            </div>
                            {selectedFormula.original_text && (
                                <div>
                                    <label className="text-sm font-semibold text-gray-700">Original Text:</label>
                                    <div className="text-gray-800 mt-1">{selectedFormula.original_text}</div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
