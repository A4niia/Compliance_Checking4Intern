import { TrendingUp, Brain, Code, Shield, CheckCircle, BarChart3, Zap, Award, Target } from 'lucide-react'

export default function Results() {
    const models = [
        { name: 'Mistral-7B', accuracy: 99.0, f1: 95.1, winner: true },
        { name: 'Llama-70B', accuracy: 92.8, f1: 89.2 },
        { name: 'Mixtral', accuracy: 88.7, f1: 84.3 },
        { name: 'Phi-3', accuracy: 82.3, f1: 78.5 }
    ]

    const ablation = [
        { experiment: 'Baseline', accuracy: 0, color: 'gray' },
        { experiment: 'E1: Explicit Definition', accuracy: 70, color: 'green', improvement: '+33.6pp' },
        { experiment: 'E2: With Context', accuracy: 70, color: 'green' },
        { experiment: 'E3: Contrastive Examples', accuracy: 30, color: 'orange' }
    ]

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <Award className="w-10 h-10 text-blue-600" />
                    Research Results & Validation
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    Comprehensive evaluation of the automated policy formalization pipeline
                </p>
            </div>

            {/* Key Findings */}
            <div className="grid grid-cols-3 gap-4">
                <div className="card bg-gradient-to-br from-purple-50 to-purple-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Brain className="w-8 h-8 text-purple-700" />
                        <div className="text-sm font-semibold text-purple-700">RQ1 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-purple-700">99% Accuracy</div>
                    <p className="text-sm text-purple-600 mt-1">Mistral-7B classification</p>
                </div>
                <div className="card bg-gradient-to-br from-green-50 to-green-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Code className="w-8 h-8 text-green-700" />
                        <div className="text-sm font-semibold text-green-700">RQ2 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-green-700">100% Success</div>
                    <p className="text-sm text-green-600 mt-1">FOL sufficient</p>
                </div>
                <div className="card bg-gradient-to-br from-orange-50 to-orange-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Shield className="w-8 h-8 text-orange-700" />
                        <div className="text-sm font-semibold text-orange-700">RQ3 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-orange-700">1,309 Triples</div>
                    <p className="text-sm text-orange-600 mt-1">SHACL validated</p>
                </div>
            </div>

            {/* Model Comparison */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <BarChart3 className="w-6 h-6 text-blue-600" />
                    <h2 className="text-2xl font-bold text-gray-800">LLM Model Comparison</h2>
                </div>
                <p className="text-gray-600 mb-6">
                    Evaluated 5 LLMs for policy rule classification (97 rules)
                </p>
                <div className="space-y-4">
                    {models.map((model, i) => (
                        <div key={i} className={`p-4 rounded-xl ${model.winner ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'}`}>
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className={`text-lg font-bold ${model.winner ? 'text-green-700' : 'text-gray-800'}`}>
                                        {model.name}
                                    </span>
                                    {model.winner && (
                                        <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 flex items-center gap-1">
                                            <CheckCircle className="w-3 h-3" /> Selected
                                        </span>
                                    )}
                                </div>
                                <div className="text-right">
                                    <div className={`text-2xl font-bold ${model.winner ? 'text-green-700' : 'text-gray-700'}`}>
                                        {model.accuracy}%
                                    </div>
                                    <div className="text-sm text-gray-500">F1: {model.f1}%</div>
                                </div>
                            </div>
                            <div className="progress-bar-container h-3">
                                <div className="progress-bar-fill" style={{ width: `${model.accuracy}%` }}></div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                    <strong>Key Finding:</strong> Mistral-7B outperformed Llama-70B despite being 10× smaller
                </div>
            </div>

            {/* Ablation Study */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <Target className="w-6 h-6 text-blue-600" />
                    <h2 className="text-2xl font-bold text-gray-800">Permission Classification Challenge</h2>
                </div>
                <p className="text-gray-600 mb-6">
                    Systematic ablation study (0% → 70% improvement)
                </p>
                <div className="space-y-4">
                    {ablation.map((result, i) => (
                        <div key={i}>
                            <div className="flex items-center gap-4 mb-2">
                                <div className="w-48 font-medium text-gray-700">{result.experiment}</div>
                                <div className="flex-1">
                                    <div className="progress-bar-container h-10">
                                        <div
                                            className={`h-full rounded-full ${result.color === 'green' ? 'bg-gradient-to-r from-green-500 to-green-600' : result.color === 'orange' ? 'bg-gradient-to-r from-orange-400 to-orange-500' : 'bg-gray-300'}`}
                                            style={{ width: `${result.accuracy}%` }}
                                        />
                                    </div>
                                </div>
                                <div className="w-24 text-right">
                                    <div className={`text-2xl font-bold ${result.accuracy === 0 ? 'text-red-600' : result.accuracy >= 70 ? 'text-green-600' : 'text-orange-600'}`}>
                                        {result.accuracy}%
                                    </div>
                                    {result.improvement && (
                                        <div className="text-sm text-green-600 font-semibold">{result.improvement}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-500 rounded">
                    <strong>Statistical Significance:</strong> Cohen's h = 1.98, p = 0.023
                </div>
            </div>

            {/* FOL & SHACL */}
            <div className="grid grid-cols-2 gap-6">
                <div className="card">
                    <div className="flex items-center gap-3 mb-4">
                        <Code className="w-6 h-6 text-green-600" />
                        <h2 className="text-xl font-bold text-gray-800">FOL Formalization</h2>
                    </div>
                    <div className="text-4xl font-bold text-green-600 mb-2">100%</div>
                    <p className="text-gray-600 mb-4">Success (97/97 rules)</p>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>Obligations:</span>
                            <span className="font-bold text-red-600">65 rules</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Permissions:</span>
                            <span className="font-bold text-green-600">17 rules</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Prohibitions:</span>
                            <span className="font-bold text-orange-600">15 rules</span>
                        </div>
                    </div>
                </div>
                <div className="card">
                    <div className="flex items-center gap-3 mb-4">
                        <Shield className="w-6 h-6 text-blue-600" />
                        <h2 className="text-xl font-bold text-gray-800">SHACL Translation</h2>
                    </div>
                    <div className="text-4xl font-bold text-blue-600 mb-2">1,309</div>
                    <p className="text-gray-600 mb-4">RDF triples</p>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>SHACL Shapes:</span>
                            <span className="font-bold">97</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>W3C Validation:</span>
                            <span className="font-bold text-green-600">✓ Passed</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Target Classes:</span>
                            <span className="font-bold">12</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Key Contributions */}
            <div className="card bg-gradient-to-br from-blue-50 to-gray-50">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <Zap className="w-6 h-6 text-blue-600" />
                    Key Research Contributions
                </h2>
                <div className="grid gap-4">
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>Mistral-7B achieves 99%</strong> accuracy, outperforming larger models</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>FOL is sufficient</strong> for institutional policies (no HOL needed)</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>Permission challenge solved</strong> (0% → 70%, p = 0.023)</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>Automated FOL → SHACL</strong> produces 1,309 W3C-compliant triples</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>Text simplification</strong> improves accuracy by +15pp (88% of rules)</div>
                    </div>
                </div>
            </div>
        </div>
    )
}
