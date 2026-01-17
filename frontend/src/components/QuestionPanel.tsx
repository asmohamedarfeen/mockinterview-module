/**
 * Enhanced Question Panel Component
 * Professional question display with typing animation
 */
import { useState, useEffect } from 'react'

interface QuestionPanelProps {
  question: string
  questionNumber: number
  totalQuestions: number
  isVisible: boolean
}

export default function QuestionPanel({
  question,
  questionNumber,
  totalQuestions,
  isVisible,
}: QuestionPanelProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    if (!isVisible || !question) {
      setDisplayedText('')
      return
    }

    setIsTyping(true)
    setDisplayedText('')

    let currentIndex = 0
    const typingInterval = setInterval(() => {
      if (currentIndex < question.length) {
        setDisplayedText(question.substring(0, currentIndex + 1))
        currentIndex++
      } else {
        setIsTyping(false)
        clearInterval(typingInterval)
      }
    }, 30) // Typing speed

    return () => clearInterval(typingInterval)
  }, [question, isVisible])

  if (!isVisible || !question) {
    return null
  }

  return (
    <div className="bg-meet-darker rounded-xl p-8 w-full max-w-3xl shadow-2xl border border-meet-gray">
      {/* Question number indicator */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-meet-blue text-white px-4 py-1 rounded-full text-sm font-semibold">
            Question {questionNumber} of {totalQuestions}
          </div>
          {isTyping && (
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-meet-blue rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-meet-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-meet-blue rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
        </div>
      </div>

      {/* Question text */}
      <div className="text-white text-xl leading-relaxed">
        {displayedText}
        {isTyping && <span className="inline-block w-1 h-6 bg-meet-blue ml-1 animate-pulse" />}
      </div>
    </div>
  )
}
