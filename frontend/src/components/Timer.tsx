/**
 * Interview Timer Component
 * Tracks interview duration with MM:SS format
 */
import { useState, useEffect, useRef } from 'react'

interface TimerProps {
  isActive: boolean
  onTimeUpdate?: (seconds: number) => void
}

export default function Timer({ isActive, onTimeUpdate }: TimerProps) {
  const [seconds, setSeconds] = useState(0)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isActive) {
      intervalRef.current = setInterval(() => {
        setSeconds((prev) => {
          const newSeconds = prev + 1
          if (onTimeUpdate) {
            onTimeUpdate(newSeconds)
          }
          return newSeconds
        })
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isActive, onTimeUpdate])

  const formatTime = (totalSeconds: number): string => {
    const minutes = Math.floor(totalSeconds / 60)
    const secs = totalSeconds % 60
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  return (
    <div className="flex items-center space-x-2">
      <div className="w-2 h-2 rounded-full bg-meet-red animate-pulse" />
      <span className="text-white font-mono text-lg font-semibold">{formatTime(seconds)}</span>
    </div>
  )
}
