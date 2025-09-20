# Azure E-Commerce Chat Application Deployment Plan

## Overview
This document outlines the comprehensive plan to transform the current GitHub Spark e-commerce chat application into a production-ready Azure-deployed solution with Python FastAPI backend, Cosmos DB integration, Microsoft Entra ID authentication, Azure OpenAI integration, and Semantic Kernel with Azure AI Agent Service.

## Current Application Analysis

### Frontend Technology Stack
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 6.3.5
- **UI Library**: Fluent UI React components
- **State Management**: React hooks with GitHub Spark KV storage
- **Styling**: Fluent UI theming + Tailwind CSS for responsive utilities
- **Icons**: Fluent UI Icons

### Current Features
- Product browsing with search, filtering, and sorting
- Real-time chat interface with shopping assistant
- Shopping cart functionality
- Responsive dual-panel layout
- Static product data and mock chat responses

## Target Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Azure         │
│   (React SPA)   │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Product UI    │    │ • REST APIs     │    │ • Cosmos DB     │
│ • Chat UI       │    │ • Auth Middleware│    │ • Entra ID      │
│ • Cart UI       │    │ • AI Integration│    │ • OpenAI        │
│ • Auth UI       │    │ • Agent Service │    │ • Key Vault     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Phase 1: Backend Development

### 1.1 Python FastAPI Backend Setup

#### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration management
│   ├── dependencies.py        # Dependency injection
│   ├── middleware.py          # Custom middleware
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_handler.py    # JWT token handling
│   │   ├── auth_middleware.py # Authentication middleware
│   │   └── entraid_client.py  # Entra ID integration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User data models
│   │   ├── product.py        # Product data models
│   │   ├── chat.py           # Chat message models
│   │   ├── cart.py           # Cart and order models
│   │   └── transaction.py    # Transaction models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cosmos_service.py # Cosmos DB operations
│   │   ├── openai_service.py # Azure OpenAI integration
│   │   ├── agent_service.py  # Semantic Kernel agents
│   │   └── product_service.py# Product business logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── products.py       # Product endpoints
│   │   ├── chat.py           # Chat endpoints
│   │   ├── cart.py           # Cart endpoints
│   │   └── orders.py         # Order endpoints
│   └── utils/
│       ├── __init__.py
│       ├── cosmos_client.py  # Cosmos DB client setup
│       ├── keyvault_client.py# Azure Key Vault client
│       └── helpers.py        # Utility functions
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

#### Key Dependencies
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
azure-cosmos==4.5.1
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0
azure-ai-openai==1.0.0
semantic-kernel==0.4.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
python-dotenv==1.0.0
```

### 1.5 Frontend Dependencies Update

#### Updated Package.json for Fluent UI + Tailwind CSS
```json
{
  "dependencies": {
    "@fluentui/react": "^8.118.0",
    "@fluentui/react-components": "^9.45.0",
    "@fluentui/react-icons": "^2.0.240",
    "@fluentui/react-theme": "^9.0.0",
    "@fluentui/react-utilities": "^9.11.0",
    "@fluentui/web-components": "^1.0.0",
    "@microsoft/teams-js": "^2.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.83.1",
    "@azure/msal-browser": "^3.5.0",
    "@azure/msal-react": "^2.0.0",
    "axios": "^1.6.0",
    "date-fns": "^3.6.0",
    "uuid": "^11.1.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.10",
    "@types/react-dom": "^19.0.4",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.7.2",
    "vite": "^6.3.5",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### 1.2 Cosmos DB Data Models

#### Container: `users`
```python
{
    "id": "user_12345",
    "partitionKey": "user_12345",
    "email": "user@example.com",
    "displayName": "John Doe",
    "entraId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "createdAt": "2024-01-01T00:00:00Z",
    "lastLoginAt": "2024-01-15T10:30:00Z",
    "preferences": {
        "notifications": True,
        "theme": "light",
        "currency": "USD"
    },
    "addresses": [
        {
            "id": "addr_1",
            "type": "billing",
            "street": "123 Main St",
            "city": "Seattle",
            "state": "WA",
            "zipCode": "98101",
            "country": "US"
        }
    ],
    "ttl": -1
}
```

#### Container: `products`
```python
{
    "id": "prod_1",
    "partitionKey": "Electronics",
    "title": "Modern Minimalist Desk Lamp",
    "price": 89.99,
    "originalPrice": 129.99,
    "rating": 4.5,
    "reviewCount": 128,
    "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",
    "category": "Electronics",
    "inStock": True,
    "description": "Sleek LED desk lamp with adjustable brightness and USB charging port",
    "tags": ["lighting", "desk", "led", "usb"],
    "inventory": {
        "quantity": 50,
        "reserved": 5
    },
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "ttl": -1
}
```

#### Container: `chat_sessions`
```python
{
    "id": "session_12345",
    "partitionKey": "user_12345",
    "userId": "user_12345",
    "sessionId": "sess_abc123",
    "messages": [
        {
            "id": "msg_1",
            "content": "Hi there! I'm looking for a desk lamp.",
            "sender": "user",
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "productReferences": ["prod_1"],
                "intent": "product_search"
            }
        },
        {
            "id": "msg_2",
            "content": "I'd be happy to help you find the perfect desk lamp!",
            "sender": "assistant",
            "timestamp": "2024-01-15T10:30:05Z",
            "metadata": {
                "agentUsed": "product_recommendation",
                "confidence": 0.95
            }
        }
    ],
    "createdAt": "2024-01-15T10:30:00Z",
    "lastActivityAt": "2024-01-15T10:30:05Z",
    "status": "active",
    "ttl": 2592000  # 30 days
}
```

#### Container: `transactions`
```python
{
    "id": "txn_12345",
    "partitionKey": "user_12345",
    "userId": "user_12345",
    "type": "order",  # order, refund, exchange
    "status": "completed",  # pending, processing, completed, cancelled, refunded
    "orderNumber": "ORD-2024-001234",
    "items": [
        {
            "productId": "prod_1",
            "title": "Modern Minimalist Desk Lamp",
            "price": 89.99,
            "quantity": 1,
            "subtotal": 89.99
        }
    ],
    "totals": {
        "subtotal": 89.99,
        "tax": 7.20,
        "shipping": 9.99,
        "total": 107.18
    },
    "payment": {
        "method": "credit_card",
        "transactionId": "pay_abc123",
        "status": "completed"
    },
    "shipping": {
        "addressId": "addr_1",
        "method": "standard",
        "trackingNumber": "1Z999AA1234567890",
        "estimatedDelivery": "2024-01-20T00:00:00Z"
    },
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:35:00Z",
    "ttl": 31536000  # 1 year
}
```

### 1.3 API Endpoints Design

#### Authentication Endpoints
```python
POST /api/auth/login          # Entra ID token exchange
POST /api/auth/refresh        # Refresh JWT token
POST /api/auth/logout         # Logout and invalidate token
GET  /api/auth/me             # Get current user info
```

#### Product Endpoints
```python
GET    /api/products          # List products with filtering
GET    /api/products/{id}     # Get product details
GET    /api/products/search   # Search products
GET    /api/categories        # Get product categories
```

#### Chat Endpoints
```python
POST   /api/chat/sessions     # Create new chat session
GET    /api/chat/sessions     # Get user's chat sessions
POST   /api/chat/sessions/{id}/messages  # Send message
GET    /api/chat/sessions/{id}/messages  # Get chat history
DELETE /api/chat/sessions/{id}           # Delete chat session
```

#### Cart & Order Endpoints
```python
GET    /api/cart              # Get user's cart
POST   /api/cart/items        # Add item to cart
PUT    /api/cart/items/{id}   # Update cart item quantity
DELETE /api/cart/items/{id}   # Remove item from cart
POST   /api/orders            # Create order from cart
GET    /api/orders            # Get user's orders
GET    /api/orders/{id}       # Get order details
```

### 1.4 Azure OpenAI Integration

#### Semantic Kernel Agent Configuration
```python
# Agent definitions for different shopping scenarios
AGENTS = {
    "product_recommendation": {
        "name": "Product Recommendation Agent",
        "description": "Helps users find products based on their needs",
        "capabilities": ["product_search", "comparison", "filtering"]
    },
    "order_assistance": {
        "name": "Order Assistance Agent", 
        "description": "Helps with order management and tracking",
        "capabilities": ["order_lookup", "status_check", "modification"]
    },
    "general_support": {
        "name": "General Support Agent",
        "description": "Handles general customer service inquiries",
        "capabilities": ["faq", "account_help", "technical_support"]
    }
}
```

#### Handoff Orchestration
```python
class AgentOrchestrator:
    def __init__(self):
        self.agents = self._initialize_agents()
        self.handoff_rules = self._load_handoff_rules()
    
    async def process_message(self, message: str, context: dict) -> dict:
        # Determine which agent should handle the message
        agent = self._select_agent(message, context)
        
        # Process with selected agent
        response = await agent.process(message, context)
        
        # Check if handoff is needed
        if self._should_handoff(response, context):
            new_agent = self._get_handoff_agent(response, context)
            response = await new_agent.process(message, context)
        
        return response
```

## Phase 2: Frontend Modifications

### 2.1 Authentication Integration

#### Microsoft Authentication Library (MSAL) Setup with Fluent UI
```typescript
// src/lib/auth.ts
import { PublicClientApplication, Configuration } from '@azure/msal-browser';

const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_AZURE_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_TENANT_ID}`,
    redirectUri: process.env.REACT_APP_REDIRECT_URI
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);
```

#### Auth Context Provider with Fluent UI Theme
```typescript
// src/contexts/AuthContext.tsx
import { ThemeProvider, createTheme } from '@fluentui/react';
import { MsalProvider } from '@azure/msal-react';

const theme = createTheme({
  palette: {
    themePrimary: '#0078d4',
    themeLighterAlt: '#eff6fc',
    themeLighter: '#deecf9',
    themeLight: '#c7e0f4',
    themeTertiary: '#71afe5',
    themeSecondary: '#2b88d8',
    themeDarkAlt: '#106ebe',
    themeDark: '#005a9e',
    themeDarker: '#004578',
    neutralLighterAlt: '#faf9f8',
    neutralLighter: '#f3f2f1',
    neutralLight: '#edebe9',
    neutralQuietAlt: '#e1dfdd',
    neutralQuiet: '#d2d0ce',
    neutralSecondary: '#c8c6c4',
    neutralSecondaryAlt: '#c8c6c4',
    neutralTertiary: '#a19f9d',
    neutralTertiaryAlt: '#8a8886',
    neutralPrimary: '#323130',
    neutralPrimaryAlt: '#3b3a39',
    neutralDark: '#605e5c',
    black: '#323130',
    white: '#ffffff'
  }
});

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string>;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <MsalProvider instance={msalInstance}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </MsalProvider>
  );
};
```

### 2.2 API Integration Layer

#### API Client Setup
```typescript
// src/lib/api.ts
class ApiClient {
  private baseURL: string;
  private authContext: AuthContextType;

  constructor(baseURL: string, authContext: AuthContextType) {
    this.baseURL = baseURL;
    this.authContext = authContext;
  }

  private async getHeaders(): Promise<HeadersInit> {
    const token = await this.authContext.getAccessToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async get<T>(endpoint: string): Promise<T> {
    // Implementation
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    // Implementation
  }
}
```

#### React Query Integration
```typescript
// src/hooks/useProducts.ts
export const useProducts = (filters: ProductFilters) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => apiClient.get<Product[]>('/api/products', { params: filters }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useChatSession = (sessionId: string) => {
  return useQuery({
    queryKey: ['chat', sessionId],
    queryFn: () => apiClient.get<ChatSession>(`/api/chat/sessions/${sessionId}`),
    enabled: !!sessionId,
  });
};
```

### 2.3 Fluent UI Component Implementation

#### Product Card Component with Tailwind CSS
```typescript
// src/components/ProductCard.tsx
import React from 'react';
import { Card, CardHeader, CardPreview, Text, Button, Rating, Badge } from '@fluentui/react-components';
import { ShoppingCartRegular, HeartRegular } from '@fluentui/react-icons';
import { Product } from '../lib/types';

interface ProductCardProps {
  product: Product;
  onAddToCart: (product: Product) => void;
  onToggleFavorite: (productId: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart, onToggleFavorite }) => {
  return (
    <Card className="w-full max-w-sm mx-auto sm:max-w-none hover:shadow-lg transition-shadow duration-200">
      <CardPreview className="relative">
        <img 
          src={product.image} 
          alt={product.title}
          className="w-full h-48 sm:h-56 object-cover"
        />
        {product.originalPrice && (
          <Badge 
            appearance="filled" 
            color="danger" 
            className="absolute top-2 right-2 z-10"
          >
            {Math.round((1 - product.price / product.originalPrice) * 100)}% OFF
          </Badge>
        )}
      </CardPreview>
      
      <CardHeader className="p-4">
        <Text weight="semibold" size={400} className="line-clamp-2 mb-2">
          {product.title}
        </Text>
        <div className="flex items-center gap-2 mb-3">
          <Rating value={product.rating} readOnly size="small" />
          <Text size={200} className="text-gray-600">
            ({product.reviewCount} reviews)
          </Text>
        </div>
      </CardHeader>
      
      <div className="p-4 pt-0">
        <div className="flex items-baseline gap-2 mb-4">
          <Text size={500} weight="bold" className="text-blue-600">
            ${product.price}
          </Text>
          {product.originalPrice && (
            <Text size={300} className="text-gray-500 line-through">
              ${product.originalPrice}
            </Text>
          )}
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            appearance="primary"
            icon={<ShoppingCartRegular />}
            onClick={() => onAddToCart(product)}
            disabled={!product.inStock}
            className="flex-1 sm:flex-none"
          >
            {product.inStock ? 'Add to Cart' : 'Out of Stock'}
          </Button>
          <Button
            appearance="subtle"
            icon={<HeartRegular />}
            onClick={() => onToggleFavorite(product.id)}
            className="sm:w-auto w-full"
          />
        </div>
      </div>
    </Card>
  );
};
```

#### Chat Panel Component with Tailwind CSS
```typescript
// src/components/ChatPanel.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardPreview,
  Text,
  Button,
  Input,
  Avatar,
  Badge,
  ScrollArea,
  Spinner
} from '@fluentui/react-components';
import { SendRegular, AttachRegular, DismissRegular } from '@fluentui/react-icons';
import { ChatMessage } from '../lib/types';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  isTyping: boolean;
  isOpen: boolean;
  onClose: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  isTyping,
  isOpen,
  onClose
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <Card className={`h-full flex flex-col ${isOpen ? 'block' : 'hidden'} lg:block`}>
      <CardHeader className="flex-shrink-0 p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Avatar name="AI Assistant" size={32} />
            <div>
              <Text weight="semibold">Shopping Assistant</Text>
              <Badge appearance="filled" color="success" size="small">
                Online
              </Badge>
            </div>
          </div>
          <Button
            appearance="subtle"
            icon={<DismissRegular />}
            onClick={onClose}
            className="lg:hidden"
          />
        </div>
      </CardHeader>
      
      <CardPreview className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}
            {isTyping && (
              <div className="flex items-center gap-2 p-3 text-gray-600">
                <Spinner size="tiny" />
                <Text size={200}>Assistant is typing...</Text>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </CardPreview>
      
      <div className="flex-shrink-0 p-4 border-t">
        <div className="flex gap-2">
          <Input
            placeholder="Ask about products, get recommendations..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isTyping}
            className="flex-1"
          />
          <Button
            appearance="primary"
            icon={<SendRegular />}
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
          />
        </div>
      </div>
    </Card>
  );
};
```

#### Chat Message Bubble Component with Tailwind CSS
```typescript
// src/components/ChatMessageBubble.tsx
import React from 'react';
import { Avatar, Text, Card } from '@fluentui/react-components';
import { PersonRegular, BotRegular } from '@fluentui/react-icons';
import { format } from 'date-fns';
import { ChatMessage } from '../lib/types';

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const isAssistant = message.sender === 'assistant';

  return (
    <div className={`flex gap-2 max-w-[80%] ${isUser ? 'flex-row-reverse ml-auto' : 'mr-auto'}`}>
      {isAssistant && (
        <Avatar 
          name="AI Assistant" 
          size={24} 
          icon={<BotRegular />}
          className="flex-shrink-0"
        />
      )}
      
      <Card className={`p-3 rounded-2xl ${isUser ? 'bg-blue-600 text-white rounded-br-md' : 'bg-gray-100 text-gray-900 rounded-bl-md'}`}>
        <Text className="whitespace-pre-wrap break-words">{message.content}</Text>
        <Text size={100} className={`mt-1 opacity-70 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {format(message.timestamp, 'h:mm a')}
        </Text>
      </Card>
      
      {isUser && (
        <Avatar 
          name="User" 
          size={24} 
          icon={<PersonRegular />}
          className="flex-shrink-0"
        />
      )}
    </div>
  );
};
```

### 2.4 Fluent UI + Tailwind CSS Configuration

#### Tailwind CSS Setup
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Extend Tailwind with Fluent UI design tokens
      colors: {
        'fluent-primary': '#0078d4',
        'fluent-secondary': '#2b88d8',
        'fluent-accent': '#ff6b35',
        'fluent-success': '#107c10',
        'fluent-warning': '#ff8c00',
        'fluent-error': '#d13438',
      },
      fontFamily: {
        'fluent': ['Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      maxWidth: {
        '8xl': '88rem',
      },
      screens: {
        'xs': '475px',
        '3xl': '1600px',
      }
    },
  },
  plugins: [
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/forms'),
  ],
}
```

#### PostCSS Configuration
```javascript
// postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

#### Main CSS File
```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Fluent UI CSS Variables for Tailwind Integration */
:root {
  --color-brand-primary: #0078d4;
  --color-brand-secondary: #2b88d8;
  --color-brand-accent: #ff6b35;
  --color-text-primary: #323130;
  --color-text-secondary: #605e5c;
  --color-neutral-light: #edebe9;
  --color-neutral-lighter: #f3f2f1;
  --color-divider: #edebe9;
  --shadow-elevation-4: 0 1.6px 3.6px 0 rgba(0, 0, 0, 0.132), 0 0.3px 0.9px 0 rgba(0, 0, 0, 0.108);
  --shadow-elevation-8: 0 3.2px 7.2px 0 rgba(0, 0, 0, 0.132), 0 0.6px 1.8px 0 rgba(0, 0, 0, 0.108);
}

/* Custom Tailwind Components */
@layer components {
  .product-grid {
    @apply grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6;
  }
  
  .chat-container {
    @apply flex flex-col lg:flex-row h-screen;
  }
  
  .product-panel {
    @apply flex-1 lg:w-2/3 p-4 lg:p-6;
  }
  
  .chat-panel {
    @apply w-full lg:w-1/3 border-l border-gray-200;
  }
  
  .mobile-chat-toggle {
    @apply fixed bottom-4 right-4 lg:hidden z-50;
  }
  
  .desktop-chat {
    @apply hidden lg:block;
  }
  
  .mobile-chat {
    @apply block lg:hidden;
  }
}

/* Responsive Utilities */
@layer utilities {
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}
```

### 2.5 Fluent UI Theming and Styling

#### Custom Theme Configuration
```typescript
// src/theme/theme.ts
import { createTheme, Theme } from '@fluentui/react';

export const ecommerceTheme: Theme = createTheme({
  palette: {
    themePrimary: '#0078d4',
    themeLighterAlt: '#eff6fc',
    themeLighter: '#deecf9',
    themeLight: '#c7e0f4',
    themeTertiary: '#71afe5',
    themeSecondary: '#2b88d8',
    themeDarkAlt: '#106ebe',
    themeDark: '#005a9e',
    themeDarker: '#004578',
    neutralLighterAlt: '#faf9f8',
    neutralLighter: '#f3f2f1',
    neutralLight: '#edebe9',
    neutralQuietAlt: '#e1dfdd',
    neutralQuiet: '#d2d0ce',
    neutralSecondary: '#c8c6c4',
    neutralSecondaryAlt: '#c8c6c4',
    neutralTertiary: '#a19f9d',
    neutralTertiaryAlt: '#8a8886',
    neutralPrimary: '#323130',
    neutralPrimaryAlt: '#3b3a39',
    neutralDark: '#605e5c',
    black: '#323130',
    white: '#ffffff',
    // Custom colors for e-commerce
    accent: '#ff6b35', // Orange for call-to-action elements
    success: '#107c10',
    warning: '#ff8c00',
    error: '#d13438'
  },
  fonts: {
    small: {
      fontSize: '12px',
      fontWeight: '400'
    },
    medium: {
      fontSize: '14px',
      fontWeight: '400'
    },
    large: {
      fontSize: '16px',
      fontWeight: '400'
    },
    xLarge: {
      fontSize: '18px',
      fontWeight: '600'
    },
    xxLarge: {
      fontSize: '24px',
      fontWeight: '600'
    }
  },
  effects: {
    elevation4: '0 1.6px 3.6px 0 rgba(0, 0, 0, 0.132), 0 0.3px 0.9px 0 rgba(0, 0, 0, 0.108)',
    elevation8: '0 3.2px 7.2px 0 rgba(0, 0, 0, 0.132), 0 0.6px 1.8px 0 rgba(0, 0, 0, 0.108)',
    elevation16: '0 6.4px 14.4px 0 rgba(0, 0, 0, 0.132), 0 1.2px 3.6px 0 rgba(0, 0, 0, 0.108)',
    elevation64: '0 25.6px 57.6px 0 rgba(0, 0, 0, 0.22), 0 4.8px 14.4px 0 rgba(0, 0, 0, 0.18)'
  }
});

// Dark theme variant
export const ecommerceDarkTheme: Theme = createTheme({
  ...ecommerceTheme,
  palette: {
    ...ecommerceTheme.palette,
    themePrimary: '#60cdff',
    themeLighterAlt: '#040506',
    themeLighter: '#0f1419',
    themeLight: '#1e2832',
    themeTertiary: '#3d5065',
    themeSecondary: '#5a7698',
    themeDarkAlt: '#6b8bb8',
    themeDark: '#7d9bc4',
    themeDarker: '#96b3d4',
    neutralLighterAlt: '#0b0b0b',
    neutralLighter: '#151515',
    neutralLight: '#1f1f1f',
    neutralQuietAlt: '#292929',
    neutralQuiet: '#323232',
    neutralSecondary: '#3d3d3d',
    neutralSecondaryAlt: '#3d3d3d',
    neutralTertiary: '#484848',
    neutralTertiaryAlt: '#525252',
    neutralPrimary: '#ffffff',
    neutralPrimaryAlt: '#e0e0e0',
    neutralDark: '#f4f4f4',
    black: '#ffffff',
    white: '#0b0b0b'
  }
});
```

#### Custom CSS for Fluent UI Components
```css
/* src/styles/fluent-ui-custom.css */

/* Product Card Customizations */
.product-card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border-radius: 8px;
  overflow: hidden;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-elevation-8);
}

.discount-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
}

.price-section {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 12px;
}

.current-price {
  color: var(--color-brand-primary);
  font-weight: 600;
}

.original-price {
  text-decoration: line-through;
  color: var(--color-text-secondary);
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Chat Panel Customizations */
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--color-divider);
}

.assistant-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.close-button {
  display: none;
}

@media (max-width: 768px) {
  .close-button {
    display: block;
  }
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.messages-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-bubble {
  display: flex;
  gap: 8px;
  max-width: 80%;
}

.user-message {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.assistant-message {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 100%;
  word-wrap: break-word;
}

.user-message .message-content {
  background-color: var(--color-brand-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant-message .message-content {
  background-color: var(--color-neutral-light);
  color: var(--color-text-primary);
  border-bottom-left-radius: 4px;
}

.message-timestamp {
  margin-top: 4px;
  opacity: 0.7;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 16px;
  border-top: 1px solid var(--color-divider);
}

.message-input {
  flex: 1;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  color: var(--color-text-secondary);
}

/* Loading States */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 32px;
}

.image-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  background-color: var(--color-neutral-lighter);
}

/* Responsive Design */
@media (max-width: 768px) {
  .product-card {
    margin-bottom: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .action-buttons button {
    width: 100%;
  }
  
  .message-bubble {
    max-width: 90%;
  }
}
```

### 2.6 Main App Component with Fluent UI + Tailwind CSS

#### App Layout Component
```typescript
// src/App.tsx
import React, { useState } from 'react';
import { ThemeProvider } from '@fluentui/react';
import { Button } from '@fluentui/react-components';
import { ChatRegular, ListRegular } from '@fluentui/react-icons';
import { ProductGrid } from './components/ProductGrid';
import { ChatPanel } from './components/ChatPanel';
import { CartDrawer } from './components/CartDrawer';
import { ecommerceTheme } from './theme/theme';
import { useIsMobile } from './hooks/use-mobile';

function App() {
  const isMobile = useIsMobile();
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);

  return (
    <ThemeProvider theme={ecommerceTheme}>
      <div className="chat-container">
        {/* Product Panel */}
        <div className="product-panel">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Modern E-Commerce</h1>
            <div className="flex items-center gap-2">
              <Button
                appearance="subtle"
                icon={<ListRegular />}
                onClick={() => setIsCartOpen(true)}
                className="lg:hidden"
              >
                Cart
              </Button>
              <Button
                appearance="primary"
                icon={<ChatRegular />}
                onClick={() => setIsChatOpen(true)}
                className="lg:hidden"
              >
                Chat
              </Button>
            </div>
          </div>
          
          <ProductGrid />
        </div>

        {/* Chat Panel - Desktop */}
        <div className="desktop-chat">
          <ChatPanel
            messages={[]}
            onSendMessage={() => {}}
            isTyping={false}
            isOpen={true}
            onClose={() => {}}
          />
        </div>

        {/* Chat Panel - Mobile */}
        <div className="mobile-chat">
          {isChatOpen && (
            <div className="fixed inset-0 z-50 bg-white">
              <ChatPanel
                messages={[]}
                onSendMessage={() => {}}
                isTyping={false}
                isOpen={isChatOpen}
                onClose={() => setIsChatOpen(false)}
              />
            </div>
          )}
        </div>

        {/* Cart Drawer */}
        <CartDrawer
          isOpen={isCartOpen}
          onClose={() => setIsCartOpen(false)}
        />

        {/* Mobile Chat Toggle */}
        <Button
          appearance="primary"
          icon={<ChatRegular />}
          onClick={() => setIsChatOpen(true)}
          className="mobile-chat-toggle"
          size="large"
        />
      </div>
    </ThemeProvider>
  );
}

export default App;
```

#### Product Grid Component
```typescript
// src/components/ProductGrid.tsx
import React from 'react';
import { ProductCard } from './ProductCard';
import { ProductFilters } from './ProductFilters';
import { Product } from '../lib/types';

interface ProductGridProps {
  products?: Product[];
  onAddToCart?: (product: Product) => void;
  onToggleFavorite?: (productId: string) => void;
}

export const ProductGrid: React.FC<ProductGridProps> = ({
  products = [],
  onAddToCart = () => {},
  onToggleFavorite = () => {}
}) => {
  return (
    <div className="space-y-6">
      {/* Filters */}
      <ProductFilters />
      
      {/* Products Grid */}
      <div className="product-grid">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onAddToCart={onAddToCart}
            onToggleFavorite={onToggleFavorite}
          />
        ))}
      </div>
      
      {/* Empty State */}
      {products.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No products found</p>
        </div>
      )}
    </div>
  );
};
```

### 2.7 Real-time Chat Integration

#### WebSocket Connection
```typescript
// src/hooks/useChat.ts
export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`wss://api.yourdomain.com/chat/${sessionId}/ws`);
    
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };
    ws.onclose = () => setIsConnected(false);

    return () => ws.close();
  }, [sessionId]);

  const sendMessage = useCallback((content: string) => {
    // Send message via WebSocket
  }, []);

  return { messages, sendMessage, isConnected };
};
```

## Phase 3: Azure Infrastructure

### 3.1 Bicep Template Structure

#### Main Template
```bicep
// main.bicep
param location string = resourceGroup().location
param environment string = 'dev'
param appName string = 'ecommerce-chat'

module cosmosdb 'modules/cosmosdb.bicep' = {
  name: 'cosmosdb'
  params: {
    location: location
    environment: environment
    appName: appName
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    environment: environment
    appName: appName
  }
}

module appservice 'modules/appservice.bicep' = {
  name: 'appservice'
  params: {
    location: location
    environment: environment
    appName: appName
    cosmosdbConnectionString: cosmosdb.outputs.connectionString
    keyvaultUri: keyvault.outputs.uri
  }
}

module frontend 'modules/frontend.bicep' = {
  name: 'frontend'
  params: {
    location: location
    environment: environment
    appName: appName
    backendUrl: appservice.outputs.backendUrl
  }
}
```

#### Cosmos DB Module
```bicep
// modules/cosmosdb.bicep
param location string
param environment string
param appName string

var cosmosAccountName = '${appName}-cosmos-${environment}'
var databaseName = 'ecommerce'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Similar containers for products, chat_sessions, transactions
```

### 3.2 Azure App Service Configuration

#### Backend App Service
```bicep
// modules/appservice.bicep
resource backendApp 'Microsoft.Web/sites@2022-03-01' = {
  name: '${appName}-backend-${environment}'
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'COSMOS_CONNECTION_STRING'
          value: cosmosdbConnectionString
        }
        {
          name: 'KEYVAULT_URI'
          value: keyvaultUri
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: keyvault.outputs.clientIdSecretName
        }
        {
          name: 'AZURE_CLIENT_SECRET'
          value: keyvault.outputs.clientSecretSecretName
        }
        {
          name: 'AZURE_TENANT_ID'
          value: keyvault.outputs.tenantIdSecretName
        }
        {
          name: 'OPENAI_ENDPOINT'
          value: keyvault.outputs.openaiEndpointSecretName
        }
        {
          name: 'OPENAI_API_KEY'
          value: keyvault.outputs.openaiApiKeySecretName
        }
      ]
    }
  }
}
```

#### Frontend App Service
```bicep
resource frontendApp 'Microsoft.Web/sites@2022-03-01' = {
  name: '${appName}-frontend-${environment}'
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      appSettings: [
        {
          name: 'REACT_APP_API_URL'
          value: backendUrl
        }
        {
          name: 'REACT_APP_AZURE_CLIENT_ID'
          value: keyvault.outputs.clientIdSecretName
        }
        {
          name: 'REACT_APP_AZURE_TENANT_ID'
          value: keyvault.outputs.tenantIdSecretName
        }
      ]
    }
  }
}
```

### 3.3 Azure Key Vault Configuration

#### Secrets Management
```bicep
// modules/keyvault.bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${appName}-kv-${environment}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: userAssignedIdentity.principalId
        permissions: {
          secrets: ['get', 'list']
        }
      }
    ]
  }
}

resource cosmosConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmos-connection-string'
  properties: {
    value: cosmosAccount.outputs.connectionString
  }
}

resource openaiApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: openaiAccount.outputs.apiKey
  }
}
```

## Phase 4: Deployment Pipeline

### 4.1 GitHub Actions Workflow

#### Backend Deployment
```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/
      
      - name: Build Docker image
        run: |
          cd backend
          docker build -t ${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }} .
      
      - name: Push to ACR
        run: |
          docker push ${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }}
      
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'ecommerce-chat-backend-dev'
          images: '${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }}'
```

#### Frontend Deployment
```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths: ['modern-e-commerce-ch/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: modern-e-commerce-ch/package-lock.json
      
      - name: Install dependencies
        run: |
          cd modern-e-commerce-ch
          npm ci
      
      - name: Build application
        run: |
          cd modern-e-commerce-ch
          npm run build
        env:
          REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL }}
          REACT_APP_AZURE_CLIENT_ID: ${{ secrets.REACT_APP_AZURE_CLIENT_ID }}
          REACT_APP_AZURE_TENANT_ID: ${{ secrets.REACT_APP_AZURE_TENANT_ID }}
      
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'ecommerce-chat-frontend-dev'
          package: modern-e-commerce-ch/dist
```

### 4.2 Infrastructure Deployment

#### Bicep Deployment
```yaml
# .github/workflows/deploy-infrastructure.yml
name: Deploy Infrastructure

on:
  push:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Deploy Bicep
        run: |
          az deployment group create \
            --resource-group ${{ secrets.RESOURCE_GROUP }} \
            --template-file infrastructure/main.bicep \
            --parameters environment=dev
```

## Phase 5: Data Migration and Seeding

### 5.1 Data Migration Scripts

#### Product Data Migration
```python
# scripts/migrate_products.py
import asyncio
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

async def migrate_products():
    client = CosmosClient(cosmos_endpoint, cosmos_key)
    database = client.get_database_client("ecommerce")
    container = database.get_container_client("products")
    
    # Migrate from static data to Cosmos DB
    for product in mock_products:
        await container.create_item({
            "id": product["id"],
            "partitionKey": product["category"],
            **product
        })
```

#### User Data Seeding
```python
# scripts/seed_users.py
async def seed_demo_users():
    demo_users = [
        {
            "id": "demo_user_1",
            "email": "demo1@example.com",
            "displayName": "Demo User 1",
            "entraId": "demo-entra-id-1",
            "preferences": {
                "notifications": True,
                "theme": "light",
                "currency": "USD"
            }
        }
        # More demo users...
    ]
    
    for user in demo_users:
        await users_container.create_item(user)
```

#### Transaction History Seeding
```python
# scripts/seed_transactions.py
async def seed_demo_transactions():
    # Create realistic order history for demo users
    for user_id in demo_user_ids:
        orders = generate_realistic_order_history(user_id)
        for order in orders:
            await transactions_container.create_item(order)
```

## Phase 6: Security and Compliance

### 6.1 Security Implementation

#### CORS Configuration
```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### Rate Limiting
```python
# backend/app/middleware.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/chat/sessions/{session_id}/messages")
@limiter.limit("10/minute")
async def send_message(request: Request, ...):
    # Implementation
```

#### Input Validation
```python
# backend/app/models/chat.py
from pydantic import BaseModel, validator
from typing import Optional

class ChatMessageCreate(BaseModel):
    content: str
    session_id: str
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Message content cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message content too long')
        return v.strip()
```

### 6.2 Monitoring and Logging

#### Application Insights Integration
```python
# backend/app/monitoring.py
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.tracer import Tracer

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
))

# Configure tracing
tracer = Tracer(
    exporter=AzureExporter(
        connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )
)
```

#### Health Checks
```python
# backend/app/health.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/ready")
async def readiness_check():
    # Check database connectivity
    # Check external service dependencies
    return {"status": "ready"}
```

## Phase 7: Testing Strategy

### 7.1 Backend Testing

#### Unit Tests
```python
# tests/test_services/test_product_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.product_service import ProductService

@pytest.mark.asyncio
async def test_get_products():
    mock_container = AsyncMock()
    mock_container.query_items.return_value = [{"id": "1", "title": "Test Product"}]
    
    service = ProductService(mock_container)
    result = await service.get_products()
    
    assert len(result) == 1
    assert result[0]["title"] == "Test Product"
```

#### Integration Tests
```python
# tests/test_integration/test_chat_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_send_chat_message():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/chat/sessions/test-session/messages",
            json={"content": "Hello, I need help finding a lamp"},
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    assert "response" in response.json()
```

### 7.2 Frontend Testing

#### Component Tests with Fluent UI
```typescript
// src/components/__tests__/ChatPanel.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatPanel } from '../ChatPanel';
import { ThemeProvider, createTheme } from '@fluentui/react';

const theme = createTheme();

test('sends message when form is submitted', () => {
  const mockSendMessage = jest.fn();
  render(
    <ThemeProvider theme={theme}>
      <ChatPanel
        messages={[]}
        onSendMessage={mockSendMessage}
        isTyping={false}
        isOpen={true}
        onClose={() => {}}
      />
    </ThemeProvider>
  );
  
  const input = screen.getByPlaceholderText(/ask about products/i);
  const sendButton = screen.getByRole('button', { name: /send/i });
  
  fireEvent.change(input, { target: { value: 'Hello' } });
  fireEvent.click(sendButton);
  
  expect(mockSendMessage).toHaveBeenCalledWith('Hello');
});

test('displays typing indicator when assistant is typing', () => {
  render(
    <ThemeProvider theme={theme}>
      <ChatPanel
        messages={[]}
        onSendMessage={() => {}}
        isTyping={true}
        isOpen={true}
        onClose={() => {}}
      />
    </ThemeProvider>
  );
  
  expect(screen.getByText('Assistant is typing...')).toBeInTheDocument();
});
```

#### E2E Tests
```typescript
// e2e/chat-flow.spec.ts
import { test, expect } from '@playwright/test';

test('complete chat flow', async ({ page }) => {
  await page.goto('/');
  
  // Login
  await page.click('[data-testid="login-button"]');
  await page.fill('[data-testid="email-input"]', 'demo@example.com');
  await page.click('[data-testid="login-submit"]');
  
  // Open chat
  await page.click('[data-testid="chat-toggle"]');
  
  // Send message
  await page.fill('[data-testid="chat-input"]', 'I need a desk lamp');
  await page.click('[data-testid="send-button"]');
  
  // Verify response
  await expect(page.locator('[data-testid="chat-messages"]')).toContainText('I can help you find a desk lamp');
});
```

## Phase 8: Performance Optimization

### 8.1 Backend Optimization

#### Caching Strategy
```python
# backend/app/services/cache_service.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import redis.asyncio as redis

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(os.getenv("REDIS_CONNECTION_STRING"))
    
    async def get_products(self, filters: dict) -> Optional[list]:
        cache_key = f"products:{hash(str(filters))}"
        cached = await self.redis.get(cache_key)
        return json.loads(cached) if cached else None
    
    async def set_products(self, filters: dict, products: list, ttl: int = 300):
        cache_key = f"products:{hash(str(filters))}"
        await self.redis.setex(cache_key, ttl, json.dumps(products))
```

#### Database Optimization
```python
# backend/app/utils/cosmos_queries.py
class CosmosQueries:
    @staticmethod
    def get_products_query(filters: ProductFilters) -> str:
        query = "SELECT * FROM c WHERE 1=1"
        parameters = []
        
        if filters.category != "All":
            query += " AND c.category = @category"
            parameters.append({"name": "@category", "value": filters.category})
        
        if filters.min_price:
            query += " AND c.price >= @minPrice"
            parameters.append({"name": "@minPrice", "value": filters.min_price})
        
        return query, parameters
```

### 8.2 Frontend Optimization

#### Code Splitting with Fluent UI
```typescript
// src/App.tsx
import { lazy, Suspense } from 'react';
import { Spinner, Text } from '@fluentui/react-components';

const ChatPanel = lazy(() => import('./components/ChatPanel'));
const ProductGrid = lazy(() => import('./components/ProductGrid'));

function App() {
  return (
    <Suspense fallback={
      <div className="loading-container">
        <Spinner size="large" />
        <Text>Loading application...</Text>
      </div>
    }>
      <ChatPanel />
      <ProductGrid />
    </Suspense>
  );
}
```

#### Image Optimization with Fluent UI
```typescript
// src/components/ProductCard.tsx
import { useState } from 'react';
import { Card, CardPreview, Spinner } from '@fluentui/react-components';

const ProductCard = ({ product }: { product: Product }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  
  return (
    <Card className="product-card">
      <CardPreview>
        {!imageLoaded && (
          <div className="image-loading">
            <Spinner size="medium" />
          </div>
        )}
        <img
          src={product.image}
          alt={product.title}
          loading="lazy"
          onLoad={() => setImageLoaded(true)}
          style={{ 
            opacity: imageLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease-in-out'
          }}
        />
      </CardPreview>
    </Card>
  );
};
```

## Phase 9: Deployment Checklist

### 9.1 Pre-deployment Checklist

- [ ] **Infrastructure**
  - [ ] Resource group created
  - [ ] Cosmos DB account provisioned with all containers
  - [ ] Azure Key Vault configured with all secrets
  - [ ] App Service plans created for frontend and backend
  - [ ] Azure OpenAI service provisioned
  - [ ] Microsoft Entra ID app registration completed

- [ ] **Backend**
  - [ ] FastAPI application developed and tested
  - [ ] All API endpoints implemented
  - [ ] Authentication middleware configured
  - [ ] Cosmos DB integration working
  - [ ] Azure OpenAI integration working
  - [ ] Semantic Kernel agents configured
  - [ ] Unit and integration tests passing
  - [ ] Docker container built and tested
  - [ ] Environment variables configured

- [ ] **Frontend**
  - [ ] React application updated with authentication
  - [ ] API integration layer implemented
  - [ ] Real-time chat functionality working
  - [ ] MSAL authentication configured
  - [ ] Component tests passing
  - [ ] E2E tests passing
  - [ ] Build process optimized
  - [ ] Environment variables configured

- [ ] **Data**
  - [ ] Product data migrated to Cosmos DB
  - [ ] Demo users seeded
  - [ ] Transaction history seeded
  - [ ] Chat session data structure validated

- [ ] **Security**
  - [ ] CORS configured correctly
  - [ ] Rate limiting implemented
  - [ ] Input validation in place
  - [ ] Authentication flows tested
  - [ ] Secrets properly stored in Key Vault

- [ ] **Monitoring**
  - [ ] Application Insights configured
  - [ ] Health checks implemented
  - [ ] Logging configured
  - [ ] Alerting rules set up

### 9.2 Deployment Steps

1. **Deploy Infrastructure**
   ```bash
   az deployment group create \
     --resource-group ecommerce-chat-rg \
     --template-file infrastructure/main.bicep \
     --parameters environment=prod
   ```

2. **Deploy Backend**
   ```bash
   # Build and push Docker image
   docker build -t ecommerce-chat-backend .
   docker tag ecommerce-chat-backend:latest your-acr.azurecr.io/backend:latest
   docker push your-acr.azurecr.io/backend:latest
   
   # Deploy to App Service
   az webapp config container set \
     --name ecommerce-chat-backend-prod \
     --resource-group ecommerce-chat-rg \
     --docker-custom-image-name your-acr.azurecr.io/backend:latest
   ```

3. **Deploy Frontend**
   ```bash
   # Build React application
   cd modern-e-commerce-ch
   npm run build
   
   # Deploy to App Service
   az webapp deployment source config-zip \
     --name ecommerce-chat-frontend-prod \
     --resource-group ecommerce-chat-rg \
     --src dist.zip
   ```

4. **Run Data Migration**
   ```bash
   python scripts/migrate_products.py
   python scripts/seed_users.py
   python scripts/seed_transactions.py
   ```

5. **Verify Deployment**
   ```bash
   # Test health endpoints
   curl https://ecommerce-chat-backend-prod.azurewebsites.net/health
   curl https://ecommerce-chat-frontend-prod.azurewebsites.net
   
   # Test authentication flow
   # Test chat functionality
   # Test product browsing
   # Test cart and checkout
   ```

## Phase 10: Post-Deployment

### 10.1 Monitoring and Maintenance

#### Performance Monitoring
- Set up Application Insights dashboards
- Monitor API response times
- Track database query performance
- Monitor memory and CPU usage

#### Security Monitoring
- Set up security alerts
- Monitor authentication failures
- Track suspicious activity
- Regular security audits

#### Business Metrics
- Track user engagement
- Monitor conversion rates
- Analyze chat effectiveness
- Track order completion rates

### 10.2 Scaling Considerations

#### Horizontal Scaling
- Configure auto-scaling for App Services
- Implement Redis caching for better performance
- Consider Azure Front Door for global distribution

#### Database Scaling
- Monitor Cosmos DB RU consumption
- Implement read replicas if needed
- Consider partitioning strategy optimization

#### AI Service Scaling
- Monitor Azure OpenAI usage
- Implement request queuing if needed
- Consider multiple model endpoints

## Conclusion

This comprehensive deployment plan transforms the current GitHub Spark e-commerce chat application into a production-ready Azure solution with:

- **Scalable Architecture**: Microservices with FastAPI backend and React frontend
- **Secure Authentication**: Microsoft Entra ID integration
- **Intelligent Chat**: Azure OpenAI with Semantic Kernel agents
- **Persistent Data**: Cosmos DB with proper data modeling
- **Infrastructure as Code**: Bicep templates for reproducible deployments
- **CI/CD Pipeline**: GitHub Actions for automated deployments
- **Monitoring**: Application Insights and health checks
- **Security**: Key Vault integration and best practices

The plan follows Azure best practices and provides a solid foundation for a production e-commerce application with AI-powered customer support capabilities.