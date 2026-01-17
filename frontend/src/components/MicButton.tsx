/**
 * Central microphone button component
 * Google Meet style with animation states
 */
interface MicButtonProps {
  isActive: boolean
  isListening: boolean
  onClick: () => void
  disabled?: boolean
}

export default function MicButton({
  isActive,
  isListening,
  onClick,
  disabled = false,
}: MicButtonProps) {
  const getButtonColor = () => {
    if (disabled) return 'bg-meet-gray cursor-not-allowed'
    if (isListening) return 'bg-meet-red hover:bg-red-600'
    if (isActive) return 'bg-meet-blue hover:bg-blue-600'
    return 'bg-meet-gray hover:bg-meet-light-gray'
  }

  const getIcon = () => {
    if (isListening) {
      return (
        <svg
          className="w-12 h-12"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
        </svg>
      )
    }
    return (
      <svg
        className="w-12 h-12"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
        />
      </svg>
    )
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        ${getButtonColor()}
        w-20 h-20
        rounded-full
        flex items-center justify-center
        text-white
        transition-all duration-200
        shadow-lg
        focus:outline-none focus:ring-4 focus:ring-blue-300
        ${isListening ? 'animate-pulse' : ''}
      `}
      aria-label={isListening ? 'Stop listening' : 'Start listening'}
    >
      {getIcon()}
    </button>
  )
}
