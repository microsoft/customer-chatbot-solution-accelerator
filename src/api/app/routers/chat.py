import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

# Handle both local debugging and Docker deployment with conditional imports
try:
    # Try relative imports first (for Docker)
    from ..auth import get_current_user_optional
    from ..config import settings
    from ..cosmos_service import get_cosmos_service
    from ..models import (APIResponse, ChatMessageCreate, ChatMessageType,
                          ChatSessionCreate, ChatSessionUpdate)
except ImportError:
    # Fall back to absolute imports (for local debugging)
    import os
    import sys

    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    from app.models import (
        ChatMessageCreate,
        ChatSessionCreate,
        ChatSessionUpdate,
        APIResponse,
        ChatMessageType,
    )
    from app.cosmos_service import get_cosmos_service

    from app.config import settings
    from app.auth import get_current_user_optional

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.ai.projects.aio import AIProjectClient

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def format_timestamp(dt: datetime) -> str:
    """Helper function to format timestamps consistently"""
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    else:
        return dt.isoformat()


@router.get("/sessions")
async def get_chat_sessions(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
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
                "created_at": session.created_at,
            }
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching chat sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
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
                    "metadata": msg.metadata,
                }
                for msg in session.messages
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching chat session: {str(e)}"
        )


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
                "user_id": new_session.user_id,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating chat session: {str(e)}"
        )


@router.put("/sessions/{session_id}")
async def update_chat_session(
    session_id: str, session_update: ChatSessionUpdate, user_id: Optional[str] = None
):
    """Update a chat session"""
    try:
        updated_session = await get_cosmos_service().update_chat_session(
            session_id, session_update, user_id
        )
        if not updated_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        return {
            "id": updated_session.id,
            "session_name": updated_session.session_name,
            "is_active": updated_session.is_active,
            "message_count": updated_session.message_count,
            "updated_at": updated_session.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating chat session: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Error deleting chat session: {str(e)}"
        )


# @router.post("/sessions/{session_id}/messages")
# async def send_message(
#     session_id: str,
#     message: ChatMessageCreate,
#     current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
# ):
#     """Send a message to a chat session"""
#     try:
#         user_id = current_user.get("user_id") if current_user else None

#         # Add user message to session
#         session = await get_cosmos_service().add_message_to_session(
#             session_id, message, user_id
#         )

#         # Generate AI response with thread caching and user context
#         ai_content = await generate_ai_response(
#             message.content, session.messages, session_id=session_id, user_id=user_id
#         )

#         # Create AI response message
#         ai_response = ChatMessageCreate(
#             content=ai_content,
#             message_type=ChatMessageType.ASSISTANT,
#             metadata={
#                 "type": "ai_response",
#                 "original_message_id": session.messages[-1].id,
#             },
#         )

#         # Add AI response to session
#         updated_session = await get_cosmos_service().add_message_to_session(
#             session_id, ai_response, user_id
#         )

#         # Return the latest message (AI response)
#         latest_message = updated_session.messages[-1]
#         return {
#             "id": latest_message.id,
#             "content": latest_message.content,
#             "sender": latest_message.message_type,
#             "timestamp": format_timestamp(latest_message.created_at),
#             "metadata": latest_message.metadata,
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


# Legacy endpoints for backward compatibility
@router.get("/history")
async def get_chat_history(
    session_id: str = "default",
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
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
                "timestamp": format_timestamp(msg.created_at),
            }
            for msg in session.messages
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching chat history: {str(e)}"
        )


@router.post("/message")
async def send_message_legacy(
    message: ChatMessageCreate,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
):
    # """Send a message to the chat (legacy endpoint)"""
    try:
        user_id = current_user.get("user_id") if current_user else None

        # Use a consistent session ID based on user or default
        if hasattr(message, "session_id") and message.session_id:
            session_id = message.session_id
        elif user_id:
            session_id = f"user_{user_id}_default"
        else:
            session_id = "anonymous_default"

        # Add user message to session
        await get_cosmos_service().add_message_to_session(session_id, message, user_id)

        ai_project_endpoint = settings.azure_foundry_endpoint
        product_agent_name = settings.foundry_custom_product_agent
        policy_agent_name = settings.foundry_policy_agent
        # Initialize result variable
        result = None

        # Importing here to avoid circular imports
        from ..utils.azure_credential_utils import get_azure_credential_async

        client_id = str(settings.azure_client_id) if settings.azure_client_id else None
        credential = await get_azure_credential_async(client_id=client_id)

        async with (
            credential,
            AIProjectClient(
                endpoint=(
                    ai_project_endpoint if ai_project_endpoint else "default_endpoint"
                ),
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

            # Retry logic for rate limit errors
            max_retries = 3
            default_retry_delay = 5  # seconds
            result = None

            for attempt in range(max_retries):
                try:
                    async with ChatAgent(
                        chat_client=AzureAIAgentClient(
                            project_client=client,
                            model_deployment_name=model_deployment_name,
                            project_endpoint=ai_project_endpoint,
                            agent_id=chat_agent_id,
                        ),
                        model="gpt-4o-mini",
                        tools=[
                            ChatAgent(
                                chat_client=AzureAIAgentClient(
                                    project_client=client,
                                    model_deployment_name=model_deployment_name,
                                    project_endpoint=ai_project_endpoint,
                                    agent_id=policy_agent_id,
                                ),
                                model="gpt-4o-mini",
                            ).as_tool(name="policy_agent"),
                            ChatAgent(
                                chat_client=AzureAIAgentClient(
                                    project_client=client,
                                    model_deployment_name=model_deployment_name,
                                    project_endpoint=ai_project_endpoint,
                                    agent_id=product_agent_id,
                                ),
                                model="gpt-4o-mini",
                            ).as_tool(name="product_agent"),
                        ],
                        # add agent here for tools
                        tool_choice="auto",
                    ) as chat_agent:
                        thread = chat_agent.get_new_thread()
                        question = message.content
                        result = await chat_agent.run(question, thread=thread, store=True)
                        break  # Success, exit retry loop

                except Exception as e:
                    error_msg = str(e)
                    is_rate_limit = any(kw in error_msg.lower() for kw in ["rate limit", "exceeded", "retry after"])

                    if is_rate_limit:
                        if attempt < max_retries - 1:
                            # Extract retry delay from error message (e.g., "retry after 4 seconds")
                            retry_match = re.search(r'retry after (\d+)', error_msg.lower())
                            retry_delay = int(retry_match.group(1)) + 1 if retry_match else default_retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limit hit, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            # Final attempt - raise 429 directly
                            logger.error(f"Rate limit retries exhausted: {error_msg}")
                            raise HTTPException(status_code=429, detail="Service temporarily unavailable due to high demand. Please try again in a few seconds.")

                    # Non-rate-limit error: raise 500 immediately
                    logger.error(f"Error running AI agent: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail=f"AI agent error: {str(e)}")

        # Handle the result properly
        if result and hasattr(result, "text"):
            response_content = result.text
        elif result:
            response_content = str(result)
        else:
            raise HTTPException(status_code=500, detail="AI agent returned no response")

        # Save AI response to Cosmos DB
        ai_response = ChatMessageCreate(
            content=response_content,
            message_type=ChatMessageType.ASSISTANT,
            metadata={"type": "ai_response"},
        )
        await get_cosmos_service().add_message_to_session(
            session_id, ai_response, user_id
        )

        return {
            "id": session_id,
            "content": response_content,
            "sender": "assistant",
            "timestamp": format_timestamp(datetime.utcnow()),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.post("/sessions/new", response_model=APIResponse)
async def create_new_chat_session(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Create a new chat session"""
    try:
        user_id = current_user.get("user_id") if current_user else None

        # Create new session
        session_data = ChatSessionCreate(
            user_id=user_id,
            session_name=f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context={},
        )

        session = await get_cosmos_service().create_chat_session(session_data)

        return APIResponse(
            message="New chat session created",
            data={
                "session_id": session.id,
                "session_name": session.session_name,
                "created_at": session.created_at.isoformat(),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating new chat session: {str(e)}"
        )
