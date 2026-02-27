import { Order, OrderItem, Product } from './types';

export function parseOrdersFromText(text: string): { orders: Order[], introText: string } {
  try {
    const orderBoundaries = findOrderBoundaries(text);
    
    if (orderBoundaries.length === 0) {
      return { orders: [], introText: text };
    }
    
    const introText = text.substring(0, orderBoundaries[0].start).trim();
    
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
    const formats = [
      /-\s*([^:]+):\s*(\d+)\s*x\s*\$([0-9,]+\.?\d*)\s*\(Total:\s*\$([0-9,]+\.?\d*)\)/,
      /-\s*([^(]+)\s*\(Quantity:\s*(\d+)\)\s*-\s*Total:\s*\$([0-9,]+\.?\d*)/,
      /-\s*([^(]+)\s*\((\d+)\)\s*-\s*\$([0-9,]+\.?\d*)/,
      /-\s*([^-]+)\s*-\s*(\d+)\s*x\s*\$([0-9,]+\.?\d*)\s*=\s*\$([0-9,]+\.?\d*)/
    ];
    
    for (const format of formats) {
      const match = line.match(format);
      if (match) {
        const name = match[1].trim();
        const quantity = parseInt(match[2]);
        
        if (format === formats[0] || format === formats[3]) {
          const unitPrice = parseFloat(match[3].replace(',', ''));
          const totalPrice = parseFloat(match[4].replace(',', ''));
          return { name, quantity, unitPrice, totalPrice };
        } else {
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
  
  const parts = text.split(/(?=\d+\.\s*\*\*[^*]+\*\*)/);
  
  let introText = '';
  let outroText = '';
  
  if (parts.length > 0) {
    introText = parts[0].trim();
    
    introText = introText.replace(/^###\s*[^\n]*\n?/gm, '').trim();
    
    const lastProductIndex = text.lastIndexOf('![');
    if (lastProductIndex !== -1) {
      const afterLastProduct = text.substring(lastProductIndex);
      const afterMatch = afterLastProduct.match(/!\[[^\]]*\]\([^)]*\)\.?\s*([\s\S]*?)$/);
      if (afterMatch && afterMatch[1].trim()) {
        const afterText = afterMatch[1].trim();
        if (!afterText.match(/^\d+\.\s*\*\*/)) {
          outroText = afterText;
        }
      }
    }
  }
  
  for (let i = 1; i < parts.length; i++) {
    const product = parseProductSection(parts[i]);
    if (product) {
      products.push(product);
    }
  }
  
  const hasImageOrLink = parts.length === 1 && (parts[0].includes('![') || /\[[^\]]+\]\([^)]+\.(jpg|jpeg|png|gif|webp|svg)/i.test(parts[0]));
  if (hasImageOrLink) {
    const product = parseProductSection(parts[0]);
    if (product) {
      products.push(product);
      const escapedTitle = product.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const productPattern = new RegExp(`.*?${escapedTitle}.*?(?:!\\[.*?\\]|\\[.*?\\])\\(.*?\\).*?`, 's');
      introText = introText.replace(productPattern, '').trim();
    }
  }
  
  return { products, introText, outroText };
}

function parseProductSection(section: string): Product | null {
  try {
    let nameMatch = section.match(/\d+\.\s*\*\*([^*]+)\*\*/);
    let title = '';
    
    if (nameMatch) {
      title = nameMatch[1].trim().replace(/:$/, '');
    } else {
      const imageAltMatch = section.match(/!\[([^\]]+)\]\([^)]+\)/);
      if (imageAltMatch && imageAltMatch[1]) {
        title = imageAltMatch[1].trim();
      } else {
        const quotedNameMatch = section.match(/^"([^"]+)"|^\*\*([^*]+)\*\*/);
        if (quotedNameMatch) {
          title = (quotedNameMatch[1] || quotedNameMatch[2] || '').trim();
        }
      }
    }
    
    if (!title) {
      const quotedBeforeDescribed = section.match(/^"([^"]+)"\s+is\s+(?:described\s+as|a\s+)/i);
      if (quotedBeforeDescribed) {
        title = quotedBeforeDescribed[1].trim();
      } else {
        const firstLineMatch = section.match(/^([A-Z][a-zA-Z\s]+?)\s+is\s+(?:described\s+as|a\s+)/i);
        if (firstLineMatch) {
          title = firstLineMatch[1].trim();
        } else {
          const linkContextMatch = section.match(/(?:image|view|see|shade)\s+of\s+([A-Z][a-zA-Z\s]+?)\s+\[/i);
          if (linkContextMatch) {
            title = linkContextMatch[1].trim();
          }
        }
      }
    }
    
    if (!title) return null;
    
    const priceMatch = section.match(/\*\*Price:\*\*\s*\$([0-9,]+\.?\d*)/);
    const price = priceMatch ? parseFloat(priceMatch[1].replace(',', '')) : 59.50;
    
    const originalPriceMatch = section.match(/Originally \$([0-9,]+\.?\d*)/);
    const originalPrice = originalPriceMatch ? parseFloat(originalPriceMatch[1].replace(',', '')) : undefined;
    
    const ratingMatch = section.match(/\*\*Rating:\*\*\s*([0-9.]+)/);
    const rating = ratingMatch ? parseFloat(ratingMatch[1]) : 4.5;
    
    const reviewMatch = section.match(/\((\d+)\s+Reviews\)/);
    const reviewCount = reviewMatch ? parseInt(reviewMatch[1]) : 0;
    
    let description = '';
    
    const descMatch = section.match(/\*\*Description:\*\*\s*([^\n]+)/);
    if (descMatch) {
      description = descMatch[1].trim();
    }
    
    if (!description) {
      const describedMatch = section.match(/"([^"]+)"\s+is\s+described\s+as\s+([^!]+?)(?=If\s+you're|!\[|$)/is);
      if (describedMatch) {
        description = describedMatch[2].trim();
      }
    }
    
    if (!description) {
      const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const isAMatch = section.match(new RegExp(`"${escapedTitle}"\\s+is\\s+(?:described\\s+as\\s+|a\\s+)(.+?)(?=If\\s+you're|!\\[|\\[[^\\]]+\\]\\(|$)`, 'is'));
      if (isAMatch) {
        description = isAMatch[1].trim();
      } else {
        const isAMatch2 = section.match(new RegExp(`${escapedTitle}\\s+is\\s+(?:described\\s+as\\s+|a\\s+)(.+?)(?=If\\s+you're|!\\[|\\[[^\\]]+\\]\\(|$)`, 'is'));
        if (isAMatch2) {
          description = isAMatch2[1].trim();
        }
      }
    }
    
    if (!description) {
      const beforeImageMatch = section.match(/^([^!\[\]]+?)(?=!\[|\[|$)/s);
      if (beforeImageMatch) {
        const textBeforeImage = beforeImageMatch[1].trim();
        const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let cleanedText = textBeforeImage
          .replace(new RegExp(`^"${escapedTitle}"\\s*`, 'i'), '')
          .replace(new RegExp(`^${escapedTitle}\\s*`, 'i'), '')
          .replace(/^is\s+(?:described\s+as|a)\s+/i, '')
          .trim();
        cleanedText = cleanedText.replace(/\s*If\s+you're\s+(?:interested|seeing)[^.]*\./i, '').trim();
        if (cleanedText && cleanedText.length > 10) {
          description = cleanedText;
        }
      }
    }
    
    if (!description) {
      const altDescMatch = section.match(/\*\*[^*]+\*\*:\s*([^\n!]+)/);
      if (altDescMatch) {
        description = altDescMatch[1].trim();
      }
    }
    
    const stockMatch = section.match(/\*\*In Stock:\*\*\s*(Yes|No)/);
    const inStock = stockMatch ? stockMatch[1] === 'Yes' : true;
    
    let image = '';
    const imageMatch = section.match(/!\[.*?\]\(([^)]+)\)/);
    if (imageMatch) {
      image = imageMatch[1];
    } else {
      const linkMatch = section.match(/\[[^\]]+\]\(([^)]+)\)/);
      if (linkMatch) {
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
  
  const hasImageOrLink = /!\[[^\]]+\]\([^)]+\)/.test(text) || /\[[^\]]+\]\([^)]+\.(jpg|jpeg|png|gif|webp|svg)/i.test(text);
  const hasImageWithDescription = hasImageOrLink && 
    (/\w+\s+is\s+(?:described\s+as|a\s+)/i.test(text) || 
     /"[^"]+"\s+is\s+(?:described\s+as|a\s+)/i.test(text));
  
  if (hasPriceAndRating || hasProductFormat || hasImageWithDescription) {
    return 'products';
  }
  
  return 'text';
}
