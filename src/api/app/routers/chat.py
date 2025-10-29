from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from models import ChatMessage, ChatMessageCreate, ChatSession, ChatSessionCreate, ChatSessionUpdate, APIResponse, ChatMessageType
from cosmos_service import get_cosmos_service
from simple_foundry_orchestrator import get_simple_foundry_orchestrator
from config import settings, has_semantic_kernel_config, has_foundry_config
from auth import get_current_user_optional

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential, AzureCliCredential
 
from agent_framework import ChatAgent,HostedFileSearchTool
from agent_framework_azure_ai import AzureAIAgentClient
 

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

def format_timestamp(dt: datetime) -> str:
    """Helper function to format timestamps consistently"""
    if dt.tzinfo is None:
        return dt.isoformat() + 'Z'
    else:
        return dt.isoformat()

async def generate_ai_response(message_content: str, chat_history: List[ChatMessage], session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
    """Generate AI response using Foundry agents only"""
    logger.info(f"Generating AI response. Foundry config: {has_foundry_config()}, Use Foundry: {settings.use_foundry_agents}")
    
    # Only use Foundry agents - no fallbacks
    if has_foundry_config() and settings.use_foundry_agents:
        try:
            simple_foundry_orchestrator = await get_simple_foundry_orchestrator()
            logger.info(f"Simple Foundry orchestrator configured: {simple_foundry_orchestrator.is_configured}")
            
            if simple_foundry_orchestrator.is_configured:
                logger.info(f"Processing message with Foundry agents: {message_content[:100]}...")
                
                enhanced_message = message_content
                if user_id:
                    enhanced_message = f"[User ID: {user_id}] {message_content}"
                
                ai_response_data = await simple_foundry_orchestrator.respond(
                    user_text=enhanced_message, 
                    conversation_id=session_id
                )
                
                if "error" in ai_response_data:
                    logger.error(f"Foundry orchestrator returned error: {ai_response_data['error']}")
                    return f"❌ Foundry Agent Error: {ai_response_data['error']}"
                
                response_text = ai_response_data.get("text", "")
                logger.info(f"Foundry orchestrator response length: {len(response_text)} chars")
                return response_text
            else:
                logger.error("Simple Foundry orchestrator is not configured properly")
                return "❌ Foundry Agent Error: Orchestrator not configured"
                
        except Exception as e:
            logger.error(f"Error with Simple Foundry orchestrator: {e}", exc_info=True)
            return f"❌ Foundry Agent Error: {str(e)}"
    else:
        logger.error(f"Foundry not configured. Foundry config: {has_foundry_config()}, Use Foundry: {settings.use_foundry_agents}")
        return "❌ Foundry Agent Error: Foundry agents not configured. Please check your environment variables."

@router.get("/sessions")
async def get_chat_sessions(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get all chat sessions for a user"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        if not user_id:
            # Return empty list for anonymous users
            return []
        
        sessions = await get_cosmos_service().get_chat_sessions_by_user(user_id)
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
        session = await get_cosmos_service().get_chat_session(session_id, user_id)
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
                    "timestamp": format_timestamp(msg.created_at),
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
        new_session = await get_cosmos_service().create_chat_session(session)
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
        updated_session = await get_cosmos_service().update_chat_session(session_id, session_update, user_id)
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
        success = await get_cosmos_service().delete_chat_session(session_id, user_id)
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
        session = await get_cosmos_service().add_message_to_session(session_id, message, user_id)
        
        # Generate AI response with thread caching and user context
        ai_content = await generate_ai_response(message.content, session.messages, session_id=session_id, user_id=user_id)
        
        # Create AI response message
        ai_response = ChatMessageCreate(
            content=ai_content,
            message_type=ChatMessageType.ASSISTANT,
            metadata={"type": "ai_response", "original_message_id": session.messages[-1].id}
        )
        
        # Add AI response to session
        updated_session = await get_cosmos_service().add_message_to_session(session_id, ai_response, user_id)
        
        # Return the latest message (AI response)
        latest_message = updated_session.messages[-1]
        return {
            "id": latest_message.id,
            "content": latest_message.content,
            "sender": latest_message.message_type,
            "timestamp": format_timestamp(latest_message.created_at),
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
        
        session = await get_cosmos_service().get_chat_session(session_id, user_id)
        if not session:
            return []
        
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "sender": msg.message_type,
                "timestamp": format_timestamp(msg.created_at)
            }
            for msg in session.messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@router.post("/message")
async def send_message_legacy(message: ChatMessageCreate, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    #"""Send a message to the chat (legacy endpoint)"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        
        # Use a consistent session ID based on user or default
        if hasattr(message, 'session_id') and message.session_id:
            session_id = message.session_id
        elif user_id:
            session_id = f"user_{user_id}_default"
        else:
            session_id = "anonymous_default"
        
        # Add user message to session
        session = await get_cosmos_service().add_message_to_session(session_id, message, user_id)
        
        # Generate AI response with thread caching and user context
        #ai_content = await generate_ai_response(message.content, session.messages, session_id=session_id, user_id=user_id)
        
        # Create AI response message
        # ai_response = ChatMessageCreate(
        #     content=ai_content,
        #     message_type=ChatMessageType.ASSISTANT,
        #     metadata={"type": "ai_response", "original_message_id": session.messages[-1].id}
        # )
        
        # Add AI response to session
        #updated_session = await get_cosmos_service().add_message_to_session(session_id, ai_response, user_id)
        
        # Return the latest message (AI response)
        #latest_message = updated_session.messages[-1]
        """Configure and test the orchestrator agent with SQL and chart agent tools."""
        ai_project_endpoint = settings.azure_foundry_endpoint #or "https://testmodle.services.ai.azure.com/api/projects/testModle-project"
        chat_agent_id = settings.foundry_chat_agent_id #or "asst_AknGrbRy1Z7TOdcQvqCluPoL"
        product_agent_id = settings.foundry_custom_product_agent_id # or "asst_lodFVY7Vt9BqKnISV6VeWt7g"
        policy_agent_id = settings.foundry_policy_agent_id #or "asst_hgDgBcRZBCvHyOWpRuph6Ts1"
        # Initialize result variable
        result = None
        
        async with (
            AzureCliCredential() as credential,
            AIProjectClient(
                endpoint=ai_project_endpoint if ai_project_endpoint else "default_endpoint",
                credential=credential,  # type: ignore
            ) as client,
        ):   
            # azure_ai_search_policies_tool = HostedFileSearchTool(
            #     additional_properties={
            #         "index_name": "policies_index",  # Name of your search index
            #         "query_type": "simple",  # Use simple search
            #         "top_k": 10,  # Get more comprehensive results
            #     },
            # )

            # azure_ai_search_products_tool = HostedFileSearchTool(
            #     additional_properties={
            #         "index_name": "products_index",  # Name of your search index
            #         "query_type": "simple",  # Use simple search  
            #         "top_k": 10,  # Get more comprehensive results
            #     },
            # )

            try:
                async with ChatAgent(
                    chat_client=AzureAIAgentClient(project_client=client, model_deployment_name="gpt-4o-mini", agent_id=chat_agent_id),
                    model='gpt-4o-mini',
                    tools=[ChatAgent(chat_client=AzureAIAgentClient(project_client=client, agent_id=policy_agent_id),  model='gpt-4o-mini').as_tool(name="policy_agent"),
                        ChatAgent(chat_client=AzureAIAgentClient(project_client=client, agent_id=product_agent_id), model='gpt-4o-mini').as_tool(name="product_agent")],
                        #add agent here for tools 
                    tool_choice="auto"
                ) as chat_agent:
                        thread = chat_agent.get_new_thread()
                question = message.content
                result = await chat_agent.run(question, thread=thread, store=True)

            except Exception as e:        
                print(f"Error occurred: {e}")
                result = None
        
        # Handle the result properly
        if result and hasattr(result, 'text'):
            response_content = result.text
        elif result:
            response_content = str(result)
        else:
            response_content = "Sorry, I encountered an error processing your request."
        
        return {
            "id": "12345",
            "content": response_content,
            "sender": "assistant",
            "timestamp": format_timestamp(datetime.utcnow())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.post("/sessions/new", response_model=APIResponse)
async def create_new_chat_session(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Create a new chat session"""
    try:
        user_id = current_user.get("user_id") if current_user else None
        
        # Create new session
        session_data = ChatSessionCreate(
            user_id=user_id,
            session_name=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context={}
        )
        
        session = await get_cosmos_service().create_chat_session(session_data)
        
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
    """Get AI service status - Foundry agents only"""
    try:
        # Check Foundry status
        foundry_configured = has_foundry_config()
        foundry_enabled = foundry_configured and settings.use_foundry_agents
        
        # Determine active service
        active_service = "Unknown"
        agent_count = 0
        agent_names = []
        
        if foundry_enabled:
            try:
                simple_foundry_orchestrator = await get_simple_foundry_orchestrator()
                if simple_foundry_orchestrator.is_configured:
                    active_service = "Azure AI Foundry Agents (Simple)"
                    # Get agent details
                    agent_count = len(simple_foundry_orchestrator.agents)
                    agent_names = list(simple_foundry_orchestrator.agents.keys())
                else:
                    active_service = "Foundry (not configured)"
            except Exception as e:
                active_service = f"Foundry (error: {str(e)})"
        else:
            active_service = "Foundry (not enabled)"
        
        return APIResponse(
            message="AI service status - Foundry agents only",
            data={
                "foundry_configured": foundry_configured,
                "foundry_enabled": foundry_enabled,
                "use_foundry_agents": settings.use_foundry_agents,
                "active_service": active_service,
                "agent_count": agent_count,
                "agent_names": agent_names,
                "foundry_endpoint": settings.azure_foundry_endpoint,
                "orchestrator_agent_id": settings.foundry_orchestrator_agent_id,
                "product_agent_id": settings.foundry_product_agent_id,
                "order_agent_id": settings.foundry_order_agent_id,
                "knowledge_agent_id": settings.foundry_knowledge_agent_id
            }
        )
    except Exception as e:
        logger.error(f"Error getting AI status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting AI status: {str(e)}")