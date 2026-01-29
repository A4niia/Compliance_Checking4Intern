import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Rules from './pages/Rules'
import FOLViewer from './pages/FOLViewer'
import Validation from './pages/Validation'
import Demo from './pages/Demo'
import Agent from './pages/Agent'

function App() {
    const [sidebarOpen, setSidebarOpen] = useState(true)

    return (
        <BrowserRouter>
            <div className="flex h-screen">
                {/* Sidebar */}
                <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />

                {/* Main content */}
                <main className={`flex-1 overflow-auto transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
                    <div className="p-8">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/rules" element={<Rules />} />
                            <Route path="/fol" element={<FOLViewer />} />
                            <Route path="/validation" element={<Validation />} />
                            <Route path="/demo" element={<Demo />} />
                            <Route path="/agent" element={<Agent />} />
                        </Routes>
                    </div>
                </main>
            </div>
        </BrowserRouter>
    )
}

export default App
