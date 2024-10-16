import React, { useState } from 'react';
import axios from 'axios';

const App: React.FC = () => {
  const [videoURL, setVideoURL] = useState<string>('');
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);

  const handleVideoStitch = async () => {
    try {
      const response = await axios.post('http://localhost:5000/process-video', {
        url: videoURL,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const { output_url } = response.data;
      const blob = await fetch(output_url).then(r => r.blob());
      setVideoBlob(blob);
    } catch (error) {
      console.error('Error during video processing:', error);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Enter video URL"
        value={videoURL}
        onChange={(e) => setVideoURL(e.target.value)}
      />
      <button onClick={handleVideoStitch}>Stitch Video</button>
      {videoBlob && (
        <video controls>
          <source src={URL.createObjectURL(videoBlob)} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      )}
    </div>
  );
};

export default App;
