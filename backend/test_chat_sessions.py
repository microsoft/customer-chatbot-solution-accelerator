#!/usr/bin/env python3
"""
Test script for the new chat session functionality.
This script tests the chat session CRUD operations and message handling.
"""

import asyncio
import logging
from datetime import datetime
from backend.app.database import db_service
from backend.app.models import ChatSessionCreate, ChatMessageCreate, ChatMessageType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_sessions():
    """Test chat session functionality"""
    try:
        logger.info("Starting chat session tests...")
        
        # Test 1: Create a new chat session
        logger.info("Test 1: Creating new chat session...")
        session_create = ChatSessionCreate(
            user_id="test_user_123",
            session_name="Test Chat Session",
            context={"test": True}
        )
        
        session = await db_service.create_chat_session(session_create)
        logger.info(f"Created session: {session.id}")
        
        # Test 2: Add messages to the session
        logger.info("Test 2: Adding messages to session...")
        
        # Add user message
        user_message = ChatMessageCreate(
            content="Hello, I need help with shopping!",
            message_type=ChatMessageType.USER,
            metadata={"test": True}
        )
        
        session = await db_service.add_message_to_session(session.id, user_message, "test_user_123")
        logger.info(f"Added user message. Session now has {session.message_count} messages")
        
        # Add assistant message
        assistant_message = ChatMessageCreate(
            content="Hello! I'd be happy to help you with your shopping needs. What are you looking for?",
            message_type=ChatMessageType.ASSISTANT,
            metadata={"type": "ai_response", "test": True}
        )
        
        session = await db_service.add_message_to_session(session.id, assistant_message, "test_user_123")
        logger.info(f"Added assistant message. Session now has {session.message_count} messages")
        
        # Test 3: Retrieve the session
        logger.info("Test 3: Retrieving chat session...")
        retrieved_session = await db_service.get_chat_session(session.id, "test_user_123")
        
        if retrieved_session:
            logger.info(f"Retrieved session: {retrieved_session.session_name}")
            logger.info(f"Session has {retrieved_session.message_count} messages")
            for i, msg in enumerate(retrieved_session.messages):
                logger.info(f"  Message {i+1}: {msg.message_type} - {msg.content[:50]}...")
        else:
            logger.error("Failed to retrieve session!")
            return False
        
        # Test 4: Get all sessions for user
        logger.info("Test 4: Getting all sessions for user...")
        user_sessions = await db_service.get_chat_sessions_by_user("test_user_123")
        logger.info(f"Found {len(user_sessions)} sessions for user")
        
        # Test 5: Update session
        logger.info("Test 5: Updating session...")
        from backend.app.models import ChatSessionUpdate
        session_update = ChatSessionUpdate(
            session_name="Updated Test Chat Session",
            context={"test": True, "updated": True}
        )
        
        updated_session = await db_service.update_chat_session(session.id, session_update, "test_user_123")
        if updated_session:
            logger.info(f"Updated session name to: {updated_session.session_name}")
        else:
            logger.error("Failed to update session!")
            return False
        
        # Test 6: Add more messages to test message ordering
        logger.info("Test 6: Adding more messages...")
        
        for i in range(3):
            message = ChatMessageCreate(
                content=f"Test message {i+1}",
                message_type=ChatMessageType.USER if i % 2 == 0 else ChatMessageType.ASSISTANT,
                metadata={"test": True, "message_number": i+1}
            )
            
            session = await db_service.add_message_to_session(session.id, message, "test_user_123")
            logger.info(f"Added message {i+1}. Total messages: {session.message_count}")
        
        # Test 7: Verify final session state
        logger.info("Test 7: Verifying final session state...")
        final_session = await db_service.get_chat_session(session.id, "test_user_123")
        
        if final_session:
            logger.info(f"Final session state:")
            logger.info(f"  - ID: {final_session.id}")
            logger.info(f"  - Name: {final_session.session_name}")
            logger.info(f"  - User ID: {final_session.user_id}")
            logger.info(f"  - Message Count: {final_session.message_count}")
            logger.info(f"  - Last Message At: {final_session.last_message_at}")
            logger.info(f"  - Is Active: {final_session.is_active}")
            logger.info(f"  - Context: {final_session.context}")
            
            logger.info("  Messages:")
            for i, msg in enumerate(final_session.messages):
                logger.info(f"    {i+1}. [{msg.message_type}] {msg.content[:50]}... (created: {msg.created_at})")
        
        # Test 8: Clean up - Delete session
        logger.info("Test 8: Cleaning up - Deleting session...")
        delete_success = await db_service.delete_chat_session(session.id, "test_user_123")
        
        if delete_success:
            logger.info("Session deleted successfully")
        else:
            logger.error("Failed to delete session!")
            return False
        
        # Verify deletion
        deleted_session = await db_service.get_chat_session(session.id, "test_user_123")
        if deleted_session is None:
            logger.info("Session deletion verified - session not found")
        else:
            logger.error("Session still exists after deletion!")
            return False
        
        logger.info("All tests passed successfully! ✅")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("Chat Session Test Suite")
    print("=" * 50)
    print("This script tests the new chat session functionality.")
    print()
    
    try:
        success = await test_chat_sessions()
        if success:
            print("\n🎉 All tests passed! The chat session functionality is working correctly.")
        else:
            print("\n❌ Some tests failed. Please check the logs for details.")
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
