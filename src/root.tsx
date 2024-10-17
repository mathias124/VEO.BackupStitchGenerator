import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import App from './App';
import StreamVideo from './StreamVideo'; // Your stream video component

const Root: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/stream/:hash_link" element={<StreamVideo />} />
      </Routes>
    </Router>
  );
};

export default Root;
