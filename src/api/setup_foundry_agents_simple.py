#!/usr/bin/env python3
"""
Simplified Azure AI Foundry Agent Setup
Uses existing Semantic Kernel plugins - no tool definitions in Foundry
"""
import argparse
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.agent_instructions import (
    ORCHESTRATOR_INSTRUCTIONS,
    ORDER_STATUS_INSTRUCTIONS,
)

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
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Get complete order details by order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to retrieve"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "List recent orders for a customer",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "limit": {"type": "integer", "description": "Max orders (default 10)", "default": 10}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Get just the status of an order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund request",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["order_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_return",
            "description": "Process a return request",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["order_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_returnable_orders",
            "description": "Get orders within 30-day return window",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders_by_date_range",
            "description": "Get orders from last N days",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "days": {"type": "integer", "default": 180}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_if_returnable",
            "description": "Check if order is within return window",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    }
]

def create_agents(
    foundry_endpoint: str,
    model_name: str = "gpt-4o-mini",
    solution_name: str = "ecommerce"
):
    print(f"🚀 Creating Azure AI Foundry agents (Simplified - using SK plugins)")
    print(f"📍 Endpoint: {foundry_endpoint}")
    print(f"🤖 Model: {model_name}\n")
    
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=foundry_endpoint, credential=credential)  # type: ignore
    
    with project_client:
        agents_client = project_client.agents
        
        print("1️⃣  Creating Orchestrator Agent...")
        orchestrator = agents_client.create_agent(
            model=model_name,
            name=f"OrchestratorAgent-{solution_name}",
            instructions=ORCHESTRATOR_INSTRUCTIONS,
        )
        print(f"   ✅ {orchestrator.name} - ID: {orchestrator.id}\n")
        
        print("2️⃣  Creating Product Lookup Agent (uses existing Semantic Kernel plugins)...")
        product = agents_client.create_agent(
            model=model_name,
            name=f"ProductLookupAgent-{solution_name}",
            instructions=SIMPLE_PRODUCT_INSTRUCTIONS,
        )
        print(f"   ✅ {product.name} - ID: {product.id}")
        print(f"   📝 No tools defined - will use ProductPlugin from Semantic Kernel\n")
        
        print("3️⃣  Creating Order Status Agent (with custom functions)...")
        order = agents_client.create_agent(
            model=model_name,
            name=f"OrderStatusAgent-{solution_name}",
            instructions=ORDER_STATUS_INSTRUCTIONS,
            tools=ORDER_TOOLS
        )
        print(f"   ✅ {order.name} - ID: {order.id}")
        print(f"   🔧 {len(ORDER_TOOLS)} order functions registered\n")
        
        print("4️⃣  Creating Knowledge Agent (uses existing Semantic Kernel plugins)...")
        knowledge = agents_client.create_agent(
            model=model_name,
            name=f"KnowledgeAgent-{solution_name}",
            instructions=SIMPLE_KNOWLEDGE_INSTRUCTIONS,
        )
        print(f"   ✅ {knowledge.name} - ID: {knowledge.id}")
        print(f"   📝 No tools defined - will use ReferencePlugin from Semantic Kernel\n")
        
        print("=" * 70)
        print("🎉 All agents created successfully!")
        print("=" * 70)
        print("\n📋 Copy these to your .env file:\n")
        print(f"AZURE_FOUNDRY_ENDPOINT={foundry_endpoint}")
        print(f"FOUNDRY_ORCHESTRATOR_AGENT_ID={orchestrator.id}")
        print(f"FOUNDRY_PRODUCT_AGENT_ID={product.id}")
        print(f"FOUNDRY_ORDER_AGENT_ID={order.id}")
        print(f"FOUNDRY_KNOWLEDGE_AGENT_ID={knowledge.id}")
        print(f"USE_FOUNDRY_AGENTS=true")
        print("\n" + "=" * 70)
        print("\n💡 HOW THIS WORKS:")
        print("   • ProductLookupAgent: No tools in Foundry → uses ProductPlugin in Semantic Kernel")
        print("   • KnowledgeAgent: No tools in Foundry → uses ReferencePlugin in Semantic Kernel")
        print("   • OrderStatusAgent: Tools in Foundry → uses OrdersPlugin in Semantic Kernel")
        print("\n   The plugins connect to:")
        print("   - ProductPlugin → Azure AI Search 'products' index + Cosmos DB")
        print("   - ReferencePlugin → Azure AI Search 'reference-docs' index")
        print("   - OrdersPlugin → Cosmos DB orders")
        print("\n" + "=" * 70)
        
        return {
            "orchestrator": orchestrator.id,
            "product": product.id,
            "order": order.id,
            "knowledge": knowledge.id,
        }

def main():
    parser = argparse.ArgumentParser(description="Create simplified Azure AI Foundry agents")
    parser.add_argument("--foundry-endpoint", required=True, help="Azure AI Foundry endpoint")
    parser.add_argument("--model-name", default="gpt-4o-mini", help="Model name (default: gpt-4o-mini)")
    parser.add_argument("--solution-name", default="ecommerce", help="Solution prefix (default: ecommerce)")
    
    args = parser.parse_args()
    
    try:
        create_agents(
            foundry_endpoint=args.foundry_endpoint,
            model_name=args.model_name,
            solution_name=args.solution_name,
        )
        
        print("\n✅ Setup complete! Next steps:")
        print("1. Copy the environment variables above to your .env file")
        print("2. Ensure your Azure AI Search indexes are populated:")
        print("   cd infrastructure")
        print("   python setup-product-search-index.py")
        print("   python setup-search-index.py")
        print("3. Restart your backend: uvicorn app.main:app --reload")
        print("4. Test with: 'I'm looking for a cool, blue-toned paint'")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: az login")
        print("2. Verify Foundry endpoint is correct")
        print("3. Check permissions to create agents")
        sys.exit(1)

if __name__ == "__main__":
    main()

