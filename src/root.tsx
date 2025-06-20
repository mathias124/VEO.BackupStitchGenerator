import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import App from './App'
import StreamVideo from './StreamVideo'
import StreamDualVideoWrapper from './StreamDualVideoWrapper'

const Root: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/stream/:hash_link" element={<StreamVideo />} />
        <Route path="/stream-dual/:hash1/:hash2" element={<StreamDualVideoWrapper />} />
      </Routes>
    </Router>
  )
}

export default Root
