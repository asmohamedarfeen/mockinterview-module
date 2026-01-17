/**
 * Main Interview Page
 * Google Meet style dark theme with centered mic button and waveform
 */
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { WebSocketClient, ServerMessageType, MessageType } from '../services/websocket'
import { AudioRecorder } from '../audio/recorder'
import { SilenceDetector } from '../audio/silenceDetector'
import MicButton from '../components/MicButton'
import Waveform from '../components/Waveform'
import Timer from '../components/Timer'
import HRAvatar from '../components/HRAvatar'
import QuestionPanel from '../components/QuestionPanel'
import StatusIndicator from '../components/StatusIndicator'

type InterviewState = 'idle' | 'setup' | 'listening' | 'thinking' | 'speaking' | 'completed'

export default function Interview() {
  const navigate = useNavigate()
  const [sessionId] = useState(() => `session-${Date.now()}`)
  const [state, setState] = useState<InterviewState>('idle')
  const [isConnected, setIsConnected] = useState(false)
  const [currentQuestion, setCurrentQuestion] = useState<string>('')
  const [questionNumber, setQuestionNumber] = useState(0)
  const [totalQuestions, setTotalQuestions] = useState(5)
  const [statusMessage, setStatusMessage] = useState('Ready to start interview')
  const [audioLevel, setAudioLevel] = useState(0)
  const [interviewStarted, setInterviewStarted] = useState(false)

  const wsClientRef = useRef<WebSocketClient | null>(null)
  const recorderRef = useRef<AudioRecorder | null>(null)
  const silenceDetectorRef = useRef<SilenceDetector | null>(null)

  // Initialize WebSocket connection
  useEffect(() => {
    const client = new WebSocketClient(sessionId)
    wsClientRef.current = client

    client.onOpen(() => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setStatusMessage('Connected - Ready to start')
    })

    client.onClose(() => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      setStatusMessage('Disconnected')
    })

    client.onError((error) => {
      console.error('WebSocket error:', error)
      setStatusMessage('Connection error')
    })

    client.onMessage((message) => {
      handleServerMessage(message)
    })

    client.connect().catch((error) => {
      console.error('Failed to connect:', error)
      setStatusMessage('Failed to connect to server')
    })

    return () => {
      client.disconnect()
    }
  }, [sessionId])

  // Handle server messages
  const handleServerMessage = (message: any) => {
    switch (message.type) {
      case ServerMessageType.QUESTION_READY:
        setCurrentQuestion(message.question)
        setQuestionNumber(message.question_number)
        setTotalQuestions(message.total_questions)
        setState('speaking')
        setStatusMessage('Question ready')
        break

      case ServerMessageType.TTS_AUDIO:
        // Phase 3: Play TTS audio
        playTTSAudio(message.audio_base64, message.audio_format)
        break

      case ServerMessageType.STATE_UPDATE:
        setState(message.state.toLowerCase() as InterviewState)
        break

      case ServerMessageType.ERROR:
        setStatusMessage(`Error: ${message.error_message}`)
        console.error('Server error:', message)
        break

      case ServerMessageType.INTERVIEW_COMPLETE:
        setState('completed')
        setStatusMessage('Interview completed!')
        // Navigate to report page after a delay
        setTimeout(() => {
          navigate(`/report/${sessionId}`)
        }, 2000)
        break

      case ServerMessageType.EVALUATION_UPDATE:
        // Real-time evaluation updates (Phase 5)
        console.log('Evaluation update:', message.scores)
        break

      default:
        console.log('Unhandled message:', message)
    }
  }

  // Start interview
  const handleStartInterview = () => {
    if (!wsClientRef.current || !isConnected) {
      setStatusMessage('Not connected to server')
      return
    }

    // For Phase 1, we'll use placeholder values
    // Phase 2-3 will add proper job role/description input
    wsClientRef.current.send({
      type: MessageType.START_INTERVIEW,
      session_id: sessionId,
      job_role: 'Software Engineer',
      job_description: 'Full-stack development role',
      question_count: totalQuestions,
    })

    setState('setup')
    setStatusMessage('Starting interview...')
    setInterviewStarted(true)
  }

  // Toggle microphone
  const handleMicToggle = async () => {
    if (state === 'idle' || state === 'setup') {
      // Start interview if not started
      if (state === 'idle') {
        handleStartInterview()
      }
      // Start listening
      await startListening()
    } else if (state === 'listening') {
      stopListening()
    }
  }

  // Start listening
  const startListening = async () => {
    try {
      // Initialize recorder
      const recorder = new AudioRecorder({
        onTranscript: (transcript, isFinal) => {
          if (wsClientRef.current && isConnected) {
            wsClientRef.current.send({
              type: MessageType.TRANSCRIBE,
              session_id: sessionId,
              transcript,
              is_final: isFinal,
            })
          }
        },
        onError: (error) => {
          console.error('Recorder error:', error)
          setStatusMessage('Recording error')
          stopListening()
        },
        onStart: () => {
          setState('listening')
          setStatusMessage('Listening...')
        },
        onStop: () => {
          // Recorder stopped
        },
      })

      recorderRef.current = recorder

      // Request microphone permission
      const hasPermission = await recorder.requestPermission()
      if (!hasPermission) {
        setStatusMessage('Microphone permission denied')
        return
      }

      // Start recording
      await recorder.start()

      // Get audio stream and initialize silence detector
      const audioStream = recorder.getAudioStream()
      if (audioStream) {
        const silenceDetector = new SilenceDetector({
          onSilenceDetected: (durationSeconds) => {
            console.log(`Silence detected: ${durationSeconds.toFixed(1)}s`)
            // Send silence detected message
            if (wsClientRef.current && isConnected) {
              wsClientRef.current.send({
                type: MessageType.SILENCE_DETECTED,
                session_id: sessionId,
                duration_seconds: durationSeconds,
              })
            }
            // Auto-stop recording
            stopListening()
          },
          onAudioLevel: (level) => {
            // Update audio level for waveform visualization
            setAudioLevel(level)
          },
          onError: (error) => {
            console.error('Silence detector error:', error)
          },
        })

        await silenceDetector.initialize(audioStream)
        silenceDetectorRef.current = silenceDetector
      }
    } catch (error) {
      console.error('Failed to start listening:', error)
      setStatusMessage('Failed to start recording')
      stopListening()
    }
  }

  // Stop listening
  const stopListening = () => {
    if (recorderRef.current) {
      // Get final transcript before stopping
      const finalTranscript = recorderRef.current.getTranscriptBuffer()
      if (finalTranscript && wsClientRef.current && isConnected) {
        wsClientRef.current.send({
          type: MessageType.TRANSCRIBE,
          session_id: sessionId,
          transcript: finalTranscript,
          is_final: true,
        })
      }
      recorderRef.current.stop()
      recorderRef.current = null
    }

    if (silenceDetectorRef.current) {
      silenceDetectorRef.current.stop()
      silenceDetectorRef.current = null
    }

    setAudioLevel(0)
    setState('thinking')
    setStatusMessage('Processing your answer...')
  }

  // Play TTS audio (Phase 3)
  const playTTSAudio = async (audioBase64: string, audioFormat: string) => {
    try {
      // Decode base64 audio
      const audioData = atob(audioBase64)
      const audioArray = new Uint8Array(audioData.length)
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i)
      }

      // Create blob and audio element
      const blob = new Blob([audioArray], { type: audioFormat || 'audio/mp3' })
      const audioUrl = URL.createObjectURL(blob)
      const audio = new Audio(audioUrl)

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl)
        // After audio finishes, transition to listening state
        setState('listening')
        setStatusMessage('Listening for your answer...')
        // Auto-start listening
        startListening()
      }

      audio.onerror = (error) => {
        console.error('Audio playback error:', error)
        URL.revokeObjectURL(audioUrl)
        setStatusMessage('Audio playback error')
      }

      // Play audio
      await audio.play()
      setState('speaking')
      setStatusMessage('Playing question...')
    } catch (error) {
      console.error('Failed to play TTS audio:', error)
      setStatusMessage('Failed to play audio')
    }
  }

  // Determine avatar state
  const getAvatarState = (): 'idle' | 'speaking' | 'listening' | 'thinking' => {
    if (state === 'listening') return 'listening'
    if (state === 'speaking') return 'speaking'
    if (state === 'thinking') return 'thinking'
    return 'idle'
  }

  return (
    <div className="min-h-screen bg-meet-dark flex flex-col">
      {/* Header Bar */}
      <div className="flex justify-between items-center p-4 border-b border-meet-gray">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold text-white">Qrow IQ</h1>
          <span className="text-xs text-meet-light-gray">AI HR Mock Interview</span>
        </div>
        <div className="flex items-center space-x-4">
          {/* Timer */}
          {interviewStarted && <Timer isActive={state !== 'idle' && state !== 'completed'} />}
          
          {/* Connection Status */}
          <div
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              isConnected
                ? 'bg-meet-green text-white'
                : 'bg-meet-red text-white'
            }`}
          >
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
      </div>

      {/* Main Content Area - Google Meet Style */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-8">
        {/* HR Avatar */}
        <div className="flex-shrink-0">
          <HRAvatar state={getAvatarState()} size={140} />
        </div>

        {/* Question Panel */}
        <div className="w-full max-w-4xl flex justify-center">
          <QuestionPanel
            question={currentQuestion}
            questionNumber={questionNumber}
            totalQuestions={totalQuestions}
            isVisible={!!currentQuestion && state !== 'idle'}
          />
        </div>

        {/* Waveform */}
        <div className="w-full max-w-4xl">
          <Waveform isActive={state === 'listening'} audioLevel={audioLevel} />
        </div>

        {/* Status Indicator */}
        <StatusIndicator status={state} message={statusMessage} />

        {/* Mic Button - Centered */}
        <div className="flex-shrink-0">
          <MicButton
            isActive={state !== 'idle'}
            isListening={state === 'listening'}
            onClick={handleMicToggle}
            disabled={!isConnected || state === 'completed'}
          />
        </div>

        {/* Completed State - Show Report Link */}
        {state === 'completed' && (
          <div className="bg-meet-darker rounded-lg p-6 max-w-md text-center">
            <div className="text-meet-green text-2xl font-bold mb-2">Interview Completed!</div>
            <p className="text-meet-light-gray mb-4">Your report is being generated...</p>
            <button
              onClick={() => navigate(`/report/${sessionId}`)}
              className="bg-meet-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            >
              View Report
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-meet-gray p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center text-xs text-meet-light-gray">
          <div>
            <span>Session: {sessionId}</span>
          </div>
          <div>
            <span>Phase 6 & 7: Report Generation & Google Meet UI</span>
          </div>
        </div>
      </div>
    </div>
  )
}
