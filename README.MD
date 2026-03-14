# 🎙️ Mora - Voice AI Testing & Evaluation Platform

**Automated testing platform for voice AI bots with multi-turn conversations and LLM-based evaluation**

---

## 🎯 What is Mora?

Mora enables you to **automatically test voice AI bots** through real phone calls with intelligent conversational agents. It evaluates both **functional behavior** (did the bot do what it should?) and **conversational quality** (was it natural and coherent?).

### Key Features:
- ✅ **Multi-turn conversations** via LiveKit voice agent (STT → LLM → TTS)
- ✅ **Real phone calls** via Twilio integration
- ✅ **LLM-based evaluation** with Gemini/GPT-4
- ✅ **Test suite management** for organizing test cases
- ✅ **Project-based testing** with batch execution
- ✅ **Real-time transcription** and conversation capture
- ✅ **Comprehensive scoring** (functional + conversational)
- ✅ **Modern frontend dashboard** (Next.js + MUI + Tailwind CSS)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   MORA PLATFORM                         │
│  ┌──────────┐    ┌────────────┐    ┌─────────────┐   │
│  │ Test Run │───▶│  LiveKit   │───▶│    Voice    │   │
│  │          │    │  Service   │    │    Agent    │   │
│  └──────────┘    └────────────┘    │ (STT→LLM→   │   │
│       │                │            │  TTS)       │   │
└───────┼────────────────┼────────────┴─────────────┴───┘
        │                │                    │
        ▼                ▼                    ▼
   ┌─────────┐     ┌──────────┐        ┌──────────┐
   │ Twilio  │────▶│ WebSocket│◀──────▶│ LiveKit  │
   │  Call   │     │  Bridge  │        │   Room   │
   └─────────┘     └──────────┘        └──────────┘
        │                                     │
        ▼                                     ▼
   ┌─────────┐                          ┌──────────┐
   │   Bot   │                          │ Deepgram │
   │  Phone  │                          │  OpenAI  │
   └─────────┘                          │ElevenLabs│
                                        └──────────┘
```

### Components:
1. **Mora Frontend** (Next.js + MUI) - Dashboard, test management, results viewer
2. **Mora Backend** (FastAPI) - REST API, test orchestration & evaluation
3. **LiveKit** - Voice agent infrastructure (STT, LLM, TTS)
4. **Twilio** - Outbound calling to bot phone numbers
5. **WebSocket Bridge** - Connects Twilio audio to LiveKit room
6. **Gemini/GPT-4** - LLM-based evaluation of conversations

---

## 🚀 Quick Start

### Prerequisites:
- Python 3.12+
- Node.js 18+ & npm
- PostgreSQL 15
- Twilio account
- LiveKit Cloud account
- API keys: Deepgram, ElevenLabs, OpenAI/Gemini

### 1. Clone & Setup

```bash
git clone <your-repo>
cd Mora

# Start PostgreSQL
docker-compose up -d

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Configure Environment

Copy `backend/.env.template` to `backend/.env` and fill in:

```bash
# Required: Database
DATABASE_URL=postgresql://mora_user:mora_password@localhost:5432/mora_db

# Required: Twilio (voice calling)
TWILIO_ACCOUNT_SID=ACxxxxxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+15551234567

# Required: LiveKit (voice agent)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxx
LIVEKIT_API_SECRET=your_secret

# Required: Deepgram (STT)
DEEPGRAM_API_KEY=your_key

# Required: ElevenLabs (TTS)
ELEVENLABS_API_KEY=your_key

# Required: OpenAI (LLM)
OPENAI_API_KEY=your_key

# Optional: Gemini (evaluation)
GEMINI_API_KEY=your_key
LLM_PROVIDER=gemini
```

**See `LIVEKIT_SETUP.md` for detailed API key setup instructions.**

### 3. Run the System (4 terminals)

**Terminal 1 - FastAPI Server:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - Next.js Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - LiveKit Agent Worker:**
```bash
cd backend
python run_agent.py
```

**Terminal 4 - ngrok (for Twilio webhooks):**
```bash
ngrok http 8000
# Copy HTTPS URL to PUBLIC_URL in .env
```

The frontend dashboard will be available at **http://localhost:3000** and the API at **http://localhost:8000**.

### 4. Test It

```bash
# Create test suite
curl -X POST http://localhost:8000/api/test-suites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restaurant Booking Tests",
    "description": "Test restaurant reservation bot"
  }'

# Create test case
curl -X POST http://localhost:8000/api/test-suites/{suite_id}/test-cases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Happy Path Booking",
    "utterance": "Hi, I need to book a table for 4 people tomorrow at 8 PM please",
    "expected_behavior": "Bot should confirm date, time, party size, then ask for name"
  }'

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Restaurant Bot",
    "bot_phone_number": "+15559876543",
    "test_suite_ids": ["{suite_id}"]
  }'

# Execute tests
curl -X POST http://localhost:8000/api/projects/{project_id}/execute

# Get evaluation results
curl http://localhost:8000/api/evaluations/test-runs/{test_run_id}/evaluation
```

---

## 📖 Documentation

- **`LIVEKIT_SETUP.md`** - Complete setup guide with API key instructions
- **`STAGE_4_LIVEKIT_COMPLETE.md`** - Technical architecture documentation
- **`STAGE_5_COMPLETE.md`** - LLM evaluation implementation details
- **`CORRECTION_SUMMARY.md`** - Why we use LiveKit (not just Twilio TTS)
- **`DEVELOPMENT_PLAN.md`** - Original TDD specification
- **`frontend/README.md`** - Frontend-specific setup (if present)

---

## 🎨 Example Conversation

### Test Case:
```json
{
  "utterance": "Hi, I need a table for 4 tomorrow at 8 PM",
  "expected_behavior": "Confirm details, ask for name"
}
```

### Actual Conversation:
```
[Call begins]
Caller: Hi, I need a table for 4 tomorrow at 8 PM
Bot: I'd be happy to help! Just to confirm, you'd like a table for 4 people tomorrow at 8 PM, correct?
Caller: Yes, that's right
Bot: Perfect! Can I have your name please?
Caller: John Smith
Bot: Thank you, John. Your reservation for 4 people tomorrow at 8 PM is confirmed!
[Call ends]
```

### Evaluation Results:
```json
{
  "functional_evaluation": {
    "passed": true,
    "score": 95,
    "reasoning": "Bot correctly confirmed details and asked for name",
    "matched_behaviors": ["confirm date/time/party size", "ask for name"],
    "missing_behaviors": []
  },
  "conversational_evaluation": {
    "overall_score": 92,
    "fluency": 95,
    "naturalness": 90,
    "error_handling": 85,
    "coherence": 98,
    "feedback": "Excellent conversational flow...",
    "strengths": ["Clear confirmation", "Polite tone", "Logical progression"],
    "weaknesses": ["Could add warmth to greeting"]
  }
}
```

---

## 🏗️ Project Structure

```
Mora/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── voice_agent.py          # LiveKit voice agent (STT→LLM→TTS)
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── test_suites.py      # Test suite CRUD
│   │   │       ├── projects.py         # Project management
│   │   │       ├── webhooks.py         # Twilio webhooks + WebSocket bridge
│   │   │       └── evaluations.py      # LLM evaluation endpoints
│   │   ├── services/
│   │   │   ├── livekit_service.py      # LiveKit room management
│   │   │   ├── livekit_bridge.py       # Twilio↔LiveKit audio bridge
│   │   │   ├── call_execution_service.py # Test execution orchestration
│   │   │   ├── llm_service.py          # LLM-based evaluation
│   │   │   ├── evaluation_service.py   # Evaluation workflow
│   │   │   └── twilio_service.py       # Twilio API wrapper
│   │   ├── core/
│   │   │   ├── config.py               # Settings & environment variables
│   │   │   └── database.py             # DB connection & session management
│   │   ├── models.py                   # SQLAlchemy models
│   │   ├── schemas.py                  # Pydantic schemas
│   │   └── main.py                     # FastAPI app
│   ├── alembic/                        # Database migrations
│   ├── run_agent.py                    # LiveKit agent worker
│   ├── requirements.txt
│   └── .env.template
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js App Router pages
│   │   │   ├── page.tsx                # Dashboard / homepage
│   │   │   ├── layout.tsx              # Root layout (MUI + Query providers)
│   │   │   ├── globals.css             # Tailwind + CSS variables
│   │   │   ├── projects/               # Project CRUD & results pages
│   │   │   └── test-suites/            # Test suite CRUD pages
│   │   ├── components/
│   │   │   ├── layout/navbar.tsx       # MUI AppBar navigation
│   │   │   └── ui/                     # shadcn/ui primitives
│   │   └── lib/
│   │       ├── api/                    # Axios API clients
│   │       ├── hooks/                  # React Query hooks
│   │       └── providers/              # MUI theme + React Query providers
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml                  # PostgreSQL container
├── LIVEKIT_SETUP.md                    # Setup guide
└── README.md                           # This file
```

---

## 🎯 API Endpoints

### Test Suites
- `POST /api/test-suites` - Create test suite
- `GET /api/test-suites` - List test suites
- `GET /api/test-suites/{id}` - Get test suite details
- `PUT /api/test-suites/{id}` - Update test suite
- `DELETE /api/test-suites/{id}` - Delete test suite
- `POST /api/test-suites/{id}/test-cases` - Add test case
- `PUT /api/test-suites/{suite_id}/test-cases/{case_id}` - Update test case
- `DELETE /api/test-suites/{suite_id}/test-cases/{case_id}` - Delete test case

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/activate` - Activate project (generate test runs)
- `POST /api/projects/{id}/execute` - Execute all test runs

### Webhooks
- `POST /api/webhooks/twilio/voice/{test_run_id}` - TwiML voice instructions
- `POST /api/webhooks/twilio/status/{test_run_id}` - Call status updates
- `WebSocket /api/webhooks/twilio/stream/{test_run_id}` - Audio stream bridge

### Evaluations
- `POST /api/evaluations/test-runs/{id}/evaluate` - Trigger evaluation
- `GET /api/evaluations/test-runs/{id}/evaluation` - Get evaluation results
- `POST /api/evaluations/projects/{id}/evaluate` - Batch evaluate project
- `GET /api/evaluations/projects/{id}/evaluation-summary` - Get project summary

---

## 💰 Cost Estimates

### Per 2-minute test call (4 conversational turns):

| Service | Cost | Purpose |
|---------|------|---------|
| Twilio | $0.026 | Phone call |
| LiveKit | $0.016 | Voice agent hosting |
| Deepgram | $0.009 | Speech-to-text |
| OpenAI GPT-4 | $0.020 | Conversation logic |
| ElevenLabs | $0.012 | Text-to-speech |
| Gemini | $0.001 | Evaluation |
| **Total** | **~$0.084** | **Full test** |

**ROI:** ~180x cheaper than manual QA testing ($15-30 per test)

---

## 🔧 Technology Stack

### Frontend:
- **Next.js** 16 - React framework (App Router)
- **React** 19 - UI library
- **Material UI (MUI)** 7 - Component library (AppBar, Typography, Chip, Paper, LinearProgress)
- **Tailwind CSS** 4 - Utility-first CSS (layout, spacing, micro-adjustments)
- **shadcn/ui** + **Radix UI** - Form primitives (Dialog, Checkbox, Select, Tabs)
- **TanStack React Query** 5 - Server state management & caching
- **React Hook Form** + **Zod** - Form validation
- **Axios** - HTTP client
- **Sonner** - Toast notifications

### Backend:
- **FastAPI** 0.109.0 - REST API framework
- **SQLAlchemy** 2.0 - ORM
- **PostgreSQL** 15 - Database
- **Pydantic** 2.5 - Data validation

### Voice Infrastructure:
- **LiveKit** 1.0 - Real-time communication platform
- **livekit-agents** 1.3 - Agent framework
- **Deepgram** Nova-2 - Speech-to-text
- **OpenAI** GPT-4o - LLM for conversation
- **ElevenLabs** Turbo v2.5 - Text-to-speech

### Telephony:
- **Twilio** 8.11 - Voice calling
- **ngrok** - Webhook tunneling (dev)

### AI Evaluation:
- **Google Gemini** 2.5 Flash - Evaluation LLM
- **OpenAI** GPT-4 - Alternative evaluator

---

## 🎓 Why LiveKit?

The original TDD specified LiveKit for good reason:

### ✅ Benefits:
- **Multi-turn conversations** (not single utterances)
- **Production-grade** (same stack as Bland.ai, Vapi.ai)
- **Scalable** (1000s of concurrent agents)
- **Flexible** (swap STT/LLM/TTS providers easily)
- **Real testing** (actual conversational behavior)

### ❌ Why Not Just Twilio TTS?
- Single utterance only
- No dynamic responses
- Can't test follow-up questions
- Not representative of real bot behavior

**See `CORRECTION_SUMMARY.md` for detailed explanation.**

---

## 🖥️ Frontend Dashboard

The frontend provides a full-featured dashboard for managing tests and reviewing results:

| Page | Description |
|------|-------------|
| **Dashboard** | Welcome page with get-started guide, feature overview, and quick links |
| **Test Suites** | Create, edit, and delete test suites with AI-generated test cases |
| **Projects** | Configure projects with bot phone numbers and attached test suites |
| **Project Detail** | View stats, attached suites, test runs table, and activate execution |
| **Results** | Summary cards with pass rate, score breakdowns (LinearProgress), transcript viewer |

### UI Design:
- **Indigo-600** primary color palette with MUI theme system
- **MUI AppBar** navigation with tab indicators
- **MUI Typography** scale for consistent heading/body hierarchy
- **MUI Chip** for status badges (colored, outlined variants)
- **MUI Paper** + **LinearProgress** for score visualizations
- **shadcn/ui Cards** with `rounded-xl` corners and hover shadow transitions
- **Inter** font via MUI CssBaseline + Next.js font optimization

---

## 📈 Development Progress

- ✅ **Stage 1:** Project foundation & database setup
- ✅ **Stage 2:** Test suite management (CRUD)
- ✅ **Stage 3:** Project management & test run generation
- ✅ **Stage 4:** LiveKit voice agent + Twilio integration
- ✅ **Stage 5:** LLM-based evaluation (Gemini/GPT-4)
- ✅ **Stage 6:** Frontend dashboard (Next.js + MUI + Tailwind)

---

## 🤝 Contributing

This is a TDD-driven project. See `DEVELOPMENT_PLAN.md` for the complete specification.

---

## 📄 License

[Your License Here]

---

## 🙏 Credits

Built following the original TDD specification with:
- LiveKit for conversational voice agents
- Twilio for telephony infrastructure  
- Gemini for LLM-based evaluation

---

## 📞 Support

For setup help, see `LIVEKIT_SETUP.md`

For technical details, see `STAGE_4_LIVEKIT_COMPLETE.md`

---

**Ready to test real conversations!** 🎉
