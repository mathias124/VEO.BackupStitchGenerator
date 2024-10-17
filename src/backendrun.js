const express = require('express');
const crypto = require('crypto');
const axios = require('axios');

const app = express();
app.use(express.json());

let videoStorage = {}; // Simple in-memory storage for demo purposes

// Generate a hash link for the video
app.post('/process-video', (req, res) => {
  const { url } = req.body;
  const hash = crypto.createHash('sha256').update(url).digest('hex');

  // Store the video URL in memory with the hash as key
  videoStorage[hash] = url;

  res.json({ hash_link: hash });
});

// Stream the video from the hash link
app.get('/stream/:hash', async (req, res) => {
  const hash = req.params.hash;
  const videoURL = videoStorage[hash];

  if (!videoURL) {
    return res.status(404).send('Video not found');
  }

  // Stream the video from the original source
  const response = await axios.get(videoURL, { responseType: 'stream' });
  response.data.pipe(res);
});

app.listen(5000, () => console.log('Server running on port 5000'));
