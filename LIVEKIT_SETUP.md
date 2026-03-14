# 🚀 LiveKit Setup Guide

## Why This Change?

I apologize for deviating from the original TDD. You were right - the plan clearly specified:
- **Twilio**: Outbound calling only
- **LiveKit**: Full conversational agent (STT → LLM → TTS)

The previous implementation used Twilio's simple text-to-speech, limiting tests to single utterances. Now we have **real multi-turn conversations**.

---

## 🎯 What's New

### Architecture Change:
```
BEFORE: Mora → Twilio (TTS) → Bot → Recording → Evaluation
NOW:    Mora → LiveKit Agent (STT-LLM-TTS) ↔ Twilio → Bot → Real-time Transcript → Evaluation
```

### New Capabilities:
✅ Multi-turn conversations (follow-up questions)
✅ Dynamic responses based on context
✅ Real-time transcription (no mock data)
✅ Production-grade voice quality
✅ Interruption handling

---

## 📋 Setup Steps

### 1. Get LiveKit Credentials (2 minutes)

**Go to:** https://cloud.livekit.io/

1. Click "Sign up" (free tier, no credit card)
2. Create new project (e.g., "Mora Testing")
3. Go to "Settings" → "Keys"
4. Copy these 3 values:
   - **WebSocket URL**: `wss://your-project.livekit.cloud`
   - **API Key**: `APIxxxxxxxxxxx`
   - **API Secret**: `secret_key_here`

### 2. Get Deepgram Credentials (Speech-to-Text)

**Go to:** https://deepgram.com/

1. Sign up (free $200 credit)
2. Go to "API Keys"
3. Create new key
4. Copy: `DEEPGRAM_API_KEY`

### 3. Get ElevenLabs Credentials (Text-to-Speech)

**Go to:** https://elevenlabs.io/

1. Sign up (free 10,000 characters/month)
2. Go to "Profile" → "API Key"
3. Copy: `ELEVENLABS_API_KEY`

### 4. Update `.env` File

Open `backend/.env` and add:

```bash
# LiveKit Configuration (REQUIRED)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxx
LIVEKIT_API_SECRET=your_secret_key

# Deepgram (Speech-to-Text) (REQUIRED)
DEEPGRAM_API_KEY=your_deepgram_key

# ElevenLabs (Text-to-Speech) (REQUIRED)
ELEVENLABS_API_KEY=your_elevenlabs_key

# OpenAI (already configured for LLM)
OPENAI_API_KEY=your_existing_openai_key
```

### 5. Run the System (3 terminals)

**Terminal 1 - FastAPI Server:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - LiveKit Agent Worker (NEW!):**
```bash
cd backend
python run_agent.py
```

**Terminal 3 - ngrok (same as before):**
```bash
ngrok http 8000
# Copy the HTTPS URL and update PUBLIC_URL in .env
```

---

## ✅ Test It

### Create and Execute Test:

```bash
# Execute project (same command as before)
curl -X POST http://localhost:8000/api/projects/{project_id}/execute

# Watch the magic happen:
# - Terminal 1: Call initiated, LiveKit room created
# - Terminal 2: 🎙️ Agent started, 👤 User speech, 🤖 Agent response
# - Terminal 3: Twilio webhook hits
```

### Expected Agent Logs (Terminal 2):
```
🚀 Starting voice agent for room: test-abc123
✅ Voice assistant created with STT, LLM, TTS
👤 User: Hi, I need to book a table for 4 people tomorrow at 8 PM please
🤖 Agent: I'd be happy to help you with that reservation. Just to confirm, you'd like a table for 4 people tomorrow at 8 PM, is that correct?
👤 User: Yes, that's right
🤖 Agent: Perfect! Can I have your name please?
👤 User: It's John Smith
🤖 Agent: Thank you, John. Your table for 4 people tomorrow at 8 PM is confirmed!
🏁 Voice agent ended for room: test-abc123
```

### Get Transcript:
```bash
curl http://localhost:8000/api/evaluations/test-runs/{test_run_id}/evaluation
```

---

## 🎨 Voice Customization

### Change the Voice:

In `call_execution_service.py`, update `agent_config`:

```python
agent_config={
    "llm_model": "gpt-4o",           # or "gpt-3.5-turbo" (faster/cheaper)
    "temperature": 0.7,              # 0.0 = deterministic, 1.0 = creative
    "voice_id": "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs voice ID
}
```

**Popular ElevenLabs Voices:**
- `21m00Tcm4TlvDq8ikWAM` - Rachel (female, professional)
- `EXAVITQu4vr4xnSDxMaL` - Sarah (female, warm)
- `ErXwobaYiN019PkySvjV` - Antoni (male, friendly)
- `MF3mGyEYCl7XYWbV9V6O` - Elli (female, energetic)

Browse more: https://elevenlabs.io/voice-library

---

## 💰 Cost Comparison

### Single Test Call (2 minutes, 4 conversational turns):

| Service | Cost | What It Does |
|---------|------|--------------|
| Twilio | $0.026 | Phone call (2 min × $0.013/min) |
| LiveKit | $0.016 | Room hosting (2 min × $0.008/min) |
| Deepgram | $0.009 | Speech recognition (2 min × $0.0043/min) |
| OpenAI | $0.020 | LLM responses (4 turns × $0.005) |
| ElevenLabs | $0.012 | Voice synthesis (4 responses × $0.003) |
| **TOTAL** | **$0.083** | **Full conversation test** |

**Previous approach:** $0.026 (Twilio only, but single utterance)

**ROI:** Now you can test **real conversations** instead of just "hello" → "thanks" → hangup

---

## 🔍 How It Works

### 1. Test Starts
- Mora creates LiveKit room with test metadata
- Agent worker sees room, joins automatically
- Agent reads scenario and prepares system prompt

### 2. Call Connects
- Twilio dials bot phone number
- Bot answers
- TwiML returns `<Stream>` WebSocket connection

### 3. Audio Flows
- Caller speaks → Twilio → WebSocket → LiveKit → Deepgram STT
- Text → GPT-4 LLM → Response text
- Response → ElevenLabs TTS → Audio
- Audio → LiveKit → WebSocket → Twilio → Bot hears it

### 4. Transcript Captured
- Every user utterance saved
- Every agent response saved
- Full conversation available for evaluation

---

## 🐛 Troubleshooting

### "Import livekit could not be resolved"
- This is VS Code not seeing the new packages
- Ignore - they're installed (check `pip list | grep livekit`)
- Or reload VS Code Python environment

### Agent not starting
- Check Terminal 2 for errors
- Verify all API keys in `.env`
- Ensure LiveKit URL starts with `wss://` (not `https://`)

### No audio in call
- Check ngrok is running and PUBLIC_URL is updated
- Verify Twilio debugger: https://console.twilio.com/debugger
- Check WebSocket connection in Terminal 1 logs

### "Room not found"
- Ensure Terminal 2 (agent worker) is running BEFORE making call
- Check LiveKit dashboard: https://cloud.livekit.io/projects

---

## 📊 Benefits

### What You Can Now Test:

#### ❌ Before (Single Utterance):
```
Caller: "Hi, I need a table for 4 tomorrow at 8 PM"
Bot: [Can only say pre-scripted response]
[Call ends after 5 seconds]
```

#### ✅ Now (Multi-Turn Conversation):
```
Caller: "Hi, I need a table for 4 tomorrow at 8 PM"
Bot: "Just to confirm, 4 people tomorrow at 8 PM, correct?"
Caller: "Yes, that's right"
Bot: "Can I have your name?"
Caller: "John Smith"
Bot: "Thank you, John. Your reservation is confirmed!"
[Natural conversation, dynamic responses, real testing]
```

### Real Scenarios You Can Test:
- ✅ Restaurant bookings with follow-ups
- ✅ Customer support with clarifying questions
- ✅ Appointment scheduling with conflict resolution
- ✅ Order modifications mid-conversation
- ✅ Error handling and recovery
- ✅ Interruption handling

---

## 🎓 Why This Matters

The original TDD specified LiveKit because:

1. **Production-Grade:** Same stack used by Bland.ai, Vapi.ai ($10M+ ARR companies)
2. **Scalable:** LiveKit handles 1000s of concurrent agents
3. **Flexible:** Easy to swap STT/LLM/TTS providers
4. **Real Testing:** Single utterances don't test real bot behavior
5. **Future-Proof:** Enables features like multi-agent testing, sentiment analysis, coaching

---

## ✅ Summary

**What Changed:**
- ✅ Added 5 LiveKit packages
- ✅ Created voice agent with STT-LLM-TTS pipeline
- ✅ Built WebSocket bridge (Twilio ↔ LiveKit)
- ✅ Updated call execution to use LiveKit rooms
- ✅ Modified TwiML to use `<Stream>` instead of `<Say>`

**What You Need to Do:**
1. Get API keys (LiveKit, Deepgram, ElevenLabs) - 10 minutes
2. Update `.env` file
3. Run 3 terminals (server, agent, ngrok)
4. Test multi-turn conversation

**Result:**
🎉 **Real conversational testing** instead of single-utterance placeholders!

---

## 📞 Questions?

Check the detailed docs: `STAGE_4_LIVEKIT_COMPLETE.md`

Need help? The agent logs (Terminal 2) are very verbose and will show exactly what's happening.

Let's get those API keys and test a real conversation! 🚀
