# E-commerce Frontend

A modern React-based e-commerce interface built with TypeScript, Vite, and TailwindCSS.

## Features

- **Product Browsing**: Browse products with search, filtering, and pagination
- **Shopping Cart**: Add/remove items, update quantities, guest checkout
- **Product Details**: Detailed product pages with images and descriptions
- **Checkout Flow**: Complete checkout process with order confirmation
- **Responsive Design**: Mobile-first responsive design with TailwindCSS
- **Modern Stack**: React 19, TypeScript, React Router, TanStack Query

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Running e-commerce backend API (see ../backend/README.md)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to http://localhost:5173

### Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ErrorBoundary.tsx
│   ├── Layout.tsx
│   ├── Loading.tsx
│   └── ProductCard.tsx
├── hooks/              # Custom React hooks
│   ├── api.ts          # API calls with TanStack Query
│   └── useSession.ts   # Session management
├── pages/              # Page components
│   ├── HomePage.tsx
│   ├── ProductsPage.tsx
│   ├── ProductDetailPage.tsx
│   ├── CartPage.tsx
│   ├── CheckoutPage.tsx
│   └── OrderConfirmationPage.tsx
├── types/              # TypeScript type definitions
│   └── index.ts
├── App.tsx             # Main app component with routing
├── main.tsx            # App entry point
└── index.css           # Global styles with Tailwind
```

## API Integration

The frontend communicates with the backend API through:

- **Base URL**: `/api` (proxied to backend in development)
- **Authentication**: Session-based for guest users
- **Data Fetching**: TanStack Query for caching and state management
- **Error Handling**: Automatic retries and error boundaries

## Key Features

### Guest Shopping
- Automatic session generation for anonymous users
- Cart persistence across browser sessions
- Guest checkout without account creation

### Product Navigation
- Search and filter products by category and availability
- Pagination for large product catalogs
- Detailed product pages with add-to-cart functionality

### Shopping Cart
- Real-time cart updates
- Quantity management
- Free shipping calculator
- Clear cart functionality

### Checkout Process
- Customer information form with validation
- Order summary with shipping calculation
- Demo checkout (no payment processing)
- Order confirmation with details

## Development

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Setup

The frontend expects the backend API to be available at `/api`. In development, Vite proxies requests to the backend server.

For production deployment, ensure your web server routes `/api/*` requests to the backend service.

## Styling

Uses TailwindCSS with:
- Utility-first approach
- Custom component classes
- Responsive design breakpoints
- Heroicons for consistent iconography

## State Management

- **TanStack Query**: Server state management with automatic caching
- **React Router**: Client-side routing with URL state
- **Local Storage**: Session ID persistence
- **React Hook Form**: Form state and validation