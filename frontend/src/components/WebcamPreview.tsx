/**
 * WebcamPreview Component
 * Google Meet style self-view video in bottom right corner
 */
import { useEffect, useRef, useState } from 'react'

interface WebcamPreviewProps {
    className?: string
}

export default function WebcamPreview({ className = '' }: WebcamPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const [hasPermission, setHasPermission] = useState(false)
    const [isMinimized, setIsMinimized] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        let stream: MediaStream | null = null

        const startWebcam = async () => {
            try {
                console.log('Requesting webcam access...')
                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 320 },
                        height: { ideal: 240 },
                        facingMode: 'user',
                    },
                    audio: false,
                })

                console.log('Webcam stream obtained:', stream.id)

                if (videoRef.current) {
                    videoRef.current.srcObject = stream
                    // Wait for video to be ready
                    videoRef.current.onloadedmetadata = () => {
                        console.log('Video metadata loaded, playing...')
                        videoRef.current?.play().catch(err => {
                            console.error('Error playing video:', err)
                        })
                        setHasPermission(true)
                        setIsLoading(false)
                    }
                }
            } catch (error) {
                console.error('Webcam access error:', error)
                setHasPermission(false)
                setIsLoading(false)
            }
        }

        startWebcam()

        // Cleanup
        return () => {
            if (stream) {
                console.log('Stopping webcam stream')
                stream.getTracks().forEach((track) => track.stop())
            }
        }
    }, [])

    if (isMinimized) {
        return (
            <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
                <button
                    onClick={() => setIsMinimized(false)}
                    className="bg-meet-darker border-2 border-meet-gray rounded-full p-3 hover:bg-meet-gray transition-all shadow-2xl group"
                    title="Show camera"
                >
                    <svg
                        className="w-6 h-6 text-white group-hover:text-meet-blue transition-colors"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                    </svg>
                </button>
            </div>
        )
    }

    return (
        <div className={`fixed bottom-6 right-6 z-50 ${className}`}>
            <div className="relative group">
                {/* Video Container */}
                <div className="relative w-64 h-48 bg-meet-darker rounded-lg overflow-hidden border-2 border-meet-gray shadow-2xl">
                    {/* Always render video element */}
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className={`w-full h-full object-cover transform scale-x-[-1] ${hasPermission ? 'block' : 'hidden'
                            }`}
                    />

                    {/* Loading State */}
                    {isLoading && !hasPermission && (
                        <div className="absolute inset-0 flex items-center justify-center bg-meet-darker">
                            <div className="text-center p-4">
                                <div className="w-8 h-8 border-4 border-meet-blue border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                                <p className="text-xs text-meet-light-gray">Loading camera...</p>
                            </div>
                        </div>
                    )}

                    {/* Camera Off State */}
                    {!isLoading && !hasPermission && (
                        <div className="absolute inset-0 flex items-center justify-center bg-meet-darker">
                            <div className="text-center p-4">
                                <svg
                                    className="w-12 h-12 text-meet-light-gray mx-auto mb-2"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                                    />
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M6 18L18 6M6 6l12 12"
                                    />
                                </svg>
                                <p className="text-xs text-meet-light-gray">Camera Off</p>
                            </div>
                        </div>
                    )}

                    {/* Overlay Controls - Show on hover */}
                    {hasPermission && (
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center">
                                <span className="text-white text-xs font-medium bg-black/50 px-2 py-1 rounded">
                                    You
                                </span>
                                <button
                                    onClick={() => setIsMinimized(true)}
                                    className="bg-black/50 hover:bg-black/70 rounded-full p-1.5 transition-colors"
                                    title="Minimize"
                                >
                                    <svg
                                        className="w-4 h-4 text-white"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M19 9l-7 7-7-7"
                                        />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Name Label */}
                <div className="absolute -top-2 left-2 bg-meet-darker border border-meet-gray px-2 py-0.5 rounded text-xs text-white shadow-lg">
                    Your Camera
                </div>
            </div>
        </div>
    )
}
