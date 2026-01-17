"""
Pydantic models for interview sessions, WebSocket messages, and API responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from enum import Enum


class InterviewState(str, Enum):
    """Interview state machine states"""
    SETUP = "SETUP"
    ASK_QUESTION = "ASK_QUESTION"
    PLAY_TTS = "PLAY_TTS"
    LISTEN = "LISTEN"
    SILENCE_DETECT = "SILENCE_DETECT"
    TRANSCRIBE = "TRANSCRIBE"
    EVALUATE = "EVALUATE"
    FOLLOWUP = "FOLLOWUP"
    NEXT_QUESTION = "NEXT_QUESTION"
    FINAL_EVALUATION = "FINAL_EVALUATION"
    REPORT = "REPORT"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class MessageType(str, Enum):
    """WebSocket message types from client"""
    TRANSCRIBE = "TRANSCRIBE"
    SILENCE_DETECTED = "SILENCE_DETECTED"
    START_INTERVIEW = "START_INTERVIEW"
    END_INTERVIEW = "END_INTERVIEW"
    PING = "PING"


class ServerMessageType(str, Enum):
    """WebSocket message types from server"""
    QUESTION_READY = "QUESTION_READY"
    TTS_AUDIO = "TTS_AUDIO"
    EVALUATION_UPDATE = "EVALUATION_UPDATE"
    INTERVIEW_COMPLETE = "INTERVIEW_COMPLETE"
    ERROR = "ERROR"
    PONG = "PONG"
    STATE_UPDATE = "STATE_UPDATE"


# Client → Server Messages
class ClientMessage(BaseModel):
    """Base class for client messages"""
    type: MessageType
    session_id: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None


class StartInterviewMessage(BaseModel):
    """Initialize interview session"""
    type: Literal[MessageType.START_INTERVIEW] = MessageType.START_INTERVIEW
    session_id: str
    job_role: str
    job_description: str
    question_count: int = Field(ge=1, le=20, default=5)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class TranscribeMessage(BaseModel):
    """Audio transcript chunk from client"""
    type: Literal[MessageType.TRANSCRIBE] = MessageType.TRANSCRIBE
    session_id: str
    transcript: str
    is_final: bool = False
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class SilenceDetectedMessage(BaseModel):
    """Client-side silence detection notification"""
    type: Literal[MessageType.SILENCE_DETECTED] = MessageType.SILENCE_DETECTED
    session_id: str
    duration_seconds: float
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


# Server → Client Messages
class ServerMessage(BaseModel):
    """Base class for server messages"""
    type: ServerMessageType
    session_id: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None


class QuestionReadyMessage(BaseModel):
    """New question generated and ready"""
    type: Literal[ServerMessageType.QUESTION_READY] = ServerMessageType.QUESTION_READY
    session_id: str
    question: str
    question_number: int
    total_questions: int
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class TTSAudioMessage(BaseModel):
    """Base64 encoded TTS audio for playback"""
    type: Literal[ServerMessageType.TTS_AUDIO] = ServerMessageType.TTS_AUDIO
    session_id: str
    audio_base64: str
    audio_format: str = "audio/mp3"
    question_id: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class EvaluationUpdateMessage(BaseModel):
    """Real-time evaluation update"""
    type: Literal[ServerMessageType.EVALUATION_UPDATE] = ServerMessageType.EVALUATION_UPDATE
    session_id: str
    scores: Dict[str, float]  # e.g., {"technical_depth": 7.5, "communication": 8.0}
    current_question_number: int
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class InterviewCompleteMessage(BaseModel):
    """Interview completed, report ready"""
    type: Literal[ServerMessageType.INTERVIEW_COMPLETE] = ServerMessageType.INTERVIEW_COMPLETE
    session_id: str
    final_scores: Dict[str, float]
    verdict: str  # "Hire", "Borderline", "No-Hire"
    report_url: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ErrorMessage(BaseModel):
    """Error notification"""
    type: Literal[ServerMessageType.ERROR] = ServerMessageType.ERROR
    session_id: str
    error_code: str
    error_message: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class StateUpdateMessage(BaseModel):
    """Interview state machine state change"""
    type: Literal[ServerMessageType.STATE_UPDATE] = ServerMessageType.STATE_UPDATE
    session_id: str
    state: InterviewState
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


# Evaluation Models
class EvaluationMetrics(BaseModel):
    """Evaluation scores for all 6 metrics"""
    technical_depth: float = Field(ge=0, le=10, default=0.0)
    communication: float = Field(ge=0, le=10, default=0.0)
    confidence: float = Field(ge=0, le=10, default=0.0)
    logical_thinking: float = Field(ge=0, le=10, default=0.0)
    problem_solving: float = Field(ge=0, le=10, default=0.0)
    culture_fit: float = Field(ge=0, le=10, default=0.0)


class AnswerEvaluationRecord(BaseModel):
    """Record of a single answer evaluation"""
    question_number: int
    question: str
    answer: str
    metrics: EvaluationMetrics
    needs_followup: bool = False
    weaknesses: List[str] = []
    strengths: List[str] = []
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FinalEvaluation(BaseModel):
    """Final evaluation summary"""
    overall_score: float = Field(ge=0, le=10, default=0.0)
    aggregated_metrics: EvaluationMetrics
    verdict: str  # "Hire", "Borderline", "No-Hire"
    insights: Dict[str, Any] = {}
    total_questions: int = 0
    total_answers: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Interview Session Model
class InterviewSession(BaseModel):
    """In-memory interview session state"""
    session_id: str
    state: InterviewState = InterviewState.SETUP
    job_role: str
    job_description: str
    question_count: int
    current_question_number: int = 0
    questions: list[str] = []
    answers: list[str] = []
    scores: Dict[str, float] = {}
    # Phase 5: Evaluation tracking
    evaluation_history: List[AnswerEvaluationRecord] = []
    final_evaluation: Optional[FinalEvaluation] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
