# E-commerce Chat Backend

FastAPI backend for the e-commerce chat application with AI-powered customer support.

## Features

- **Product Management**: CRUD operations for products with filtering and search
- **AI Chat**: Azure OpenAI integration with fallback responses
- **Shopping Cart**: Full cart management functionality
- **Database Support**: Cosmos DB integration with mock data fallback
- **Authentication**: Microsoft Entra ID integration (ready for implementation)
- **API Documentation**: Interactive Swagger/OpenAPI docs
- **Testing**: Comprehensive unit tests
- **Error Handling**: Robust error handling and logging

## Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── database.py          # Database abstraction layer
│   ├── cosmos_service.py    # Cosmos DB implementation
│   ├── ai_service.py        # Azure OpenAI integration
│   └── routers/
│       ├── products.py      # Product endpoints
│       ├── chat.py          # Chat endpoints
│       └── cart.py          # Cart endpoints
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the environment template:
```bash
cp env.example .env
```

Update `.env` with your Azure credentials (optional for local development):
```env
# Azure Cosmos DB (optional - will use mock data if not provided)
COSMOS_DB_ENDPOINT=your_cosmos_db_endpoint
COSMOS_DB_KEY=your_cosmos_db_key
COSMOS_DB_DATABASE_NAME=ecommerce_db

# Azure OpenAI (optional - will use fallback responses if not provided)
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Microsoft Entra ID (optional - for future authentication)
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
```

### 3. Running Locally

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## API Endpoints

### Products
- `GET /api/products` - Get all products with filtering
- `GET /api/products/{id}` - Get product by ID
- `POST /api/products` - Create product (Admin)
- `PUT /api/products/{id}` - Update product (Admin)
- `DELETE /api/products/{id}` - Delete product (Admin)
- `GET /api/products/categories/list` - Get all categories

### Chat
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/message` - Send message
- `POST /api/chat/session` - Create chat session
- `GET /api/chat/sessions` - Get chat sessions
- `GET /api/chat/ai/status` - Get AI service status

### Cart
- `GET /api/cart` - Get user's cart
- `POST /api/cart/add` - Add item to cart
- `PUT /api/cart/update` - Update cart item
- `DELETE /api/cart/{id}` - Remove item from cart
- `DELETE /api/cart` - Clear cart

### Health
- `GET /` - Root endpoint with API info
- `GET /health` - Health check with service status

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_main.py

# Run with verbose output
pytest -v
```

## Database Support

The backend supports two database modes:

### 1. Mock Database (Default)
- In-memory storage for development
- No external dependencies
- Perfect for local development and testing

### 2. Cosmos DB (Production)
- Azure Cosmos DB integration
- Persistent storage
- Scalable and production-ready
- Automatically enabled when environment variables are provided

## AI Integration

### Azure OpenAI (Production)
- GPT-4o model integration
- Context-aware responses
- Product recommendations
- Natural language processing

### Fallback Responses (Development)
- Keyword-based responses
- No external dependencies
- Perfect for local development

## Configuration

The application uses environment-based configuration with sensible defaults:

- **Database**: Automatically detects Cosmos DB configuration
- **AI Service**: Automatically detects Azure OpenAI configuration
- **Authentication**: Ready for Microsoft Entra ID integration
- **CORS**: Configurable allowed origins
- **Logging**: Configurable log levels

## Error Handling

- Comprehensive error handling for all endpoints
- Detailed error messages for debugging
- Proper HTTP status codes
- Logging for monitoring and debugging

## Security

- CORS configuration
- Input validation with Pydantic
- SQL injection prevention (Cosmos DB)
- Rate limiting ready (can be added)
- Authentication ready (Microsoft Entra ID)

## Monitoring

- Health check endpoint
- Service status monitoring
- Error logging
- Request/response logging

## Development

### Adding New Endpoints

1. Create router in `app/routers/`
2. Add models in `app/models.py`
3. Update database service if needed
4. Add tests in `tests/`
5. Update API documentation

### Database Changes

1. Update models in `app/models.py`
2. Update database service in `app/database.py`
3. Update Cosmos DB service in `app/cosmos_service.py`
4. Add migration scripts if needed

## Deployment

The backend is ready for deployment to:
- Azure App Service
- Azure Container Instances
- Azure Kubernetes Service
- Any Python hosting platform

See the main Azure deployment plan for detailed deployment instructions.