#!/usr/bin/env python3
"""
Migration script to convert individual chat messages to chat sessions with message arrays.
This script migrates data from the old format (individual ChatMessage entities) to the new format (ChatSession entities with message arrays).
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatSessionMigrator:
    def __init__(self, cosmos_endpoint: str, cosmos_key: str, database_name: str, container_name: str):
        self.client = CosmosClient(cosmos_endpoint, cosmos_key)
        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)
    
    async def migrate_chat_data(self):
        """Migrate individual chat messages to chat sessions"""
        try:
            logger.info("Starting chat data migration...")
            
            # Get all existing chat messages
            query = "SELECT * FROM c WHERE c.session_id != null"
            messages = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Found {len(messages)} individual chat messages to migrate")
            
            # Group messages by session_id and user_id
            sessions = {}
            for message in messages:
                session_key = f"{message.get('session_id', 'default')}_{message.get('user_id', 'anonymous')}"
                
                if session_key not in sessions:
                    sessions[session_key] = {
                        'session_id': message.get('session_id', 'default'),
                        'user_id': message.get('user_id'),
                        'messages': []
                    }
                
                # Convert message to new format
                new_message = {
                    'id': message.get('id'),
                    'content': message.get('content'),
                    'message_type': message.get('message_type'),
                    'user_id': message.get('user_id'),
                    'metadata': message.get('metadata', {}),
                    'created_at': message.get('created_at')
                }
                
                sessions[session_key]['messages'].append(new_message)
            
            logger.info(f"Grouped messages into {len(sessions)} sessions")
            
            # Create new chat session documents
            migrated_count = 0
            for session_key, session_data in sessions.items():
                try:
                    # Sort messages by created_at
                    session_data['messages'].sort(key=lambda x: x.get('created_at', ''))
                    
                    # Create new chat session document
                    chat_session = {
                        'id': f"session_{session_data['session_id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        'user_id': session_data['user_id'],
                        'session_name': f"Migrated Chat {session_data['session_id']}",
                        'is_active': True,
                        'context': {},
                        'messages': session_data['messages'],
                        'message_count': len(session_data['messages']),
                        'last_message_at': session_data['messages'][-1].get('created_at') if session_data['messages'] else None,
                        'created_at': session_data['messages'][0].get('created_at') if session_data['messages'] else datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    # Insert new chat session
                    self.container.create_item(chat_session)
                    migrated_count += 1
                    
                    logger.info(f"Created chat session {chat_session['id']} with {len(session_data['messages'])} messages")
                    
                except Exception as e:
                    logger.error(f"Error creating session for {session_key}: {str(e)}")
                    continue
            
            logger.info(f"Migration completed. Created {migrated_count} chat sessions.")
            
            # Optional: Delete old individual message documents
            delete_old = input("Do you want to delete the old individual message documents? (y/N): ").lower().strip()
            if delete_old == 'y':
                await self.delete_old_messages(messages)
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            raise
    
    async def delete_old_messages(self, messages: List[Dict[str, Any]]):
        """Delete old individual message documents"""
        try:
            deleted_count = 0
            for message in messages:
                try:
                    self.container.delete_item(
                        item=message['id'],
                        partition_key=message.get('session_id', 'default')
                    )
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting message {message['id']}: {str(e)}")
                    continue
            
            logger.info(f"Deleted {deleted_count} old message documents")
            
        except Exception as e:
            logger.error(f"Error deleting old messages: {str(e)}")
            raise

async def main():
    """Main migration function"""
    # Configuration - update these values
    COSMOS_ENDPOINT = "your-cosmos-endpoint"
    COSMOS_KEY = "your-cosmos-key"
    DATABASE_NAME = "your-database-name"
    CONTAINER_NAME = "chat_sessions"  # The container name for chat sessions
    
    print("Chat Session Migration Tool")
    print("=" * 50)
    print("This tool will migrate individual chat messages to chat sessions with message arrays.")
    print("Make sure to backup your data before running this migration!")
    print()
    
    confirm = input("Do you want to proceed with the migration? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Migration cancelled.")
        return
    
    # Update configuration
    cosmos_endpoint = input(f"Cosmos DB Endpoint [{COSMOS_ENDPOINT}]: ").strip() or COSMOS_ENDPOINT
    cosmos_key = input(f"Cosmos DB Key [{COSMOS_KEY}]: ").strip() or COSMOS_KEY
    database_name = input(f"Database Name [{DATABASE_NAME}]: ").strip() or DATABASE_NAME
    container_name = input(f"Container Name [{CONTAINER_NAME}]: ").strip() or CONTAINER_NAME
    
    try:
        migrator = ChatSessionMigrator(cosmos_endpoint, cosmos_key, database_name, container_name)
        await migrator.migrate_chat_data()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return

if __name__ == "__main__":
    asyncio.run(main())
