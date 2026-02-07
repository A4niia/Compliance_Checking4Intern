import { useState, useEffect, useRef } from 'react'
import {
    Play, Upload, RefreshCw, CheckCircle, XCircle, Clock,
    FileText, Brain, Code, Database, Shield, ChevronDown, ChevronUp,
    Activity, Zap, Circle, Loader2
} from 'lucide-react'

/**
 * LivePipeline - Real-time agentic pipeline processing
 * 
 * Features:
 * - PDF upload and processing
 * - SSE stream for real-time updates
 * - ReAct reasoning traces (Think → Act → Observe)
 * - Intermediate output display
 * - Timing metrics per phase
 * - Run history and comparison
 */

const phases = [
    {
        id: 'extraction',
        name: 'Text Extraction',
        icon: FileText,
        description: 'Extract and simplify text from PDF documents'
    },
    {
        id: 'classification',
        name: 'LLM Classification',
        icon: Brain,
        description: 'Classify rules using Mistral LLM (obligation/permission/prohibition)'
    },
    {
        id: 'fol_generation',
        name: 'FOL Generation',
        icon: Code,
        description: 'Generate First-Order Logic formulas with deontic operators'
    },
    {
        id: 'shacl_translation',
        name: 'SHACL Translation',
        icon: Database,
        description: 'Translate FOL to SHACL constraint shapes'
    },
    {
        id: 'validation',
        name: 'Validation',
        icon: Shield,
        description: 'Validate SHACL shapes against RDF test data'
    }
]

export default function LivePipeline() {
    const [isRunning, setIsRunning] = useState(false)
    const [currentPhase, setCurrentPhase] = useState(-1)
    const [phaseData, setPhaseData] = useState({})
    const [reactTraces, setReactTraces] = useState([])
    const [runHistory, setRunHistory] = useState([])
    const [selectedFiles, setSelectedFiles] = useState([])
    const [currentRunId, setCurrentRunId] = useState(null)
    const [expandedPhases, setExpandedPhases] = useState({})
    const [error, setError] = useState(null)
    const [totalTime, setTotalTime] = useState(0)

    const eventSourceRef = useRef(null)
    const fileInputRef = useRef(null)

    // Load run history on mount
    useEffect(() => {
        fetchRunHistory()
    }, [])

    // Cleanup SSE on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close()
            }
        }
    }, [])

    const fetchRunHistory = async () => {
        try {
            const response = await fetch('/api/live/history')
            // Check if response is OK and content type is JSON
            if (!response.ok) {
                console.error('Failed to fetch history: HTTP', response.status)
                return
            }
            const contentType = response.headers.get('content-type')
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Expected JSON response but got:', contentType)
                return
            }
            const data = await response.json()
            setRunHistory(data.runs || [])
        } catch (err) {
            console.error('Failed to fetch history:', err)
        }
    }

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files || [])
        if (files.length > 0) {
            setSelectedFiles(prev => [...prev, ...files])
        }
        // Reset input to allow selecting same file again
        e.target.value = ''
    }

    const removeFile = (index) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    }

    const clearAllFiles = () => {
        setSelectedFiles([])
    }

    const startPipeline = async () => {
        setIsRunning(true)
        setError(null)
        setCurrentPhase(0)
        setPhaseData({})
        setReactTraces([])
        setTotalTime(0)

        try {
            // Upload files and start processing
            const formData = new FormData()
            selectedFiles.forEach((file) => {
                formData.append('files', file)
            })

            const response = await fetch('/api/live/upload', {
                method: 'POST',
                body: formData
            })

            // Check if response is JSON
            if (!response.ok) {
                throw new Error(`Upload failed: HTTP ${response.status}`)
            }
            const contentType = response.headers.get('content-type')
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Backend returned non-JSON response. Is the backend running?')
            }

            const data = await response.json()
            setCurrentRunId(data.run_id)

            // Connect to SSE stream
            connectToEventStream(data.run_id)

        } catch (err) {
            setError(err.message)
            setIsRunning(false)
        }
    }

    const connectToEventStream = (runId) => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
        }

        const eventSource = new EventSource(`/api/live/stream/${runId}`)
        eventSourceRef.current = eventSource

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                // Check for error event from backend
                if (data.error) {
                    setError(data.error)
                    eventSource.close()
                    setIsRunning(false)
                    return
                }
                handleEvent(data)
            } catch (err) {
                console.error('Failed to parse SSE event:', err)
            }
        }

        eventSource.onerror = (err) => {
            console.error('SSE connection error:', err)
            eventSource.close()
            setIsRunning(false)
            // Only set error if we haven't received any phases yet
            if (Object.keys(phaseData).length === 0) {
                setError('Connection to pipeline lost. Please try again.')
            }
        }
    }

    const handleEvent = (event) => {
        switch (event.type) {
            case 'phase_start':
                const phaseIndex = phases.findIndex(p => p.id === event.data.phase)
                setCurrentPhase(phaseIndex)
                setPhaseData(prev => ({
                    ...prev,
                    [event.data.phase]: { ...prev[event.data.phase], status: 'running' }
                }))
                break

            case 'phase_complete':
                setPhaseData(prev => ({
                    ...prev,
                    [event.data.phase]: {
                        ...prev[event.data.phase],
                        ...event.data.result,
                        time_seconds: event.data.time_seconds,
                        status: 'complete'
                    }
                }))
                break

            case 'react_trace':
                setReactTraces(prev => [...prev, event.data])
                break

            case 'intermediate_output':
                setPhaseData(prev => ({
                    ...prev,
                    [event.data.phase]: {
                        ...prev[event.data.phase],
                        intermediate: {
                            ...prev[event.data.phase]?.intermediate,
                            [event.data.output_type]: event.data.content
                        }
                    }
                }))
                break

            case 'progress':
                setPhaseData(prev => ({
                    ...prev,
                    [event.data.phase]: {
                        ...prev[event.data.phase],
                        progress: event.data.progress,
                        progressMessage: event.data.message
                    }
                }))
                break

            case 'error':
                setError(event.data.error)
                break

            case 'complete':
                setIsRunning(false)
                setTotalTime(event.data.final_result?.total_time_seconds || 0)
                if (eventSourceRef.current) {
                    eventSourceRef.current.close()
                }
                fetchRunHistory()
                break

            case 'close':
                if (eventSourceRef.current) {
                    eventSourceRef.current.close()
                }
                break
        }
    }

    const togglePhaseExpand = (phaseId) => {
        setExpandedPhases(prev => ({
            ...prev,
            [phaseId]: !prev[phaseId]
        }))
    }

    const getPhaseStatus = (phaseId, index) => {
        const data = phaseData[phaseId]
        if (data?.status === 'complete') return 'complete'
        if (currentPhase === index && isRunning) return 'running'
        if (currentPhase > index) return 'complete'
        return 'pending'
    }

    const getStatusIcon = (status) => {
        switch (status) {
            case 'complete':
                return <CheckCircle className="w-5 h-5 text-green-500" />
            case 'running':
                return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            case 'pending':
            default:
                return <Circle className="w-5 h-5 text-gray-300" />
        }
    }

    return (
        <div className="space-y-8">
            {/* Header Section */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
                <h1 className="text-3xl font-bold mb-2">Live Pipeline Processing</h1>
                <p className="text-indigo-100">
                    Real-time agentic framework with ReAct reasoning traces
                </p>

                {/* Upload and Start Controls */}
                <div className="mt-6 flex flex-wrap items-center gap-4">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf"
                        multiple
                        onChange={handleFileSelect}
                        className="hidden"
                    />

                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg flex items-center gap-2 transition-colors"
                        disabled={isRunning}
                    >
                        <Upload className="w-4 h-4" />
                        Add PDF Files
                    </button>

                    {selectedFiles.length > 0 && (
                        <button
                            onClick={clearAllFiles}
                            className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-sm transition-colors"
                            disabled={isRunning}
                        >
                            Clear All ({selectedFiles.length})
                        </button>
                    )}

                    <button
                        onClick={startPipeline}
                        disabled={isRunning}
                        className={`px-6 py-2 rounded-lg flex items-center gap-2 font-semibold transition-all ${isRunning
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-white text-indigo-600 hover:bg-indigo-50'
                            }`}
                    >
                        {isRunning ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <Play className="w-4 h-4" />
                                Start Pipeline
                            </>
                        )}
                    </button>

                    {currentRunId && (
                        <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                            Run ID: {currentRunId}
                        </span>
                    )}

                    {totalTime > 0 && (
                        <span className="px-3 py-1 bg-green-500/30 rounded-full text-sm flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {totalTime.toFixed(1)}s total
                        </span>
                    )}
                </div>

                {/* Selected Files List */}
                {selectedFiles.length > 0 && (
                    <div className="mt-4 bg-white/10 rounded-lg p-3">
                        <div className="text-sm font-medium mb-2">Selected Files ({selectedFiles.length}):</div>
                        <div className="flex flex-wrap gap-2">
                            {selectedFiles.map((file, index) => (
                                <div key={index} className="flex items-center gap-2 bg-white/20 rounded-lg px-3 py-1 text-sm">
                                    <FileText className="w-3 h-3" />
                                    <span className="max-w-[200px] truncate">{file.name}</span>
                                    <button
                                        onClick={() => removeFile(index)}
                                        className="hover:text-red-300 transition-colors"
                                        disabled={isRunning}
                                    >
                                        <XCircle className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
                    <XCircle className="w-5 h-5 text-red-500" />
                    <span className="text-red-700">{error}</span>
                </div>
            )}

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Pipeline Phases */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Activity className="w-5 h-5 text-indigo-500" />
                        Pipeline Phases
                    </h2>

                    {phases.map((phase, index) => {
                        const status = getPhaseStatus(phase.id, index)
                        const data = phaseData[phase.id] || {}
                        const isExpanded = expandedPhases[phase.id]
                        const Icon = phase.icon

                        return (
                            <div
                                key={phase.id}
                                className={`bg-white rounded-xl border transition-all ${status === 'running'
                                    ? 'border-blue-300 shadow-lg shadow-blue-100'
                                    : status === 'complete'
                                        ? 'border-green-200'
                                        : 'border-gray-200'
                                    }`}
                            >
                                {/* Phase Header */}
                                <div
                                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                                    onClick={() => togglePhaseExpand(phase.id)}
                                >
                                    <div className="flex items-center gap-4">
                                        {getStatusIcon(status)}
                                        <div className={`p-2 rounded-lg ${status === 'complete' ? 'bg-green-100' :
                                            status === 'running' ? 'bg-blue-100' : 'bg-gray-100'
                                            }`}>
                                            <Icon className={`w-5 h-5 ${status === 'complete' ? 'text-green-600' :
                                                status === 'running' ? 'text-blue-600' : 'text-gray-400'
                                                }`} />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">{phase.name}</h3>
                                            <p className="text-sm text-gray-500">{phase.description}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-4">
                                        {data.time_seconds && (
                                            <span className="text-sm text-gray-500 flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {data.time_seconds.toFixed(2)}s
                                            </span>
                                        )}
                                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                    </div>
                                </div>

                                {/* Progress Bar */}
                                {status === 'running' && data.progress && (
                                    <div className="px-4 pb-2">
                                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-blue-500 transition-all duration-300"
                                                style={{ width: `${data.progress * 100}%` }}
                                            />
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">{data.progressMessage}</p>
                                    </div>
                                )}

                                {/* Expanded Content */}
                                {isExpanded && (data.intermediate || status !== 'pending') && (
                                    <div className="border-t p-4 bg-gray-50 space-y-3">
                                        {/* Phase Results */}
                                        {phase.id === 'classification' && (data.obligations !== undefined || data.intermediate?.distribution) && (
                                            <div className="grid grid-cols-3 gap-3">
                                                <div className="bg-blue-50 p-3 rounded-lg text-center">
                                                    <div className="text-2xl font-bold text-blue-600">
                                                        {data.obligations ?? data.intermediate?.distribution?.obligations ?? 0}
                                                    </div>
                                                    <div className="text-xs text-blue-500">Obligations</div>
                                                </div>
                                                <div className="bg-green-50 p-3 rounded-lg text-center">
                                                    <div className="text-2xl font-bold text-green-600">
                                                        {data.permissions ?? data.intermediate?.distribution?.permissions ?? 0}
                                                    </div>
                                                    <div className="text-xs text-green-500">Permissions</div>
                                                </div>
                                                <div className="bg-red-50 p-3 rounded-lg text-center">
                                                    <div className="text-2xl font-bold text-red-600">
                                                        {data.prohibitions ?? data.intermediate?.distribution?.prohibitions ?? 0}
                                                    </div>
                                                    <div className="text-xs text-red-500">Prohibitions</div>
                                                </div>
                                            </div>
                                        )}

                                        {phase.id === 'extraction' && data.intermediate?.extracted_text && (
                                            <div className="bg-white p-3 rounded-lg">
                                                <div className="text-sm font-medium mb-2">Extracted Rules</div>
                                                <div className="text-2xl font-bold text-indigo-600">
                                                    {data.intermediate.extracted_text.total_rules} rules
                                                </div>
                                                <div className="text-xs text-gray-500 mt-1">
                                                    Sources: {data.intermediate.extracted_text.sources?.join(', ')}
                                                </div>
                                            </div>
                                        )}

                                        {phase.id === 'fol_generation' && data.intermediate?.formulas && (
                                            <div className="bg-white p-3 rounded-lg">
                                                <div className="text-sm font-medium mb-2">Sample FOL Formulas</div>
                                                <div className="space-y-2 font-mono text-sm">
                                                    {data.intermediate.formulas.slice(0, 3).map((f, i) => (
                                                        <div key={i} className="p-2 bg-gray-100 rounded text-xs">
                                                            {f.fol}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {phase.id === 'shacl_translation' && data.intermediate?.shacl_preview && (
                                            <div className="bg-white p-3 rounded-lg">
                                                <div className="text-sm font-medium mb-2">SHACL Preview</div>
                                                <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-40">
                                                    {data.intermediate.shacl_preview}
                                                </pre>
                                            </div>
                                        )}

                                        {phase.id === 'validation' && data.passed !== undefined && (
                                            <div className={`p-4 rounded-lg ${data.passed ? 'bg-green-50' : 'bg-red-50'}`}>
                                                <div className="flex items-center gap-2">
                                                    {data.passed ? (
                                                        <CheckCircle className="w-5 h-5 text-green-500" />
                                                    ) : (
                                                        <XCircle className="w-5 h-5 text-red-500" />
                                                    )}
                                                    <span className={data.passed ? 'text-green-700' : 'text-red-700'}>
                                                        {data.passed ? 'Validation Passed' : 'Validation Failed'}
                                                    </span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>

                {/* ReAct Traces Sidebar */}
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Zap className="w-5 h-5 text-yellow-500" />
                        ReAct Traces
                    </h2>

                    <div className="bg-white rounded-xl border border-gray-200 p-4 max-h-[600px] overflow-y-auto">
                        {reactTraces.length === 0 ? (
                            <p className="text-gray-400 text-center py-8">
                                ReAct reasoning traces will appear here as the agent processes...
                            </p>
                        ) : (
                            <div className="space-y-4">
                                {reactTraces.map((trace, index) => (
                                    <div key={index} className="border-l-2 border-indigo-300 pl-3 space-y-2">
                                        <div>
                                            <span className="text-xs font-semibold text-purple-600 uppercase">Think</span>
                                            <p className="text-sm text-gray-700">{trace.thought}</p>
                                        </div>
                                        <div>
                                            <span className="text-xs font-semibold text-blue-600 uppercase">Act</span>
                                            <p className="text-sm text-gray-700">{trace.action}</p>
                                        </div>
                                        <div>
                                            <span className="text-xs font-semibold text-green-600 uppercase">Observe</span>
                                            <p className="text-sm text-gray-700">{trace.observation}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Run History */}
                    <h2 className="text-xl font-semibold flex items-center gap-2 mt-6">
                        <RefreshCw className="w-5 h-5 text-gray-500" />
                        Run History
                    </h2>

                    <div className="bg-white rounded-xl border border-gray-200 divide-y max-h-[300px] overflow-y-auto">
                        {runHistory.length === 0 ? (
                            <p className="text-gray-400 text-center py-4">No runs yet</p>
                        ) : (
                            runHistory.slice(0, 10).map((run) => (
                                <div key={run.run_id} className="p-3 hover:bg-gray-50">
                                    <div className="flex items-center justify-between">
                                        <span className="font-mono text-sm">{run.run_id}</span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs ${run.success ? 'bg-green-100 text-green-700' :
                                            run.status === 'running' ? 'bg-blue-100 text-blue-700' :
                                                'bg-red-100 text-red-700'
                                            }`}>
                                            {run.status}
                                        </span>
                                    </div>
                                    {run.total_time_seconds && (
                                        <div className="text-xs text-gray-500 mt-1">
                                            {run.total_time_seconds.toFixed(2)}s
                                        </div>
                                    )}
                                    {run.final_shacl_hash && (
                                        <div className="text-xs text-gray-400 font-mono">
                                            Hash: {run.final_shacl_hash}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
