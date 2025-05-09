"use client"

import { forwardRef, useEffect, useState, useImperativeHandle } from "react"

interface VideoPlayerProps {
  onTimeUpdate?: (time: number) => void
  onPlay?: () => void
  onPause?: () => void
}

const VideoPlayer = forwardRef<HTMLVideoElement, VideoPlayerProps>(({ onTimeUpdate, onPlay, onPause }, ref) => {
  const [videoSrc, setVideoSrc] = useState("")

  useEffect(() => {
    // Use the soccer field image as a placeholder until we have a real video
    // In a real implementation, you would use an actual video file
    setVideoSrc("/soccer-field.jpg")
  }, [])

  useImperativeHandle(ref, () => ({
    play: () => {

      if (onPlay) onPlay()
    },
    pause: () => {
      if (onPause) onPause()
    },
    get currentTime() {
      return 0
    },
  }))

  return (
    <div className="w-full h-full bg-black flex items-center justify-center">
      {/* For a real video player, you would use the video element */}
      {/* <video
          ref={ref}
          src={videoSrc}
          className="w-full h-full object-contain"
          onTimeUpdate={(e) => onTimeUpdate?.(e.currentTarget.currentTime)}
          onPlay={() => onPlay?.()}
          onPause={() => onPause?.()}
        /> */}

      {/* Using an image for the demo */}
      <img
        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/image-vvoe9mgJVBDd8RdHBpzYJ2uZgzQMnN.png"
        alt="Soccer field"
        className="w-full h-full object-contain"
      />
    </div>
  )
})

VideoPlayer.displayName = "VideoPlayer"

export default VideoPlayer
