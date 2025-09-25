# Semantic Kernel Integration

This document describes the semantic kernel integration that has been added to the e-commerce chat API.

## Overview

The semantic kernel integration provides advanced AI capabilities through specialized agents and handoff orchestration. It replaces the simple AI service with a more sophisticated system that can route different types of queries to specialized agents.

## Architecture

### Components

1. **Semantic Kernel Service** (`semantic_kernel_service.py`)
   - Manages the semantic kernel instance
   - Provides simple routing when handoff orchestration is disabled
   - Handles kernel configuration and plugin registration

2. **Handoff Orchestrator** (`handoff_orchestrator.py`)
   - Manages agent handoff orchestration
   - Routes queries to specialized agents
   - Handles complex multi-agent conversations

3. **Plugins** (`plugins/`)
   - **Product Plugin**: Product search and SKU lookup
   - **Reference Plugin**: Policy and support document lookup
   - **Orders Plugin**: Order management and status

### Agents

- **TriageAgent**: Routes customer requests to appropriate specialists
- **ProductLookupAgent**: Handles product-related queries
- **ReferenceLookupAgent**: Handles policy and support queries
- **OrderStatusAgent**: Handles order status and tracking
- **RefundAgent**: Handles refund requests
- **OrderReturnAgent**: Handles return requests

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Semantic Kernel Configuration
USE_SEMANTIC_KERNEL=true
HANDOFF_ORCHESTRATION_ENABLED=true
USE_SIMPLE_ROUTER=false

# Azure Search (for reference plugin)
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX=reference-docs

# Existing Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

### Settings

The following settings control the semantic kernel behavior:

- `use_semantic_kernel`: Enable/disable semantic kernel (default: true)
- `handoff_orchestration_enabled`: Enable handoff orchestration (default: true)
- `use_simple_router`: Use simple routing instead of handoff orchestration (default: false)
- `semantic_kernel_plugins`: List of enabled plugins (default: ["product", "reference", "orders"])

## Usage

### API Endpoints

The existing chat endpoints automatically use semantic kernel when configured:

- `POST /api/chat/sessions/{session_id}/messages` - Send message with semantic kernel
- `POST /api/chat/message` - Legacy endpoint with semantic kernel
- `GET /api/chat/ai/status` - Check AI service status including semantic kernel

### Response Format

The semantic kernel integration maintains backward compatibility with existing response formats. Additional information is available in the response:

```json
{
  "id": "message-id",
  "content": "AI response text",
  "sender": "assistant",
  "timestamp": "2024-01-01T00:00:00Z",
  "metadata": {
    "type": "ai_response",
    "original_message_id": "original-message-id"
  }
}
```

## Fallback Behavior

The system includes robust fallback mechanisms:

1. **Semantic Kernel with Handoff Orchestration** (preferred)
2. **Semantic Kernel with Simple Routing** (fallback)
3. **Original AI Service** (final fallback)

## Health Check

The `/health` endpoint now includes semantic kernel status:

```json
{
  "status": "healthy",
  "database": "connected",
  "openai": "configured",
  "auth": "configured",
  "semantic_kernel": "configured",
  "handoff_orchestration": "enabled"
}
```

## Troubleshooting

### Common Issues

1. **Semantic Kernel Not Configured**
   - Check Azure OpenAI configuration
   - Verify `USE_SEMANTIC_KERNEL=true`

2. **Handoff Orchestration Disabled**
   - Check `HANDOFF_ORCHESTRATION_ENABLED=true`
   - Verify all required environment variables

3. **Plugin Errors**
   - Check Cosmos DB connection for product/orders plugins
   - Check Azure Search configuration for reference plugin

### Debugging

Enable debug logging to see agent interactions:

```python
import logging
logging.getLogger("backend.app.semantic_kernel_service").setLevel(logging.DEBUG)
logging.getLogger("backend.app.handoff_orchestrator").setLevel(logging.DEBUG)
```

## Performance Considerations

- Handoff orchestration adds overhead but provides better routing
- Simple router is faster but less sophisticated
- Plugin calls to external services (Cosmos DB, Azure Search) may add latency
- Consider caching for frequently accessed data

## Future Enhancements

- Add more specialized agents (shipping, warranty, etc.)
- Implement conversation memory across agents
- Add metrics and monitoring for agent performance
- Support for custom plugins

