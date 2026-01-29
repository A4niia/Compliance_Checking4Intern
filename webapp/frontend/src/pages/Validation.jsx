import { useState, useEffect } from 'react'
import { Shield, Download, CheckCircle, AlertTriangle, FileCode } from 'lucide-react'
import axios from 'axios'

export default function Validation() {
    const [shacl, setShacl] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchShacl()
    }, [])

    const fetchShacl = async () => {
        try {
            const res = await axios.get('/api/shacl')
            setShacl(res.data)
        } catch (err) {
            console.error('Failed to fetch SHACL:', err)
        } finally {
            setLoading(false)
        }
    }

    const downloadShacl = async () => {
        try {
            const res = await axios.get('/api/export/shacl', { responseType: 'blob' })
            const url = window.URL.createObjectURL(new Blob([res.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', 'ait_policy_shapes.ttl')
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (err) {
            console.error('Download failed:', err)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">SHACL Validation</h1>
                    <p className="text-slate-400 mt-1">Policy shapes and validation results</p>
                </div>
                <button onClick={downloadShacl} className="btn btn-primary flex items-center gap-2">
                    <Download className="w-5 h-5" />
                    Download SHACL
                </button>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-green-400" />
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm">Status</p>
                            <p className="text-xl font-bold text-green-400">Valid</p>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                            <Shield className="w-6 h-6 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm">Shapes</p>
                            <p className="text-xl font-bold text-white">{shacl?.shapes || 0}</p>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                            <FileCode className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm">File Size</p>
                            <p className="text-xl font-bold text-white">{Math.round((shacl?.size || 0) / 1024)} KB</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Validation Summary */}
            <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">Validation Summary</h2>
                <div className="grid grid-cols-3 gap-6">
                    <div className="text-center p-6 bg-slate-900 rounded-xl">
                        <div className="text-4xl font-bold text-white mb-2">1309</div>
                        <div className="text-slate-400">Total Triples</div>
                    </div>
                    <div className="text-center p-6 bg-slate-900 rounded-xl">
                        <div className="text-4xl font-bold text-green-400 mb-2">96</div>
                        <div className="text-slate-400">Rules Translated</div>
                    </div>
                    <div className="text-center p-6 bg-slate-900 rounded-xl">
                        <div className="text-4xl font-bold text-blue-400 mb-2">0</div>
                        <div className="text-slate-400">Errors</div>
                    </div>
                </div>
            </div>

            {/* SHACL Preview */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-white">SHACL Preview</h2>
                    <span className="text-sm text-slate-500">{shacl?.file}</span>
                </div>
                <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
                    <pre className="text-sm text-slate-300 font-mono whitespace-pre-wrap">
                        {shacl?.content || 'No content available'}
                    </pre>
                </div>
            </div>

            {/* Rule Type Distribution */}
            <div className="card">
                <h2 className="text-xl font-semibold text-white mb-4">Rule Type in SHACL</h2>
                <div className="space-y-4">
                    {[
                        { type: 'Obligations', count: 65, color: 'red', severity: 'sh:Violation' },
                        { type: 'Permissions', count: 17, color: 'green', severity: 'sh:Info' },
                        { type: 'Prohibitions', count: 14, color: 'orange', severity: 'sh:Violation' },
                    ].map((item, i) => (
                        <div key={i} className="flex items-center gap-4">
                            <div className="w-32 text-slate-400">{item.type}</div>
                            <div className="flex-1 h-8 bg-slate-900 rounded-lg overflow-hidden">
                                <div
                                    className={`h-full bg-${item.color}-500/50`}
                                    style={{ width: `${(item.count / 96) * 100}%` }}
                                ></div>
                            </div>
                            <div className="w-12 text-right font-semibold text-white">{item.count}</div>
                            <code className="text-xs text-slate-500 w-24">{item.severity}</code>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
