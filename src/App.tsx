import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const App: React.FC = () => {
  const [videoURL, setVideoURL] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const navigate = useNavigate();

 const handleStreamVideo = async () => {
  setErrorMessage(null); // Reset any previous error messages
  try {
    const response = await fetch('http://localhost:5000/process-video', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: videoURL }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const { output_url } = await response.json();
    const videoId = output_url.split('/').pop(); // Extract video ID from output_url

    // Navigate to the streaming page using the video ID
    navigate(`/stream/${videoId}`);
  } catch (error: unknown) {
    console.error('Error generating hash link:', error);

  }
};


  return (
    <div className="app">
      <h1>Stream MP4 Recording</h1>

      <input
        type="text"
        placeholder="Enter video URL"
        value={videoURL}
        onChange={(e) => setVideoURL(e.target.value)}
      />
      <button onClick={handleStreamVideo}>Stream Video</button>
      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
    </div>
  );
};

export default App;
