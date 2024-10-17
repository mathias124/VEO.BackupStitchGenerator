import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const StreamVideo: React.FC = () => {
  const { hash_link } = useParams<{ hash_link: string }>(); // Retrieve the hash from the URL
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);

  useEffect(() => {
    const fetchVideo = async () => {
      try {
        // Ensure the correct URL is used based on your setup
        const response = await fetch(`http://localhost:5000/stream/${hash_link}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const blob = await response.blob();
        setVideoBlob(blob);
      } catch (error) {
        console.error('Error fetching video:', error);
      }
    };

    fetchVideo();
  }, [hash_link]);

  return (
    <div>
      {videoBlob ? (
        <video controls>
          <source src={URL.createObjectURL(videoBlob)} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      ) : (
        <p>Loading video...</p>
      )}
    </div>
  );
};

export default StreamVideo;
