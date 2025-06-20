import React from 'react'
import { useParams } from 'react-router-dom'
import StreamDualVideo from './StreamDualVideo'

const StreamDualVideoWrapper: React.FC = () => {
  const { hash1, hash2 } = useParams<{ hash1: string; hash2: string }>()

  return <StreamDualVideo hash1={hash1!} hash2={hash2!} />
}

export default StreamDualVideoWrapper
