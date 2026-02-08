import { TrendingUp, Brain, Code, Shield, CheckCircle, BarChart3, Zap, Award, Target, Activity, Timer, Hash, AlertTriangle, RefreshCw } from 'lucide-react'

export default function Results() {
    // ═══════════════════════════════════════════
    //  V4 Pipeline Data (from irr_metrics.json)
    // ═══════════════════════════════════════════
    const irr = {
        kappa: 0.8503,
        interpretation: 'Almost Perfect Agreement',
        accuracy: 95.88,
        precision: 97.53,
        recall: 97.53,
        f1: 97.53,
        totalSentences: 97,  // Candidate sentences extracted
        validatedRules: 83,  // Confirmed as policy rules
        matrix: { tp: 79, tn: 14, fp: 2, fn: 2 },  // tn=14 are non-rules
        thresholdMet: true
    }

    const typeAgreement = [
        { type: 'Obligation', agree: 41, disagree: 5, color: 'red', emoji: '⚡' },
        { type: 'Permission', agree: 14, disagree: 14, color: 'green', emoji: '✋' },
        { type: 'Prohibition', agree: 5, disagree: 0, color: 'orange', emoji: '🚫' }
    ]

    const journey = [
        { version: 'v2', label: 'Baseline', kappa: 0.50, accuracy: 83.5, errors: 16, color: 'red' },
        { version: 'v3', label: 'Prompt + Post‑processing', kappa: 0.606, accuracy: 89.69, errors: 10, color: 'yellow' },
        { version: 'v4', label: 'Option C (Annotations + Code)', kappa: 0.8503, accuracy: 95.88, errors: 4, color: 'green' }
    ]

    const reproducibility = {
        totalRuns: 10,
        successfulRuns: 10,
        allIdentical: true,
        finalHash: '520a0fa978c4aabd',
        meanTime: 123.17,
        phases: {
            extraction: { mean: 0.001, label: 'Extraction' },
            classification: { mean: 45.70, label: 'Classification (LLM)' },
            fol: { mean: 77.45, label: 'FOL Generation (LLM)' },
            shacl: { mean: 0.004, label: 'SHACL Translation' },
            validation: { mean: 0.01, label: 'Validation' }
        }
    }

    const disagreements = [
        { id: 'GS-033', human: true, llm: false, text: '"Direct communication may sometimes follow consultation..."', nature: 'Weak deontic — "may sometimes"' },
        { id: 'GS-035', human: false, llm: true, text: '"If equally qualified, the student who has been at AIT longer should receive preference"', nature: 'Advisory vs normative "should"' },
        { id: 'GS-049', human: true, llm: false, text: '"Notes of the interview...should be agreed upon by all parties"', nature: 'LLM filtered by "should" heuristic' },
        { id: 'GS-070', human: false, llm: true, text: '"The appeal should be addressed to the VP for Academic Affairs"', nature: 'Advisory vs procedural "should"' }
    ]

    const kappaScale = [
        { range: '< 0', label: 'Poor', active: false },
        { range: '0.00–0.20', label: 'Slight', active: false },
        { range: '0.21–0.40', label: 'Fair', active: false },
        { range: '0.41–0.60', label: 'Moderate', active: false },
        { range: '0.61–0.80', label: 'Substantial', active: false },
        { range: '0.81–1.00', label: 'Almost Perfect', active: true }
    ]

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <Award className="w-10 h-10 text-blue-600" />
                    Pipeline Results & Validation
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    Inter-rater reliability, reproducibility, and classification metrics — v4 (Option C)
                </p>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 1 — KPI CARDS                       */}
            {/* ═══════════════════════════════════════ */}
            <div className="grid grid-cols-4 gap-4">
                <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200">
                    <div className="flex items-center gap-2 mb-1">
                        <Brain className="w-5 h-5 text-purple-600" />
                        <span className="text-xs font-bold text-purple-600 uppercase tracking-wider">Cohen's Kappa</span>
                    </div>
                    <div className="text-4xl font-black text-purple-700">κ = {irr.kappa.toFixed(4)}</div>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-purple-200 text-purple-800">
                            {irr.interpretation}
                        </span>
                        <CheckCircle className="w-4 h-4 text-green-600" />
                    </div>
                </div>
                <div className="card bg-gradient-to-br from-green-50 to-green-100 border border-green-200">
                    <div className="flex items-center gap-2 mb-1">
                        <Target className="w-5 h-5 text-green-600" />
                        <span className="text-xs font-bold text-green-600 uppercase tracking-wider">Accuracy</span>
                    </div>
                    <div className="text-4xl font-black text-green-700">{irr.accuracy}%</div>
                    <div className="text-sm text-green-600 mt-1">Target ≥95% <CheckCircle className="w-4 h-4 inline text-green-600" /></div>
                </div>
                <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
                    <div className="flex items-center gap-2 mb-1">
                        <BarChart3 className="w-5 h-5 text-blue-600" />
                        <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">F1-Score</span>
                    </div>
                    <div className="text-4xl font-black text-blue-700">{irr.f1}%</div>
                    <div className="text-sm text-blue-600 mt-1">P: {irr.precision}% · R: {irr.recall}%</div>
                </div>
                <div className="card bg-gradient-to-br from-teal-50 to-teal-100 border border-teal-200">
                    <div className="flex items-center gap-2 mb-1">
                        <RefreshCw className="w-5 h-5 text-teal-600" />
                        <span className="text-xs font-bold text-teal-600 uppercase tracking-wider">Reproducibility</span>
                    </div>
                    <div className="text-4xl font-black text-teal-700">{reproducibility.successfulRuns}/{reproducibility.totalRuns}</div>
                    <div className="text-sm text-teal-600 mt-1">100% Identical <CheckCircle className="w-4 h-4 inline text-green-600" /></div>
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 2 — CONFUSION MATRIX + KAPPA SCALE  */}
            {/* ═══════════════════════════════════════ */}
            <div className="grid grid-cols-2 gap-6">
                {/* Confusion Matrix */}
                <div className="card">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-blue-600" />
                        Confusion Matrix
                    </h2>
                    <div className="grid grid-cols-3 gap-1 text-center">
                        {/* Header row */}
                        <div></div>
                        <div className="text-xs font-bold text-gray-500 py-2">LLM: Not Rule</div>
                        <div className="text-xs font-bold text-gray-500 py-2">LLM: Is Rule</div>
                        {/* Row 1 */}
                        <div className="text-xs font-bold text-gray-500 flex items-center justify-end pr-3">Human: Not Rule</div>
                        <div className="bg-green-100 border-2 border-green-300 rounded-xl p-4">
                            <div className="text-3xl font-black text-green-700">{irr.matrix.tn}</div>
                            <div className="text-xs text-green-600 font-bold">TN</div>
                        </div>
                        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4">
                            <div className="text-3xl font-black text-red-500">{irr.matrix.fp}</div>
                            <div className="text-xs text-red-500 font-bold">FP</div>
                        </div>
                        {/* Row 2 */}
                        <div className="text-xs font-bold text-gray-500 flex items-center justify-end pr-3">Human: Is Rule</div>
                        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4">
                            <div className="text-3xl font-black text-red-500">{irr.matrix.fn}</div>
                            <div className="text-xs text-red-500 font-bold">FN</div>
                        </div>
                        <div className="bg-green-200 border-2 border-green-400 rounded-xl p-4">
                            <div className="text-3xl font-black text-green-800">{irr.matrix.tp}</div>
                            <div className="text-xs text-green-700 font-bold">TP</div>
                        </div>
                    </div>
                    <div className="mt-3 text-center text-sm text-gray-500">
                        n = {irr.totalRules} annotated gold standard rules
                    </div>
                </div>

                {/* Kappa Scale */}
                <div className="card">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-purple-600" />
                        Cohen's Kappa Scale (Landis & Koch, 1977)
                    </h2>
                    <div className="space-y-2">
                        {kappaScale.map((level, i) => (
                            <div key={i} className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${level.active
                                ? 'bg-purple-100 border-2 border-purple-400 shadow-md'
                                : 'bg-gray-50'
                                }`}>
                                <div className={`w-3 h-3 rounded-full ${level.active ? 'bg-purple-600 ring-4 ring-purple-200' : 'bg-gray-300'}`} />
                                <div className={`w-24 text-sm font-mono ${level.active ? 'font-bold text-purple-700' : 'text-gray-500'}`}>
                                    {level.range}
                                </div>
                                <div className={`flex-1 text-sm ${level.active ? 'font-bold text-purple-700' : 'text-gray-600'}`}>
                                    {level.label}
                                </div>
                                {level.active && (
                                    <span className="text-xs font-bold bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center gap-1">
                                        <CheckCircle className="w-3 h-3" /> Your result
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 3 — IMPROVEMENT JOURNEY             */}
            {/* ═══════════════════════════════════════ */}
            <div className="card">
                <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                    <TrendingUp className="w-6 h-6 text-blue-600" />
                    Improvement Journey
                </h2>
                <p className="text-gray-500 mb-6 text-sm">Iterative refinement across 3 versions</p>

                <div className="overflow-hidden rounded-xl border border-gray-200">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-gray-50 text-left">
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Version</th>
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Changes</th>
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase text-center">Cohen's κ</th>
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase text-center">Accuracy</th>
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase text-center">Errors</th>
                                <th className="px-4 py-3 text-xs font-bold text-gray-500 uppercase">Kappa Progress</th>
                            </tr>
                        </thead>
                        <tbody>
                            {journey.map((v, i) => (
                                <tr key={i} className={`border-t ${v.version === 'v4' ? 'bg-green-50' : ''}`}>
                                    <td className="px-4 py-4">
                                        <span className={`px-2 py-1 rounded text-sm font-bold ${v.color === 'green' ? 'bg-green-100 text-green-700' :
                                            v.color === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                                                'bg-red-100 text-red-700'
                                            }`}>{v.version}</span>
                                    </td>
                                    <td className="px-4 py-4 text-sm text-gray-700">{v.label}</td>
                                    <td className="px-4 py-4 text-center">
                                        <span className="text-lg font-bold text-gray-800">{v.kappa.toFixed(v.kappa < 1 ? (v.kappa === 0.5 ? 2 : 3) : 2)}</span>
                                    </td>
                                    <td className="px-4 py-4 text-center">
                                        <span className={`text-lg font-bold ${v.accuracy >= 95 ? 'text-green-700' : v.accuracy >= 89 ? 'text-yellow-700' : 'text-red-700'}`}>
                                            {v.accuracy}%
                                        </span>
                                    </td>
                                    <td className="px-4 py-4 text-center">
                                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${v.errors <= 5 ? 'bg-green-100 text-green-700' : v.errors <= 10 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                                            }`}>{v.errors}</span>
                                    </td>
                                    <td className="px-4 py-4">
                                        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all duration-1000 ${v.color === 'green' ? 'bg-gradient-to-r from-green-400 to-green-600' :
                                                    v.color === 'yellow' ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' :
                                                        'bg-gradient-to-r from-red-400 to-red-500'
                                                    }`}
                                                style={{ width: `${(v.kappa / 1.0) * 100}%` }}
                                            />
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Target threshold line annotation */}
                <div className="mt-4 flex items-center gap-2 px-4 py-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                    <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <span className="text-sm">
                        <strong>Target met:</strong> κ = 0.8503 exceeds threshold of ≥0.80 (Landis & Koch "Almost perfect agreement")
                    </span>
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 4 — DEONTIC TYPE AGREEMENT          */}
            {/* ═══════════════════════════════════════ */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                    Deontic Type Agreement (Rule Type Classification)
                </h2>
                <div className="space-y-4">
                    {typeAgreement.map((t, i) => {
                        const total = t.agree + t.disagree
                        const pct = total > 0 ? ((t.agree / total) * 100).toFixed(0) : 0
                        return (
                            <div key={i}>
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg">{t.emoji}</span>
                                        <span className="font-bold text-gray-700">{t.type}</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm text-gray-500">{t.agree}/{total}</span>
                                        <span className={`text-xl font-black ${Number(pct) >= 90 ? 'text-green-600' : Number(pct) >= 70 ? 'text-yellow-600' : 'text-red-500'}`}>
                                            {pct}%
                                        </span>
                                    </div>
                                </div>
                                <div className="flex gap-1 h-8 rounded-lg overflow-hidden">
                                    <div
                                        className={`${t.color === 'red' ? 'bg-red-400' : t.color === 'green' ? 'bg-green-400' : 'bg-orange-400'} flex items-center justify-center text-white text-xs font-bold`}
                                        style={{ width: `${(t.agree / total) * 100}%` }}
                                    >
                                        {t.agree} agree
                                    </div>
                                    {t.disagree > 0 && (
                                        <div
                                            className="bg-gray-300 flex items-center justify-center text-gray-600 text-xs font-bold"
                                            style={{ width: `${(t.disagree / total) * 100}%` }}
                                        >
                                            {t.disagree} disagree
                                        </div>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border-l-4 border-yellow-400 text-sm">
                    <AlertTriangle className="w-4 h-4 inline text-yellow-600 mr-1" />
                    <strong>Known limitation:</strong> Permission classification (50%) reflects the inherent ambiguity of "may" in policy text — descriptive vs prescriptive modality.
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 5 — REPRODUCIBILITY                 */}
            {/* ═══════════════════════════════════════ */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <RefreshCw className="w-5 h-5 text-teal-600" />
                    Reproducibility Test (10 Runs)
                </h2>
                <div className="grid grid-cols-2 gap-6">
                    {/* Run Consistency */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-600 mb-3 uppercase tracking-wider">Run Consistency</h3>
                        <div className="grid grid-cols-5 gap-2">
                            {Array.from({ length: 10 }, (_, i) => (
                                <div key={i} className="bg-green-100 border-2 border-green-300 rounded-lg p-3 text-center">
                                    <div className="text-xs text-green-600 font-bold">Run {i + 1}</div>
                                    <CheckCircle className="w-5 h-5 text-green-600 mx-auto mt-1" />
                                </div>
                            ))}
                        </div>
                        <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                            <Hash className="w-4 h-4" />
                            <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{reproducibility.finalHash}</span>
                            <span>— identical across all runs</span>
                        </div>
                    </div>

                    {/* Phase Timing */}
                    <div>
                        <h3 className="text-sm font-bold text-gray-600 mb-3 uppercase tracking-wider">Phase Timing Breakdown</h3>
                        <div className="space-y-3">
                            {Object.values(reproducibility.phases).map((phase, i) => {
                                const pct = (phase.mean / reproducibility.meanTime) * 100
                                return (
                                    <div key={i}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-gray-700">{phase.label}</span>
                                            <span className="font-mono font-bold text-gray-800">{phase.mean.toFixed(phase.mean < 1 ? 3 : 1)}s</span>
                                        </div>
                                        <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                                            <div
                                                className="h-full rounded-full bg-gradient-to-r from-teal-400 to-teal-600"
                                                style={{ width: `${Math.max(pct, 1)}%` }}
                                            />
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                        <div className="mt-3 flex items-center gap-2 text-sm">
                            <Timer className="w-4 h-4 text-gray-500" />
                            <span className="text-gray-600">Mean total: <strong>{reproducibility.meanTime}s</strong> per run</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 6 — REMAINING DISAGREEMENTS         */}
            {/* ═══════════════════════════════════════ */}
            <div className="card">
                <h2 className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                    Remaining Disagreements ({disagreements.length})
                </h2>
                <p className="text-sm text-gray-500 mb-4">
                    All involve the "should" ambiguity — a known challenge in deontic logic
                </p>
                <div className="overflow-hidden rounded-xl border border-gray-200">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-gray-50">
                                <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Rule ID</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Text</th>
                                <th className="px-4 py-3 text-center text-xs font-bold text-gray-500 uppercase">Human</th>
                                <th className="px-4 py-3 text-center text-xs font-bold text-gray-500 uppercase">LLM</th>
                                <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase">Nature</th>
                            </tr>
                        </thead>
                        <tbody>
                            {disagreements.map((d, i) => (
                                <tr key={i} className="border-t hover:bg-gray-50">
                                    <td className="px-4 py-3 font-mono font-bold text-purple-700">{d.id}</td>
                                    <td className="px-4 py-3 text-gray-700 max-w-xs truncate italic">{d.text}</td>
                                    <td className="px-4 py-3 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${d.human ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                            {d.human ? 'Rule' : 'Not rule'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${d.llm ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
                                            {d.llm ? 'Rule' : 'Not rule'}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-gray-600">{d.nature}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* ═══════════════════════════════════════ */}
            {/* ROW 7 — RESEARCH CONTRIBUTIONS           */}
            {/* ═══════════════════════════════════════ */}
            <div className="card bg-gradient-to-br from-blue-50 to-gray-50">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <Zap className="w-6 h-6 text-blue-600" />
                    Key Research Contributions
                </h2>
                <div className="grid gap-4">
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>κ = 0.8503 (Almost Perfect Agreement)</strong> — LLM classifications are highly reliable for policy rule identification</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>95.88% accuracy, 97.53% F1</strong> — exceeding all target thresholds</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>100% reproducible</strong> — 10/10 runs produce identical SHACL output</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>Iterative refinement documented</strong> — v2 → v3 → v4 shows systematic improvement methodology</div>
                    </div>
                    <div className="flex gap-3">
                        <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div><strong>"Should" ambiguity identified</strong> as the primary remaining challenge in deontic classification</div>
                    </div>
                </div>
            </div>
        </div>
    )
}
