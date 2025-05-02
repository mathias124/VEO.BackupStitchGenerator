import React, { useState } from 'react';

const App: React.FC = () => {
  const [videoURL1, setVideoURL1] = useState<string>('');
  const [videoURL2, setVideoURL2] = useState<string>('');
  const [trimURL, setTrimURL] = useState<string>(''); // Stream URL for trim
  const [startTime, setStartTime] = useState<string>(''); // Start time in seconds
  const [duration, setDuration] = useState<string>(''); // Duration in seconds
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleMergeVideos = async () => {
    setErrorMessage(null);
    try {
      const response = await fetch('http://localhost:5000/process-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url1: videoURL1, url2: videoURL2 }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.hash) {
        window.location.href = `/stream/${data.hash}`;
      }
    } catch (error) {
      console.error('Error merging videos:', error);
      setErrorMessage('Failed to merge videos. Please check the URLs and try again.');
    }
  };

  const handleTrimVideo = async () => {
    setErrorMessage(null);
    try {
      const response = await fetch('http://localhost:5000/trim-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: trimURL,
          start: startTime,
          duration: duration,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.hash) {
        window.location.href = `/stream/${data.hash}`;
      }
    } catch (error) {
      console.error('Error trimming video:', error);
      setErrorMessage('Failed to trim video. Please check the URL, start time, and duration.');
    }
  };

  return (
    <div className="app">
      <h1>Merge 2 Veo Follow Cam Recordings</h1>
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

      <hr />

      <h1>Trim a Veo Recording (Start + Duration)</h1>
      <div>
        <input
          type="text"
          placeholder="Enter streamable video URL"
          value={trimURL}
          onChange={(e) => setTrimURL(e.target.value)}
        />
        <br />
        <input
          type="text"
          placeholder="Start time in seconds (e.g. 30)"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
        />
        <br />
        <input
          type="text"
          placeholder="Duration in seconds (e.g. 45)"
          value={duration}
          onChange={(e) => setDuration(e.target.value)}
        />
        <br />
        <button onClick={handleTrimVideo}>Trim Video</button>
      </div>

      {errorMessage && <p style={{ color: 'red' }}>{errorMessage}</p>}
    </div>
  );
};

export default App;
