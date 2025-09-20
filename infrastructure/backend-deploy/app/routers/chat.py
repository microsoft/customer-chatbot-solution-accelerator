from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from ..models import ChatMessage, ChatMessageCreate, ChatSession, ChatSessionCreate, ChatSessionUpdate, APIResponse
from ..database import db_service
from ..ai_service import ai_service
from ..config import settings
from ..auth import get_current_user_optional

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.get("/sessions")
async def get_chat_sessions(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get all chat sessions for a user"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        if not user_id:
            # Return empty list for anonymous users
            return []
        
        sessions = await db_service.get_chat_sessions_by_user(user_id)
        return [
            {
                "id": session.id,
                "session_name": session.session_name,
                "message_count": session.message_count,
                "last_message_at": session.last_message_at,
                "is_active": session.is_active,
                "created_at": session.created_at
            }
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat sessions: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_chat_session(session_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get a specific chat session with messages"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        session = await db_service.get_chat_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {
            "id": session.id,
            "session_name": session.session_name,
            "message_count": session.message_count,
            "last_message_at": session.last_message_at,
            "is_active": session.is_active,
            "created_at": session.created_at,
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "sender": msg.message_type,
                    "timestamp": msg.created_at,
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat session: {str(e)}")

@router.post("/sessions", response_model=APIResponse)
async def create_chat_session(session: ChatSessionCreate):
    """Create a new chat session"""
    try:
        new_session = await db_service.create_chat_session(session)
        return APIResponse(
            message="Chat session created successfully",
            data={
                "id": new_session.id,
                "session_name": new_session.session_name,
                "user_id": new_session.user_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat session: {str(e)}")

@router.put("/sessions/{session_id}")
async def update_chat_session(session_id: str, session_update: ChatSessionUpdate, user_id: Optional[str] = None):
    """Update a chat session"""
    try:
        updated_session = await db_service.update_chat_session(session_id, session_update, user_id)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return {
            "id": updated_session.id,
            "session_name": updated_session.session_name,
            "is_active": updated_session.is_active,
            "message_count": updated_session.message_count,
            "updated_at": updated_session.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chat session: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str, user_id: Optional[str] = None):
    """Delete a chat session"""
    try:
        success = await db_service.delete_chat_session(session_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return APIResponse(message="Chat session deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat session: {str(e)}")

@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, message: ChatMessageCreate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Send a message to a chat session"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        # Add user message to session
        session = await db_service.add_message_to_session(session_id, message, user_id)
        
        # Get products for AI context
        products = await db_service.get_products()
        
        # Generate AI response
        ai_content = await ai_service.generate_chat_response(
            user_message=message.content,
            chat_history=session.messages,
            products=products
        )
        
        # Create AI response message
        ai_response = ChatMessageCreate(
            content=ai_content,
            message_type="assistant",
            metadata={"type": "ai_response", "original_message_id": session.messages[-1].id}
        )
        
        # Add AI response to session
        updated_session = await db_service.add_message_to_session(session_id, ai_response, user_id)
        
        # Return the latest message (AI response)
        latest_message = updated_session.messages[-1]
        return {
            "id": latest_message.id,
            "content": latest_message.content,
            "sender": latest_message.message_type,
            "timestamp": latest_message.created_at,
            "metadata": latest_message.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

# Legacy endpoints for backward compatibility
@router.get("/history")
async def get_chat_history(session_id: str = "default", current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get chat history for a session (legacy endpoint)"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        # Use consistent session ID logic
        if session_id == "default":
            if user_id:
                session_id = f"user_{user_id}_default"
            else:
                session_id = "anonymous_default"
        
        session = await db_service.get_chat_session(session_id, user_id)
        if not session:
            return []
        
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "sender": msg.message_type,
                "timestamp": msg.created_at
            }
            for msg in session.messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.post("/message")
async def send_message_legacy(message: ChatMessageCreate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Send a message to the chat (legacy endpoint)"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        # Use a consistent session ID based on user or default
        if message.session_id:
            session_id = message.session_id
        elif user_id:
            session_id = f"user_{user_id}_default"
        else:
            session_id = "anonymous_default"
        
        # Add user message to session
        session = await db_service.add_message_to_session(session_id, message, user_id)
        
        # Get products for AI context
        products = await db_service.get_products()
        
        # Generate AI response
        ai_content = await ai_service.generate_chat_response(
            user_message=message.content,
            chat_history=session.messages,
            products=products
        )
        
        # Create AI response message
        ai_response = ChatMessageCreate(
            content=ai_content,
            message_type="assistant",
            metadata={"type": "ai_response", "original_message_id": session.messages[-1].id}
        )
        
        # Add AI response to session
        updated_session = await db_service.add_message_to_session(session_id, ai_response, user_id)
        
        # Return the latest message (AI response)
        latest_message = updated_session.messages[-1]
        return {
            "id": latest_message.id,
            "content": latest_message.content,
            "sender": latest_message.message_type,
            "timestamp": latest_message.created_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.post("/sessions/new", response_model=APIResponse)
async def create_new_chat_session(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Create a new chat session"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        
        # Generate a new session ID
        new_session_id = str(uuid.uuid4())
        
        # Create new session
        session_data = ChatSessionCreate(
            user_id=user_id,
            session_name=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context={}
        )
        
        session = await db_service.create_chat_session(session_data)
        
        return APIResponse(
            message="New chat session created",
            data={
                "session_id": session.id,
                "session_name": session.session_name,
                "created_at": session.created_at.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating new chat session: {str(e)}")

@router.get("/ai/status", response_model=APIResponse)
async def get_ai_status():
    """Get AI service status"""
    try:
        return APIResponse(
            message="AI service status",
            data={
                "configured": ai_service.is_configured,
                "service": "Azure OpenAI" if ai_service.is_configured else "Fallback"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting AI status: {str(e)}")