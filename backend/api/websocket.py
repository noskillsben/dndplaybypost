from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
import json
import logging

from core.database import get_db
from models.user import User
from models.campaign_member import CampaignMember
from models.message import Message
from models.character import Character
from services.connection_manager import manager
from services.dice_roller import DiceRoller
from schemas.schemas import DiceRollData
from api.deps import get_current_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["websocket"])





@router.websocket("/{campaign_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    campaign_id: UUID,
    token: Optional[str] = None
):
    """WebSocket endpoint for campaign chat"""
    logger.info(f"WebSocket connection attempt for campaign {campaign_id}")
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Check if user is a member of the campaign
        result = await db.execute(
            select(CampaignMember)
            .where(CampaignMember.campaign_id == campaign_id)
            .where(CampaignMember.user_id == user.id)
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connect to campaign room
        await manager.connect(websocket, campaign_id, user.id)
        
        # Notify others that user joined
        await manager.broadcast(campaign_id, {
            "type": "user_joined",
            "data": {
                "user_id": str(user.id),
                "username": user.username
            }
        })
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                message_type = data.get("type")
                
                if message_type == "message":
                    # Create message in database
                    content = data.get("content", "")
                    character_id = data.get("character_id")
                    is_ic = data.get("is_ic", True)
                    dice_expression = data.get("dice_expression")
                    
                    extra_data = {}
                    
                    # Handle dice roll if present
                    if dice_expression:
                        try:
                            roller = DiceRoller()
                            roll_result = roller.roll(dice_expression)
                            extra_data["dice_roll"] = {
                                "expression": roll_result.expression,
                                "total": roll_result.total,
                                "rolls": roll_result.rolls,
                                "breakdown": roll_result.breakdown
                            }
                        except ValueError as e:
                            # Send error back to sender
                            await websocket.send_json({
                                "type": "error",
                                "data": {"message": f"Invalid dice expression: {str(e)}"}
                            })
                            continue
                    
                    # Verify character ownership if posting as character
                    if character_id:
                        result = await db.execute(
                            select(Character)
                            .where(Character.id == UUID(character_id))
                            .where(Character.campaign_id == campaign_id)
                            .where(Character.player_id == user.id)
                        )
                        if not result.scalar_one_or_none():
                            await websocket.send_json({
                                "type": "error",
                                "data": {"message": "Character not found or not owned by you"}
                            })
                            continue
                    
                    # Create message
                    message = Message(
                        campaign_id=campaign_id,
                        user_id=user.id,
                        character_id=UUID(character_id) if character_id else None,
                        content=content,
                        is_ic=is_ic,
                        extra_data=extra_data
                    )
                    db.add(message)
                    await db.commit()
                    await db.refresh(message)
                    
                    # Broadcast message to all connected clients
                    await manager.broadcast(campaign_id, {
                        "type": "message",
                        "data": {
                            "id": str(message.id),
                            "user_id": str(message.user_id),
                            "username": user.username,
                            "character_id": str(message.character_id) if message.character_id else None,
                            "content": message.content,
                            "is_ic": message.is_ic,
                            "extra_data": message.extra_data,
                            "created_at": message.created_at.isoformat()
                        }
                    })
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, campaign_id)
            # Notify others that user left
            await manager.broadcast(campaign_id, {
                "type": "user_left",
                "data": {
                    "user_id": str(user.id),
                    "username": user.username
                }
            })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        await db.close()
