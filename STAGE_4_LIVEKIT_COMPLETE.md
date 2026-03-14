# Stage 4 Complete - LiveKit Voice Agent Integration

## ✅ Implementation Complete

Following the **original TDD specifications**, Mora now uses:
- **Twilio** for outbound calling only (dialing the phone number)
- **LiveKit** for the actual conversational voice agent (STT → LLM → TTS)

This enables **multi-turn conversations** instead of single utterance tests.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MORA PLATFORM                           │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │  Test Run    │───▶│   LiveKit   │───▶│    Voice     │  │
│  │  Execution   │    │   Service   │    │    Agent     │  │
│  └──────────────┘    └─────────────┘    └──────────────┘  │
│         │                   │                    │          │
└─────────┼───────────────────┼────────────────────┼──────────┘
          │                   │                    │
          ▼                   ▼                    ▼
    ┌─────────┐         ┌──────────┐        ┌──────────┐
    │ Twilio  │◀───────▶│ LiveKit  │◀──────▶│   STT    │
    │  Call   │         │   Room   │        │   LLM    │
    └─────────┘         └──────────┘        │   TTS    │
          │                                  └──────────┘
          ▼
    ┌─────────┐
    │   Bot   │
    │  Phone  │
    └─────────┘
```

### Flow:

1. **Test Execution** → Creates LiveKit room with agent configuration
2. **Twilio Call** → Dials bot phone number
3. **TwiML Stream** → Connects call audio to WebSocket bridge
4. **WebSocket Bridge** → Forwards audio between Twilio ↔ LiveKit
5. **Voice Agent** → Handles conversation (STT → LLM → TTS)
6. **Transcript Capture** → Records full conversation
7. **Evaluation** → LLM evaluates transcript against expected behavior

---

## 📦 New Components

### 1. Voice Agent (`app/agents/voice_agent.py`)

**Purpose:** LiveKit voice agent that handles multi-turn conversations

**Architecture:**
- **STT:** Deepgram Nova-2 (fast, accurate speech recognition)
- **LLM:** OpenAI GPT-4o (can switch to Gemini)
- **TTS:** ElevenLabs Turbo v2.5 (natural voice synthesis)

**Key Features:**
- Dynamic system prompt from test scenario
- Real-time transcript capture
- Event-driven conversation turns
- Configurable LLM model, temperature, voice

**Usage:**
```python
agent = MoraVoiceAgent(
    scenario_description="Restaurant booking system",
    expected_behavior="Confirm date, time, party size, then ask for name",
    initial_utterance="Hi, I need a table for 4 tomorrow at 8 PM",
    agent_config={
        "llm_model": "gpt-4o",
        "temperature": 0.7,
        "voice_id": "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs Rachel
    }
)

assistant = await agent.create_assistant()
# ... connect to LiveKit room
transcript = agent.get_transcript()
```

### 2. LiveKit Service (`app/services/livekit_service.py`)

**Purpose:** Manages LiveKit rooms and access tokens

**Key Methods:**
```python
# Create room for test
room_info = await livekit_service.create_room_for_test(
    test_run_id="uuid",
    scenario_description="...",
    expected_behavior="...",
    initial_utterance="...",
    agent_config={...}
)

# Get room info
info = await livekit_service.get_room_info("test-uuid")

# Delete room
await livekit_service.delete_room("test-uuid")

# Generate participant token
token = livekit_service.generate_participant_token(
    room_name="test-uuid",
    identity="twilio-caller",
    name="Caller"
)
```

### 3. WebSocket Bridge (`app/services/livekit_bridge.py`)

**Purpose:** Bridges Twilio Media Stream to LiveKit room

**Features:**
- Receives audio from Twilio call (mulaw 8kHz)
- Converts mulaw → PCM16
- Forwards to LiveKit room
- Bidirectional audio streaming

**Flow:**
1. Twilio call answered → TwiML returns `<Stream>` with WebSocket URL
2. Twilio establishes WebSocket connection
3. Bridge accepts connection
4. Bridge connects to LiveKit room as participant
5. Bridge publishes audio track from Twilio
6. Bridge subscribes to agent audio track
7. Audio flows: Caller → Twilio → Bridge → LiveKit → Agent → LiveKit → Bridge → Twilio → Caller

### 4. Updated Webhooks (`app/api/routes/webhooks.py`)

**New Endpoints:**

#### `POST /api/webhooks/twilio/voice/{test_run_id}`
Returns TwiML with `<Stream>` instead of `<Say>`:
```xml
<Response>
    <Connect>
        <Stream url="wss://your-domain.com/api/webhooks/twilio/stream/{test_run_id}">
            <Parameter name="room_name" value="test-{uuid}" />
            <Parameter name="test_run_id" value="{uuid}" />
        </Stream>
    </Connect>
</Response>
```

#### `WebSocket /api/webhooks/twilio/stream/{test_run_id}`
WebSocket endpoint that:
- Accepts Twilio Media Stream connection
- Creates LiveKit room participant
- Bridges audio bidirectionally

### 5. Updated Call Execution (`app/services/call_execution_service.py`)

**New Flow:**
```python
async def execute_test_run(db, test_run_id, base_url):
    # 1. Create LiveKit room
    room_info = await livekit_service.create_room_for_test(...)
    
    # 2. Make Twilio call (connects to WebSocket stream)
    call_sid = twilio_service.make_call(
        to_phone=bot_phone,
        twiml_url=f"{base_url}/api/webhooks/twilio/voice/{test_run_id}"
    )
    
    # 3. Agent automatically starts in LiveKit room
    # 4. Caller → Twilio → Bridge → LiveKit → Agent
    # 5. Transcript captured in real-time
```

---

## 🚀 Setup Instructions

### 1. Get LiveKit Credentials

Sign up at https://cloud.livekit.io/ (free tier):
1. Create new project
2. Copy credentials:
   - WebSocket URL (e.g., `wss://your-project.livekit.cloud`)
   - API Key
   - API Secret

### 2. Update `.env`

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

### 3. Get Additional API Keys

**Deepgram (STT):**
- Sign up at https://deepgram.com/
- Create API key
- Add to `.env`: `DEEPGRAM_API_KEY=your_key`

**ElevenLabs (TTS):**
- Sign up at https://elevenlabs.io/
- Get API key
- Add to `.env`: `ELEVENLABS_API_KEY=your_key`

**OpenAI (LLM + optional Whisper):**
- Already configured: `OPENAI_API_KEY=your_key`

### 4. Run the System

**Terminal 1 - FastAPI Server:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - LiveKit Agent Worker:**
```bash
cd backend
python run_agent.py
```

**Terminal 3 - ngrok (for Twilio webhooks):**
```bash
ngrok http 8000
```

---

## 🎯 Testing

### Test Multi-Turn Conversation

```bash
# 1. Create test run
curl -X POST http://localhost:8000/api/projects/{project_id}/execute

# 2. Watch logs:
# Terminal 1: FastAPI logs (call execution, webhooks)
# Terminal 2: Agent logs (STT, LLM, TTS)

# 3. After call ends, get transcript:
curl http://localhost:8000/api/evaluations/test-runs/{test_run_id}/evaluation
```

**Expected Transcript:**
```
[Call begins]
Caller: Hi, I need to book a table for 4 people tomorrow at 8 PM please
Bot: I'd be happy to help you with that reservation. Just to confirm, you'd like a table for 4 people tomorrow at 8 PM, is that correct?
Caller: Yes, that's right
Bot: Perfect! Can I have your name please?
Caller: It's John Smith
Bot: Thank you, John. Your table for 4 people tomorrow at 8 PM is confirmed. We look forward to seeing you!
[Call ends]
```

---

## 📊 Benefits vs. Previous Approach

### Previous (Twilio TTS Only):
- ❌ Single utterance only
- ❌ No follow-up questions
- ❌ No dynamic responses
- ❌ Limited to simple scenarios
- ✅ Simple setup

### Current (LiveKit Voice Agent):
- ✅ **Multi-turn conversations**
- ✅ **Dynamic responses** based on context
- ✅ **Follow-up questions** and clarifications
- ✅ **Interruption handling**
- ✅ **Real-time transcription**
- ✅ **Complex scenario testing**
- ✅ **Production-grade voice quality**

---

## 💰 Cost Estimates (per test call)

| Service | Cost | Notes |
|---------|------|-------|
| Twilio Voice | $0.013/min | Outbound call |
| LiveKit | $0.008/min | Cloud hosting |
| Deepgram STT | $0.0043/min | Speech recognition |
| OpenAI GPT-4o | $0.005/turn | ~3-5 turns average |
| ElevenLabs TTS | $0.003/turn | Voice synthesis |
| **Total** | **~$0.05/test** | 2-minute call, 4 turns |

Compare to:
- Previous approach: $0.013/min (Twilio only)
- But limited to single utterance (not real testing)

---

## 🔍 How It Works

### 1. Test Run Creation
```python
# Mora creates LiveKit room
room = livekit.create_room(
    name="test-abc123",
    metadata={
        "scenario": "Restaurant booking",
        "expected": "Confirm details, ask for name",
        "utterance": "Hi, I need a table for 4..."
    }
)

# Voice agent joins room automatically
# Agent reads metadata and prepares system prompt
```

### 2. Twilio Call
```python
# Twilio dials bot
call = twilio.make_call(
    to="+1234567890",
    twiml_url="https://mora.com/api/webhooks/twilio/voice/abc123"
)
```

### 3. TwiML Stream
```xml
<!-- Twilio receives TwiML, establishes WebSocket -->
<Response>
    <Connect>
        <Stream url="wss://mora.com/api/webhooks/twilio/stream/abc123" />
    </Connect>
</Response>
```

### 4. WebSocket Bridge
```python
# Twilio sends audio over WebSocket
# Bridge forwards to LiveKit room
bridge.forward_audio(twilio_audio → livekit_room)

# Agent responds via LiveKit
# Bridge forwards back to Twilio
bridge.forward_audio(livekit_room → twilio_call)
```

### 5. Voice Agent Conversation
```python
# Agent listens (Deepgram STT)
user_speech = "Hi, I need a table for 4..."

# Agent thinks (OpenAI GPT-4)
response = llm.chat([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_speech}
])

# Agent speaks (ElevenLabs TTS)
audio = tts.synthesize(response)
agent.speak(audio)

# Transcript captured
conversation.append({"role": "user", "text": user_speech})
conversation.append({"role": "assistant", "text": response})
```

### 6. Transcript Retrieval
```python
# After call ends
transcript = agent.get_transcript()
db.store_transcript(test_run_id, transcript)

# Evaluation service uses real transcript
evaluation = llm.evaluate(
    transcript=transcript,
    expected_behavior="Confirm details, ask for name"
)
```

---

## 🎨 Voice Customization

### Change LLM Model
```python
agent_config = {
    "llm_model": "gpt-4o",  # or "gpt-3.5-turbo", "gemini-pro"
    "temperature": 0.7      # 0.0-1.0 (lower = more deterministic)
}
```

### Change Voice
```python
# ElevenLabs voices
agent_config = {
    "voice_id": "21m00Tcm4TlvDq8ikWAM"  # Rachel (default)
    # "EXAVITQu4vr4xnSDxMaL"  # Sarah
    # "ErXwobaYiN019PkySvjV"  # Antoni
    # "MF3mGyEYCl7XYWbV9V6O"  # Elli
}
```

### Modify System Prompt
Edit `voice_agent.py`:
```python
def build_system_prompt(self) -> str:
    return f"""You are a {self.scenario_description} assistant.
    
    Your behavior:
    {self.expected_behavior}
    
    Additional instructions:
    - Be concise (1-2 sentences)
    - Confirm important details
    - Ask clarifying questions
    - Handle interruptions gracefully
    """
```

---

## 🐛 Troubleshooting

### Agent not responding
- Check Terminal 2 (agent worker) for errors
- Verify LiveKit credentials in `.env`
- Ensure `run_agent.py` is running

### No audio in call
- Check WebSocket connection logs
- Verify ngrok tunnel is running
- Check Twilio debugger: https://console.twilio.com/debugger

### Transcript empty
- Check agent event handlers (`_on_user_speech`, `_on_agent_speech`)
- Verify Deepgram API key
- Check STT logs for errors

### High latency
- Use `eleven_turbo_v2_5` TTS model (fastest)
- Use `gpt-3.5-turbo` for faster LLM responses
- Consider regional LiveKit server

---

## 📈 Next Steps

### Stage 5 Enhancements:
- ✅ Real-time transcript streaming to dashboard
- ✅ Conversation turn tracking (user vs. bot)
- ✅ Interruption detection
- ✅ Sentiment analysis per turn

### Stage 6 Frontend:
- Live audio waveform visualization
- Real-time transcript display
- WebSocket updates for live test monitoring
- Multi-agent testing (parallel calls)

---

## 🎓 Why This Architecture?

**Original TDD Requirement:**
> "Stage 4: LiveKit simulated caller + Twilio outbound calls"

**Benefits:**
1. **Scalability:** LiveKit handles thousands of concurrent agents
2. **Flexibility:** Easy to swap STT/LLM/TTS providers
3. **Quality:** Professional voice quality with ElevenLabs
4. **Testing:** Enables complex multi-turn scenarios
5. **Production-Ready:** Same stack used by commercial voice AI products

**Industry Standard:**
- This is the architecture used by Bland.ai, Vapi.ai, and other voice AI platforms
- Proven to work at scale
- Easy to add features (recording, analytics, multi-agent)

---

## ✅ Summary

Mora now correctly implements the **original TDD architecture**:
- ✅ Twilio for outbound calling
- ✅ LiveKit for voice agent (STT-LLM-TTS)
- ✅ Multi-turn conversations
- ✅ Real-time transcription
- ✅ Production-grade voice quality
- ✅ Scalable and flexible

Ready for **Stage 5: Enhanced Evaluation** and **Stage 6: Frontend Dashboard**! 🚀
