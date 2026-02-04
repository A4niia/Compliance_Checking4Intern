import { useState, useEffect } from 'react'
import {
    TrendingUp, Brain, Code, Shield, CheckCircle, BarChart3,
    Zap, Award, Target
} from 'lucide-react'
import axios from 'axios'

export default function Results() {
    const [modelData, setModelData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Load model comparison and ablation data
        setLoading(false)
    }, [])

    // Model comparison data (from research)
    const models = [
        { name: 'Mistral-7B', accuracy: 99.0, f1: 95.1, winner: true },
        { name: 'Llama-70B', accuracy: 92.8, f1: 89.2 },
        { name: 'Mixtral', accuracy: 88.7, f1: 84.3 },
        { name: 'Gemma', accuracy: 85.6, f1: 81.9 },
        { name: 'Phi-3', accuracy: 82.3, f1: 78.5 }
    ]

    // Ablation study results
    const ablationResults = [
        { experiment: 'Baseline', accuracy: 0, color: 'gray' },
        { experiment: 'E1: Explicit Definition', accuracy: 70, color: 'success', improvement: '+33.6pp' },
        { experiment: 'E2: With Context', accuracy: 70, color: 'success' },
        { experiment: 'E3: Contrastive Examples', accuracy: 30, color: 'warning' }
    ]

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-neutral-800 flex items-center gap-3">
                    <Award className="w-10 h-10 text-primary-600" />
                    Research Results & Validation
                </h1>
                <p className="text-neutral-600 mt-2 text-lg">
                    Comprehensive evaluation of the automated policy formalization pipeline
                </p>
            </div>

            {/* Key Findings Summary */}
            <div className="grid grid-cols-3 gap-4">
                <div className="card bg-gradient-to-br from-primary-50 to-primary-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Brain className="w-8 h-8 text-primary-700" />
                        <div className="text-sm font-semibold text-primary-700">RQ1 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-primary-700">99% Accuracy</div>
                    <p className="text-sm text-primary-600 mt-1">Mistral-7B for rule classification</p>
                </div>

                <div className="card bg-gradient-to-br from-success-50 to-success-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Code className="w-8 h-8 text-success-700" />
                        <div className="text-sm font-semibold text-success-700">RQ2 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-success-700">100% Success</div>
                    <p className="text-sm text-success-600 mt-1">FOL sufficient for all policies</p>
                </div>

                <div className="card bg-gradient-to-br from-warning-50 to-warning-100">
                    <div className="flex items-center gap-3 mb-2">
                        <Shield className="w-8 h-8 text-warning-700" />
                        <div className="text-sm font-semibold text-warning-700">RQ3 ANSWERED</div>
                    </div>
                    <div className="text-3xl font-bold text-warning-700">1,309 Triples</div>
                    <p className="text-sm text-warning-600 mt-1">W3C-compliant SHACL shapes</p>
                </div>
            </div>

            {/* Model Comparison */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <BarChart3 className="w-6 h-6 text-primary-600" />
                    <h2 className="text-2xl font-bold text-neutral-800">LLM Model Comparison</h2>
                </div>
                <p className="text-neutral-600 mb-6">
                    Evaluated 5 state-of-the-art LLMs for policy rule classification
                </p>

                <div className="space-y-4">
                    {models.map((model, index) => (
                        <div key={index} className={`p-4 rounded-xl ${model.winner ? 'bg-success-50 border-2 border-success-500' : 'bg-neutral-50'}`}>
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className={`text-lg font-bold ${model.winner ? 'text-success-700' : 'text-neutral-800'}`}>
                                        {model.name}
                                    </span>
                                    {model.winner && (
                                        <span className="status-badge complete">
                                            <CheckCircle className="w-4 h-4" />
                                            Selected
                                        </span>
                                    )}
                                </div>
                                <div className="text-right">
                                    <div className={`text-2xl font-bold ${model.winner ? 'text-success-700' : 'text-neutral-700'}`}>
                                        {model.accuracy}%
                                    </div>
                                    <div className="text-sm text-neutral-500">F1: {model.f1}%</div>
                                </div>
                            </div>
                            <div className="progress-bar-container h-3">
                                <div
                                    className={`progress-bar-fill ${model.winner ? '' : 'opacity-60'}`}
                                    style={{ width: `${model.accuracy}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>

                <div className="alert alert-info mt-6">
                    <strong>Key Finding:</strong> Mistral-7B outperformed Llama-70B (92.8%) despite being 10× smaller,
                    demonstrating that model efficiency doesn't sacrifice accuracy for this task.
                </div>
            </div>

            {/* Permission Ablation Study */}
            <div className="card">
                <div className="flex items-center gap-3 mb-6">
                    <Target className="w-6 h-6 text-primary-600" />
                    <h2 className="text-2xl font-bold text-neutral-800">Permission Classification Challenge</h2>
                </div>
                <p className="text-neutral-600 mb-6">
                    Systematic ablation study to improve permission vs. prohibition disambiguation
                </p>

                <div className="space-y-4">
                    {ablationResults.map((result, index) => (
                        <div key={index} className="relative">
                            <div className="flex items-center gap-4 mb-2">
                                <div className="w-48 font-medium text-neutral-700">
                                    {result.experiment}
                                </div>
                                <div className="flex-1">
                                    <div className="progress-bar-container h-10">
                                        <div
                                            className={`progress-bar-fill ${result.color === 'success' ? 'bg-gradient-to-r from-success-500 to-success-600' : result.color === 'warning' ? 'bg-gradient-to-r from-warning-400 to-warning-500' : 'bg-gray-300'}`}
                                            style={{ width: `${result.accuracy}%` }}
                                        />
                                    </div>
                                </div>
                                <div className="w-24 text-right">
                                    <div className={`text-2xl font-bold ${result.accuracy === 0 ? 'text-error-600' : result.accuracy >= 70 ? 'text-success-600' : 'text-warning-600'}`}>
                                        {result.accuracy}%
                                    </div>
                                    {result.improvement && (
                                        <div className="text-sm text-success-600 font-semibold">
                                            {result.improvement}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="alert alert-success mt-6">
                    <strong>Statistical Significance:</strong> E1 improvement is statistically significant
                    (Cohen's h = 1.98, p = 0.023). Explicit definition in prompt engineering solved the permission challenge.
                </div>
            </div>

            {/* FOL & SHACL Validation */}
            <div className="grid grid-cols-2 gap-6">
                <div className="card">
                    <div className="flex items-center gap-3 mb-4">
                        <Code className="w-6 h-6 text-success-600" />
                        <h2 className="text-xl font-bold text-neutral-800">FOL Formalization</h2>
                    </div>
                    <div className="text-4xl font-bold text-success-600 mb-2">100%</div>
                    <p className="text-neutral-600 mb-4">Success rate (97/97 rules)</p>

                    <div className="space-y-2 mt-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">Obligations:</span>
                            <span className="font-bold text-error-600">65 rules</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">Permissions:</span>
                            <span className="font-bold text-success-600">17 rules</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">Prohibitions:</span>
                            <span className="font-bold text-warning-600">15 rules</span>
                        </div>
                    </div>

                    <div className="alert alert-success mt-4">
                        No Higher-Order Logic required!
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center gap-3 mb-4">
                        <Shield className="w-6 h-6 text-primary-600" />
                        <h2 className="text-xl font-bold text-neutral-800">SHACL Translation</h2>
                    </div>
                    <div className="text-4xl font-bold text-primary-600 mb-2">1,309</div>
                    <p className="text-neutral-600 mb-4">RDF triples generated</p>

                    <div className="space-y-2 mt-4">
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">SHACL Shapes:</span>
                            <span className="font-bold text-neutral-800">97</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">W3C Validation:</span>
                            <span className="font-bold text-success-600">✓ Passed</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-neutral-600">Target Classes:</span>
                            <span className="font-bold text-neutral-800">12</span>
                        </div>
                    </div>

                    <div className="alert alert-info mt-4">
                        Automated FOL → SHACL translation
                    </div>
                </div>
            </div>

            {/* Research Contributions */}
            <div className="card bg-gradient-to-br from-primary-50 to-neutral-50">
                <h2 className="text-2xl font-bold text-neutral-800 mb-6 flex items-center gap-3">
                    <Zap className="w-6 h-6 text-primary-600" />
                    Key Research Contributions
                </h2>
                <div className="grid gap-4">
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <strong>Mistral-7B achieves 99% accuracy</strong> for policy rule classification,
                            outperforming larger models
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <strong>First-Order Logic is sufficient</strong>  for institutional policy formalization
                            (no HOL needed)
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <strong>Permission challenge solved</strong> through prompt engineering
                            (0% → 70%, statistically significant)
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <strong>Automated FOL → SHACL translation</strong> produces W3C-compliant constraints
                            (1,309 validated triples)
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-success-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <strong>Text simplification improves accuracy</strong> by +15pp
                            (88% of rules affected)
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
