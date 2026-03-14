#!/usr/bin/env python3
"""
LiveKit Voice Agent Worker
Run this in a separate terminal to handle voice agent connections
"""

import asyncio
import logging
from livekit.agents import WorkerOptions, cli
from app.agents.voice_agent import entrypoint, prewarm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Starting LiveKit Voice Agent Worker")
    logger.info("📞 Ready to handle incoming phone calls...")
    
    # Run the agent worker with prewarm for faster call handling
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="mora-voice-agent",
        )
    )
