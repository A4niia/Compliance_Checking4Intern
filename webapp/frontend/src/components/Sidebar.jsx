import { NavLink } from 'react-router-dom'
import { Home, Workflow, BarChart3, FileText, Code, ChevronLeft, ChevronRight, Sparkles, Shield } from 'lucide-react'

const navItems = [
    { path: '/', icon: Home, label: 'Research Overview', description: 'Key findings & RQs' },
    { path: '/methodology', icon: Workflow, label: '5-Phase Pipeline', description: 'Complete methodology' },
    { path: '/results', icon: BarChart3, label: 'Results & Validation', description: 'All experiments' },
    { path: '/validation', icon: Shield, label: 'Validation Demo', description: 'Interactive checking' },
    { path: '/rules', icon: FileText, label: 'Rules Browser', description: '97 annotated rules' },
    { path: '/fol', icon: Code, label: 'FOL Formulas', description: 'Logic representations' }
]

export default function Sidebar({ open, setOpen }) {
    return (
        <aside className={`fixed left-0 top-0 h-screen bg-white border-r border-gray-200 transition-all duration-300 z-50 shadow-md ${open ? 'w-72' : 'w-20'}`}>
            <div className="flex items-center gap-3 p-6 border-b border-gray-100">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                </div>
                {open && (
                    <div>
                        <h1 className="font-bold text-lg text-gray-800">AITPolicyChecker</h1>
                        <p className="text-xs text-gray-500">Mr.Ponkrit Kaewsawee st124960</p>
                    </div>
                )}
            </div>
            <nav className="p-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-start gap-3 px-4 py-3 rounded-xl transition-all ${isActive ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-100' : 'text-gray-600 hover:bg-gray-50'
                            }`
                        }
                    >
                        <item.icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        {open && (
                            <div>
                                <div className="font-semibold text-sm">{item.label}</div>
                                <div className="text-xs text-gray-500 mt-0.5">{item.description}</div>
                            </div>
                        )}
                    </NavLink>
                ))}
            </nav>
            {open && (
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100 bg-gray-50">
                    <div className="text-xs text-gray-600">
                        <div className="font-semibold text-gray-800 mb-1">Data Status:</div>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <span>97 rules loaded ✓</span>
                        </div>
                        <div className="text-gray-500 mt-1">Updated: Jan 31, 2026</div>
                    </div>
                </div>
            )}
            <button
                onClick={() => setOpen(!open)}
                className="absolute bottom-24 right-[-12px] w-6 h-6 bg-white border border-gray-200 shadow-md rounded-full flex items-center justify-center text-gray-400 hover:text-gray-700"
            >
                {open ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
        </aside>
    )
}
