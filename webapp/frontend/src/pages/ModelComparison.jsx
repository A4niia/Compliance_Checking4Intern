import { useState } from 'react'
import {
    BarChart3, Brain, Zap, Clock, CheckCircle, XCircle,
    ChevronDown, ChevronUp, Play, RefreshCw
} from 'lucide-react'
import axios from 'axios'

const AVAILABLE_MODELS = [
    { id: 'glm-4.7-flash', name: 'GLM 4.7 Flash', size: '19 GB', context: '64k', recommended: true },
    { id: 'mistral', name: 'Mistral 7B', size: '4.4 GB', context: '32k', recommended: false },
    { id: 'mixtral', name: 'Mixtral', size: '26 GB', context: '32k', recommended: false },
    { id: 'qwen3:32b', name: 'Qwen3 32B', size: '20 GB', context: '32k', recommended: false },
    { id: 'qwen2.5:32b-instruct', name: 'Qwen2.5 Instruct', size: '19 GB', context: '32k', recommended: false },
    { id: 'llama3.1:70b', name: 'Llama 3.1 70B', size: '42 GB', context: '128k', recommended: false },
    { id: 'llama3.2', name: 'Llama 3.2', size: '2 GB', context: '8k', recommended: false },
    { id: 'phi3', name: 'Phi3', size: '2.2 GB', context: '4k', recommended: false },
    // NEW MODELS
    { id: 'deepseek-r1:70b', name: 'DeepSeek-R1 70B', size: '42 GB', context: '64k', recommended: true },
    { id: 'gemma2:27b', name: 'Gemma 2 27B', size: '16 GB', context: '8k', recommended: false },
    { id: 'codestral', name: 'Codestral', size: '12 GB', context: '32k', recommended: false },
    { id: 'granite3.2:8b', name: 'Granite 3.2 8B', size: '5 GB', context: '128k', recommended: false },
]

const SAMPLE_RULES = [
    "Students must pay all outstanding fees before registering for the next semester.",
    "Faculty members may request sabbatical leave after five years of service.",
    "Research data cannot be shared with external parties without prior approval.",
    "All graduate students are required to complete a thesis defense before graduation.",
]

export default function ModelComparison() {
    const [selectedModels, setSelectedModels] = useState(['glm-4.7-flash', 'mistral', 'qwen3:32b'])
    const [testText, setTestText] = useState(SAMPLE_RULES[0])
    const [task, setTask] = useState('classification')
    const [results, setResults] = useState(null)
    const [running, setRunning] = useState(false)
    const [expandedModel, setExpandedModel] = useState(null)

    const toggleModel = (modelId) => {
        setSelectedModels(prev =>
            prev.includes(modelId)
                ? prev.filter(m => m !== modelId)
                : [...prev, modelId]
        )
    }

    const runComparison = async () => {
        if (selectedModels.length === 0) return
        setRunning(true)
        setResults(null)

        // Simulate API call for comparison
        await new Promise(r => setTimeout(r, 2000))

        // Mock results
        const mockResults = {}
        for (const model of selectedModels) {
            const isRule = Math.random() > 0.2
            mockResults[model] = {
                success: true,
                duration: (Math.random() * 5 + 1).toFixed(2),
                classification: {
                    is_rule: isRule,
                    confidence: (0.85 + Math.random() * 0.14).toFixed(2),
                    rule_type: isRule ? ['obligation', 'permission', 'prohibition'][Math.floor(Math.random() * 3)] : null,
                    reasoning: isRule
                        ? 'Contains "must" which is an obligation marker'
                        : 'No deontic markers found',
                    deontic_markers: isRule ? ['must'] : []
                }
            }
        }

        setResults(mockResults)
        setRunning(false)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
                    <BarChart3 className="w-8 h-8 text-blue-600" />
                    Model Comparison
                </h1>
                <p className="text-slate-500 mt-1">Compare LLM performance on classification and formalization tasks</p>
            </div>

            {/* Model Selection */}
            <div className="card">
                <h2 className="text-lg font-semibold text-slate-800 mb-4">Select Models to Compare</h2>
                <div className="grid grid-cols-4 gap-3">
                    {AVAILABLE_MODELS.map(model => (
                        <div
                            key={model.id}
                            onClick={() => toggleModel(model.id)}
                            className={`p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedModels.includes(model.id)
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-slate-200 hover:border-slate-300'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={selectedModels.includes(model.id)}
                                    readOnly
                                    className="w-4 h-4 text-blue-600"
                                />
                                <span className="font-medium text-slate-800">{model.name}</span>
                                {model.recommended && (
                                    <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded">★</span>
                                )}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {model.size} • {model.context} context
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Test Input */}
            <div className="card">
                <h2 className="text-lg font-semibold text-slate-800 mb-4">Test Input</h2>

                <div className="flex gap-4 mb-4">
                    <select
                        value={task}
                        onChange={(e) => setTask(e.target.value)}
                        className="px-4 py-2 border border-slate-200 rounded-lg"
                    >
                        <option value="classification">Classification (RQ1)</option>
                        <option value="formalization">Formalization (RQ2)</option>
                    </select>

                    <select
                        value={testText}
                        onChange={(e) => setTestText(e.target.value)}
                        className="flex-1 px-4 py-2 border border-slate-200 rounded-lg"
                    >
                        {SAMPLE_RULES.map((rule, i) => (
                            <option key={i} value={rule}>{rule.substring(0, 60)}...</option>
                        ))}
                    </select>
                </div>

                <textarea
                    value={testText}
                    onChange={(e) => setTestText(e.target.value)}
                    rows={3}
                    className="w-full p-4 border border-slate-200 rounded-lg text-slate-700"
                    placeholder="Enter text to classify..."
                />

                <button
                    onClick={runComparison}
                    disabled={running || selectedModels.length === 0}
                    className="btn btn-primary mt-4 flex items-center gap-2"
                >
                    {running ? (
                        <><RefreshCw className="w-5 h-5 animate-spin" /> Running {selectedModels.length} models...</>
                    ) : (
                        <><Play className="w-5 h-5" /> Run Comparison</>
                    )}
                </button>
            </div>

            {/* Results */}
            {results && (
                <div className="card">
                    <h2 className="text-lg font-semibold text-slate-800 mb-4">Comparison Results</h2>

                    <div className="space-y-3">
                        {Object.entries(results).map(([modelId, result]) => {
                            const model = AVAILABLE_MODELS.find(m => m.id === modelId)
                            const isExpanded = expandedModel === modelId

                            return (
                                <div key={modelId} className="border border-slate-200 rounded-xl overflow-hidden">
                                    <div
                                        className="p-4 flex items-center gap-4 cursor-pointer hover:bg-slate-50"
                                        onClick={() => setExpandedModel(isExpanded ? null : modelId)}
                                    >
                                        {/* Status */}
                                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${result.classification.is_rule ? 'bg-green-100' : 'bg-slate-100'
                                            }`}>
                                            {result.classification.is_rule ? (
                                                <CheckCircle className="w-5 h-5 text-green-600" />
                                            ) : (
                                                <XCircle className="w-5 h-5 text-slate-400" />
                                            )}
                                        </div>

                                        {/* Model Info */}
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2">
                                                <span className="font-semibold text-slate-800">{model?.name}</span>
                                                {model?.recommended && (
                                                    <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded">Recommended</span>
                                                )}
                                            </div>
                                            <div className="text-sm text-slate-500">
                                                {result.classification.is_rule ? (
                                                    <span className="text-green-600">✓ Is Rule ({result.classification.rule_type})</span>
                                                ) : (
                                                    <span className="text-slate-500">✗ Not a Rule</span>
                                                )}
                                                <span className="mx-2">•</span>
                                                Confidence: {(parseFloat(result.classification.confidence) * 100).toFixed(0)}%
                                            </div>
                                        </div>

                                        {/* Duration */}
                                        <div className="text-sm text-slate-500 flex items-center gap-1">
                                            <Clock className="w-4 h-4" />
                                            {result.duration}s
                                        </div>

                                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                    </div>

                                    {isExpanded && (
                                        <div className="p-4 bg-slate-50 border-t border-slate-100">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <h4 className="text-sm font-semibold text-slate-600 mb-2">Reasoning</h4>
                                                    <p className="text-sm text-slate-700">{result.classification.reasoning}</p>
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-semibold text-slate-600 mb-2">Deontic Markers</h4>
                                                    <div className="flex gap-2">
                                                        {result.classification.deontic_markers.length > 0 ? (
                                                            result.classification.deontic_markers.map((m, i) => (
                                                                <span key={i} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm">{m}</span>
                                                            ))
                                                        ) : (
                                                            <span className="text-sm text-slate-500">None found</span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>

                    {/* Summary */}
                    <div className="mt-4 p-4 bg-blue-50 rounded-xl">
                        <h3 className="font-semibold text-blue-800 mb-2">Summary</h3>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <span className="text-blue-600">Models Tested:</span>
                                <span className="ml-2 font-semibold">{Object.keys(results).length}</span>
                            </div>
                            <div>
                                <span className="text-blue-600">Agreement:</span>
                                <span className="ml-2 font-semibold">
                                    {Object.values(results).filter(r => r.classification.is_rule).length}/{Object.keys(results).length} say "Is Rule"
                                </span>
                            </div>
                            <div>
                                <span className="text-blue-600">Fastest:</span>
                                <span className="ml-2 font-semibold">
                                    {Object.entries(results).sort((a, b) => parseFloat(a[1].duration) - parseFloat(b[1].duration))[0]?.[0]}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
