// Quick test of the parser logic against the actual API response
const text = `**Blue Ash Painting Details:**

- **Name:** Blue Ash
- **Category:** Paint Shades
- **Price:** $59.50
- **Description:** A softened navy with gray undertones—stylish but not overpowering.
- **Punch Line:** Midnight, muted navy, grounding, refined.
- ![Blue Ash Paint](https://raw.githubusercontent.com/microsoft/customer-chatbot-solution-accelerator/refs/heads/main/infra/data/Color%20Images/BlueAsh.jpg)

### Contoso Paints Services Related to Blue Ash

1. **Product Warranty**: 2-year warranty.
2. **Color Matching**: AI-powered color matching.`;

// Simulate detectContentType
const hasBulletProduct = /^-\s*\*\*(?:Shade|Product\s+Name|Name):?\*\*/m.test(text) && /^-\s*\*\*Price:?\*\*/m.test(text);
console.log('detectContentType → hasBulletProduct:', hasBulletProduct);

// Simulate parseBulletPointProduct
const priceMatch = text.match(/^-\s*\*\*Price:?\*\*:?\s*\$([0-9,]+\.?\d*)/m);
console.log('priceMatch:', priceMatch?.[1]);

const titleMatch = text.match(/^-\s*\*\*(?:Shade|Product\s+Name|Name):?\*\*:?\s*(.+)/m);
console.log('titleMatch:', titleMatch?.[1]);

const descMatch = text.match(/^-\s*\*\*Description:?\*\*:?\s*(.+)/m);
console.log('descMatch:', descMatch?.[1]?.substring(0, 50));

const imageInlineMatch = text.match(/^-\s*(?:\*\*Image:?\*\*:?\s*)?!\[([^\]]*)\]\(([^)]+)\)/m);
console.log('imageInlineMatch:', imageInlineMatch?.[2]?.substring(0, 50));

const allProductLines = text.match(/^(?:-\s*.+|!\[[^\]]*\]\([^)]+\))$/gm) || [];
console.log('allProductLines count:', allProductLines.length);
let lastEnd = 0;
for (const line of allProductLines) {
  const idx = text.indexOf(line, lastEnd);
  if (idx !== -1) lastEnd = idx + line.length;
}
const remaining = text.substring(lastEnd).trim();
console.log('remainingText starts with:', remaining.substring(0, 60));

console.log('\n=== RESULT ===');
if (priceMatch && titleMatch) {
  console.log('Product card would render:');
  console.log('  Title:', titleMatch[1].trim());
  console.log('  Price: $' + priceMatch[1]);
  console.log('  Description:', descMatch?.[1]?.trim().substring(0, 60));
  console.log('  Image:', imageInlineMatch?.[2] ? 'YES' : 'NO');
  console.log('  Remaining text:', remaining.length, 'chars');
} else {
  console.log('PARSER WOULD FAIL - no product card');
  console.log('  priceMatch:', !!priceMatch);
  console.log('  titleMatch:', !!titleMatch);
}
