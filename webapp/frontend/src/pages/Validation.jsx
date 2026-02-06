import { useState } from 'react'
import { Database, RefreshCw, Code, Shield, Brain, CheckCircle, XCircle, ArrowRight, Sparkles, PlayCircle, AlertCircle } from 'lucide-react'

export default function Validation() {
    const [currentStep, setCurrentStep] = useState(0)
    const [scenario, setScenario] = useState('multiple_violations')
    const [animating, setAnimating] = useState(false)
    const [validationData, setValidationData] = useState(null)
    const [loading, setLoading] = useState(false)

    // Real policy rules from AIT Student Handbook
    const scenarios = {
        compliant: {
            name: 'On-Time Submission ✅',
            ruleText: '"Students must submit assignments by 5:00 PM on the due date"',
            ruleId: 'R12',
            deonticType: 'Obligation',
            student: 'ST124960',
            assignment: 'A01',
            submittedAt: '16:55:00',
            deadline: '17:00:00',
            result: 'compliant',
            violations: []
        },
        late_submission: {
            name: 'Late Submission ❌ (Single Violation)',
            ruleText: '"Students must submit assignments by 5:00 PM on the due date"',
            ruleId: 'R12',
            deonticType: 'Obligation',
            student: 'ST124960',
            assignment: 'A01',
            submittedAt: '17:30:00',
            deadline: '17:00:00',
            result: 'violation',
            violations: [
                {
                    constraint: 'submittedAt maxInclusive deadline',
                    actual: '17:30:00',
                    expected: '≤17:00:00',
                    message: 'Submitted 30 minutes after deadline'
                }
            ]
        },
        multiple_violations: {
            name: 'Multiple Violations ❌❌ (2 Constraints)',
            ruleText: '"Students must submit assignments by 5:00 PM AND include a cover page"',
            ruleId: 'R48',
            deonticType: 'Obligation',
            student: 'ST999999',
            assignment: 'A02',
            submittedAt: '18:45:00',
            deadline: '17:00:00',
            hasCoverPage: false,
            result: 'multiple',
            violations: [
                {
                    constraint: 'submittedAt maxInclusive deadline',
                    actual: '18:45:00',
                    expected: '≤17:00:00',
                    message: 'Submitted 1 hour 45 minutes after deadline'
                },
                {
                    constraint: 'hasCoverPage minCount 1',
                    actual: 'false',
                    expected: 'true',
                    message: 'Missing required cover page'
                }
            ]
        }
    }

    const currentScenario = scenarios[scenario]

    const steps = [
        {
            id: 1,
            title: 'Database Retrieval',
            icon: Database,
            color: 'blue',
            description: 'Fetch student submission record'
        },
        {
            id: 2,
            title: 'RDF Transformation',
            icon: RefreshCw,
            color: 'purple',
            description: 'Convert to RDF triples'
        },
        {
            id: 3,
            title: 'SHACL Validation',
            icon: Shield,
            color: 'orange',
            description: 'Apply SHACL constraints & check compliance'
        },
        {
            id: 4,
            title: 'LLM Translation',
            icon: Brain,
            color: 'green',
            description: 'Generate human-readable explanation'
        }
    ]

    const handleRunValidation = async () => {
        setLoading(true)
        setAnimating(true)
        setCurrentStep(0)

        try {
            // Call real API
            const response = await fetch('/api/validation/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario })
            })
            const data = await response.json()
            setValidationData(data)

            // Animate steps
            const interval = setInterval(() => {
                setCurrentStep(s => {
                    if (s >= 3) {
                        clearInterval(interval)
                        setAnimating(false)
                        setLoading(false)
                        return s
                    }
                    return s + 1
                })
            }, 1500)
        } catch (error) {
            console.error('Validation failed:', error)
            setLoading(false)
            setAnimating(false)
        }
    }

    const handleReset = () => {
        setCurrentStep(0)
        setAnimating(false)
        setValidationData(null)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <Shield className="w-10 h-10 text-blue-600" />
                    Interactive Validation Demo
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    Database → RDF → SHACL → LLM Explanation (with real AIT policy rules)
                </p>
            </div>

            {/* Rule Display */}
            <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
                <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Code className="w-5 h-5 text-purple-600" />
                    Policy Rule: {currentScenario.ruleId}
                </h3>
                <div className="bg-white p-4 rounded-lg border border-purple-200 mb-3">
                    <div className="text-gray-800 text-lg italic mb-2">{currentScenario.ruleText}</div>
                    <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${currentScenario.deonticType === 'Obligation' ? 'bg-red-100 text-red-700' :
                            currentScenario.deonticType === 'Permission' ? 'bg-green-100 text-green-700' :
                                'bg-orange-100 text-orange-700'
                            }`}>
                            {currentScenario.deonticType}
                        </span>
                        <span className="text-sm text-gray-600">from AIT Student Handbook</span>
                    </div>
                </div>
            </div>

            {/* Scenario Selector */}
            <div className="card">
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-600" />
                    Select Test Scenario
                </h3>
                <div className="grid grid-cols-3 gap-3">
                    {Object.entries(scenarios).map(([key, scn]) => (
                        <button
                            key={key}
                            onClick={() => {
                                setScenario(key)
                                handleReset()
                            }}
                            className={`p-4 rounded-lg border-2 transition-all text-left ${scenario === key
                                ? 'border-blue-500 bg-blue-50 shadow-lg'
                                : 'border-gray-300 bg-white hover:border-blue-300'
                                }`}
                        >
                            <div className="font-semibold text-gray-800 mb-1">{scn.name}</div>
                            <div className="text-xs text-gray-600">
                                {scn.violations.length === 0 ? (
                                    <span className="text-green-600">✓ All constraints satisfied</span>
                                ) : scn.violations.length === 1 ? (
                                    <span className="text-red-600">✗ 1 constraint violated</span>
                                ) : (
                                    <span className="text-red-700 font-semibold">✗ {scn.violations.length} constraints violated</span>
                                )}
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3">
                <button
                    onClick={handleRunValidation}
                    disabled={animating}
                    className={`btn ${animating ? 'btn-secondary cursor-not-allowed' : 'btn-primary'}`}
                >
                    {animating ? (
                        <>
                            <div className="processing-spinner border-white" />
                            Validating...
                        </>
                    ) : (
                        <>
                            <PlayCircle className="w-5 h-5" />
                            Run Validation
                        </>
                    )}
                </button>
                <button onClick={handleReset} className="btn btn-secondary">
                    <RefreshCw className="w-5 h-5" />
                    Reset
                </button>
            </div>

            {/* Step Progress */}
            <div className="grid grid-cols-4 gap-3">
                {steps.map((step, idx) => {
                    const isActive = idx === currentStep && animating
                    const isComplete = idx < currentStep || (idx === currentStep && !animating)
                    const isPending = idx > currentStep

                    return (
                        <div
                            key={step.id}
                            className={`card text-center transition-all ${isActive ? `bg-${step.color}-100 border-2 border-${step.color}-500 shadow-lg` :
                                isComplete ? `bg-${step.color}-50` :
                                    'bg-gray-50'
                                }`}
                        >
                            <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${isActive ? `bg-${step.color}-500 animate-pulse` :
                                isComplete ? `bg-${step.color}-500` :
                                    'bg-gray-300'
                                }`}>
                                {isComplete ? (
                                    <CheckCircle className="w-6 h-6 text-white" />
                                ) : (
                                    <step.icon className={`w-6 h-6 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                                )}
                            </div>
                            <div className="text-sm font-semibold text-gray-800">{step.title}</div>
                            <div className="text-xs text-gray-600 mt-1">{step.description}</div>
                        </div>
                    )
                })}</div>

            {/* Step Content */}
            <div className="space-y-6">
                {/* Step 1: Database */}
                {currentStep >= 0 && (
                    <div className="card border-l-4 border-blue-500">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
                                1
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">Database Retrieval</h3>
                            {currentStep > 0 && <CheckCircle className="w-6 h-6 text-green-600" />}
                        </div>
                        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
                            <div className="text-blue-400">// SQL Query</div>
                            <div>SELECT * FROM submissions WHERE student_id = '{currentScenario.student}';</div>
                            <div className="mt-3 text-green-400">// Result (JSON)</div>
                            <pre className="text-xs mt-1">{JSON.stringify({
                                student_id: currentScenario.student,
                                assignment_id: currentScenario.assignment,
                                submitted_at: currentScenario.submittedAt,
                                deadline: currentScenario.deadline,
                                ...(currentScenario.hasCoverPage !== undefined && { has_cover_page: currentScenario.hasCoverPage })
                            }, null, 2)}</pre>
                        </div>
                    </div>
                )}

                {/* Step 2: RDF Transform */}
                {currentStep >= 1 && (
                    <div className="card border-l-4 border-purple-500">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold">
                                2
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">RDF Transformation</h3>
                            {currentStep > 1 && <CheckCircle className="w-6 h-6 text-green-600" />}
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Input (JSON)</div>
                                <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs">
                                    <pre>{JSON.stringify({
                                        student_id: currentScenario.student,
                                        submitted_at: currentScenario.submittedAt,
                                        has_cover_page: currentScenario.hasCoverPage
                                    }, null, 2)}</pre>
                                </div>
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Output (RDF Turtle)</div>
                                <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs">
                                    <pre>{`:${currentScenario.student} a :Student ;
  :submitted :${currentScenario.assignment} .

:${currentScenario.assignment} a :Assignment ;
  :submittedAt "${currentScenario.submittedAt}"^^xsd:time ;
  :deadline "${currentScenario.deadline}"^^xsd:time${currentScenario.hasCoverPage !== undefined ? ` ;
  :hasCoverPage ${currentScenario.hasCoverPage}` : ''} .`}</pre>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 3: SHACL Validation */}
                {currentStep >= 2 && (
                    <div className="card border-l-4 border-orange-500">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full bg-orange-500 text-white flex items-center justify-center font-bold">
                                3
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">SHACL Validation</h3>
                            {currentStep > 2 && <CheckCircle className="w-6 h-6 text-green-600" />}
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">SHACL Shape ({currentScenario.ruleId})</div>
                                <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs">
                                    <pre>{`:SubmissionShape a sh:NodeShape ;
  sh:targetClass :Assignment ;
  sh:property [
    sh:path :submittedAt ;
    sh:maxInclusive "${currentScenario.deadline}"^^xsd:time
  ]${currentScenario.hasCoverPage !== undefined ? ` ;
  sh:property [
    sh:path :hasCoverPage ;
    sh:minCount 1 ;
    sh:hasValue true
  ]` : ''} .`}</pre>
                                </div>
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Validation Result</div>
                                <div className={`p-4 rounded-lg ${currentScenario.result === 'compliant'
                                    ? 'bg-green-100 border-2 border-green-500'
                                    : 'bg-red-100 border-2 border-red-500'
                                    }`}>
                                    {currentScenario.result === 'compliant' ? (
                                        <>
                                            <div className="flex items-center gap-2 mb-2">
                                                <CheckCircle className="w-8 h-8 text-green-700" />
                                                <span className="text-xl font-bold text-green-800">COMPLIANT ✅</span>
                                            </div>
                                            <div className="text-sm text-green-700">
                                                All constraints satisfied
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="flex items-center gap-2 mb-3">
                                                <XCircle className="w-8 h-8 text-red-700" />
                                                <span className="text-xl font-bold text-red-800">
                                                    {currentScenario.violations.length === 1 ? 'VIOLATION' : `${currentScenario.violations.length} VIOLATIONS`} ❌
                                                </span>
                                            </div>
                                            <div className="space-y-3">
                                                {currentScenario.violations.map((v, idx) => (
                                                    <div key={idx} className="bg-red-50 p-3 rounded border border-red-300">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <AlertCircle className="w-4 h-4 text-red-700" />
                                                            <span className="font-bold text-red-800 text-sm">Violation #{idx + 1}</span>
                                                        </div>
                                                        <div className="text-xs text-red-700 space-y-1 font-mono">
                                                            <div><strong>Constraint:</strong> {v.constraint}</div>
                                                            <div><strong>Actual:</strong> {v.actual}</div>
                                                            <div><strong>Expected:</strong> {v.expected}</div>
                                                            <div className="mt-2 font-bold text-red-800">{v.message}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 4: LLM Translation */}
                {currentStep >= 3 && (
                    <div className="card border-l-4 border-green-500">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-full bg-green-500 text-white flex items-center justify-center font-bold">
                                4
                            </div>
                            <h3 className="text-xl font-bold text-gray-800">LLM Human-Readable Translation</h3>
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Technical Output</div>
                                <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-xs">
                                    {currentScenario.result === 'compliant' ? (
                                        <pre>ValidationResult: Conforms
                                            Conformance: true
                                            Violations: []</pre>
                                    ) : (
                                        <pre>{`ValidationResult: Violation
Violations: ${currentScenario.violations.length}
${currentScenario.violations.map((v, i) => `
Violation ${i + 1}:
  Constraint: ${v.constraint}
  Severity: sh:Violation`).join('\n')}`}</pre>
                                    )}
                                </div>
                            </div>
                            <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">LLM Explanation</div>
                                <div className={`p-4 rounded-lg ${currentScenario.result === 'compliant'
                                    ? 'bg-green-50 border-2 border-green-300'
                                    : 'bg-red-50 border-2 border-red-300'
                                    }`}>
                                    {currentScenario.result === 'compliant' ? (
                                        <div className="text-green-800">
                                            <div className="font-bold mb-2">✅ Policy Compliance Confirmed</div>
                                            <p className="text-sm leading-relaxed">
                                                Student {currentScenario.student} successfully submitted assignment {currentScenario.assignment} at {currentScenario.submittedAt},
                                                which is <strong>before</strong> the {currentScenario.deadline} deadline.
                                                This submission fully complies with AIT's submission policy (Rule {currentScenario.ruleId}).
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="text-red-800">
                                            <div className="font-bold mb-2">
                                                ❌ {currentScenario.violations.length === 1 ? 'Policy Violation' : `${currentScenario.violations.length} Policy Violations`} Detected
                                            </div>
                                            <p className="text-sm leading-relaxed mb-3">
                                                Student {currentScenario.student}'s submission of assignment {currentScenario.assignment} violates AIT policy rule {currentScenario.ruleId}:
                                            </p>
                                            <div className="space-y-2">
                                                {currentScenario.violations.map((v, idx) => (
                                                    <div key={idx} className="bg-red-100 p-2 rounded text-sm">
                                                        <strong>{idx + 1}.</strong> {v.message}
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="mt-3 p-3 bg-red-100 rounded text-xs">
                                                <strong>Recommended Action:</strong> Contact student {currentScenario.student} regarding policy violations.
                                                {currentScenario.violations.length > 1 && ' Multiple issues require immediate attention.'}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Summary */}
            {currentStep >= 3 && !animating && (
                <div className={`card border-2 ${currentScenario.result === 'compliant'
                    ? 'border-green-500 bg-gradient-to-r from-green-50 to-green-100'
                    : 'border-red-500 bg-gradient-to-r from-red-50 to-red-100'
                    }`}>
                    <div className="flex items-center gap-3 mb-3">
                        <Sparkles className={`w-8 h-8 ${currentScenario.result === 'compliant' ? 'text-green-700' : 'text-red-700'}`} />
                        <div>
                            <h3 className="text-2xl font-bold text-gray-800">Validation Complete</h3>
                            <p className="text-sm text-gray-600">All 4 steps executed successfully</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-5 gap-4">
                        <div className="text-center bg-white p-3 rounded-lg">
                            <div className="text-2xl font-bold text-blue-600">✓</div>
                            <div className="text-xs text-gray-600 mt-1">Database</div>
                        </div>
                        <div className="text-center bg-white p-3 rounded-lg">
                            <div className="text-2xl font-bold text-purple-600">✓</div>
                            <div className="text-xs text-gray-600 mt-1">RDF</div>
                        </div>
                        <div className="text-center bg-white p-3 rounded-lg">
                            <div className="text-2xl font-bold text-orange-600">✓</div>
                            <div className="text-xs text-gray-600 mt-1">SHACL</div>
                        </div>
                        <div className="text-center bg-white p-3 rounded-lg">
                            <div className="text-2xl font-bold text-green-600">✓</div>
                            <div className="text-xs text-gray-600 mt-1">LLM</div>
                        </div>
                        <div className="text-center bg-white p-3 rounded-lg">
                            <div className={`text-2xl font-bold ${currentScenario.result === 'compliant' ? 'text-green-600' : 'text-red-600'}`}>
                                {currentScenario.violations.length}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">Violations</div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
