/**
 * Landing Page
 * Job role and description input form before starting interview
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Landing() {
    const navigate = useNavigate()
    const [jobRole, setJobRole] = useState('')
    const [jobDescription, setJobDescription] = useState('')
    const [questionCount, setQuestionCount] = useState(5)
    const [errors, setErrors] = useState<{ jobRole?: string }>({})

    const handleStartInterview = () => {
        // Validate required fields
        const newErrors: { jobRole?: string } = {}

        if (!jobRole.trim()) {
            newErrors.jobRole = 'Job role is required'
        }

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors)
            return
        }

        // Navigate to interview with job data
        navigate('/interview', {
            state: {
                jobRole: jobRole.trim(),
                jobDescription: jobDescription.trim() || 'General position',
                questionCount,
            },
        })
    }

    return (
        <div className="min-h-screen bg-meet-dark flex flex-col">
            {/* Header */}
            <div className="border-b border-meet-gray p-6">
                <div className="max-w-4xl mx-auto">
                    <h1 className="text-3xl font-bold text-white mb-2">Qrow IQ</h1>
                    <p className="text-meet-light-gray">AI-Powered Mock Interview Platform</p>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex items-center justify-center p-6">
                <div className="w-full max-w-2xl">
                    {/* Welcome Card */}
                    <div className="bg-meet-darker rounded-2xl p-8 shadow-2xl border border-meet-gray">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-white mb-3">
                                Start Your Mock Interview
                            </h2>
                            <p className="text-meet-light-gray">
                                Practice with our AI interviewer and get real-time feedback
                            </p>
                        </div>

                        {/* Form */}
                        <div className="space-y-6">
                            {/* Job Role Input */}
                            <div>
                                <label htmlFor="jobRole" className="block text-sm font-medium text-white mb-2">
                                    Job Role <span className="text-meet-red">*</span>
                                </label>
                                <input
                                    id="jobRole"
                                    type="text"
                                    value={jobRole}
                                    onChange={(e) => {
                                        setJobRole(e.target.value)
                                        setErrors({ ...errors, jobRole: undefined })
                                    }}
                                    placeholder="e.g., Software Engineer, Product Manager"
                                    className={`w-full px-4 py-3 bg-meet-dark border ${errors.jobRole ? 'border-meet-red' : 'border-meet-gray'
                                        } rounded-lg text-white placeholder-meet-light-gray focus:outline-none focus:ring-2 focus:ring-meet-blue focus:border-transparent transition-all`}
                                />
                                {errors.jobRole && (
                                    <p className="mt-2 text-sm text-meet-red">{errors.jobRole}</p>
                                )}
                            </div>

                            {/* Job Description Textarea */}
                            <div>
                                <label htmlFor="jobDescription" className="block text-sm font-medium text-white mb-2">
                                    Job Description <span className="text-meet-light-gray text-xs">(Optional)</span>
                                </label>
                                <textarea
                                    id="jobDescription"
                                    value={jobDescription}
                                    onChange={(e) => setJobDescription(e.target.value)}
                                    placeholder="Paste the job description here or leave blank for general questions..."
                                    rows={6}
                                    className="w-full px-4 py-3 bg-meet-dark border border-meet-gray rounded-lg text-white placeholder-meet-light-gray focus:outline-none focus:ring-2 focus:ring-meet-blue focus:border-transparent transition-all resize-none"
                                />
                            </div>

                            {/* Question Count Selector */}
                            <div>
                                <label htmlFor="questionCount" className="block text-sm font-medium text-white mb-2">
                                    Number of Questions
                                </label>
                                <select
                                    id="questionCount"
                                    value={questionCount}
                                    onChange={(e) => setQuestionCount(Number(e.target.value))}
                                    className="w-full px-4 py-3 bg-meet-dark border border-meet-gray rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-meet-blue focus:border-transparent transition-all cursor-pointer"
                                >
                                    <option value={3}>3 Questions (Quick)</option>
                                    <option value={5}>5 Questions (Standard)</option>
                                    <option value={7}>7 Questions (Extended)</option>
                                    <option value={10}>10 Questions (Comprehensive)</option>
                                </select>
                            </div>

                            {/* Start Button */}
                            <button
                                onClick={handleStartInterview}
                                className="w-full bg-gradient-to-r from-meet-blue to-blue-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-4 focus:ring-meet-blue focus:ring-opacity-50 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg"
                            >
                                Start Interview
                            </button>
                        </div>

                        {/* Info Cards */}
                        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-meet-dark rounded-lg p-4 border border-meet-gray">
                                <div className="text-meet-blue text-2xl mb-2">🎯</div>
                                <h3 className="text-white font-semibold text-sm mb-1">Realistic Practice</h3>
                                <p className="text-meet-light-gray text-xs">
                                    Experience FAANG-style interviews
                                </p>
                            </div>
                            <div className="bg-meet-dark rounded-lg p-4 border border-meet-gray">
                                <div className="text-meet-green text-2xl mb-2">📊</div>
                                <h3 className="text-white font-semibold text-sm mb-1">Instant Feedback</h3>
                                <p className="text-meet-light-gray text-xs">
                                    Get detailed performance metrics
                                </p>
                            </div>
                            <div className="bg-meet-dark rounded-lg p-4 border border-meet-gray">
                                <div className="text-purple-400 text-2xl mb-2">🤖</div>
                                <h3 className="text-white font-semibold text-sm mb-1">AI-Powered</h3>
                                <p className="text-meet-light-gray text-xs">
                                    Dynamic questions based on your answers
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="border-t border-meet-gray p-4">
                <div className="max-w-7xl mx-auto text-center text-xs text-meet-light-gray">
                    <p>Powered by Google Gemini AI • Voice-enabled Mock Interviews</p>
                </div>
            </div>
        </div>
    )
}
