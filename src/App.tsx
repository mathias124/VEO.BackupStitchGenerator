"use client"

import type React from "react"
import { useRef, useState } from "react"
import "./App.css"

const App: React.FC = () => {
  const [videoURL1, setVideoURL1] = useState("")
  const [videoURL2, setVideoURL2] = useState("")
  const [trimURL, setTrimURL] = useState("")
  const [startTime, setStartTime] = useState<number>(0)
  const [endTime, setEndTime] = useState<number>(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  const handleMergeVideos = async () => {
    setErrorMessage(null)
    try {
      const response = await fetch("http://localhost:5000/process-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url1: videoURL1, url2: videoURL2 }),
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const data = await response.json()
      if (data.hash) window.location.href = `/stream/${data.hash}`
    } catch (error) {
      console.error("Error merging videos:", error)
      setErrorMessage("Failed to merge videos. Please check the URLs and try again.")
    }
  }

  const handleTrimVideo = async () => {
    setErrorMessage(null)
    const duration = Math.max(0, endTime - startTime)

    if (!trimURL || duration <= 0) {
      setErrorMessage("Please set a valid start and end time.")
      return
    }

    try {
      const response = await fetch("http://localhost:5000/trim-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: trimURL,
          start: startTime.toFixed(2),
          duration: duration.toFixed(2),
        }),
      })

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

      const data = await response.json()
      if (data.hash) window.location.href = `/stream/${data.hash}`
    } catch (error) {
      console.error("Error trimming video:", error)
      setErrorMessage("Failed to trim video. Please check the URL and try again.")
    }
  }

  const getProxiedSrc = (url: string) => `http://localhost:5000/proxy-video?url=${encodeURIComponent(url)}`

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying)
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
    }
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes.toString().padStart(2, "0")}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const timeline = e.currentTarget
    const rect = timeline.getBoundingClientRect()
    const pos = (e.clientX - rect.left) / rect.width
    if (videoRef.current) {
      videoRef.current.currentTime = pos * duration
    }
  }

  return (
    <div className="app">
      <div className="veo-container">
        <div className="veo-header">
          <div className="veo-title-section">
            <div className="veo-title">Veo Fusionizer</div>


          </div>
          <div className="veo-actions">
            <div className="veo-avatar">Support</div>
          </div>
        </div>

        <div className="veo-player">
          {trimURL ? (
            <video
              ref={videoRef}
              src={getProxiedSrc(trimURL)}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              className="veo-video"
            />
          ) : (
            <div className="veo-placeholder">
              <img
                src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-vvoe9mgJVBDd8RdHBpzYJ2uZgzQMnN.png"
                alt="Soccer field"
                className="veo-placeholder-image"
              />
            </div>
          )}

          <div className="veo-controls">
            <div className="veo-timeline-container">
              <div className="veo-timeline" onClick={handleSeek}>
                <div className="veo-progress" style={{ width: `${(currentTime / duration) * 100}%` }}></div>
                {Array.from({ length: 20 }).map((_, i) => (
                  <div key={i} className="veo-marker" style={{ left: `${(i / 19) * 100}%` }}></div>
                ))}
              </div>
            </div>

            <div className="veo-controls-buttons">
              <button className="veo-control-button" onClick={togglePlayPause}>
                {isPlaying ? "❚❚" : "▶"}
              </button>


              <div className="veo-time">
                {formatTime(currentTime)} / {formatTime(duration)}
              </div>

              <div className="veo-spacer"></div>


            </div>
          </div>


        </div>
      </div>

      <div className="tools-container">
        <div className="tool-section">
          <h1>Merge 2 Veo Follow Cam Recordings</h1>
          <input
            type="text"
            placeholder="Enter first video URL"
            value={videoURL1}
            onChange={(e) => setVideoURL1(e.target.value)}
          />
          <input
            type="text"
            placeholder="Enter second video URL"
            value={videoURL2}
            onChange={(e) => setVideoURL2(e.target.value)}
          />
          <button onClick={handleMergeVideos} className="action-button">
            Merge Videos
          </button>
        </div>

        <div className="tool-section">
          <h1>Trim a Veo Recording Visually</h1>
          <input
            type="text"
            placeholder="Enter streamable video URL"
            value={trimURL}
            onChange={(e) => setTrimURL(e.target.value)}
          />

          {trimURL && (
            <div className="trim-controls">
              <div className="trim-buttons">
                <button onClick={() => setStartTime(videoRef.current?.currentTime || 0)} className="action-button">
                  Set Start Time ({formatTime(startTime)})
                </button>

                <button onClick={() => setEndTime(videoRef.current?.currentTime || 0)} className="action-button">
                  Set End Time ({formatTime(endTime)})
                </button>
              </div>

              <div className="trim-range">
                <strong>Trim Range:</strong> {formatTime(startTime)} → {formatTime(endTime)}
              </div>

              <button onClick={handleTrimVideo} className="action-button">
                Trim Video
              </button>
            </div>
          )}
        </div>



        {errorMessage && <div className="error-message">{errorMessage}</div>}
      </div>
    </div>
  )
}

export default App
