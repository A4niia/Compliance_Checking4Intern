import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import FOLViewer from './pages/FOLViewer'
import Pipeline from './pages/Pipeline'
import Results from './pages/Results'
import Validation from './pages/Validation'

function App() {
    const [sidebarOpen, setSidebarOpen] = useState(true)

    return (
        <BrowserRouter>
            <div className="flex h-screen bg-gray-50">
                <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
                <main className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? 'ml-72' : 'ml-20'}`}>
                    <div className="p-8 max-w-7xl mx-auto">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/methodology" element={<Pipeline />} />
                            <Route path="/results" element={<Results />} />
                            <Route path="/validation" element={<Validation />} />
                            <Route path="/rules" element={<Rules />} />
                            <Route path="/fol" element={<FOLViewer />} />
                        </Routes>
                    </div>
                </main>
            </div>
        </BrowserRouter>
    )
}

export default App
