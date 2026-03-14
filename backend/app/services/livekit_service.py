"""
LiveKit Room Management Service
Creates rooms, generates tokens, manages agent connections
"""

import logging
from typing import Dict, Optional, Any
from livekit import api
from app.core.config import settings

logger = logging.getLogger(__name__)


class LiveKitService:
    """
    Manages LiveKit rooms and agent deployment for voice tests
    """
    
    def __init__(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.url = settings.LIVEKIT_URL
        
        # Create LiveKit API client
        self.lk_api = api.LiveKitAPI(
            url=self.url,
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        
        logger.info(f"✅ LiveKit service initialized: {self.url}")
    
    async def create_test_room(
        self,
        room_name: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a LiveKit room for outbound test call
        
        Args:
            room_name: Unique room name
            metadata: Test configuration (scenario, test_cases, etc.)
            
        Returns:
            Dictionary with room info and SIP URI
        """
        try:
            import json
            
            logger.info(f"📦 Creating test room: {room_name}")
            logger.info(f"🤖 Dispatching LiveKit agent: {settings.LIVEKIT_DISPATCH_AGENT}")
            
            # Create room with agent dispatch so the voice agent auto-joins
            room = await self.lk_api.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    metadata=json.dumps(metadata),
                    empty_timeout=600,  # 10 minutes
                    max_participants=10,
                    agents=[
                        api.RoomAgentDispatch(agent_name=settings.LIVEKIT_DISPATCH_AGENT),
                    ],
                )
            )
            
            logger.info(f"✅ Room created with agent dispatch: {room.name}")
            
            # Generate SIP participant token/URI for Twilio
            # The SIP participant will be the bot answering our call
            sip_uri = f"sip:{room_name}@{self.url.replace('wss://', '').replace('https://', '')}"
            
            return {
                'room_name': room.name,
                'room_sid': room.sid,
                'sip_uri': sip_uri,
                'metadata': metadata,
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating test room: {e}", exc_info=True)
            raise
    
    async def create_room_for_test(
        self,
        test_run_id: str,
        scenario_description: str,
        expected_behavior: str,
        initial_utterance: str,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a LiveKit room for a specific test run
        
        Args:
            test_run_id: UUID of test run
            scenario_description: Business scenario description
            expected_behavior: What bot should do
            initial_utterance: How caller starts
            agent_config: Optional LLM/voice config
            
        Returns:
            Room details including room_name, room_sid, metadata
        """
        try:
            room_name = f"test-{test_run_id}"
            
            # Prepare room metadata (used by voice agent)
            import json
            metadata = json.dumps({
                "test_run_id": test_run_id,
                "scenario_description": scenario_description,
                "expected_behavior": expected_behavior,
                "initial_utterance": initial_utterance,
                "agent_config": agent_config or {}
            })
            
            # Create room
            room = await self.lk_api.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    metadata=metadata,
                    empty_timeout=300,  # Auto-cleanup after 5 min if empty
                    max_participants=10
                )
            )
            
            logger.info(f"🏠 Created LiveKit room: {room_name} (SID: {room.sid})")
            
            return {
                "room_name": room.name,
                "room_sid": room.sid,
                "metadata": metadata,
                "url": self.url
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create room: {e}")
            raise
    
    async def get_room_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a room
        """
        try:
            rooms = await self.lk_api.room.list_rooms(
                api.ListRoomsRequest(names=[room_name])
            )
            
            if rooms and len(rooms) > 0:
                room = rooms[0]
                return {
                    "room_name": room.name,
                    "room_sid": room.sid,
                    "num_participants": room.num_participants,
                    "metadata": room.metadata
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get room info: {e}")
            return None
    
    async def delete_room(self, room_name: str):
        """
        Delete a room after test completes
        """
        try:
            await self.lk_api.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            logger.info(f"🗑️ Deleted room: {room_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete room: {e}")
    
    def generate_participant_token(
        self,
        room_name: str,
        identity: str,
        name: str = "",
        can_publish: bool = True,
        can_subscribe: bool = True
    ) -> str:
        """
        Generate access token for a participant
        """
        token = api.AccessToken(
            api_key=self.api_key,
            api_secret=self.api_secret
        )
        token.with_identity(identity)
        token.with_name(name or identity)
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=can_publish,
                can_subscribe=can_subscribe
            )
        )
        
        return token.to_jwt()


# Global instance
_livekit_service: Optional[LiveKitService] = None


def get_livekit_service() -> LiveKitService:
    """
    Get or create LiveKit service singleton
    """
    global _livekit_service
    if _livekit_service is None:
        _livekit_service = LiveKitService()
    return _livekit_service


# Export singleton instance
livekit_service = get_livekit_service()
