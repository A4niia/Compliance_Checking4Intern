import { NavLink } from 'react-router-dom'
import {
    Home,
    Workflow,
    BarChart3,
    FileText,
    Code,
    ChevronLeft,
    ChevronRight,
    Sparkles
} from 'lucide-react'

const navItems = [
    {
        path: '/',
        icon: Home,
        label: 'Research Overview',
        description: 'Key findings & RQs',
        color: 'primary'
    },
    {
        path: '/methodology',
        icon: Workflow,
        label: '4-Phase Pipeline',
        description: 'Methodology execution',
        color: 'purple'
    },
    {
        path: '/results',
        icon: BarChart3,
        label: 'Results & Validation',
        description: 'Experiments & findings',
        color: 'success'
    },
    {
        path: '/rules',
        icon: FileText,
        label: 'Rules Browser',
        description: '97 annotated rules',
        color: 'neutral'
    },
    {
        path: '/fol',
        icon: Code,
        label: 'FOL Formulas',
        description: 'Formal logic views',
        color: 'neutral'
    }
]

export default function Sidebar({ open, setOpen }) {
    return (
        <aside className={`fixed left-0 top-0 h-screen bg-white border-r border-neutral-200 transition-all duration-300 z-50 shadow-md ${open ? 'w-72' : 'w-20'}`}>
            {/* Logo */}
            <div className="flex items-center gap-3 p-6 border-b border-neutral-100">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                </div>
                {open && (
                    <div>
                        <h1 className="font-bold text-lg text-neutral-800">PolicyChecker</h1>
                        <p className="text-xs text-neutral-500">Research Demonstration</p>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `group flex items-start gap-3 px-4 py-3 rounded-xl transition-all duration-200 
                            ${isActive
                                ? 'bg-primary-50 text-primary-700 shadow-sm border border-primary-100'
                                : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
                            }`
                        }
                    >
                        <item.icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        {open && (
                            <div className="flex-1 min-w-0">
                                <div className="font-semibold text-sm">{item.label}</div>
                                <div className="text-xs text-neutral-500 mt-0.5 leading-tight">
                                    {item.description}
                                </div>
                            </div>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer Info */}
            {open && (
                <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-neutral-100 bg-neutral-50">
                    <div className="text-xs text-neutral-600">
                        <div className="font-semibold text-neutral-800 mb-1">Data Status:</div>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 rounded-full bg-success-500"></div>
                            <span>97 rules loaded ✓</span>
                        </div>
                        <div className="text-neutral-500 mt-1">
                            Updated: Jan 31, 2026
                        </div>
                    </div>
                </div>
            )}

            {/* Toggle button */}
            <button
                onClick={() => setOpen(!open)}
                className="absolute bottom-24 right-[-12px] w-6 h-6 bg-white border border-neutral-200 shadow-md rounded-full flex items-center justify-center text-neutral-400 hover:text-neutral-700 hover:bg-neutral-50 transition-colors"
            >
                {open ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </button>
        </aside>
    )
}
