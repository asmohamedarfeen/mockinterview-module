/**
 * Enhanced Status Indicator Component
 * Color-coded states with smooth animations and icons
 */
type StatusType = 'idle' | 'setup' | 'listening' | 'thinking' | 'speaking' | 'completed'

interface StatusIndicatorProps {
  status: StatusType
  message?: string
}

export default function StatusIndicator({ status, message }: StatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'listening':
        return {
          color: 'bg-meet-red',
          text: 'Listening',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          ),
        }
      case 'speaking':
        return {
          color: 'bg-meet-blue',
          text: 'Speaking',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
            </svg>
          ),
        }
      case 'thinking':
        return {
          color: 'bg-yellow-500',
          text: 'Processing',
          icon: (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ),
        }
      case 'completed':
        return {
          color: 'bg-meet-green',
          text: 'Completed',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
          ),
        }
      default:
        return {
          color: 'bg-meet-gray',
          text: 'Ready',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          ),
        }
    }
  }

  const config = getStatusConfig()
  const isAnimated = status === 'listening' || status === 'thinking'

  return (
    <div className="flex items-center space-x-3">
      <div
        className={`${config.color} ${
          isAnimated ? 'animate-pulse' : ''
        } w-3 h-3 rounded-full transition-all duration-300`}
      />
      <div className="flex items-center space-x-2 text-meet-light-gray">
        {config.icon}
        <span className="text-sm font-medium capitalize">{config.text}</span>
      </div>
      {message && (
        <span className="text-sm text-meet-light-gray ml-2">• {message}</span>
      )}
    </div>
  )
}
