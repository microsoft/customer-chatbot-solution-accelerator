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



export function parseProductsFromText(text: string): { products: Product[], introText: string, outroText: string } {
  const products: Product[] = [];
  
  // Extract all text that's not part of numbered product listings
  // Split the text into parts
  const parts = text.split(/(?=\d+\.\s*\*\*[^*]+\*\*)/);
  
  let introText = '';
  let outroText = '';
  
  if (parts.length > 0) {
    // First part contains the intro text
    introText = parts[0].trim();
    
    // Remove markdown headers
    introText = introText.replace(/^###\s*[^\n]*\n?/gm, '').trim();
    
    // Find text after the last product
    const lastProductIndex = text.lastIndexOf('![');
    if (lastProductIndex !== -1) {
      const afterLastProduct = text.substring(lastProductIndex);
      const afterMatch = afterLastProduct.match(/!\[[^\]]*\]\([^)]*\)\.?\s*([\s\S]*?)$/);
      if (afterMatch && afterMatch[1].trim()) {
        const afterText = afterMatch[1].trim();
        // This is outro text, not intro text
        if (!afterText.match(/^\d+\.\s*\*\*/)) {
          outroText = afterText;
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
  
  // Also check for products with images/links but without numbered format
  // Look for patterns like: "Product Name" description... ![Product Name](url) or [text](url)
  const hasImageOrLink = parts.length === 1 && (parts[0].includes('![') || /\[[^\]]+\]\([^)]+\.(jpg|jpeg|png|gif|webp|svg)/i.test(parts[0]));
  if (hasImageOrLink) {
    // Try to parse the entire text as a product if it contains an image or image link
    const product = parseProductSection(parts[0]);
    if (product) {
      products.push(product);
      // Remove the product content from intro text
      const escapedTitle = product.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const productPattern = new RegExp(`.*?${escapedTitle}.*?(?:!\\[.*?\\]|\\[.*?\\])\\(.*?\\).*?`, 's');
      introText = introText.replace(productPattern, '').trim();
    }
  }
  
  return { products, introText, outroText };
}

function parseProductSection(section: string): Product | null {
  try {
    // Try numbered format first: "1. **Product Name**"
    let nameMatch = section.match(/\d+\.\s*\*\*([^*]+)\*\*/);
    let title = '';
    
    if (nameMatch) {
      title = nameMatch[1].trim().replace(/:$/, '');
    } else {
      // Try to extract product name from image alt text: ![Product Name](url)
      const imageAltMatch = section.match(/!\[([^\]]+)\]\([^)]+\)/);
      if (imageAltMatch && imageAltMatch[1]) {
        title = imageAltMatch[1].trim();
      } else {
        // Try to find product name at the start of the text (quoted or bold)
        const quotedNameMatch = section.match(/^"([^"]+)"|^\*\*([^*]+)\*\*/);
        if (quotedNameMatch) {
          title = (quotedNameMatch[1] || quotedNameMatch[2] || '').trim();
        }
      }
    }
    
    // If we still don't have a title, try to find it before the description
    if (!title) {
      // Look for quoted product name before "is described as" or "is a"
      const quotedBeforeDescribed = section.match(/^"([^"]+)"\s+is\s+(?:described\s+as|a\s+)/i);
      if (quotedBeforeDescribed) {
        title = quotedBeforeDescribed[1].trim();
      } else {
        // Look for a capitalized phrase at the start that might be the product name
        // Pattern: "Product Name is a..." or "Product Name is described as..."
        const firstLineMatch = section.match(/^([A-Z][a-zA-Z\s]+?)\s+is\s+(?:described\s+as|a\s+)/i);
        if (firstLineMatch) {
          title = firstLineMatch[1].trim();
        } else {
          // Try to extract from link context: "image of Product Name [here](url)"
          const linkContextMatch = section.match(/(?:image|view|see|shade)\s+of\s+([A-Z][a-zA-Z\s]+?)\s+\[/i);
          if (linkContextMatch) {
            title = linkContextMatch[1].trim();
          }
        }
      }
    }
    
    // If no title found, return null
    if (!title) return null;
    
    const priceMatch = section.match(/\*\*Price:\*\*\s*\$([0-9,]+\.?\d*)/);
    const price = priceMatch ? parseFloat(priceMatch[1].replace(',', '')) : 59.50;
    
    const originalPriceMatch = section.match(/Originally \$([0-9,]+\.?\d*)/);
    const originalPrice = originalPriceMatch ? parseFloat(originalPriceMatch[1].replace(',', '')) : undefined;
    
    const ratingMatch = section.match(/\*\*Rating:\*\*\s*([0-9.]+)/);
    const rating = ratingMatch ? parseFloat(ratingMatch[1]) : 4.5;
    
    const reviewMatch = section.match(/\((\d+)\s+Reviews\)/);
    const reviewCount = reviewMatch ? parseInt(reviewMatch[1]) : 0;
    
    // Try multiple description extraction methods
    let description = '';
    
    // Method 1: **Description:** format
    const descMatch = section.match(/\*\*Description:\*\*\s*([^\n]+)/);
    if (descMatch) {
      description = descMatch[1].trim();
    }
    
    // Method 2: "Product Name" is described as...
    if (!description) {
      const describedMatch = section.match(/"([^"]+)"\s+is\s+described\s+as\s+([^!]+?)(?=If\s+you're|!\[|$)/is);
      if (describedMatch) {
        description = describedMatch[2].trim();
      }
    }
    
    // Method 3: Product name followed by "is a" or description (with or without quotes)
    if (!description) {
      const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      // Try with quotes first
      const isAMatch = section.match(new RegExp(`"${escapedTitle}"\\s+is\\s+(?:described\\s+as\\s+|a\\s+)(.+?)(?=If\\s+you're|!\\[|\\[[^\\]]+\\]\\(|$)`, 'is'));
      if (isAMatch) {
        description = isAMatch[1].trim();
      } else {
        // Try without quotes - handle "is a" and "is described as"
        const isAMatch2 = section.match(new RegExp(`${escapedTitle}\\s+is\\s+(?:described\\s+as\\s+|a\\s+)(.+?)(?=If\\s+you're|!\\[|\\[[^\\]]+\\]\\(|$)`, 'is'));
        if (isAMatch2) {
          description = isAMatch2[1].trim();
        }
      }
    }
    
    // Method 4: Extract text before the image/link that describes the product
    if (!description) {
      const beforeImageMatch = section.match(/^([^!\[\]]+?)(?=!\[|\[|$)/s);
      if (beforeImageMatch) {
        const textBeforeImage = beforeImageMatch[1].trim();
        // Remove the product name if it's at the start, and clean up
        const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let cleanedText = textBeforeImage
          .replace(new RegExp(`^"${escapedTitle}"\\s*`, 'i'), '')
          .replace(new RegExp(`^${escapedTitle}\\s*`, 'i'), '')
          .replace(/^is\s+(?:described\s+as|a)\s+/i, '')
          .trim();
        // Remove "If you're interested..." type phrases
        cleanedText = cleanedText.replace(/\s*If\s+you're\s+(?:interested|seeing)[^.]*\./i, '').trim();
        if (cleanedText && cleanedText.length > 10) {
          description = cleanedText;
        }
      }
    }
    
    // Method 5: Fallback to any text after title markers
    if (!description) {
      const altDescMatch = section.match(/\*\*[^*]+\*\*:\s*([^\n!]+)/);
      if (altDescMatch) {
        description = altDescMatch[1].trim();
      }
    }
    
    const stockMatch = section.match(/\*\*In Stock:\*\*\s*(Yes|No)/);
    const inStock = stockMatch ? stockMatch[1] === 'Yes' : true;
    
    // Try to extract image URL from both image markdown ![alt](url) and regular links [text](url)
    let image = '';
    const imageMatch = section.match(/!\[.*?\]\(([^)]+)\)/);
    if (imageMatch) {
      image = imageMatch[1];
    } else {
      // Try regular markdown link - look for links that appear after "image of" or similar context
      const linkMatch = section.match(/\[[^\]]+\]\(([^)]+)\)/);
      if (linkMatch) {
        // Check if it's likely an image URL (jpg, jpeg, png, gif, webp, svg)
        const url = linkMatch[1];
        if (/\.(jpg|jpeg|png|gif|webp|svg)(\?|$)/i.test(url)) {
          image = url;
        }
      }
    }
    
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
    return null;
  }
}

export function detectContentType(text: string): 'orders' | 'products' | 'text' {
  const hasOrderNumber = text.includes('**Order Number:**') || text.includes('Order Number:');
  const hasOrderKeywords = text.includes('recent orders') || text.includes('past orders') || text.includes('your orders');
  const hasOrderStructure = text.includes('**Status:**') || text.includes('**Items:**') || text.includes('**Subtotal:**');
  
  if (hasOrderNumber || (hasOrderKeywords && hasOrderStructure)) {
    return 'orders';
  }
  
  const hasProductFormat = /\d+\.\s*\*\*[^*]+\*\*.*!\[/s.test(text);
  const hasPriceAndRating = text.includes('**Price:**') && text.includes('**Rating:**');
  
  // Also detect products with images/links and descriptive text (like "Product Name" is described as...)
  const hasImageOrLink = /!\[[^\]]+\]\([^)]+\)/.test(text) || /\[[^\]]+\]\([^)]+\.(jpg|jpeg|png|gif|webp|svg)/i.test(text);
  const hasImageWithDescription = hasImageOrLink && 
    (/\w+\s+is\s+(?:described\s+as|a\s+)/i.test(text) || 
     /"[^"]+"\s+is\s+(?:described\s+as|a\s+)/i.test(text));
  
  if (hasPriceAndRating || hasProductFormat || hasImageWithDescription) {
    return 'products';
  }
  
  return 'text';
}
