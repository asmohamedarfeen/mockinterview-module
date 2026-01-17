import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Interview from './pages/Interview'
import Report from './pages/Report'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Interview />} />
        <Route path="/report/:sessionId" element={<Report />} />
      </Routes>
    </Router>
  )
}

export default App
