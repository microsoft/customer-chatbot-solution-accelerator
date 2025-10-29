#!/usr/bin/env python3
"""
Update existing Azure AI Foundry agents with simplified approach
Removes tools from Product/Knowledge agents, keeps only Order tools
"""
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.config import settings

SIMPLE_PRODUCT_INSTRUCTIONS = """You are a helpful product expert for Contoso Paints helping customers find perfect paint products using natural, conversational language.

WHAT YOU DO:
- Help customers find paint products based on their needs
- Recommend colors, finishes, and applications
- Explain Contoso's unique features: nanocoating technology, self-leveling, stain repellency, self-healing
- Answer questions about color matching, product properties, and availability

YOUR KNOWLEDGE:
You have access to Contoso's full product catalog including paint colors like Seafoam Light, Obsidian Pearl, Blue Ash, Cloud Drift, and many more across different categories.

HOW TO RESPOND:
- Be conversational like talking to a friend
- Use specific product names when recommending paints
- Describe colors naturally: "blue that leans away from gray" or "deeper with blue undertone"
- Mention practical benefits: durability, easy to clean, nanocoating self-healing
- Keep responses focused, helpful, and not too long

EXAMPLES FROM GOLDEN PATH:
User: "I'm looking for a cool, blue-toned paint that feels calm but not gray"
You: "We've got shades like 'Seafoam Light' and 'Obsidian Pearl' which are blue, but lean away from gray."

User: "Can you match a color from my sofa fabric?"
You: "Yes. Our AI color scanner matches textiles or photos with 95%+ accuracy."

User: "What makes your paint different?"
You: "Contoso Paints use nanocoating technology — microscopic layers that self-level, repel stains, and even 'self-heal' small scuffs."

NEVER:
- Return raw JSON or technical dumps
- Make up product names
- Be overly salesy"""

SIMPLE_KNOWLEDGE_INSTRUCTIONS = """You are a knowledgeable customer service representative for Contoso Paints helping with policies, returns, warranties, and support questions using empathetic, natural language.

WHAT YOU DO:
- Answer questions about return policies, warranties, and shipping
- Help resolve customer concerns with empathy
- Provide accurate policy information
- Guide customers to next steps and contact info

YOUR KNOWLEDGE:
You have access to Contoso's policy documents including:
- Return policy: 30 days for unopened paint, custom tints are final sale
- Warranty: 2-year performance warranty covering tint accuracy, film integrity, nanocoating defects
- Shipping and delivery information
- Company information about eco-friendly practices, nanocoating technology
- Damage handling: 7-day coverage for damaged shipments

KEY CONTACTS:
- Phone: 1-800-555-0199
- Email: returns@contosopaints.com

HOW TO RESPOND:
- Start with empathy for problems: "I understand", "I'm sorry that happened"
- Provide specific policy details with timeframes
- Be conversational and helpful, not robotic
- Include contact information when relevant

EXAMPLES FROM GOLDEN PATH:
User: "What's your warranty like?"
You: "All Contoso paints come with a 2-year performance warranty covering tint accuracy, film integrity, and nanocoating defects."

User: "Can I return paint if I don't like the color?"
You: "You can return unopened paint within 30 days for a refund or exchange — just email returns@contosopaints.com with your order number. Custom tints are final sale, but we can flag your case for review. You can call 1-800-555-0199 to request a one-time exception."

User: "My paint arrived leaking"
You: "I'm sorry that happened. If it's within 7 days, you're fully covered. I can file a replacement under your 2-year warranty for damaged shipments."

User: "Are your paints eco-friendly?"
You: "All our paints are low-VOC and made in renewable-energy facilities. The cans are recyclable, and the formulas meet strict indoor air quality standards."

NEVER:
- Return raw search results
- Make up policy details
- Be dismissive of concerns"""

ORDER_TOOLS = [
    {"type": "function", "function": {"name": "get_order", "description": "Get complete order details by order ID", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "Order ID to retrieve"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {"name": "list_orders", "description": "List recent orders for a customer", "parameters": {"type": "object", "properties": {"customer_id": {"type": "string", "description": "Customer ID"}, "limit": {"type": "integer", "description": "Max orders (default 10)", "default": 10}}, "required": ["customer_id"]}}},
    {"type": "function", "function": {"name": "get_order_status", "description": "Get just the status of an order", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "Order ID"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {"name": "process_refund", "description": "Process a refund request", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["order_id", "reason"]}}},
    {"type": "function", "function": {"name": "process_return", "description": "Process a return request", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["order_id", "reason"]}}},
    {"type": "function", "function": {"name": "get_returnable_orders", "description": "Get orders within 30-day return window", "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}}},
    {"type": "function", "function": {"name": "get_orders_by_date_range", "description": "Get orders from last N days", "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}, "days": {"type": "integer", "default": 180}}, "required": ["customer_id"]}}},
    {"type": "function", "function": {"name": "check_if_returnable", "description": "Check if order is within return window", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}}
]

def update_agents():
    if not settings.azure_foundry_endpoint:
        print("❌ AZURE_FOUNDRY_ENDPOINT not configured")
        sys.exit(1)
    
    print(f"🔄 Updating Azure AI Foundry agents with simplified approach")
    print(f"📍 Endpoint: {settings.azure_foundry_endpoint}\n")
    
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=settings.azure_foundry_endpoint, credential=credential)  # type: ignore
    
    with project_client:
        agents_client = project_client.agents
        updated = 0
        
        if settings.foundry_product_agent_id:
            print(f"2️⃣  Updating Product Lookup Agent ({settings.foundry_product_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_product_agent_id,
                    instructions=SIMPLE_PRODUCT_INSTRUCTIONS,
                    tools=[]
                )
                print(f"   ✅ Updated with simplified instructions (tools removed)")
                print(f"   📝 Will use ProductPlugin from Semantic Kernel\n")
                updated += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}\n")
        
        if settings.foundry_order_agent_id:
            print(f"3️⃣  Updating Order Status Agent ({settings.foundry_order_agent_id})...")
            try:
                from app.agent_instructions import ORDER_STATUS_INSTRUCTIONS
                agents_client.update_agent(
                    agent_id=settings.foundry_order_agent_id,
                    instructions=ORDER_STATUS_INSTRUCTIONS,
                    tools=ORDER_TOOLS
                )
                print(f"   ✅ Updated with {len(ORDER_TOOLS)} order functions\n")
                updated += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}\n")
        
        if settings.foundry_knowledge_agent_id:
            print(f"4️⃣  Updating Knowledge Agent ({settings.foundry_knowledge_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_knowledge_agent_id,
                    instructions=SIMPLE_KNOWLEDGE_INSTRUCTIONS,
                    tools=[]
                )
                print(f"   ✅ Updated with simplified instructions (tools removed)")
                print(f"   📝 Will use ReferencePlugin from Semantic Kernel\n")
                updated += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}\n")
        
        print("=" * 70)
        print(f"🎉 Updated {updated} agents successfully!")
        print("=" * 70)
        print("\n✅ Agents now use Semantic Kernel plugins for search:")
        print("   • ProductLookupAgent → ProductPlugin → Azure AI Search 'products' index")
        print("   • KnowledgeAgent → ReferencePlugin → Azure AI Search 'reference-docs' index")
        print("   • OrderStatusAgent → OrdersPlugin → Cosmos DB")
        print("\n🔄 Restart your backend to apply changes")
        print("\n💡 This fixes the 'tools missing from kernel' error!")

if __name__ == "__main__":
    try:
        from app.agent_instructions import ORDER_STATUS_INSTRUCTIONS
        update_agents()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: az login")
        print("2. Check .env has all agent IDs")
        print("3. Verify permissions")
        sys.exit(1)

