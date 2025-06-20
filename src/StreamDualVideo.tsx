import React, { useEffect, useState } from "react"

interface Props {
  hash1: string
  hash2: string
}

const StreamDualVideo: React.FC<Props> = ({ hash1, hash2 }) => {
  const [videoBlob1, setVideoBlob1] = useState<Blob | null>(null)
  const [videoBlob2, setVideoBlob2] = useState<Blob | null>(null)

  useEffect(() => {
    const fetchVideo = async (hash: string, setter: (blob: Blob) => void) => {
      try {
        const response = await fetch(`http://localhost:5000/stream/${hash}`, {
          headers: { Range: "bytes=0-" },
        })
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
        const blob = await response.blob()
        setter(blob)
      } catch (e) {
        console.error("Error loading video:", e)
      }
    }

    fetchVideo(hash1, setVideoBlob1)
    fetchVideo(hash2, setVideoBlob2)
  }, [hash1, hash2])

  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", padding: "2rem" }}>
      <div style={{ flex: 1 }}>
        <h3>Interactive</h3>
        {videoBlob1 ? (
          <video controls width="100%">
            <source src={URL.createObjectURL(videoBlob1)} type="video/mp4" />
            Your browser does not support video 1.
          </video>
        ) : (
          <p>Loading Video 1…</p>
        )}
      </div>

      <div style={{ flex: 1 }}>
        <h3>FollowCam</h3>
        {videoBlob2 ? (
          <video controls width="100%">
            <source src={URL.createObjectURL(videoBlob2)} type="video/mp4" />
            Your browser does not support video 2.
          </video>
        ) : (
          <p>Loading Video 2…</p>
        )}
      </div>
    </div>
  )
}

export default StreamDualVideo
