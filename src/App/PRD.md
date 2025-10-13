# Shopping Assistant App

A modern e-commerce application with integrated AI shopping assistant featuring a dual-panel layout for seamless product browsing and customer support.

**Experience Qualities**:
1. **Intuitive** - Natural product discovery with intelligent search and filtering that feels effortless
2. **Connected** - Seamless chat integration that provides personalized shopping guidance without interrupting browsing flow  
3. **Professional** - Clean, modern interface that builds trust and confidence in purchasing decisions

**Complexity Level**: Light Application (multiple features with basic state)
The app combines product browsing with chat functionality while maintaining simplicity in user flows and state management.

## Essential Features

### Product Listings Panel
- **Functionality**: Display products in responsive grid with search, filters, and sorting
- **Purpose**: Enable efficient product discovery and comparison
- **Trigger**: App load or search/filter interaction
- **Progression**: Load products → Display grid → Apply filters/search → Update results → Select product
- **Success criteria**: Products load within 2s, filters work instantly, smooth responsive behavior

### Chat Assistant Panel
- **Functionality**: Real-time chat interface with shopping assistant
- **Purpose**: Provide personalized shopping guidance and support
- **Trigger**: User clicks chat or types message
- **Progression**: Open chat → Send message → Receive AI response → Continue conversation → Get product recommendations
- **Success criteria**: Messages send instantly, responses feel natural, chat persists during browsing

### Shopping Cart Integration
- **Functionality**: Add products to cart with quantity management
- **Purpose**: Streamline purchasing workflow
- **Trigger**: Click "Add to Cart" button
- **Progression**: Click add → Confirm addition → Update cart count → View cart → Proceed to checkout
- **Success criteria**: Cart updates immediately, quantities persist, visual feedback on additions

### Responsive Layout Management
- **Functionality**: Adaptive dual-panel layout that collapses on mobile
- **Purpose**: Optimal experience across all device sizes
- **Trigger**: Screen resize or mobile device detection
- **Progression**: Detect screen size → Apply appropriate layout → Toggle panels on mobile → Maintain functionality
- **Success criteria**: Smooth transitions, no content loss, touch-friendly on mobile

## Edge Case Handling
- **Empty States**: Show helpful messages and suggestions when no products match filters or cart is empty
- **Loading Failures**: Display retry options with clear error messages when product data fails to load
- **Network Issues**: Queue chat messages and retry automatically when connection is restored
- **Mobile Interactions**: Ensure chat doesn't interfere with product browsing on small screens
- **Long Product Names**: Truncate with ellipsis and show full name on hover/focus

## Design Direction
The design should feel modern and trustworthy with a clean, spacious interface that emphasizes products while making the chat assistant feel helpful rather than intrusive - minimal interface serves the dual purpose of showcasing products and enabling natural conversation.

## Color Selection
Complementary (opposite colors) - Using blue and warm orange to create visual distinction between product browsing (cooler, focused) and chat interaction (warmer, conversational).

- **Primary Color**: Deep Blue (oklch(0.45 0.15 240)) - Communicates trust and professionalism for primary actions
- **Secondary Colors**: Light Blue (oklch(0.85 0.08 240)) for backgrounds and Neutral Gray (oklch(0.7 0.02 240)) for secondary elements  
- **Accent Color**: Warm Orange (oklch(0.7 0.15 50)) - Creates energy and warmth for chat elements and notifications
- **Foreground/Background Pairings**: 
  - Background (White oklch(1 0 0)): Dark Gray text (oklch(0.2 0.01 240)) - Ratio 15.8:1 ✓
  - Primary (Deep Blue oklch(0.45 0.15 240)): White text (oklch(1 0 0)) - Ratio 8.2:1 ✓
  - Accent (Warm Orange oklch(0.7 0.15 50)): White text (oklch(1 0 0)) - Ratio 4.8:1 ✓
  - Card (Light Gray oklch(0.98 0.005 240)): Dark Gray text (oklch(0.2 0.01 240)) - Ratio 14.1:1 ✓

## Font Selection
Clean, modern sans-serif typography that balances readability for product information with friendliness for chat conversations - Inter provides excellent legibility and contemporary feel.

- **Typographic Hierarchy**:
  - H1 (App Title): Inter Bold/32px/tight letter spacing
  - H2 (Panel Headings): Inter Semibold/24px/normal spacing  
  - H3 (Product Titles): Inter Medium/18px/normal spacing
  - Body (Product Details): Inter Regular/16px/relaxed line height
  - Small (Prices/Meta): Inter Medium/14px/tight line height
  - Chat Messages: Inter Regular/15px/comfortable line height

## Animations
Subtle and purposeful animations that guide attention and provide feedback without feeling busy - focus on micro-interactions that enhance the shopping experience.

- **Purposeful Meaning**: Smooth transitions between panels reinforce the connection between browsing and chat, while hover effects on products create tactile shopping feel
- **Hierarchy of Movement**: Product cards have gentle hover lift, chat messages slide in naturally, filter changes animate smoothly to maintain context

## Component Selection
- **Components**: Cards for products, Dialog for mobile chat, Input/Button for search/chat, Badge for cart count, Avatar for chat assistant, Separator between panels, Skeleton for loading states
- **Customizations**: Custom product grid layout, chat bubble styling, mobile panel transitions, floating action button for mobile chat access
- **States**: Products (loading/loaded/error), chat (typing/sent/received), cart (empty/filled), panels (expanded/collapsed on mobile)
- **Icon Selection**: Shopping cart, search, filter, send arrow, attachment, online indicator, close X, hamburger menu
- **Spacing**: Consistent 4/8/16/24px spacing using Tailwind scale, generous padding in chat for comfortable conversation
- **Mobile**: Stacked layout with sticky chat toggle, swipe gestures for panel navigation, touch-optimized button sizes, collapsible product filters