# Qrow IQ - AI HR Mock Interview Platform

Voice-only AI HR mock interview web application with Gemini 2.0 Flash, WebSocket real-time communication, and Google Meet-style UI.

## 🏗️ Architecture Overview

Qrow IQ is a monorepo application consisting of:

- **Backend**: FastAPI (Python) with WebSocket support
- **Frontend**: React + Vite + TypeScript with Tailwind CSS
- **LLM**: Google Gemini 2.0 Flash for interview questions
- **STT**: Browser Web Speech API
- **TTS**: Google Cloud Text-to-Speech (female professional voice)
- **Real-time**: WebSocket bidirectional communication

### Project Structure

```
qrow-iq/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── main.py      # FastAPI app entry, WebSocket routes
│   │   ├── websocket/   # WebSocket connection handlers
│   │   ├── llm/         # Gemini 2.0 Flash integration (Phase 3)
│   │   ├── tts/         # Google TTS integration (Phase 3)
│   │   ├── stt/         # STT fallback/delegation (Phase 2)
│   │   ├── interview_engine/  # State machine orchestrator (Phase 4)
│   │   ├── report/      # PDF generation (Phase 6)
│   │   ├── core/        # Config, models, utilities
│   │   └── models/      # Pydantic models for requests/responses
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # React + Vite application
│   ├── src/
│   │   ├── pages/       # Main interview page
│   │   ├── components/  # UI components (waveform, mic button, etc.)
│   │   ├── services/    # WebSocket client, API calls
│   │   ├── audio/       # Audio processing, silence detection
│   │   ├── hooks/       # Custom React hooks
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml   # Local development orchestration
├── .env.example         # Environment variables template
└── README.md
```

## 🔄 System Behavior - State Machine

The interview system operates as a state machine:

```
SETUP → ASK_QUESTION → PLAY_TTS → LISTEN → SILENCE_DETECT → 
TRANSCRIBE → EVALUATE → FOLLOWUP/NEXT_QUESTION → ... → 
FINAL_EVALUATION → REPORT
```

### State Descriptions

- **SETUP**: Initialize interview session with job role and description
- **ASK_QUESTION**: Generate next question using Gemini
- **PLAY_TTS**: Play question audio via Google TTS
- **LISTEN**: Capture user response via Web Speech API
- **SILENCE_DETECT**: Detect 2-second silence to end response
- **TRANSCRIBE**: Finalize transcript from Web Speech API
- **EVALUATE**: Score answer using Gemini (Phase 5)
- **FOLLOWUP/NEXT_QUESTION**: Decide on follow-up or next question
- **FINAL_EVALUATION**: Calculate overall scores
- **REPORT**: Generate PDF report and dashboard

## 📡 WebSocket Protocol

### Connection

```
ws://localhost:8000/ws/interview/{session_id}
```

### Message Types

#### Client → Server

1. **START_INTERVIEW**
   ```json
   {
     "type": "START_INTERVIEW",
     "session_id": "session-123",
     "job_role": "Software Engineer",
     "job_description": "Full-stack development...",
     "question_count": 5
   }
   ```

2. **TRANSCRIBE**
   ```json
   {
     "type": "TRANSCRIBE",
     "session_id": "session-123",
     "transcript": "I have 5 years of experience...",
     "is_final": true
   }
   ```

3. **SILENCE_DETECTED**
   ```json
   {
     "type": "SILENCE_DETECTED",
     "session_id": "session-123",
     "duration_seconds": 2.1
   }
   ```

4. **END_INTERVIEW**
   ```json
   {
     "type": "END_INTERVIEW",
     "session_id": "session-123"
   }
   ```

#### Server → Client

1. **QUESTION_READY**
   ```json
   {
     "type": "QUESTION_READY",
     "session_id": "session-123",
     "question": "Tell me about yourself.",
     "question_number": 1,
     "total_questions": 5
   }
   ```

2. **TTS_AUDIO**
   ```json
   {
     "type": "TTS_AUDIO",
     "session_id": "session-123",
     "audio_base64": "base64_encoded_audio...",
     "audio_format": "audio/mp3"
   }
   ```

3. **EVALUATION_UPDATE**
   ```json
   {
     "type": "EVALUATION_UPDATE",
     "session_id": "session-123",
     "scores": {
       "technical_depth": 7.5,
       "communication": 8.0,
       "confidence": 7.0
     },
     "current_question_number": 1
   }
   ```

4. **INTERVIEW_COMPLETE**
   ```json
   {
     "type": "INTERVIEW_COMPLETE",
     "session_id": "session-123",
     "final_scores": {...},
     "verdict": "Hire",
     "report_url": "/api/reports/session-123.pdf"
   }
   ```

5. **ERROR**
   ```json
   {
     "type": "ERROR",
     "session_id": "session-123",
     "error_code": "SESSION_NOT_FOUND",
     "error_message": "Session not found"
   }
   ```

6. **STATE_UPDATE**
   ```json
   {
     "type": "STATE_UPDATE",
     "session_id": "session-123",
     "state": "LISTEN"
   }
   ```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- Google Gemini API key
- Google Cloud TTS credentials (optional for Phase 3)

### Environment Variables

Create a `.env` file in the project root:

```bash
# Google Gemini 2.0 Flash API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud Text-to-Speech (optional for Phase 1)
GOOGLE_TTS_KEY=your_google_tts_key_here
# OR
GOOGLE_TTS_SERVICE_ACCOUNT_PATH=./service-account.json

# Server Configuration
FRONTEND_URL=http://localhost:5173
BACKEND_PORT=8000
DEBUG=false
```

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### Docker Development

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing Phase 1

After setup, verify the following:

1. **Backend Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **WebSocket Connection**
   - Open browser console at `http://localhost:5173`
   - Check for "WebSocket connected" message
   - Verify connection status indicator shows "Connected"

3. **Message Flow**
   - Click mic button to start interview
   - Verify WebSocket messages in browser console
   - Check backend logs for message handling

## 📋 Phase Implementation Status

### ✅ Phase 1: Monorepo + Base Architecture (COMPLETE)
- [x] Directory structure
- [x] FastAPI skeleton with WebSocket
- [x] React + Vite + TypeScript setup
- [x] WebSocket infrastructure
- [x] Basic UI components
- [x] Docker configuration

### 🔄 Phase 2: Voice Pipeline (NEXT)
- [ ] Web Speech API integration
- [ ] Real-time waveform visualization
- [ ] Silence detection (2-second threshold)
- [ ] Audio streaming to backend

### 📅 Phase 3: Gemini HR Brain
- [ ] Gemini 2.0 Flash integration
- [ ] Question generation system
- [ ] Google TTS integration
- [ ] Dynamic follow-up logic

### 📅 Phase 4: Interview Orchestrator
- [ ] State machine implementation
- [ ] Question counter
- [ ] Context memory
- [ ] Difficulty ramping

### 📅 Phase 5: Evaluation Engine
- [ ] Scoring metrics (Technical, Communication, etc.)
- [ ] Real-time evaluation
- [ ] Weakness detection

### 📅 Phase 6: Report Generation
- [ ] PDF report generation
- [ ] Score dashboard
- [ ] Improvement suggestions

### 📅 Phase 7: Google Meet Style UI
- [ ] UI polish
- [ ] Animations
- [ ] Responsive design

### 📅 Phase 8: GCP Deployment
- [ ] GCP configuration
- [ ] Nginx reverse proxy
- [ ] Production deployment

## 🛠️ Development Commands

### Backend

```bash
# Run with auto-reload
uvicorn app.main:app --reload

# Run with specific port
uvicorn app.main:app --port 8000

# Run production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 📚 Key Technologies

- **Backend**: FastAPI 0.104+, Python 3.11+, WebSockets
- **Frontend**: React 18+, Vite 5+, TypeScript, Tailwind CSS
- **LLM**: Google Gemini 2.0 Flash
- **STT**: Web Speech API (Browser)
- **TTS**: Google Cloud Text-to-Speech
- **Real-time**: Native WebSocket API

## 🔒 Security Notes

- Phase 1 is a demo with no authentication
- API keys should be stored securely in production
- WebSocket connections should use WSS in production
- CORS is configured for local development only

## 📝 License

This project is part of a startup MVP development.

## 🤝 Contributing

This is a phased development project. Each phase builds upon the previous one.

---

**Qrow IQ** - AI HR Mock Interview Platform  
Phase 1: Base Architecture Complete ✅
# mockinterview-module
