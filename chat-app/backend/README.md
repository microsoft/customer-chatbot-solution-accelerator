# Chat Backend API

AI-powered chat application backend built with FastAPI, designed to integrate with Azure AI services.

## Features

- **Multiple AI Agents**: Customer support, sales assistant, and technical support agents
- **Conversation Management**: Create, manage, and track chat conversations
- **Streaming Responses**: Real-time AI responses with Server-Sent Events
- **Azure AI Integration**: Connects to Azure OpenAI and AI Search for enhanced capabilities
- **Session-based Authentication**: Guest user sessions for development
- **Flexible Storage**: In-memory storage for development, Azure Cosmos DB for production

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Git

### Installation

1. **Clone and navigate to the backend directory**:
   ```bash
   cd chat-app/backend
   ```

2. **Set up environment**:
   ```bash
   # Copy environment template
   cp .env.template .env
   
   # Edit .env with your configuration (Azure keys are optional for development)
   ```

3. **Run with startup script**:
   ```bash
   # Linux/macOS
   chmod +x start.sh
   ./start.sh
   
   # Windows
   start.bat
   ```

**Or manually**:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m app.main
```

The API will be available at `http://localhost:8001`

## API Documentation

When running in development mode, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Main Endpoints

#### Conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations` - Get user conversations
- `GET /api/conversations/{id}` - Get specific conversation
- `PUT /api/conversations/{id}` - Update conversation
- `POST /api/conversations/{id}/end` - End conversation

#### Messages
- `GET /api/conversations/{id}/messages` - Get conversation messages
- `POST /api/conversations/{id}/messages` - Send message and get AI response
- `POST /api/conversations/{id}/messages/stream` - Send message with streaming response

#### Agents
- `GET /api/agents` - List available AI agents
- `GET /api/agents/{id}` - Get agent details
- `POST /api/agents/search` - Search knowledge base

## Configuration

### Development Mode (Default)
- Uses in-memory storage
- Mock AI responses
- Debug logging enabled
- No Azure services required

### Production Mode
Configure these environment variables in `.env`:

```bash
# Required for production
ENVIRONMENT=production
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_COSMOS_CONNECTION_STRING=your-cosmos-connection

# Optional enhancements
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_AI_SEARCH_KEY=your-search-key
```

## Development

### Project Structure
```
chat-app/backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── auth.py              # Authentication
│   ├── models.py            # Data models
│   ├── routers/
│   │   ├── conversations.py # Conversation endpoints
│   │   ├── messages.py      # Message endpoints
│   │   └── agents.py        # Agent endpoints
│   └── services/
│       ├── ai_service.py    # AI integration
│       └── data_service.py  # Data management
├── requirements.txt         # Python dependencies
├── .env.template           # Environment template
├── start.sh               # Linux/macOS startup
└── start.bat              # Windows startup
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Code Style

```bash
# Format code
black app/

# Check style
flake8 app/
```

## Architecture

### AI Service
- **Mock Mode**: Development responses without Azure dependencies
- **Azure Mode**: Azure OpenAI integration with streaming support
- **Agent System**: Multiple specialized AI agents with different capabilities

### Data Service
- **In-Memory**: Fast development storage
- **Cosmos DB**: Production-ready document storage
- **Session Management**: Guest user sessions with conversation tracking

### Authentication
- Session-based authentication for guest users
- Extensible for Azure AD integration
- Per-session conversation isolation

## Deployment

This backend is designed to work with Azure Container Apps and the broader solution's deployment pipeline. See the main project documentation for deployment instructions.

## Integration

### With E-commerce App
The chat backend is separate from the e-commerce application, allowing for independent scaling and deployment.

### With Frontend
Designed to work with the React chat frontend in `../frontend/`.

## Support

For issues and questions:
1. Check the logs for error details
2. Verify environment configuration
3. Ensure Azure services (if used) are properly configured
4. Review the API documentation at `/docs`