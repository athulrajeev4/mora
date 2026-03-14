"""
Scripted Test Caller Agent for Mora Platform
This agent MAKES calls to user's bots and follows test scripts
"""

import os
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, google, elevenlabs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestCallerAgent:
    """
    AI-powered test caller that executes scripted conversations with voice bots
    
    This agent:
    1. Loads a persona (e.g., "Act as Nora Parker...")
    2. Executes test cases sequentially (speaks utterances)
    3. Listens to bot responses
    4. Evaluates if bot behaved as expected
    5. Records transcript and results
    """
    
    def __init__(
        self,
        scenario: str,
        test_cases: List[Dict[str, Any]],
        test_run_id: str,
    ):
        """
        Initialize test caller agent
        
        Args:
            scenario: Persona and context (e.g., "Act as Nora Parker, calling to check case status...")
            test_cases: List of test cases with utterance and expected_behavior
            test_run_id: UUID of the test run for result storage
        """
        self.scenario = scenario
        self.test_cases = sorted(test_cases, key=lambda x: x.get('order', 0))
        self.test_run_id = test_run_id
        
        # Results tracking
        self.transcript = []
        self.evaluations = []
        self.current_test_case_index = 0
        
        # Voice components
        self.stt = None
        self.llm = None
        self.tts = None
        self.session = None
        
        logger.info(f"🎭 TestCallerAgent initialized with persona: {scenario[:50]}...")
        logger.info(f"📋 Loaded {len(self.test_cases)} test cases")
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt that includes persona and instructions
        """
        return f"""
{self.scenario}

IMPORTANT INSTRUCTIONS:
You are an AI test caller executing a scripted conversation to test a voice bot.
You must follow the test script EXACTLY while sounding natural and conversational.

Your conversation script:
{self._format_test_cases_for_prompt()}

BEHAVIOR RULES:
1. Speak each test case utterance in order
2. Wait for the bot to respond after each utterance
3. Sound natural, like a real person making a call
4. Keep your tone consistent with your persona
5. If the bot asks something unexpected, respond naturally but try to steer back to the script
6. Be conversational but concise (1-2 sentences per response)

Remember: You are testing the bot, so follow the script closely!
"""
    
    def _format_test_cases_for_prompt(self) -> str:
        """Format test cases for the system prompt"""
        lines = []
        for i, tc in enumerate(self.test_cases, 1):
            lines.append(f"{i}. You say: \"{tc['utterance']}\"")
            lines.append(f"   Expected bot behavior: {tc['expected_behavior']}")
        return "\n".join(lines)
    
    async def initialize_components(self):
        """Initialize STT, LLM, and TTS components"""
        logger.info("🔧 Initializing voice components...")
        
        # Speech-to-Text (Deepgram)
        self.stt = deepgram.STT(
            model="nova-2-general",
            language="en",
        )
        
        # Language Model (Google Gemini for understanding responses)
        self.llm = google.LLM(
            model="gemini-2.0-flash-exp",
        )
        
        # Text-to-Speech (ElevenLabs)
        self.tts = elevenlabs.TTS(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            model="eleven_turbo_v2_5",
        )
        
        logger.info("✅ Voice components initialized")
    
    async def start_session(self, ctx: JobContext):
        """
        Start the agent session in the LiveKit room
        
        Args:
            ctx: JobContext from LiveKit
        """
        logger.info(f"🚀 Starting test caller session in room: {ctx.room.name}")
        
        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Store context for later use
        self.ctx = ctx
        
        # Wait for the bot (SIP participant) to join
        logger.info("⏳ Waiting for bot to answer the call...")
        bot_participant = await ctx.wait_for_participant()
        
        logger.info(f"📞 Bot answered! Participant: {bot_participant.identity}")
        
        # Create the voice agent with our persona
        # The agent will handle the conversation naturally while following the script
        agent = Agent(
            instructions=self._build_system_prompt(),
            stt=self.stt,
            llm=self.llm,
            tts=self.tts,
        )
        
        # Start agent session
        self.session = AgentSession()
        
        # Subscribe to agent events to capture conversation
        self.session.on("agent_speech_committed", self._on_agent_speech)
        self.session.on("user_speech_committed", self._on_user_speech)
        
        await self.session.start(agent=agent, room=ctx.room)
        
        logger.info("✅ Agent session started, ready to execute test script")
        
        return bot_participant
    
    def _on_agent_speech(self, speech):
        """Callback when agent speaks"""
        logger.info(f"🗣️ Agent said: {speech.text if hasattr(speech, 'text') else speech}")
        self.transcript.append({
            'speaker': 'test_caller',
            'text': str(speech.text if hasattr(speech, 'text') else speech),
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def _on_user_speech(self, speech):
        """Callback when user (bot) speaks"""
        logger.info(f"🤖 Bot said: {speech.text if hasattr(speech, 'text') else speech}")
        self.transcript.append({
            'speaker': 'bot',
            'text': str(speech.text if hasattr(speech, 'text') else speech),
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    async def execute_test_script(self, bot_participant):
        """
        Execute the test script: speak utterances and evaluate responses
        """
        logger.info("🎬 Starting test script execution...")
        
        # Give the bot a moment to settle after answering
        await asyncio.sleep(2)
        
        # Start the conversation by speaking the first test case
        if self.test_cases:
            first_test = self.test_cases[0]
            logger.info(f"\n{'='*60}")
            logger.info(f"📝 Starting conversation with Test Case 1/{len(self.test_cases)}")
            logger.info(f"Utterance: {first_test['utterance']}")
            logger.info(f"{'='*60}")
            
            # Speak the first utterance to initiate the conversation
            await self.session.say(first_test['utterance'], allow_interruptions=True)
            
            # Record in transcript
            self.transcript.append({
                'speaker': 'test_caller',
                'text': first_test['utterance'],
                'timestamp': datetime.utcnow().isoformat(),
                'test_case_id': first_test.get('id'),
            })
        
        # Now let the agent continue the conversation naturally
        # The LLM will follow the script based on the system prompt
        logger.info("🤖 Agent is now in conversation mode, following the script...")
        
        # Keep the session alive for the duration of the test
        # The agent will naturally follow the conversation script
        test_duration = len(self.test_cases) * 10  # ~10 seconds per test case
        logger.info(f"⏱️ Running test for approximately {test_duration} seconds...")
        
        await asyncio.sleep(test_duration)
        
        logger.info("🏁 Test duration completed, ending call...")
        
        # End the call gracefully
        await self.session.say("Thank you for your help. Goodbye!")
        await asyncio.sleep(2)
        
        # Wait for bot to disconnect
        try:
            await asyncio.wait_for(
                bot_participant.wait_for_disconnection(),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for bot disconnection")
    
    async def _execute_single_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case: speak utterance, listen to response, evaluate
        
        Args:
            test_case: Test case with utterance and expected_behavior
            
        Returns:
            Evaluation result with passed/failed, score, and feedback
        """
        utterance = test_case['utterance']
        expected_behavior = test_case['expected_behavior']
        
        # 1. Speak the test utterance
        logger.info(f"🗣️ Test Caller says: {utterance}")
        await self.session.say(utterance, allow_interruptions=True)
        
        # Record in transcript
        self.transcript.append({
            'speaker': 'test_caller',
            'text': utterance,
            'timestamp': datetime.utcnow().isoformat(),
            'test_case_id': test_case.get('id'),
        })
        
        # 2. Wait for bot response (give it time to process and respond)
        await asyncio.sleep(3)  # Wait for bot to start responding
        
        # Note: In real implementation, we'd capture the actual bot response from STT
        # For now, we'll use a placeholder. The LiveKit agent will handle the actual conversation.
        bot_response = "[Bot response will be captured from STT stream]"
        
        logger.info(f"👂 Listening for bot response...")
        
        # Record bot response placeholder in transcript
        self.transcript.append({
            'speaker': 'bot',
            'text': bot_response,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        # 3. Evaluate the response
        # TODO: Implement actual evaluation using LLM
        evaluation = await self._evaluate_response(bot_response, expected_behavior)
        
        logger.info(f"📊 Evaluation: {'✅ PASSED' if evaluation['passed'] else '❌ FAILED'}")
        logger.info(f"   Score: {evaluation['score']}/100")
        logger.info(f"   Feedback: {evaluation['feedback']}")
        
        return {
            'test_case_id': test_case.get('id'),
            'utterance': utterance,
            'bot_response': bot_response,
            'expected_behavior': expected_behavior,
            'passed': evaluation['passed'],
            'score': evaluation['score'],
            'feedback': evaluation['feedback'],
            'critical_failure': evaluation.get('critical_failure', False),
        }
    
    async def _evaluate_response(
        self,
        bot_response: str,
        expected_behavior: str
    ) -> Dict[str, Any]:
        """
        Evaluate if bot response matches expected behavior
        
        Args:
            bot_response: What the bot said
            expected_behavior: What the bot should have done
            
        Returns:
            Evaluation with passed, score, and feedback
        """
        # TODO: Use LLM to evaluate the response
        # For now, return a placeholder evaluation
        
        evaluation_prompt = f"""
Evaluate this voice bot interaction:

EXPECTED BEHAVIOR: {expected_behavior}
ACTUAL BOT RESPONSE: {bot_response}

Did the bot do what was expected?

Provide your evaluation in JSON format:
{{
    "passed": true/false,
    "score": 0-100,
    "feedback": "Detailed explanation of why it passed or failed",
    "critical_failure": true/false (true if bot completely failed, false if minor issue)
}}
"""
        
        try:
            # Use LLM to evaluate
            result = await self.llm.generate(evaluation_prompt)
            evaluation = json.loads(result)
            return evaluation
        except Exception as e:
            logger.error(f"❌ Error evaluating response: {e}")
            # Return conservative evaluation on error
            return {
                'passed': False,
                'score': 0,
                'feedback': f"Evaluation error: {str(e)}",
                'critical_failure': False,
            }
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get final test results
        
        Returns:
            Dictionary with transcript and evaluations
        """
        total_tests = len(self.evaluations)
        passed_tests = sum(1 for e in self.evaluations if e['passed'])
        avg_score = sum(e['score'] for e in self.evaluations) / total_tests if total_tests > 0 else 0
        
        return {
            'test_run_id': self.test_run_id,
            'transcript': self.transcript,
            'evaluations': self.evaluations,
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'average_score': avg_score,
            },
            'completed_at': datetime.utcnow().isoformat(),
        }


# LiveKit worker entrypoint for on-demand test calls
async def test_caller_entrypoint(ctx: JobContext):
    """
    Entrypoint for LiveKit worker when making a test call
    
    This is called when we create a room for a test call.
    The room metadata should contain the test configuration.
    """
    logger.info(f"🚀 Test Caller entrypoint for room: {ctx.room.name}")
    
    # Parse room metadata to get test configuration
    # Format: test-{project_id}-{test_case_id}-{uuid}
    # Metadata should contain scenario, test_cases, test_run_id
    
    try:
        # Get metadata from room
        room_metadata = json.loads(ctx.room.metadata or '{}')
        
        scenario = room_metadata.get('scenario', 'Act as a test caller')
        test_cases = room_metadata.get('test_cases', [])
        test_run_id = room_metadata.get('test_run_id', 'unknown')
        
        # Create test caller agent
        agent = TestCallerAgent(
            scenario=scenario,
            test_cases=test_cases,
            test_run_id=test_run_id,
        )
        
        # Initialize components
        await agent.initialize_components()
        
        # Start session and wait for bot
        bot_participant = await agent.start_session(ctx)
        
        # Execute test script
        await agent.execute_test_script(bot_participant)
        
        # Get results
        results = agent.get_results()
        
        logger.info("✅ Test call completed successfully")
        logger.info(f"📊 Results: {results['summary']}")
        
        # TODO: Store results in database via API callback
        
    except Exception as e:
        logger.error(f"❌ Error in test caller entrypoint: {e}", exc_info=True)
        raise


def prewarm(proc: JobProcess):
    """Preload resources when worker starts"""
    proc.userdata["ready"] = True
    logger.info("🔥 Test Caller worker prewarmed and ready")


# CLI entry point for running as standalone worker
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=test_caller_entrypoint,
            prewarm_fnc=prewarm,
            agent_name="mora-test-caller",
        )
    )
