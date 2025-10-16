import { Order, OrderItem, Product } from './types';

export function parseOrdersFromText(text: string): { orders: Order[], introText: string } {
  try {
    // Find all order boundaries (numbered orders)
    const orderBoundaries = findOrderBoundaries(text);
    
    if (orderBoundaries.length === 0) {
      return { orders: [], introText: text };
    }
    
    // Extract intro text (everything before first order)
    const introText = text.substring(0, orderBoundaries[0].start).trim();
    
    // Parse each order
    const orders: Order[] = [];
    for (let i = 0; i < orderBoundaries.length; i++) {
      const boundary = orderBoundaries[i];
      const nextBoundary = orderBoundaries[i + 1];
      const orderEnd = nextBoundary ? nextBoundary.start : text.length;
      
      const orderText = text.substring(boundary.start, orderEnd);
      const order = extractOrderFields(orderText);
      
      if (order) {
        orders.push(order);
      }
    }
    
    return { orders, introText };
  } catch (error) {
    console.error('Error parsing orders:', error);
    return { orders: [], introText: text };
  }
}

function findOrderBoundaries(text: string): Array<{ start: number, number: number }> {
  const boundaries: Array<{ start: number, number: number }> = [];
  
  // Look for patterns like "1. **Order Number:**" or "1. Order Number:"
  const patterns = [
    /(\d+)\.\s*\*\*Order Number\*\*:/g,
    /(\d+)\.\s*Order Number:/g,
    /(\d+)\.\s*\*\*Order\*\*:/g
  ];
  
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      boundaries.push({
        start: match.index,
        number: parseInt(match[1])
      });
    }
  }
  
  // Sort by position in text
  return boundaries.sort((a, b) => a.start - b.start);
}

function extractOrderFields(orderText: string): Order | null {
  try {
    const orderNumber = extractField(orderText, 'Order Number');
    if (!orderNumber) return null;
    
    const status = extractField(orderText, 'Status') || 'Unknown';
    const orderDate = extractField(orderText, 'Order Date') || '';
    const subtotal = parsePrice(extractField(orderText, 'Subtotal'));
    const tax = parsePrice(extractField(orderText, 'Tax'));
    const total = parsePrice(extractField(orderText, 'Total'));
    const shippingAddress = extractMultiLineField(orderText, 'Shipping Address');
    
    const items = extractOrderItems(orderText);
    
    return normalizeOrderData({
      orderNumber,
      status,
      orderDate,
      items,
      subtotal,
      tax,
      total,
      shippingAddress
    });
  } catch (error) {
    console.error('Error extracting order fields:', error);
    return null;
  }
}

function extractField(text: string, fieldName: string): string | null {
  const patterns = [
    `\\*\\*${fieldName}\\*\\*:\\s*([^\\n]+)`,
    `${fieldName}:\\s*([^\\n]+)`,
    `\\*\\*${fieldName}\\*\\*\\s*([^\\n]+)`,
    `${fieldName}\\s*([^\\n]+)`
  ];
  
  for (const pattern of patterns) {
    const match = text.match(new RegExp(pattern, 'i'));
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  return null;
}

function extractMultiLineField(text: string, fieldName: string): string {
  const patterns = [
    `\\*\\*${fieldName}\\*\\*:\\s*([\\s\\S]*?)(?=\\*\\*[A-Za-z]+\\*\\*:|$)`,
    `${fieldName}:\\s*([\\s\\S]*?)(?=\\*\\*[A-Za-z]+\\*\\*:|$)`
  ];
  
  for (const pattern of patterns) {
    const match = text.match(new RegExp(pattern, 'i'));
    if (match && match[1]) {
      return match[1].trim().replace(/\s+/g, ' ');
    }
  }
  
  return '';
}

function extractOrderItems(orderText: string): OrderItem[] {
  const items: OrderItem[] = [];
  
  // Find the items section
  const itemsMatch = orderText.match(/\*\*Items\*\*:\s*([\s\S]*?)(?=\*\*(?:Subtotal|Total)\*\*|$)/i);
  if (!itemsMatch) return items;
  
  const itemsText = itemsMatch[1];
  const itemLines = itemsText.split('\n').filter(line => line.trim().startsWith('-'));
  
  for (const line of itemLines) {
    const item = parseOrderItem(line);
    if (item) items.push(item);
  }
  
  return items;
}

function parseOrderItem(line: string): OrderItem | null {
  try {
    // Try multiple item formats
    const formats = [
      // Format 1: "- Olive Stone: 3 x $59.50 (Total: $178.50)"
      /-\s*([^:]+):\s*(\d+)\s*x\s*\$([0-9,]+\.?\d*)\s*\(Total:\s*\$([0-9,]+\.?\d*)\)/,
      // Format 2: "- Olive Stone (Quantity: 3) - Total: $178.50"
      /-\s*([^(]+)\s*\(Quantity:\s*(\d+)\)\s*-\s*Total:\s*\$([0-9,]+\.?\d*)/,
      // Format 3: "- Olive Stone (3) - $178.50"
      /-\s*([^(]+)\s*\((\d+)\)\s*-\s*\$([0-9,]+\.?\d*)/,
      // Format 4: "- Olive Stone - 3 x $59.50 = $178.50"
      /-\s*([^-]+)\s*-\s*(\d+)\s*x\s*\$([0-9,]+\.?\d*)\s*=\s*\$([0-9,]+\.?\d*)/
    ];
    
    for (const format of formats) {
      const match = line.match(format);
      if (match) {
        const name = match[1].trim();
        const quantity = parseInt(match[2]);
        
        if (format === formats[0] || format === formats[3]) {
          // Has both unit price and total price
          const unitPrice = parseFloat(match[3].replace(',', ''));
          const totalPrice = parseFloat(match[4].replace(',', ''));
          return { name, quantity, unitPrice, totalPrice };
        } else {
          // Only has total price, calculate unit price
          const totalPrice = parseFloat(match[3].replace(',', ''));
          const unitPrice = totalPrice / quantity;
          return { name, quantity, unitPrice, totalPrice };
        }
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error parsing order item:', error);
    return null;
  }
}

function parsePrice(priceText: string | null): number {
  if (!priceText) return 0;
  
  const match = priceText.match(/\$?([0-9,]+\.?\d*)/);
  return match ? parseFloat(match[1].replace(',', '')) : 0;
}

function normalizeOrderData(order: Partial<Order>): Order {
  return {
    orderNumber: order.orderNumber || '',
    status: order.status || 'Unknown',
    orderDate: order.orderDate || '',
    items: order.items || [],
    subtotal: order.subtotal || 0,
    tax: order.tax || 0,
    total: order.total || 0,
    shippingAddress: order.shippingAddress || ''
  };
}



export function parseProductsFromText(text: string): { products: Product[], introText: string } {
  const products: Product[] = [];
  
  // Extract all text that's not part of numbered product listings
  // Split the text into parts
  const parts = text.split(/(?=\d+\.\s*\*\*[^*]+\*\*)/);
  
  let introText = '';
  if (parts.length > 0) {
    // First part contains the intro text
    introText = parts[0].trim();
    
    // Remove markdown headers
    introText = introText.replace(/^###\s*[^\n]*\n?/gm, '').trim();
    
    // Find text after the last product
    const lastProductIndex = text.lastIndexOf('![');
    if (lastProductIndex !== -1) {
      const afterLastProduct = text.substring(lastProductIndex);
      const afterMatch = afterLastProduct.match(/!\[[^\]]*\]\([^)]*\)\s*([\s\S]*?)(?=\d+\.\s*\*\*[^*]+\*\*|$)/);
      if (afterMatch && afterMatch[1].trim()) {
        const afterText = afterMatch[1].trim();
        if (!afterText.match(/^\d+\./)) {
          introText = introText + (introText ? '\n\n' : '') + afterText;
        }
      }
    }
  }
  
  // Parse products from all parts except the first
  for (let i = 1; i < parts.length; i++) {
    const product = parseProductSection(parts[i]);
    if (product) {
      products.push(product);
    }
  }
  
  return { products, introText };
}

function parseProductSection(section: string): Product | null {
  try {
    // Extract product name
    const nameMatch = section.match(/\d+\.\s*\*\*([^*]+)\*\*/);
    if (!nameMatch) return null;
    
    const title = nameMatch[1].trim();
    
    // Extract price
    const priceMatch = section.match(/\*\*Price:\*\*\s*\$([0-9,]+\.?\d*)/);
    const price = priceMatch ? parseFloat(priceMatch[1].replace(',', '')) : 0;
    
    // Extract original price
    const originalPriceMatch = section.match(/Originally \$([0-9,]+\.?\d*)/);
    const originalPrice = originalPriceMatch ? parseFloat(originalPriceMatch[1].replace(',', '')) : undefined;
    
    // Extract rating
    const ratingMatch = section.match(/\*\*Rating:\*\*\s*([0-9.]+)/);
    const rating = ratingMatch ? parseFloat(ratingMatch[1]) : 4.0;
    
    // Extract review count
    const reviewMatch = section.match(/\((\d+)\s+Reviews\)/);
    const reviewCount = reviewMatch ? parseInt(reviewMatch[1]) : 0;
    
    // Extract description
    const descMatch = section.match(/\*\*Description:\*\*\s*([^\n]+)/);
    const description = descMatch ? descMatch[1].trim() : '';
    
    // Extract in stock status
    const stockMatch = section.match(/\*\*In Stock:\*\*\s*(Yes|No)/);
    const inStock = stockMatch ? stockMatch[1] === 'Yes' : true;
    
    // Extract image URL
    const imageMatch = section.match(/!\[.*?\]\(([^)]+)\)/);
    const image = imageMatch ? imageMatch[1] : '';
    
    return {
      id: `product-${title.toLowerCase().replace(/\s+/g, '-')}`,
      title,
      price,
      originalPrice,
      rating,
      reviewCount,
      image,
      category: 'Paint Shades',
      inStock,
      description
    };
  } catch (error) {
    console.error('Error parsing product section:', error);
    return null;
  }
}

export function detectContentType(text: string): 'orders' | 'products' | 'text' {
  // Check for order indicators
  const hasOrderNumber = text.includes('**Order Number:**') || text.includes('Order Number:');
  const hasOrderKeywords = text.includes('recent orders') || text.includes('past orders') || text.includes('your orders');
  const hasOrderStructure = text.includes('**Status:**') || text.includes('**Items:**') || text.includes('**Subtotal:**');
  
  if (hasOrderNumber || (hasOrderKeywords && hasOrderStructure)) {
    return 'orders';
  }
  
  if (text.includes('**Price:**') && text.includes('**Rating:**')) {
    return 'products';
  }
  
  return 'text';
}
