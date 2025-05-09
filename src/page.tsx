"use client"

import { useRef, useState } from "react"
import { ChevronLeft, ChevronRight, Play, Pause, RefreshCw, Maximize2, Volume2, Settings } from "lucide-react"
import VideoPlayer from "@/components/video-player"

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(1106) // 18:26 in seconds
  const videoRef = useRef<HTMLVideoElement>(null)

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

  return (
    <div className="flex flex-col h-screen bg-black text-white">
      {/* Header */}
      <div className="flex justify-between items-center p-3 bg-black">
        <div className="flex items-center gap-2">
          <div className="text-white font-semibold">Serie 1 vs. Høng</div>
          <div className="text-xs text-gray-400">May 9, 2019 • 27 views</div>
          <div className="text-xs bg-gray-700 px-2 py-0.5 rounded">LEAGUE</div>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-1 bg-white/10 hover:bg-white/20 px-3 py-1 rounded">
            <span>Open in Zube</span>
          </button>
          <button className="flex items-center gap-1 bg-white/10 hover:bg-white/20 px-3 py-1 rounded">
            <span>Share</span>
          </button>
          <button className="flex items-center gap-1 bg-white/10 hover:bg-white/20 px-3 py-1 rounded">
            <span>Download</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">MP</div>
        </div>
      </div>

      {/* Main Video Area */}
      <div className="flex-1 relative">
        <VideoPlayer
          ref={videoRef}
          onTimeUpdate={(time) => setCurrentTime(time)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />

        {/* Video Controls Overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
          {/* Timeline */}
          <div className="flex items-center gap-2 mb-2">
            <button onClick={togglePlayPause} className="text-white hover:text-gray-300">
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>
            <button className="text-white hover:text-gray-300">
              <ChevronLeft size={20} />
            </button>
            <button className="text-white hover:text-gray-300">
              <ChevronRight size={20} />
            </button>
            <button className="text-white hover:text-gray-300">
              <RefreshCw size={16} />
            </button>

            <div className="text-xs text-white/80 ml-2">
              {formatTime(currentTime)} / {formatTime(duration)}
            </div>

            <div className="flex-1 mx-4">
              <div className="relative h-1 bg-white/30 rounded-full">
                <div
                  className="absolute top-0 left-0 h-full bg-white rounded-full"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
                {/* Timeline markers */}
                {Array.from({ length: 20 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 w-0.5 h-1 bg-white/50"
                    style={{ left: `${(i / 19) * 100}%` }}
                  />
                ))}
              </div>
            </div>

            <button className="text-white hover:text-gray-300">
              <Volume2 size={20} />
            </button>
            <button className="text-white hover:text-gray-300">
              <Settings size={20} />
            </button>
            <button className="text-white hover:text-gray-300">
              <Maximize2 size={20} />
            </button>
          </div>
        </div>

        {/* Veo Logo Watermark */}
        <div className="absolute bottom-20 right-10 opacity-50">
          <div className="text-4xl font-bold text-white/70">veo</div>
        </div>
      </div>
    </div>
  )
}
