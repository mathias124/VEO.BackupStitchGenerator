import React, { useState } from 'react';

const App: React.FC = () => {
  const [videoURL1, setVideoURL1] = useState<string>('');
  const [videoURL2, setVideoURL2] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleMergeVideos = async () => {
    setErrorMessage(null); // Reset error message
    try {
      const response = await fetch('http://localhost:5000/process-video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url1: videoURL1, url2: videoURL2 }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.hash) {
        window.location.href = `/stream/${data.hash}`; // Redirect to the stream page
      }
    } catch (error) {
      console.error('Error merging videos:', error);
      setErrorMessage('Failed to merge videos. Please check the URLs and try again.');
    }
  };

  return (
    <div className="app">
      <h1>Merge 2 Veo Follow Cam Streams</h1>
      <div>
        <input
          type="text"
          placeholder="Enter first video URL"
          value={videoURL1}
          onChange={(e) => setVideoURL1(e.target.value)}
        />
        <br />
        <input
          type="text"
          placeholder="Enter second video URL"
          value={videoURL2}
          onChange={(e) => setVideoURL2(e.target.value)}
        />
        <br />
        <button onClick={handleMergeVideos}>Merge Videos</button>
      </div>
      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
      <div>
        <p>Enter two video URLs and click "Merge Videos" to see the result.</p>
      </div>
    </div>
  );
};

export default App;
