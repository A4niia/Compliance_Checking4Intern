import { useState } from 'react'
import { Play, Pause, RotateCcw, CheckCircle, Loader, FileText, Brain, Shield } from 'lucide-react'

export default function Pipeline() {
    const [running, setRunning] = useState(false)
    const [currentPhase, setCurrentPhase] = useState(0)
    const [progress, setProgress] = useState(0)

    const phases = [
        {
            id: 1,
            name: 'Text Simplification',
            description: 'OCR cleanup & normalization',
            finding: '+15pp accuracy improvement',
            detail: '88% of rules affected, 247 line breaks removed',
            icon: FileText,
            color: 'blue'
        },
        {
            id: 2,
            name: 'LLM Classification',
            description: 'Deontic type identification',
            finding: 'Permission challenge solved',
            detail: '0% → 70% (p = 0.023), Mistral-7B 99% accuracy',
            icon: Brain,
            color: 'purple'
        },
        {
            id: 3,
            name: 'FOL Formalization',
            description: 'First-order logic generation',
            finding: 'FOL is sufficient',
            detail: '100% success, no HOL needed for institutional policies',
            icon: Shield,
            color: 'green'
        },
        {
            id: 4,
            name: 'SHACL Translation',
            description: 'Semantic web constraints',
            finding: '1,309 W3C-compliant triples',
            detail: '97 shapes, 12 target classes, validated',
            icon: Shield,
            color: 'orange'
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
                        if (cp >= 3) {
                            clearInterval(interval)
                            setRunning(false)
                            return cp
                        }
                        setProgress(0)
                        return cp + 1
                    })
                    return 0
                }
                return p + 2
            })
        }, 50)
    }

    const handleReset = () => {
        setRunning(false)
        setCurrentPhase(0)
        setProgress(0)
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold text-gray-800">4-Phase Methodology</h1>
                    <p className="text-gray-600 mt-2 text-lg">End-to-end policy formalization pipeline</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleRun}
                        disabled={running}
                        className={`btn ${running ? 'btn-secondary' : 'btn-primary'}`}
                    >
                        {running ? <Loader className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                        {running ? 'Running...' : 'Run Pipeline'}
                    </button>
                    <button onClick={handleReset} className="btn btn-secondary">
                        <RotateCcw className="w-5 h-5" />
                        Reset
                    </button>
                </div>
            </div>

            {/* Overall Progress */}
            <div className="card">
                <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-700">Overall Progress</span>
                    <span className="text-sm text-gray-600">
                        Phase {currentPhase + 1}/4 ({Math.round((currentPhase * 25) + (progress / 4))}%)
                    </span>
                </div>
                <div className="progress-bar-container h-4">
                    <div
                        className={`progress-bar-fill ${running ? 'animated' : ''}`}
                        style={{ width: `${(currentPhase * 25) + (progress / 4)}%` }}
                    />
                </div>
            </div>

            {/* Phase Cards */}
            <div className="space-y-4">
                {phases.map((phase, idx) => {
                    const isComplete = idx < currentPhase
                    const isRunning = idx === currentPhase && running
                    const isPending = idx > currentPhase

                    return (
                        <div
                            key={phase.id}
                            className={`card border-l-4 transition-all ${isComplete ? `border-${phase.color}-500 bg-gradient-to-r from-${phase.color}-50 to-white` :
                                    isRunning ? `border-${phase.color}-500 bg-gradient-to-r from-${phase.color}-50 to-white shadow-lg` :
                                        'border-gray-300 bg-gray-50'
                                }`}
                        >
                            <div className="flex items-start gap-4">
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-xl ${isComplete ? `bg-${phase.color}-500` :
                                        isRunning ? `bg-${phase.color}-500 animate-pulse` :
                                            'bg-gray-300'
                                    }`}>
                                    {isComplete ? <CheckCircle className="w-6 h-6" /> : phase.id}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="text-xl font-bold text-gray-800">{phase.name}</h3>
                                        {isRunning && (
                                            <span className="status-badge bg-blue-100 text-blue-700 flex items-center gap-1">
                                                <div className="processing-spinner border-blue-700" />
                                                Running
                                            </span>
                                        )}
                                        {isComplete && (
                                            <span className="status-badge bg-green-100 text-green-700">
                                                <CheckCircle className="w-4 h-4" /> Complete
                                            </span>
                                        )}
                                        {isPending && (
                                            <span className="status-badge bg-gray-100 text-gray-600">Pending</span>
                                        )}
                                    </div>
                                    <p className="text-gray-600 mb-3">{phase.description}</p>

                                    {isRunning && (
                                        <div className="mb-3">
                                            <div className="progress-bar-container h-2">
                                                <div className="progress-bar-fill animated" style={{ width: `${progress}%` }} />
                                            </div>
                                        </div>
                                    )}

                                    {(isComplete || isRunning) && (
                                        <div className={`p-3 rounded-lg bg-${phase.color}-50 border-l-4 border-${phase.color}-500`}>
                                            <div className="font-semibold text-gray-800 mb-1">
                                                🔍 Research Finding: {phase.finding}
                                            </div>
                                            <div className="text-sm text-gray-600">{phase.detail}</div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Final Results */}
            {currentPhase === 3 && progress === 100 && (
                <div className="card bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-500">
                    <div className="flex items-center gap-3 mb-3">
                        <CheckCircle className="w-10 h-10 text-green-700" />
                        <h2 className="text-2xl font-bold text-green-800">Pipeline Complete!</h2>
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-700">97</div>
                            <div className="text-sm text-green-600">Rules Processed</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-700">99%</div>
                            <div className="text-sm text-green-600">Classification</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-700">100%</div>
                            <div className="text-sm text-green-600">Formalized</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-700">1,309</div>
                            <div className="text-sm text-green-600">SHACL Triples</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
