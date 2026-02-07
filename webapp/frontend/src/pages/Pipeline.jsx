import { useState } from 'react'
import { Play, Pause, RotateCcw, CheckCircle, Loader, FileText, Brain, Code, Shield, ArrowRight, Sparkles, AlertTriangle, Database } from 'lucide-react'

export default function Pipeline() {
    const [running, setRunning] = useState(false)
    const [currentPhase, setCurrentPhase] = useState(-1)
    const [progress, setProgress] = useState(0)

    const phases = [
        {
            id: 1,
            name: 'Text Simplification',
            description: 'OCR cleanup & normalization',
            finding: '+15pp accuracy improvement',
            detail: '88% of rules affected, 247 line breaks removed',
            icon: FileText,
            color: 'blue',
            input: {
                title: 'Raw OCR Text',
                content: 'Students must\\nsubmit\\nassignments by\\n5:00\\nPM on the\\ndue date.',
                issues: ['8 line breaks', 'Fragmented text', 'Hard to parse']
            },
            output: {
                title: 'Simplified Text',
                content: 'Students must submit assignments by 5:00 PM on the due date.',
                improvements: ['Single line', 'Clean format', '+15pp accuracy']
            }
        },
        {
            id: 2,
            name: 'LLM Classification',
            description: 'Deontic type identification using Mistral-7B',
            finding: 'Permission challenge solved',
            detail: '0% → 50% (p = 0.023), 95.88% validated accuracy',
            icon: Brain,
            color: 'purple',
            input: {
                title: 'Simplified Rule',
                content: 'Students must submit assignments by 5:00 PM on the due date.',
                task: 'Classify: Obligation, Permission, or Prohibition?'
            },
            output: {
                title: 'LLM Classification',
                content: 'Type: Obligation',
                improvements: ['95.88% accuracy', 'κ = 0.8503', 'Mistral-7B']
            }
        },
        {
            id: 3,
            name: 'FOL Formalization',
            description: 'First-order logic formula generation',
            finding: 'FOL is sufficient',
            detail: '100% success, no HOL needed',
            icon: Code,
            color: 'green',
            input: {
                title: 'Classified Rule',
                content: '[Obligation] Students must submit assignments by 5:00 PM.',
                task: 'Convert to First-Order Logic'
            },
            output: {
                title: 'FOL Formula',
                content: '∀s,a,d (Student(s) ∧ Assignment(a,d) → MustSubmitBy(s,a,"17:00",d))',
                improvements: ['100% success', 'No HOL needed', 'Executable logic']
            }
        },
        {
            id: 4,
            name: 'SHACL Translation',
            description: 'W3C-compliant RDF constraints',
            finding: '1,309 W3C-compliant triples',
            detail: '96 shapes, 12 target classes',
            icon: Shield,
            color: 'orange',
            input: {
                title: 'FOL Formula',
                content: '∀s,a,d (Student(s) ∧ Assignment(a,d) → MustSubmitBy(s,a,"17:00",d))',
                task: 'Convert to SHACL shapes'
            },
            output: {
                title: 'SHACL Shape',
                content: ':SubmissionShape a sh:NodeShape ;\n  sh:targetClass :Assignment ;\n  sh:property [\n    sh:path :submittedAt ;\n    sh:maxInclusive "17:00:00"^^xsd:time\n  ] .',
                improvements: ['W3C valid', '1,309 triples', 'Semantic web ready']
            }
        },
        {
            id: 5,
            name: 'Rule Validation',
            description: 'SHACL-based compliance checking',
            finding: 'Automated policy enforcement',
            detail: 'Real-time validation with human-readable explanations',
            icon: AlertTriangle,
            color: 'red',
            input: {
                title: 'Student Data (RDF)',
                content: ':ST124960 a :Student ;\n  :submitted :A01 .\n:A01 :submittedAt "17:30:00"^^xsd:time ;\n  :deadline "17:00:00"^^xsd:time .',
                task: 'Apply SHACL shape from Phase 4'
            },
            output: {
                title: 'Validation Result + LLM Explanation',
                content: '❌ VIOLATION:\n"Student ST124960 submitted assignment A01 at 5:30 PM, which is 30 minutes after the 5:00 PM deadline. This violates the submission policy."',
                improvements: ['Automated checking', 'LLM-translated', 'Actionable feedback']
            }
        }
    ]

    const handleRun = () => {
        setRunning(true)
        setCurrentPhase(0)
        setProgress(0)

        const interval = setInterval(() => {
            setProgress(p => {
                if (p >= 100) {
                    setCurrentPhase(cp => {
                        if (cp >= 5) {
                            clearInterval(interval)
                            setRunning(false)
                            return cp
                        }
                        setProgress(0)
                        return cp + 1
                    })
                    return 0
                }
                return p + 5
            })
        }, 100)
    }

    const handleReset = () => {
        setRunning(false)
        setCurrentPhase(-1)
        setProgress(0)
    }

    const getPhaseStyle = (idx) => {
        const isComplete = idx < currentPhase || (idx === currentPhase && progress === 100 && running === false)
        const isRunning = idx === currentPhase && running
        const isPending = idx > currentPhase

        return {
            isComplete,
            isRunning,
            isPending
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-gray-800">5-Phase Complete Pipeline</h1>
                    <p className="text-gray-600 mt-2 text-lg">End-to-end: Rule creation → Validation</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleRun}
                        disabled={running}
                        className={`btn ${running ? 'btn-secondary cursor-not-allowed' : 'btn-primary'}`}
                    >
                        {running ? (
                            <>
                                <Loader className="w-5 h-5 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5" />
                                Run Demo
                            </>
                        )}
                    </button>
                    <button onClick={handleReset} className="btn btn-secondary">
                        <RotateCcw className="w-5 h-5" />
                        Reset
                    </button>
                </div>
            </div>

            {/* Overall Progress */}
            <div className="card bg-gradient-to-r from-blue-50 to-purple-50">
                <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-700 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-blue-600" />
                        Overall Pipeline Progress
                    </span>
                    <span className="text-sm text-gray-600 font-mono">
                        {currentPhase === -1 ? 'Ready to start' : `Phase ${currentPhase + 1}/5 • ${Math.round((currentPhase * 20) + (progress / 5))}%`}
                    </span>
                </div>
                <div className="progress-bar-container h-4">
                    <div
                        className={`progress-bar-fill ${running ? 'animated' : ''}`}
                        style={{ width: currentPhase === -1 ? '0%' : `${(currentPhase * 20) + (progress / 5)}%` }}
                    />
                </div>
            </div>

            {/* Phase Visualizations */}
            <div className="space-y-6">
                {phases.map((phase, idx) => {
                    const { isComplete, isRunning, isPending } = getPhaseStyle(idx)
                    const showDemo = isRunning || isComplete

                    return (
                        <div
                            key={phase.id}
                            className={`card border-l-4 transition-all duration-300 ${isComplete ? `border-${phase.color}-500 bg-gradient-to-r from-${phase.color}-50 to-white` :
                                isRunning ? `border-${phase.color}-500 bg-gradient-to-r from-${phase.color}-50 to-white shadow-xl` :
                                    'border-gray-300 bg-gray-50'
                                }`}
                        >
                            {/* Phase Header */}
                            <div className="flex items-start gap-4 mb-4">
                                <div className={`w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl flex-shrink-0 transition-all ${isComplete ? `bg-${phase.color}-500` :
                                    isRunning ? `bg-${phase.color}-500 animate-pulse shadow-lg` :
                                        'bg-gray-400'
                                    }`}>
                                    {isComplete ? <CheckCircle className="w-7 h-7" /> : phase.id}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-1">
                                        <h3 className="text-2xl font-bold text-gray-800">{phase.name}</h3>
                                        {isRunning && (
                                            <span className="status-badge bg-blue-100 text-blue-700 flex items-center gap-1 animate-pulse">
                                                <div className="processing-spinner border-blue-700" />
                                                Processing
                                            </span>
                                        )}
                                        {isComplete && (
                                            <span className="status-badge bg-green-100 text-green-700">
                                                <CheckCircle className="w-4 h-4" /> Complete
                                            </span>
                                        )}
                                        {isPending && (
                                            <span className="status-badge bg-gray-200 text-gray-600">Pending</span>
                                        )}
                                    </div>
                                    <p className="text-gray-600">{phase.description}</p>
                                </div>
                            </div>

                            {/* Progress Bar (only when running) */}
                            {isRunning && (
                                <div className="mb-4">
                                    <div className="progress-bar-container h-3">
                                        <div className="progress-bar-fill animated" style={{ width: `${progress}%` }} />
                                    </div>
                                </div>
                            )}

                            {/* Input → Output Visualization */}
                            {showDemo && (
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    {/* Input */}
                                    <div className={`p-4 rounded-lg border-2 ${isRunning ? 'border-yellow-300 bg-yellow-50' : 'border-gray-300 bg-white'}`}>
                                        <div className="flex items-center gap-2 mb-2">
                                            <ArrowRight className="w-4 h-4 text-gray-400" />
                                            <span className="text-sm font-semibold text-gray-700 uppercase">Input</span>
                                        </div>
                                        <h4 className="font-semibold text-gray-800 mb-2">{phase.input.title}</h4>
                                        <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs mb-2 whitespace-pre-wrap">
                                            {phase.input.content}
                                        </div>
                                        {phase.input.issues && (
                                            <div className="space-y-1">
                                                {phase.input.issues.map((issue, i) => (
                                                    <div key={i} className="text-xs text-red-600 flex items-center gap-1">
                                                        <span>❌</span>
                                                        <span>{issue}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        {phase.input.task && (
                                            <div className="mt-2 text-sm text-gray-600 italic">{phase.input.task}</div>
                                        )}
                                    </div>

                                    {/* Output */}
                                    <div className={`p-4 rounded-lg border-2 ${isComplete ? `border-${phase.color}-500 bg-${phase.color}-50` : isRunning ? 'border-blue-300 bg-blue-50 animate-pulse' : 'border-gray-200 bg-gray-50'}`}>
                                        <div className="flex items-center gap-2 mb-2">
                                            <ArrowRight className="w-4 h-4 text-gray-400" />
                                            <span className="text-sm font-semibold text-gray-700 uppercase">Output</span>
                                        </div>
                                        <h4 className="font-semibold text-gray-800 mb-2">{phase.output.title}</h4>
                                        <div className={`bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs mb-2 whitespace-pre-wrap ${isRunning ? 'opacity-50' : ''}`}>
                                            {progress > 50 || isComplete ? phase.output.content : 'Processing...'}
                                        </div>
                                        {(isComplete || (isRunning && progress > 70)) && (
                                            <div className="space-y-1">
                                                {phase.output.improvements.map((imp, i) => (
                                                    <div key={i} className="text-xs text-green-600 flex items-center gap-1">
                                                        <span>✅</span>
                                                        <span className="font-medium">{imp}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Research Finding */}
                            {isComplete && (
                                <div className={`p-4 rounded-lg bg-${phase.color}-100 border-l-4 border-${phase.color}-600`}>
                                    <div className="flex items-center gap-2 mb-1">
                                        <Sparkles className={`w-4 h-4 text-${phase.color}-700`} />
                                        <span className={`font-semibold text-${phase.color}-900`}>
                                            {phase.id <= 4 ? 'Research Finding' : 'Application'}
                                        </span>
                                    </div>
                                    <div className={`font-bold text-${phase.color}-800 mb-1`}>{phase.finding}</div>
                                    <div className={`text-sm text-${phase.color}-700`}>{phase.detail}</div>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Final Results */}
            {currentPhase === 4 && progress === 100 && (
                <div className="card bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-500">
                    <div className="flex items-center gap-3 mb-4">
                        <CheckCircle className="w-12 h-12 text-green-700" />
                        <div>
                            <h2 className="text-3xl font-bold text-green-800">Complete Pipeline Executed! 🎉</h2>
                            <p className="text-green-700">Rule creation + validation demonstration</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-5 gap-4">
                        <div className="text-center bg-white p-4 rounded-lg">
                            <div className="text-3xl font-bold text-blue-600 mb-1">97</div>
                            <div className="text-xs text-gray-600">Rules</div>
                        </div>
                        <div className="text-center bg-white p-4 rounded-lg">
                            <div className="text-3xl font-bold text-purple-600 mb-1">95.88%</div>
                            <div className="text-xs text-gray-600">Accuracy</div>
                        </div>
                        <div className="text-center bg-white p-4 rounded-lg">
                            <div className="text-3xl font-bold text-green-600 mb-1">100%</div>
                            <div className="text-xs text-gray-600">Formalized</div>
                        </div>
                        <div className="text-center bg-white p-4 rounded-lg">
                            <div className="text-3xl font-bold text-orange-600 mb-1">1,309</div>
                            <div className="text-xs text-gray-600">Triples</div>
                        </div>
                        <div className="text-center bg-white p-4 rounded-lg">
                            <div className="text-3xl font-bold text-red-600 mb-1">✓</div>
                            <div className="text-xs text-gray-600">Validated</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
