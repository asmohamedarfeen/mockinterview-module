/**
 * Real-time audio waveform visualization
 * Google Meet style dark theme
 */
import { useEffect, useRef } from 'react'

interface WaveformProps {
  isActive: boolean
  audioLevel?: number // 0-1 for visualization
}

export default function Waveform({ isActive, audioLevel = 0 }: WaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number>()
  const barHeightsRef = useRef<number[]>([])
  const lastAudioLevelRef = useRef<number>(0)

  // Initialize bar heights array
  useEffect(() => {
    if (barHeightsRef.current.length === 0) {
      barHeightsRef.current = new Array(50).fill(0)
    }
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const barCount = 50
    const barWidth = width / barCount - 2
    const maxBarHeight = height * 0.8

    // Smooth audio level changes
    const smoothingFactor = 0.3
    lastAudioLevelRef.current = 
      lastAudioLevelRef.current * (1 - smoothingFactor) + audioLevel * smoothingFactor

    const draw = () => {
      // Clear canvas
      ctx.fillStyle = '#202124'
      ctx.fillRect(0, 0, width, height)

      if (!isActive) {
        // Draw idle state - minimal bars
        ctx.fillStyle = '#3c4043'
        const barSpacing = 8
        const centerY = height / 2

        for (let i = 0; i < width; i += barWidth + barSpacing) {
          const barHeight = 2
          ctx.fillRect(i, centerY - barHeight / 2, barWidth, barHeight)
        }
      } else {
        // Update bar heights with smooth animation
        const baseLevel = lastAudioLevelRef.current
        
        for (let i = 0; i < barCount; i++) {
          // Create wave pattern with audio level influence
          const wavePhase = (i / barCount) * Math.PI * 4
          const waveComponent = Math.sin(wavePhase + Date.now() * 0.01) * 0.3
          const randomVariation = (Math.random() - 0.5) * 0.2
          
          // Target height based on audio level
          const targetHeight = Math.max(0.1, baseLevel + waveComponent + randomVariation)
          
          // Smooth transition to target height
          barHeightsRef.current[i] = 
            barHeightsRef.current[i] * 0.7 + targetHeight * 0.3
        }

        // Draw active waveform with gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, height)
        gradient.addColorStop(0, '#1a73e8') // Google Meet blue
        gradient.addColorStop(0.5, '#4285f4')
        gradient.addColorStop(1, '#34a853') // Green for high levels
        
        ctx.fillStyle = gradient

        for (let i = 0; i < barCount; i++) {
          const barHeight = barHeightsRef.current[i] * maxBarHeight
          const x = (width / barCount) * i
          const y = (height - barHeight) / 2

          // Draw rounded rectangle for smoother look
          const radius = 2
          ctx.beginPath()
          ctx.moveTo(x + radius, y)
          ctx.lineTo(x + barWidth - radius, y)
          ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius)
          ctx.lineTo(x + barWidth, y + barHeight - radius)
          ctx.quadraticCurveTo(x + barWidth, y + barHeight, x + barWidth - radius, y + barHeight)
          ctx.lineTo(x + radius, y + barHeight)
          ctx.quadraticCurveTo(x, y + barHeight, x, y + barHeight - radius)
          ctx.lineTo(x, y + radius)
          ctx.quadraticCurveTo(x, y, x + radius, y)
          ctx.closePath()
          ctx.fill()
        }
      }

      animationFrameRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [isActive, audioLevel])

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={100}
      className="w-full h-24 rounded-lg"
    />
  )
}
