# Chat Session Migration Guide

## Overview

This document describes the migration from individual chat message storage to a proper chat session structure in Cosmos DB. The new structure stores chat sessions as single documents containing arrays of messages, which is more efficient and better suited for chat history management.

## What Changed

### Before (Old Structure)
- Individual `ChatMessage` entities stored separately
- Each message had a `session_id` field
- No proper session grouping
- Difficult to manage chat history

### After (New Structure)
- `ChatSession` entities containing arrays of `ChatMessage` objects
- Proper session management with user correlation
- Efficient storage and retrieval
- Better chat history management

## New Data Models

### ChatSession
```python
class ChatSession(BaseEntity):
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    is_active: bool = True
    context: Dict[str, Any] = {}
    messages: List[ChatMessage] = []
    message_count: int = 0
    last_message_at: Optional[datetime] = None
```

### ChatMessage (Updated)
```python
class ChatMessage(BaseModel):
    id: str
    content: str
    message_type: ChatMessageType
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
```

## New API Endpoints

### Session Management
- `GET /api/chat/sessions` - Get all chat sessions for a user
- `GET /api/chat/sessions/{session_id}` - Get specific chat session with messages
- `POST /api/chat/sessions` - Create new chat session
- `PUT /api/chat/sessions/{session_id}` - Update chat session
- `DELETE /api/chat/sessions/{session_id}` - Delete chat session

### Message Management
- `POST /api/chat/sessions/{session_id}/messages` - Send message to session
- `GET /api/chat/history` - Legacy endpoint for backward compatibility
- `POST /api/chat/message` - Legacy endpoint for backward compatibility

## Migration Process

### 1. Run the Migration Script

```bash
cd backend
python migrate_chat_sessions.py
```

The script will:
- Group existing individual messages by session_id and user_id
- Create new ChatSession documents with message arrays
- Optionally delete old individual message documents

### 2. Update Your Frontend

Update your frontend to use the new API endpoints:

#### Get Chat Sessions
```javascript
// Get all sessions for a user
const sessions = await fetch('/api/chat/sessions?user_id=USER_ID');
```

#### Get Session with Messages
```javascript
// Get specific session with all messages
const session = await fetch('/api/chat/sessions/SESSION_ID?user_id=USER_ID');
```

#### Send Message
```javascript
// Send message to a session
const response = await fetch('/api/chat/sessions/SESSION_ID/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: 'Hello!',
    message_type: 'user'
  })
});
```

## Benefits of New Structure

### 1. Performance
- Single document read for entire chat history
- Reduced Cosmos DB RU consumption
- Faster chat loading

### 2. Data Consistency
- Atomic updates to entire chat session
- No orphaned messages
- Better data integrity

### 3. Scalability
- Better partition key strategy (user_id)
- Efficient querying by user
- Reduced cross-partition queries

### 4. Features
- Easy session management
- Chat history pagination
- Session metadata storage
- Better user experience

## Example Data Structure

### New ChatSession Document
```json
{
  "id": "session_12345_20240101_120000",
  "user_id": "user_123",
  "session_name": "Shopping Chat",
  "is_active": true,
  "context": {},
  "messages": [
    {
      "id": "msg_1",
      "content": "Hello!",
      "message_type": "user",
      "user_id": "user_123",
      "metadata": {},
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "msg_2",
      "content": "Hi! How can I help you?",
      "message_type": "assistant",
      "user_id": "user_123",
      "metadata": {"type": "ai_response"},
      "created_at": "2024-01-01T12:00:01Z"
    }
  ],
  "message_count": 2,
  "last_message_at": "2024-01-01T12:00:01Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:01Z"
}
```

## Backward Compatibility

The old API endpoints (`/api/chat/history` and `/api/chat/message`) are still available for backward compatibility. However, they now work with the new session structure internally.

## Troubleshooting

### Common Issues

1. **Migration Script Fails**
   - Check Cosmos DB connection string
   - Verify container permissions
   - Ensure database exists

2. **Frontend Not Loading Chats**
   - Update API calls to use new endpoints
   - Check user_id parameter
   - Verify session_id format

3. **Performance Issues**
   - Monitor Cosmos DB RU consumption
   - Check partition key distribution
   - Consider pagination for large chat histories

### Support

If you encounter issues during migration:
1. Check the logs for detailed error messages
2. Verify your Cosmos DB configuration
3. Test with a small subset of data first
4. Contact support if needed

## Next Steps

After migration:
1. Update your frontend to use new endpoints
2. Test chat functionality thoroughly
3. Monitor performance and RU consumption
4. Consider implementing additional features like:
   - Chat session search
   - Message pagination
   - Session archiving
   - Export functionality
