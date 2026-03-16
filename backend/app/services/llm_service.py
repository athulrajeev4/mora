"""
LLM Service - Handles transcription and evaluation using Gemini/OpenAI
"""
import os
import json
import httpx
from typing import Optional, Dict, Any
from pathlib import Path
from google import genai
from openai import OpenAI

from app.core.config import settings


class LLMService:
    """Service for LLM-based transcription and evaluation"""
    
    def __init__(self):
        """Initialize LLM clients based on configuration"""
        self.provider = settings.LLM_PROVIDER
        
        # Initialize Gemini
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_key":
            # Use gemini-2.5-flash (latest, fastest model available)
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = "gemini-2.5-flash"
        else:
            self.gemini_client = None
            self.gemini_model = None
        
        # Initialize OpenAI (for Whisper transcription)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_key":
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
    
    # ========================================================================
    # TRANSCRIPTION
    # ========================================================================
    
    async def transcribe_audio(self, audio_url: str, audio_format: str = "mp3") -> Optional[str]:
        """
        Transcribe audio using Whisper (primary) or Gemini (fallback).
        Returns None if neither provider is available.
        """
        try:
            audio_path = await self._download_audio(audio_url)
            if not audio_path:
                print(f"Failed to download audio from {audio_url}")
                return None

            file_size = os.path.getsize(audio_path)
            print(f"✅ Audio downloaded ({file_size} bytes)")

            transcript = None

            if self.openai_client:
                print("📝 Transcribing with Whisper...")
                transcript = await self._transcribe_with_whisper(audio_path)

            if not transcript and self.gemini_client:
                print("📝 Transcribing with Gemini (audio fallback)...")
                transcript = await self._transcribe_with_gemini(audio_path)

            if os.path.exists(audio_path):
                os.remove(audio_path)

            if not transcript:
                print("❌ No transcription provider available (need OPENAI_API_KEY or GEMINI_API_KEY)")
                return None

            return transcript

        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _download_audio(self, audio_url: str) -> Optional[str]:
        """
        Download audio file from Twilio to temporary location
        
        Args:
            audio_url: Twilio recording URL
            
        Returns:
            Path to downloaded file or None
        """
        try:
            # Create temp directory if not exists
            temp_dir = Path("/tmp/mora_audio")
            temp_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            filename = f"recording_{os.urandom(8).hex()}.mp3"
            file_path = temp_dir / filename
            
            # Download with Twilio authentication
            async with httpx.AsyncClient() as client:
                # Twilio recording URLs require auth
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                response = await client.get(audio_url, auth=auth, follow_redirects=True)
                
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    return str(file_path)
                else:
                    print(f"Failed to download audio: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            return None
    
    async def _transcribe_with_whisper(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # Can be made configurable
                )
            return transcript.text
            
        except Exception as e:
            print(f"Whisper transcription error: {str(e)}")
            return None
    
    async def _transcribe_with_gemini(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using Gemini multimodal (supports audio natively)."""
        try:
            if not self.gemini_client:
                return None

            audio_file = self.gemini_client.files.upload(file=audio_path)

            prompt = (
                "Transcribe this phone call recording as a dialogue. "
                "Use the format 'Caller: ...' and 'Bot: ...' for each speaker turn. "
                "If you cannot distinguish speakers, just transcribe sequentially. "
                "Return ONLY the transcript text, no commentary."
            )
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=[prompt, audio_file],
            )

            return response.text

        except Exception as e:
            print(f"Gemini transcription error: {str(e)}")
            return None
    
    # ========================================================================
    # FUNCTIONAL EVALUATION
    # ========================================================================
    
    async def evaluate_functional(
        self, 
        transcript: str, 
        expected_behavior: str,
        test_scenario: str
    ) -> Dict[str, Any]:
        """
        Evaluate if the conversation achieved expected functional outcomes
        
        Args:
            transcript: Full conversation transcript
            expected_behavior: Expected bot behavior from test case
            test_scenario: Business context (e.g., "Customer calling restaurant")
            
        Returns:
            Dictionary with evaluation results:
            {
                "passed": bool,
                "score": float (0-100),
                "reasoning": str,
                "matched_behaviors": List[str],
                "missing_behaviors": List[str]
            }
        """
        prompt = f"""You are evaluating a voice AI bot's performance in a phone call.

**Scenario:** {test_scenario}

**Expected Behavior:**
{expected_behavior}

**Call Transcript:**
{transcript}

**Task:** Evaluate if the bot achieved the expected behavior based on the transcript.

Provide your evaluation in the following JSON format:
{{
    "passed": true/false,
    "score": 0-100 (numeric score),
    "reasoning": "Clear explanation of why it passed or failed",
    "matched_behaviors": ["list", "of", "behaviors", "that", "were", "met"],
    "missing_behaviors": ["list", "of", "expected", "behaviors", "that", "were", "missing"]
}}

Be specific and objective. Focus on whether functional requirements were met."""

        return await self._call_llm(prompt, response_type="json")
    
    # ========================================================================
    # CONVERSATIONAL EVALUATION
    # ========================================================================
    
    async def evaluate_conversational(
        self,
        transcript: str,
        test_scenario: str
    ) -> Dict[str, Any]:
        """
        Evaluate the conversational quality of the bot
        
        Args:
            transcript: Full conversation transcript
            test_scenario: Business context
            
        Returns:
            Dictionary with conversational metrics:
            {
                "overall_score": float (0-100),
                "fluency": float (0-100),
                "naturalness": float (0-100),
                "error_handling": float (0-100),
                "coherence": float (0-100),
                "feedback": str,
                "strengths": List[str],
                "weaknesses": List[str]
            }
        """
        prompt = f"""You are evaluating the conversational quality of a voice AI bot.

**Scenario:** {test_scenario}

**Call Transcript:**
{transcript}

**Task:** Evaluate the bot's conversational abilities across multiple dimensions.

Provide your evaluation in the following JSON format:
{{
    "overall_score": 0-100 (average of all scores),
    "fluency": 0-100 (how smoothly the conversation flows),
    "naturalness": 0-100 (how human-like and natural the responses are),
    "error_handling": 0-100 (how well the bot handles unclear inputs or errors),
    "coherence": 0-100 (logical consistency and context awareness),
    "feedback": "Overall assessment of conversational quality",
    "strengths": ["list", "of", "strong", "points"],
    "weaknesses": ["list", "of", "areas", "for", "improvement"]
}}

Be constructive and specific in your feedback."""

        return await self._call_llm(prompt, response_type="json")
    
    # ========================================================================
    # LLM CALL HELPER
    # ========================================================================
    
    async def _call_llm(self, prompt: str, response_type: str = "json") -> Dict[str, Any]:
        """
        Call LLM (Gemini or OpenAI) with given prompt
        
        Args:
            prompt: The evaluation prompt
            response_type: "json" or "text"
            
        Returns:
            Parsed response
        """
        try:
            if self.provider == "gemini" and self.gemini_model:
                return await self._call_gemini(prompt, response_type)
            elif self.provider == "openai" and self.openai_client:
                return await self._call_openai(prompt, response_type)
            else:
                raise ValueError(f"LLM provider '{self.provider}' not configured")
                
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            return self._get_error_response()
    
    async def _call_gemini(self, prompt: str, response_type: str) -> Dict[str, Any]:
        """Call Gemini API"""
        response = None
        try:
            if not self.gemini_client:
                raise ValueError("Gemini client not configured")

            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
            )
            
            if response_type == "json":
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                return json.loads(text)
            return {"response": response.text}
            
        except json.JSONDecodeError as e:
            print(f"Gemini JSON parse error: {str(e)}")
            if response and hasattr(response, 'text'):
                print(f"Response text: {response.text[:500]}")
            return self._get_error_response()
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self._get_error_response()
    
    async def _call_openai(self, prompt: str, response_type: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            response_format = {"type": "json_object"} if response_type == "json" else None
            
            completion = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert voice AI evaluator."},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_format,
                temperature=0.3  # Lower temperature for more consistent evaluations
            )
            
            content = completion.choices[0].message.content
            
            if response_type == "json":
                return json.loads(content)
            return {"response": content}
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return self._get_error_response()
    
    def _get_error_response(self) -> Dict[str, Any]:
        """Return error response structure"""
        return {
            "error": True,
            "passed": False,
            "score": 0,
            "reasoning": "Evaluation failed due to LLM error",
            "overall_score": 0,
            "feedback": "Unable to complete evaluation"
        }
    
    def generate_test_cases(self, scenario: str, prompt: str, num_cases: int = 5) -> list[dict]:
        """
        Generate test cases using LLM based on scenario and bot prompt
        
        Args:
            scenario: Testing scenario with context, auth details, caller info
            prompt: Bot system prompt to test against
            num_cases: Number of test cases to generate (default 5)
        
        Returns:
            List of test cases with utterance and expected_behavior
        """
        generation_prompt = f"""You are an expert QA engineer creating test cases for a voice AI assistant.

**Scenario Context:**
{scenario}

**Bot System Prompt:**
{prompt}

**Task:** Generate {num_cases} diverse test cases to thoroughly test this voice AI bot.

For each test case, provide:
1. **utterance**: What the caller will say (be realistic and conversational)
2. **expected_behavior**: What the bot should do in response

**Important Guidelines:**
- Cover happy paths, edge cases, and error handling
- Include authentication scenarios if mentioned in context
- Test different conversation flows (greetings, questions, requests, objections)
- Be specific about expected bot behaviors
- Make utterances sound natural and human-like
- Consider the persona/context from the scenario

**Output Format (JSON array):**
```json
[
  {{
    "utterance": "Hi, I'd like to check my account balance",
    "expected_behavior": "Bot should authenticate user by asking for account number or credentials, then provide balance information"
  }},
  ...
]
```

Generate exactly {num_cases} test cases. Return ONLY the JSON array, no other text."""

        try:
            if self.gemini_client:
                # Use Gemini
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=generation_prompt,
                )
                response_text = response.text.strip()
            elif self.openai_client:
                # Fallback to OpenAI
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert QA engineer creating test cases for voice AI systems."},
                        {"role": "user", "content": generation_prompt}
                    ],
                    temperature=0.7,
                )
                response_text = response.choices[0].message.content.strip()
            else:
                raise Exception("No LLM provider configured")
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            test_cases = json.loads(response_text)
            
            # Validate structure
            if not isinstance(test_cases, list):
                raise ValueError("Response is not a list")
            
            for case in test_cases:
                if not isinstance(case, dict) or "utterance" not in case or "expected_behavior" not in case:
                    raise ValueError("Invalid test case structure")
            
            return test_cases
            
        except Exception as e:
            print(f"Error generating test cases: {e}")
            # Return fallback test cases
            return [
                {
                    "utterance": "Hello, can you help me?",
                    "expected_behavior": "Bot should greet the caller warmly and ask how it can assist"
                },
                {
                    "utterance": "I need to speak to a human agent",
                    "expected_behavior": "Bot should acknowledge the request and provide transfer options or escalation path"
                },
                {
                    "utterance": "What are your business hours?",
                    "expected_behavior": "Bot should provide accurate business hours information"
                }
            ]


# Singleton instance
llm_service = LLMService()
