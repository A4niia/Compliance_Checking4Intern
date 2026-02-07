import { useState, useEffect } from 'react'
import { Database, RefreshCw, Code, Shield, CheckCircle, XCircle, Search, Loader, User, AlertTriangle } from 'lucide-react'

export default function Validation() {
    const [rules, setRules] = useState([])
    const [selectedRule, setSelectedRule] = useState(null)
    const [validationResult, setValidationResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')

    // Student selection state
    const [students, setStudents] = useState([])
    const [selectedScenario, setSelectedScenario] = useState('multiple_violations')
    const [dbStats, setDbStats] = useState(null)

    // Load all rules and students on component mount
    useEffect(() => {
        fetchRules()
        fetchStudents()
    }, [])

    const fetchRules = async () => {
        try {
            const response = await fetch('/api/validation/rules')
            const data = await response.json()
            setRules(data.rules || [])
            if (data.rules && data.rules.length > 0) {
                setSelectedRule(data.rules[0].id)
            }
        } catch (error) {
            console.error('Failed to load rules:', error)
        }
    }

    const fetchStudents = async () => {
        try {
            const response = await fetch('/api/validation/students')
            const data = await response.json()
            setStudents(data.scenarios || [])
            setDbStats(data.stats || null)
        } catch (error) {
            console.error('Failed to load students:', error)
        }
    }

    const handleValidateRule = async () => {
        if (!selectedRule) return

        setLoading(true)
        try {
            const response = await fetch('/api/validation/validate-rule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rule_id: selectedRule,
                    scenario: selectedScenario
                })
            })
            const data = await response.json()
            setValidationResult(data)
        } catch (error) {
            console.error('Validation failed:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredRules = rules.filter(rule =>
        rule.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rule.id.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const currentRule = rules.find(r => r.id === selectedRule)
    const currentStudent = students.find(s => s.scenario === selectedScenario)

    const scenarioLabels = {
        'compliant': '✅ Compliant Student',
        'single_violation': '⚠️ Single Violation',
        'multiple_violations': '❌ Multiple Violations'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-gray-800 flex items-center gap-3">
                    <Shield className="w-10 h-10 text-blue-600" />
                    Policy Rule Validation
                </h1>
                <p className="text-gray-600 mt-2 text-lg">
                    Validate individual policy rules against student data using SHACL constraints
                </p>
            </div>

            <div className="grid grid-cols-3 gap-6">
                {/* Left: Rule Selector */}
                <div className="col-span-1 space-y-4">
                    {/* Student Selector */}
                    <div className="card bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-200">
                        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <User className="w-5 h-5 text-amber-600" />
                            Test Student
                        </h3>
                        <select
                            value={selectedScenario}
                            onChange={(e) => {
                                setSelectedScenario(e.target.value)
                                setValidationResult(null)
                            }}
                            className="w-full px-3 py-2 border border-amber-300 rounded-lg bg-white focus:ring-2 focus:ring-amber-500"
                        >
                            {Object.entries(scenarioLabels).map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                        {currentStudent && (
                            <div className="mt-3 text-sm text-gray-600 space-y-1">
                                <div><strong>ID:</strong> {currentStudent.student_id}</div>
                                <div><strong>Name:</strong> {currentStudent.name}</div>
                                <div><strong>Program:</strong> {currentStudent.program}</div>
                                <div className={`flex items-center gap-1 ${currentStudent.violation_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                    {currentStudent.violation_count > 0 ? (
                                        <AlertTriangle className="w-4 h-4" />
                                    ) : (
                                        <CheckCircle className="w-4 h-4" />
                                    )}
                                    <strong>{currentStudent.violation_count}</strong> expected violations
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="card">
                        <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <Code className="w-5 h-5 text-blue-600" />
                            Select Rule ({filteredRules.length}/{rules.length})
                        </h3>

                        {/* Search */}
                        <div className="relative mb-3">
                            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search rules..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>

                        {/* Rule List */}
                        <div className="max-h-64 overflow-y-auto space-y-2">
                            {filteredRules.map((rule) => (
                                <button
                                    key={rule.id}
                                    onClick={() => {
                                        setSelectedRule(rule.id)
                                        setValidationResult(null)
                                    }}
                                    className={`w-full text-left p-3 rounded-lg border transition-all ${selectedRule === rule.id
                                        ? 'border-blue-500 bg-blue-50 shadow-md'
                                        : 'border-gray-200 bg-white hover:border-blue-300'
                                        }`}
                                >
                                    <div className="font-semibold text-sm text-gray-800">{rule.id}</div>
                                    <div className="text-xs text-gray-600 mt-1 line-clamp-2">{rule.text}</div>
                                    <div className="mt-2 flex items-center gap-2">
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${rule.deontic_type === 'obligation' ? 'bg-red-100 text-red-700' :
                                            rule.deontic_type === 'permission' ? 'bg-green-100 text-green-700' :
                                                'bg-orange-100 text-orange-700'
                                            }`}>
                                            {rule.deontic_type || 'N/A'}
                                        </span>
                                        {rule.has_shacl && (
                                            <span className="px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700">SHACL</span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Rule Details & Validation */}
                <div className="col-span-2 space-y-4">
                    {currentRule ? (
                        <>
                            {/* Rule Display */}
                            <div className="card bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
                                <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                                    <Code className="w-5 h-5 text-purple-600" />
                                    Rule: {currentRule.id}
                                </h3>
                                <div className="bg-white p-4 rounded-lg border border-purple-200">
                                    <div className="text-gray-800 mb-3">{currentRule.text}</div>
                                    <div className="flex items-center gap-2">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${currentRule.deontic_type === 'obligation' ? 'bg-red-100 text-red-700' :
                                            currentRule.deontic_type === 'permission' ? 'bg-green-100 text-green-700' :
                                                'bg-orange-100 text-orange-700'
                                            }`}>
                                            {currentRule.deontic_type || 'Unknown'}
                                        </span>
                                        <span className="text-sm text-gray-600">from AIT Policy Documents</span>
                                    </div>
                                </div>
                            </div>

                            {/* FOL Formula */}
                            {currentRule.fol && (
                                <div className="card">
                                    <h4 className="font-semibold text-gray-800 mb-2">FOL Formula</h4>
                                    <pre className="bg-gray-50 p-3 rounded-lg text-sm font-mono overflow-x-auto">
                                        {currentRule.fol}
                                    </pre>
                                </div>
                            )}

                            {/* Validation Button */}
                            <button
                                onClick={handleValidateRule}
                                disabled={loading || !currentRule.has_shacl}
                                className={`btn ${loading ? 'btn-secondary' : 'btn-primary'} ${!currentRule.has_shacl && 'opacity-50 cursor-not-allowed'}`}
                            >
                                {loading ? (
                                    <>
                                        <Loader className="w-5 h-5 animate-spin" />
                                        Validating with pySHACL...
                                    </>
                                ) : (
                                    <>
                                        <Shield className="w-5 h-5" />
                                        Run SHACL Validation on {scenarioLabels[selectedScenario]?.split(' ')[0]}
                                    </>
                                )}
                            </button>

                            {!currentRule.has_shacl && (
                                <p className="text-sm text-amber-600">
                                    ⚠️ No SHACL shape available for this rule
                                </p>
                            )}

                            {/* Validation Results */}
                            {validationResult && (
                                <>
                                    {/* LLM Explanation - Prominent First */}
                                    {validationResult.llm_explanation && (
                                        <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300">
                                            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                                <span className="text-2xl">💡</span>
                                                What This Means
                                            </h4>
                                            <div className="bg-white p-4 rounded-lg border border-blue-200">
                                                <p className="text-gray-800 text-lg leading-relaxed">
                                                    {validationResult.llm_explanation}
                                                </p>
                                            </div>
                                            <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                                                <span>✨</span>
                                                <span>AI-generated explanation powered by Mistral</span>
                                            </div>
                                        </div>
                                    )}

                                    <div className="card">
                                        <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                                            {validationResult.conforms ? (
                                                <CheckCircle className="w-5 h-5 text-green-600" />
                                            ) : (
                                                <XCircle className="w-5 h-5 text-red-600" />
                                            )}
                                            Technical Validation Results
                                            {validationResult.is_mock && (
                                                <span className="ml-2 px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded">
                                                    pySHACL not installed
                                                </span>
                                            )}
                                        </h4>

                                        {/* Student Info */}
                                        {validationResult.student && (
                                            <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                                                <h5 className="font-semibold text-sm text-blue-800 mb-2">Student Data Used:</h5>
                                                <div className="text-sm text-gray-700 grid grid-cols-2 gap-2">
                                                    <div><strong>ID:</strong> {validationResult.student.id}</div>
                                                    <div><strong>Name:</strong> {validationResult.student.name}</div>
                                                    <div><strong>Program:</strong> {validationResult.student.program}</div>
                                                    <div><strong>Fees Paid:</strong> {validationResult.student.fees_paid ? '✅ Yes' : '❌ No'}</div>
                                                </div>
                                            </div>
                                        )}

                                        <div className={`p-4 rounded-lg mb-4 ${validationResult.conforms
                                            ? 'bg-green-50 border border-green-200'
                                            : 'bg-red-50 border border-red-200'
                                            }`}>
                                            <div className="font-semibold mb-1">
                                                {validationResult.conforms ? '✅ CONFORMS' : '❌ VIOLATIONS DETECTED'}
                                            </div>
                                            <div className="text-sm text-gray-600">
                                                {validationResult.validation_result?.message ||
                                                    validationResult.validation_result?.report_text?.substring(0, 200)}
                                            </div>
                                        </div>

                                        {/* Violations */}
                                        {validationResult.violations && validationResult.violations.length > 0 && (
                                            <div className="mb-4">
                                                <h5 className="font-semibold text-sm text-red-700 mb-2">
                                                    Violations ({validationResult.violations.length}):
                                                </h5>
                                                <div className="bg-red-50 p-3 rounded-lg space-y-1 max-h-32 overflow-y-auto">
                                                    {validationResult.violations.map((v, i) => (
                                                        <div key={i} className="text-xs font-mono text-red-800">{v}</div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Student RDF */}
                                        {validationResult.student_rdf && (
                                            <div>
                                                <h5 className="font-semibold text-sm text-gray-700 mb-2">Student RDF (Turtle):</h5>
                                                <pre className="bg-gray-50 p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-48">
                                                    {validationResult.student_rdf}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </>
                    ) : (
                        <div className="card text-center py-12 text-gray-500">
                            <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>Select a rule to view details</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Stats Footer */}
            <div className="grid grid-cols-5 gap-4">
                <div className="card text-center">
                    <div className="text-3xl font-bold text-blue-600">{rules.length}</div>
                    <div className="text-sm text-gray-600">Total Rules</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-green-600">
                        {rules.filter(r => r.has_shacl).length}
                    </div>
                    <div className="text-sm text-gray-600">With SHACL</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-red-600">
                        {rules.filter(r => r.deontic_type === 'obligation').length}
                    </div>
                    <div className="text-sm text-gray-600">Obligations</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-purple-600">
                        {rules.filter(r => r.deontic_type === 'permission').length}
                    </div>
                    <div className="text-sm text-gray-600">Permissions</div>
                </div>
                <div className="card text-center">
                    <div className="text-3xl font-bold text-amber-600">
                        {dbStats?.total_students || '?'}
                    </div>
                    <div className="text-sm text-gray-600">Test Students</div>
                </div>
            </div>
        </div>
    )
}

