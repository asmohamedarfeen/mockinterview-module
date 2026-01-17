/**
 * HR Avatar Component
 * Professional female HR interviewer avatar with state animations
 */
interface HRAvatarProps {
  state: 'idle' | 'speaking' | 'listening' | 'thinking'
  size?: number
}

export default function HRAvatar({ state, size = 120 }: HRAvatarProps) {
  const getAvatarColor = () => {
    switch (state) {
      case 'speaking':
        return 'bg-meet-blue'
      case 'listening':
        return 'bg-meet-green'
      case 'thinking':
        return 'bg-yellow-500'
      default:
        return 'bg-meet-gray'
    }
  }

  const getAnimation = () => {
    if (state === 'speaking' || state === 'listening') {
      return 'animate-pulse'
    }
    return ''
  }

  // Professional female avatar SVG
  const AvatarSVG = () => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="absolute inset-0"
    >
      {/* Face circle */}
      <circle cx="60" cy="60" r="50" fill="#f4c2a1" />
      
      {/* Hair */}
      <path
        d="M30 45 Q30 25 50 25 Q70 25 90 25 Q110 25 110 45 Q110 55 100 60 Q90 65 80 60 Q70 55 60 55 Q50 55 40 60 Q30 65 20 60 Q10 55 10 45 Q10 25 30 45"
        fill="#4a3728"
      />
      
      {/* Eyes */}
      <circle cx="45" cy="55" r="4" fill="#202124" />
      <circle cx="75" cy="55" r="4" fill="#202124" />
      
      {/* Nose */}
      <ellipse cx="60" cy="65" rx="3" ry="4" fill="#d4a574" />
      
      {/* Mouth */}
      <path
        d="M50 75 Q60 80 70 75"
        stroke="#202124"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
      />
      
      {/* Professional blazer */}
      <rect x="35" y="70" width="50" height="40" fill="#1a73e8" rx="5" />
      <path d="M60 70 L60 110" stroke="#0d47a1" strokeWidth="2" />
    </svg>
  )

  return (
    <div className="relative flex items-center justify-center">
      <div
        className={`${getAvatarColor()} ${getAnimation()} rounded-full flex items-center justify-center shadow-lg transition-all duration-300`}
        style={{ width: size, height: size }}
      >
        <div className="relative w-full h-full">
          <AvatarSVG />
        </div>
      </div>
      
      {/* Status ring */}
      {state !== 'idle' && (
        <div
          className={`absolute inset-0 rounded-full border-4 ${
            state === 'speaking'
              ? 'border-meet-blue animate-ping'
              : state === 'listening'
              ? 'border-meet-green animate-pulse'
              : 'border-yellow-500'
          }`}
          style={{ width: size, height: size }}
        />
      )}
    </div>
  )
}
