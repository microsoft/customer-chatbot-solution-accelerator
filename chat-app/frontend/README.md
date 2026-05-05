# Chat Frontend

AI-powered chat application frontend built with React 19, TypeScript, and Vite. Features real-time conversations with multiple AI agents, streaming responses, and a modern responsive UI.

## Features

- **Real-time Chat**: Streaming AI responses with Server-Sent Events
- **Multiple AI Agents**: Switch between customer support, sales, and technical agents
- **Conversation Management**: Create, view, and manage chat conversations
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Modern UI**: Built with TailwindCSS and Lucide icons
- **TypeScript**: Full type safety throughout the application
- **Session-based**: Guest user sessions with conversation persistence

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Chat Backend API running on port 8001

### Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd chat-app/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3001`

## Scripts

- `npm run dev` - Start development server on port 3001
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Architecture

### Project Structure
```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main app layout with sidebar
│   ├── ChatInterface.tsx # Main chat interface
│   ├── MessageList.tsx # Message display
│   ├── MessageInput.tsx # Message input
│   ├── AgentSelector.tsx # AI agent selection
│   ├── LoadingSpinner.tsx
│   └── ErrorMessage.tsx
├── pages/              # Page components
│   └── ChatPage.tsx    # Main chat page
├── hooks/              # Custom React hooks
│   └── useChat.ts      # Chat API hooks
├── types/              # TypeScript types
│   └── chat.ts         # Chat data types
├── utils/              # Utility functions
│   └── api.ts          # API client
├── App.tsx            # Main App component
├── main.tsx           # React entry point
└── index.css          # Global styles
```

### Key Components

- **Layout**: Sidebar navigation with conversation list and responsive design
- **ChatInterface**: Main chat area with message list and input
- **MessageList**: Displays conversation messages with timestamps and actions
- **MessageInput**: Text input with auto-resize and keyboard shortcuts
- **AgentSelector**: Dropdown to switch between different AI agents

### State Management

- **TanStack Query**: Server state management and caching
- **React Router**: Client-side routing
- **React Hooks**: Local component state management

### API Integration

- **RESTful API**: Standard HTTP requests for CRUD operations
- **Server-Sent Events**: Real-time streaming responses
- **Automatic Retries**: Built-in error handling and retry logic
- **Optimistic Updates**: Immediate UI updates for better UX

## Configuration

### Environment Variables

Create a `.env.local` file for local overrides:

```env
VITE_API_BASE_URL=http://localhost:8001/api
```

### API Proxy

The Vite development server is configured to proxy API requests:
- Frontend: `http://localhost:3001`
- Backend API: `http://localhost:8001`
- API Proxy: `/api/*` → `http://localhost:8001/api/*`

## Features

### Chat Interface
- **Streaming Responses**: Real-time AI responses with typing indicators
- **Message Actions**: Copy messages, regenerate responses
- **Auto-scroll**: Automatically scrolls to new messages
- **Message Metadata**: Shows agent info, confidence scores, timestamps

### Agent System
- **Multiple Agents**: Customer support, sales assistant, technical support
- **Agent Switching**: Create new conversations with different agents
- **Agent Capabilities**: Display agent-specific capabilities and features

### Conversation Management
- **Conversation List**: Sidebar with recent conversations
- **Auto-save**: Conversations saved automatically
- **Session Persistence**: Maintains state across browser sessions
- **Search and Filter**: Easy navigation through conversation history

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Sidebar Toggle**: Collapsible navigation on smaller screens
- **Touch-Friendly**: Large tap targets and intuitive gestures
- **Cross-Browser**: Works on all modern browsers

## Customization

### Styling
The app uses TailwindCSS with custom components:
- Edit `src/index.css` for global styles
- Modify `tailwind.config.js` for theme customization
- Update color scheme in the `colors` section

### Adding New Agents
1. Backend: Add agent to `ai_service.py`
2. Frontend: Update icon mapping in `AgentSelector.tsx`
3. Add agent-specific styling and capabilities

### Custom Components
Create new components in `src/components/`:
- Follow existing naming conventions
- Use TypeScript interfaces
- Include proper prop validation
- Add responsive design considerations

## Development

### Code Style
- **TypeScript**: Strict mode enabled
- **ESLint**: Configured with React best practices
- **Prettier**: Automatic code formatting
- **File Organization**: Components, hooks, utils separation

### Best Practices
- Use custom hooks for API interactions
- Implement error boundaries for graceful failures
- Follow React 19 patterns and concurrent features
- Optimize for performance with proper memoization

### Testing
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Manual testing checklist:
# - Create new conversations
# - Send messages and verify responses
# - Test agent switching
# - Verify mobile responsiveness
# - Test error scenarios
```

## Integration

### With Backend
- Connects to FastAPI backend on port 8001
- Uses session-based authentication
- Handles streaming responses via Server-Sent Events
- Automatic error handling and retry logic

### With E-commerce App
- Runs on separate port (3001 vs 5174)
- Independent deployment and scaling
- Can share common components and utilities
- Separate domain and user sessions

## Deployment

### Production Build
```bash
npm run build
```

### Environment Configuration
Set production environment variables:
- `VITE_API_BASE_URL`: Production API URL
- Configure CORS on backend for production domain

### Hosting Options
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **Container Deployment**: Docker with nginx
- **Azure Static Web Apps**: Integrated with Azure services
- **CDN**: CloudFlare, Azure CDN for global distribution

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify backend is running on port 8001
   - Check CORS configuration
   - Verify proxy settings in `vite.config.ts`

2. **Streaming Not Working**:
   - Check browser support for Server-Sent Events
   - Verify network doesn't block streaming
   - Check backend streaming implementation

3. **Build Failures**:
   - Run `npm run type-check` to find TypeScript errors
   - Check for missing dependencies
   - Verify Node.js version compatibility

### Debug Mode
Enable debug logging by adding to console:
```javascript
localStorage.debug = 'chat:*'
```

## Contributing

1. Follow existing code patterns
2. Add TypeScript types for new features
3. Update documentation for significant changes
4. Test on multiple browsers and devices
5. Ensure mobile responsiveness