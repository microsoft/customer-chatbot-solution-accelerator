import argparse
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.agent_instructions import (
    ORCHESTRATOR_INSTRUCTIONS,
    PRODUCT_LOOKUP_INSTRUCTIONS,
    ORDER_STATUS_INSTRUCTIONS,
    KNOWLEDGE_AGENT_INSTRUCTIONS,
)

def create_agents(
    foundry_endpoint: str,
    model_name: str = "gpt-4o-mini",
    solution_name: str = "ecommerce"
):
    print(f"🚀 Creating Azure AI Foundry agents for {solution_name}")
    print(f"📍 Endpoint: {foundry_endpoint}")
    print(f"🤖 Model: {model_name}\n")
    
    credential = DefaultAzureCredential()
    
    project_client = AIProjectClient(
        endpoint=foundry_endpoint,
        credential=credential,
    )
    
    with project_client:
        agents_client = project_client.agents
        
        print("1️⃣  Creating Orchestrator Agent...")
        orchestrator_agent = agents_client.create_agent(
            model=model_name,
            name=f"OrchestratorAgent-{solution_name}",
            instructions=ORCHESTRATOR_INSTRUCTIONS,
        )
        print(f"   ✅ Created: {orchestrator_agent.name}")
        print(f"   ID: {orchestrator_agent.id}\n")
        
        print("2️⃣  Creating Product Lookup Agent...")
        product_agent = agents_client.create_agent(
            model=model_name,
            name=f"ProductLookupAgent-{solution_name}",
            instructions=PRODUCT_LOOKUP_INSTRUCTIONS,
        )
        print(f"   ✅ Created: {product_agent.name}")
        print(f"   ID: {product_agent.id}\n")
        
        print("3️⃣  Creating Order Status Agent...")
        order_agent = agents_client.create_agent(
            model=model_name,
            name=f"OrderStatusAgent-{solution_name}",
            instructions=ORDER_STATUS_INSTRUCTIONS,
        )
        print(f"   ✅ Created: {order_agent.name}")
        print(f"   ID: {order_agent.id}\n")
        
        print("4️⃣  Creating Knowledge Agent...")
        knowledge_agent = agents_client.create_agent(
            model=model_name,
            name=f"KnowledgeAgent-{solution_name}",
            instructions=KNOWLEDGE_AGENT_INSTRUCTIONS,
        )
        print(f"   ✅ Created: {knowledge_agent.name}")
        print(f"   ID: {knowledge_agent.id}\n")
        
        print("=" * 70)
        print("🎉 All agents created successfully!")
        print("=" * 70)
        print("\n📋 Copy these values to your .env file:\n")
        print(f"AZURE_FOUNDRY_ENDPOINT={foundry_endpoint}")
        print(f"FOUNDRY_ORCHESTRATOR_AGENT_ID={orchestrator_agent.id}")
        print(f"FOUNDRY_PRODUCT_AGENT_ID={product_agent.id}")
        print(f"FOUNDRY_ORDER_AGENT_ID={order_agent.id}")
        print(f"FOUNDRY_KNOWLEDGE_AGENT_ID={knowledge_agent.id}")
        print(f"USE_FOUNDRY_AGENTS=true")
        print("\n" + "=" * 70)
        
        return {
            "orchestrator": orchestrator_agent.id,
            "product": product_agent.id,
            "order": order_agent.id,
            "knowledge": knowledge_agent.id,
        }

def main():
    parser = argparse.ArgumentParser(
        description="Create Azure AI Foundry agents for e-commerce chatbot"
    )
    parser.add_argument(
        "--foundry-endpoint",
        required=True,
        help="Azure AI Foundry project endpoint (e.g., https://your-project.api.azureml.ms)",
    )
    parser.add_argument(
        "--model-name",
        default="gpt-4o-mini",
        help="Model deployment name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--solution-name",
        default="ecommerce",
        help="Solution name prefix for agents (default: ecommerce)",
    )
    
    args = parser.parse_args()
    
    try:
        agent_ids = create_agents(
            foundry_endpoint=args.foundry_endpoint,
            model_name=args.model_name,
            solution_name=args.solution_name,
        )
        
        print("\n✅ Setup complete! Next steps:")
        print("1. Copy the environment variables above to your .env file")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the backend: uvicorn app.main:app --reload")
        print("4. Test the Foundry integration: python test_foundry_integration.py")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error creating agents: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you're logged in: az login")
        print("2. Verify the Foundry endpoint is correct")
        print("3. Check you have permissions to create agents in the project")
        sys.exit(1)

if __name__ == "__main__":
    main()


