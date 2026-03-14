# Mora — End-to-End Development Plan

## Overview

This document outlines the complete development plan for Mora, broken into **6 stages**.
Each stage ends with an **end-to-end test checkpoint** to validate functionality before proceeding.

---

## Stage 1: Project Foundation & Database
**Goal:** Set up project structure, database, and basic API skeleton

### Tasks

| # | Task | Description |
|---|------|-------------|
| 1.1 | Create project structure | Backend (FastAPI), Frontend (Next.js), Docker setup |
| 1.2 | Set up PostgreSQL with Docker | Local development database |
| 1.3 | Define SQLAlchemy models | TestSuite, TestCase, Project, TestRun |
| 1.4 | Create Pydantic schemas | Request/response validation |
| 1.5 | Set up database migrations | Alembic for schema management |
| 1.6 | Create basic FastAPI app | Health check, CORS, middleware |
| 1.7 | Environment configuration | .env handling, settings management |

### End-to-End Test: Stage 1
```
✅ Backend starts without errors
✅ Database connection works
✅ Health endpoint returns 200
✅ Tables created in PostgreSQL
```

**Command to verify:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "database": "connected"}
```

---

## Stage 2: Test Suite Management API
**Goal:** Complete CRUD operations for Test Suites and Test Cases

### Tasks

| # | Task | Description |
|---|------|-------------|
| 2.1 | Test Suite CRUD endpoints | POST, GET, PUT, DELETE /test-suites |
| 2.2 | Test Case management | Add, edit, delete test cases within suites |
| 2.3 | Input validation | Scenario, prompt, utterance validation |
| 2.4 | Test Suite service layer | Business logic separation |
| 2.5 | Unit tests for Test Suite | pytest for service layer |
| 2.6 | API integration tests | Test full request/response cycle |

### Endpoints Delivered
```
POST   /api/test-suites              # Create test suite
GET    /api/test-suites              # List all test suites
GET    /api/test-suites/{id}         # Get single test suite
PUT    /api/test-suites/{id}         # Update test suite
DELETE /api/test-suites/{id}         # Delete test suite
POST   /api/test-suites/{id}/cases   # Add test case
PUT    /api/test-suites/{id}/cases/{case_id}    # Update test case
DELETE /api/test-suites/{id}/cases/{case_id}    # Delete test case
```

### End-to-End Test: Stage 2
```
✅ Create a test suite with name, scenario, prompt
✅ Add 3 test cases to the suite
✅ Edit one test case
✅ Delete one test case
✅ Retrieve test suite with remaining 2 cases
✅ Delete entire test suite
```

**Verification Script:**
```bash
# Create test suite
curl -X POST http://localhost:8000/api/test-suites \
  -H "Content-Type: application/json" \
  -d '{"name": "Dental Bot Auth", "scenario": "Caller books appointment", "prompt": "You are a dental receptionist..."}'

# Expected: Returns created test suite with ID
```

---

## Stage 3: Project Management & Execution Setup
**Goal:** Project CRUD, test suite attachment, and execution framework

### Tasks

| # | Task | Description |
|---|------|-------------|
| 3.1 | Project CRUD endpoints | Create, read, update projects |
| 3.2 | Attach test suites to project | Many-to-many relationship |
| 3.3 | Define run parameters | Number of calls configuration |
| 3.4 | Project activation endpoint | POST /projects/{id}/activate |
| 3.5 | Execution state machine | pending → running → completed → failed |
| 3.6 | Background task framework | FastAPI BackgroundTasks setup |
| 3.7 | TestRun model & tracking | Individual call result tracking |

### Endpoints Delivered
```
POST   /api/projects                    # Create project
GET    /api/projects                    # List all projects
GET    /api/projects/{id}               # Get project with status
PUT    /api/projects/{id}               # Update project
POST   /api/projects/{id}/activate      # Start test execution
GET    /api/projects/{id}/runs          # Get all test runs for project
```

### End-to-End Test: Stage 3
```
✅ Create a project with bot phone number
✅ Attach 2 test suites to project
✅ Set number_of_calls = 2
✅ Activate project (status changes to "running")
✅ Verify TestRun records created (4 total: 2 suites × 2 calls)
✅ Check project status updates
```

**Verification:**
```bash
# Create project
curl -X POST http://localhost:8000/api/projects \
  -d '{"name": "Dental QA", "bot_phone_number": "+14155552671", "test_suite_ids": ["uuid1", "uuid2"], "number_of_calls": 2}'

# Activate
curl -X POST http://localhost:8000/api/projects/{id}/activate

# Check status
curl http://localhost:8000/api/projects/{id}
# Expected: {"status": "running", "runs": [...]}
```

---

## Stage 4: Voice Agent & Telephony Integration
**Goal:** LiveKit Cloud SIP Telephony + Voice AI Agent

### Architecture Overview
```
┌──────────────┐       SIP        ┌─────────────────┐      Agent      ┌──────────────┐
│    Twilio    │ ←────────────→   │  LiveKit Cloud  │ ←────────────→  │  Voice Agent │
│  SIP Trunk   │                  │  SIP Telephony  │                 │  (STT→LLM→TTS)│
└──────────────┘                  └─────────────────┘                 └──────────────┘
      ↕                                   ↕                                    ↕
 Phone Number                      Dispatch Rules                    Deepgram + Gemini
 +1XXXXXXXXXX                      Agent: mora-voice-agent           + ElevenLabs
```

### Tasks

| # | Task | Description |
|---|------|-------------|
| 4.1 | Twilio SIP Trunk setup | Create Elastic SIP Trunk with origination/termination |
| 4.2 | LiveKit Cloud setup | Enable SIP Telephony in LiveKit Cloud project |
| 4.3 | SIP Integration | Connect Twilio SIP Trunk ↔ LiveKit SIP endpoint |
| 4.4 | LiveKit Inbound Trunk | Configure inbound trunk with phone number |
| 4.5 | LiveKit Outbound Trunk | Configure outbound trunk with Twilio credentials |
| 4.6 | Dispatch Rules | Create SIP dispatch rule to route calls to agent |
| 4.7 | Voice Agent implementation | Build agent with Deepgram STT, Gemini LLM, ElevenLabs TTS |
| 4.8 | Agent deployment | Deploy agent worker to LiveKit Cloud |
| 4.9 | Call execution service | Backend service to initiate test calls via Twilio API |
| 4.10 | Webhook handlers | Twilio webhooks for call status, recordings, transcripts |

### Voice Agent Stack
```python
# STT: Deepgram Nova-2 (fast, accurate speech recognition)
stt = deepgram.STT(model="nova-2-general", language="en")

# LLM: Google Gemini 2.0 Flash (low latency conversational AI)
llm = google.LLM(model="gemini-2.0-flash-exp")

# TTS: ElevenLabs Turbo v2.5 (natural voice synthesis)
tts = elevenlabs.TTS(voice_id="Rachel", model="eleven_turbo_v2_5")

# Agent with STT → LLM → TTS pipeline
agent = Agent(instructions="...", stt=stt, llm=llm, tts=tts)
session = AgentSession()
await session.start(agent=agent, room=ctx.room)
```

### Call Flow
```
1. Test Run Activation → Backend initiates Twilio call
2. Twilio calls bot phone number (+1XXXXXXXXXX)
3. Twilio SIP Trunk routes to LiveKit SIP endpoint
4. LiveKit Dispatch Rule creates room and invokes agent
5. Voice Agent connects to room as participant
6. Agent greets caller and engages in conversation
7. Call ends → Twilio saves recording
8. Backend webhook receives call status and recording URL
9. TestRun updated with audio_url and transcript
```

### End-to-End Test: Stage 4
```
✅ Twilio SIP Trunk configured with LiveKit SIP endpoint
✅ LiveKit Inbound Trunk created with phone number
✅ LiveKit Outbound Trunk configured with Twilio credentials
✅ Dispatch Rule routes calls to "mora-voice-agent"
✅ Voice Agent deployed and running on LiveKit Cloud
✅ Test call successfully initiated via Twilio API
✅ Agent answers call and has bidirectional conversation
✅ Call recording saved to Twilio
✅ Transcript generated and stored in database
✅ TestRun marked as SUCCESS with audio_url
```

**Verification:**
```bash
# 1. Start voice agent worker
cd backend && python run_agent.py dev

# 2. Make test call manually
# Call +1XXXXXXXXXX from your phone
# Expected: Voice agent answers and greets you

# 3. Activate project via API
curl -X POST http://localhost:8000/api/projects/{id}/activate

# 4. Check test run results
curl http://localhost:8000/api/projects/{id}/runs | jq '.[0]'
# Expected: 
# {
#   "status": "SUCCESS",
#   "audio_url": "https://api.twilio.com/...",
#   "transcript": "...",
#   "call_sid": "CA..."
# }
```

---

## Stage 5: LLM Integration & Evaluation Engine
**Goal:** AI-powered test generation and call evaluation

### Tasks

| # | Task | Description |
|---|------|-------------|
| 5.1 | LLM client setup | OpenAI/Gemini configurable client |
| 5.2 | Test case generation | Generate cases from scenario + prompt |
| 5.3 | Functional evaluation | Rule-based checks (auth, flow) |
| 5.4 | Conversational evaluation | LLM-as-judge for quality |
| 5.5 | Evaluation prompts | Structured prompts for LLM |
| 5.6 | Result aggregation | Combine functional + conversational |
| 5.7 | Feedback formatting | Structured JSON output |

### Test Case Generation
```
Input:
  - Scenario: "Caller wants to book dental appointment"
  - Prompt: "You are a dental receptionist..."

Output:
  - Test Case 1: {"utterance": "I need an appointment", "expected": "Ask for patient name"}
  - Test Case 2: {"utterance": "My name is John", "expected": "Ask for preferred date"}
  - ...
```

### Evaluation Output
```json
{
  "functional": {
    "auth_passed": true,
    "flow_correct": false,
    "call_terminated_properly": true
  },
  "conversational": {
    "working_well": ["Clear greeting", "Polite tone"],
    "needs_improvement": ["Repeated same question", "Long pauses"]
  }
}
```

### End-to-End Test: Stage 5
```
✅ Generate 5 test cases from scenario description
✅ Execute a real call with test case
✅ Functional evaluation produces correct pass/fail
✅ LLM evaluation returns structured feedback
✅ Aggregated report shows both functional + conversational
```

**Verification:**
```bash
# Generate test cases
curl -X POST http://localhost:8000/api/test-suites/{id}/generate-cases \
  -d '{"count": 5}'

# Run evaluation on completed call
curl http://localhost:8000/api/test-runs/{id}/evaluate

# Get project report
curl http://localhost:8000/api/projects/{id}/report
```

---

## Stage 6: Frontend & Complete Integration
**Goal:** Next.js UI for full user workflow

### Tasks

| # | Task | Description |
|---|------|-------------|
| 6.1 | Next.js project setup | App router, Tailwind CSS |
| 6.2 | API client layer | Fetch wrapper for backend |
| 6.3 | Test Suites page | List, create, edit suites |
| 6.4 | Test Suite Editor | Add/edit/delete test cases |
| 6.5 | Generate Cases UI | Button to trigger LLM generation |
| 6.6 | Projects page | List, create projects |
| 6.7 | Project Detail page | Attach suites, set parameters |
| 6.8 | Activate Project UI | Start execution button |
| 6.9 | Results View | Show feedback after completion |
| 6.10 | Loading & error states | UX polish |

### Pages

| Page | Route | Features |
|------|-------|----------|
| Test Suites | `/test-suites` | List all, create new |
| Test Suite Editor | `/test-suites/[id]` | Edit suite, manage cases |
| Projects | `/projects` | List all, create new |
| Project Detail | `/projects/[id]` | Configure, activate |
| Results | `/projects/[id]/results` | View feedback |

### End-to-End Test: Stage 6 (Full System Test)
```
✅ User creates test suite via UI
✅ User adds test cases manually OR generates via LLM
✅ User creates project, attaches test suite
✅ User sets phone number and call count
✅ User activates project
✅ System executes calls (visible progress)
✅ User views results with functional + conversational feedback
```

---

## Complete System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│   Test Suites UI → Projects UI → Activate → Results View        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND API                              │
│   /test-suites  →  /projects  →  /activate  →  /evaluate       │
└─────────────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
      ┌──────────────┐          ┌──────────────┐
      │   Gemini     │          │    Twilio    │
      │   LLM API    │          │   API Call   │
      │  (Evaluate)  │          │   Initiate   │
      └──────────────┘          └──────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  Twilio SIP      │
                              │  Trunk           │
                              └──────────────────┘
                                        │
                                        ▼ SIP Protocol
                              ┌──────────────────┐
                              │  LiveKit Cloud   │
                              │  SIP Endpoint    │
                              └──────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  Dispatch Rule   │
                              │  Room + Agent    │
                              └──────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │   Voice Agent    │
                              │   Worker         │
                              │  (Deepgram STT)  │
                              │  (Gemini LLM)    │
                              │  (ElevenLabs TTS)│
                              └──────────────────┘
                                        │
                                        ▼ Calls
                              ┌──────────────────┐
                              │   Bot Under      │
                              │   Test           │
                              │   (Your Phone)   │
                              └──────────────────┘
                                        │
                                        ▼ Recording
                              ┌──────────────────┐
                              │   Twilio         │
                              │   Storage        │
                              │   (Audio Files)  │
                              └──────────────────┘
```

---

## Development Timeline (Suggested)

| Stage | Duration | Cumulative |
|-------|----------|------------|
| Stage 1: Foundation | 2-3 days | Day 3 |
| Stage 2: Test Suites API | 2-3 days | Day 6 |
| Stage 3: Projects API | 2-3 days | Day 9 |
| Stage 4: Voice/Telephony | 5-7 days | Day 16 |
| Stage 5: LLM/Evaluation | 3-4 days | Day 20 |
| Stage 6: Frontend | 4-5 days | Day 25 |

**Total: ~4 weeks for MVP**

---

## Dependencies & Prerequisites

### External Services
- [x] Twilio account with Voice capabilities and SIP Trunking enabled
- [x] LiveKit Cloud account with SIP Telephony enabled
- [x] Google Gemini API key (for LLM)
- [x] Deepgram API key (for STT)
- [x] ElevenLabs API key (for TTS)
- [ ] AWS S3 or compatible storage (optional for MVP - currently using Twilio storage)

### Local Development
- [ ] Docker & Docker Compose
- [ ] Python 3.11+
- [ ] Node.js 18+
- [ ] PostgreSQL 15+

---

## Next Step

**Ready to start Stage 1?**

I will create:
1. Complete project directory structure
2. Docker Compose for PostgreSQL
3. FastAPI app with health check
4. SQLAlchemy models
5. Alembic migrations
6. Environment configuration

Say **"Start Stage 1"** to begin!
