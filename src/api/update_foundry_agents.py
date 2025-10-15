import os
import sys
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.agent_instructions import (
    ORCHESTRATOR_INSTRUCTIONS,
    PRODUCT_LOOKUP_INSTRUCTIONS,
    ORDER_STATUS_INSTRUCTIONS,
    KNOWLEDGE_AGENT_INSTRUCTIONS,
)
from app.config import settings

def update_agents():
    if not settings.azure_foundry_endpoint:
        print("AZURE_FOUNDRY_ENDPOINT not configured in environment")
        sys.exit(1)
    
    print(f"Updating Azure AI Foundry agents")
    print(f"Endpoint: {settings.azure_foundry_endpoint}\n")
    
    credential = DefaultAzureCredential()
    
    project_client = AIProjectClient(
        endpoint=settings.azure_foundry_endpoint,
        credential=credential,
    )
    
    with project_client:
        agents_client = project_client.agents
        
        updated_count = 0
        
        if settings.foundry_orchestrator_agent_id:
            print(f"Updating Orchestrator Agent ({settings.foundry_orchestrator_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_orchestrator_agent_id,
                    instructions=ORCHESTRATOR_INSTRUCTIONS,
                )
                print(f"   Updated\n")
                updated_count += 1
            except Exception as e:
                print(f"   Failed: {e}\n")
        
        if settings.foundry_product_agent_id:
            print(f"Updating Product Lookup Agent ({settings.foundry_product_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_product_agent_id,
                    instructions=PRODUCT_LOOKUP_INSTRUCTIONS,
                )
                print(f"   Updated\n")
                updated_count += 1
            except Exception as e:
                print(f"   Failed: {e}\n")
        
        if settings.foundry_order_agent_id:
            print(f"Updating Order Status Agent ({settings.foundry_order_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_order_agent_id,
                    instructions=ORDER_STATUS_INSTRUCTIONS,
                )
                print(f"   Updated\n")
                updated_count += 1
            except Exception as e:
                print(f"   Failed: {e}\n")
        
        if settings.foundry_knowledge_agent_id:
            print(f"Updating Knowledge Agent ({settings.foundry_knowledge_agent_id})...")
            try:
                agents_client.update_agent(
                    agent_id=settings.foundry_knowledge_agent_id,
                    instructions=KNOWLEDGE_AGENT_INSTRUCTIONS,
                )
                print(f"   Updated\n")
                updated_count += 1
            except Exception as e:
                print(f"   Failed: {e}\n")
        
        print("=" * 70)
        print(f"Updated {updated_count} agents successfully!")
        print("=" * 70)
        print("\nThe agents now have updated instructions.")
        print("Restart your backend service to pick up the changes.")

if __name__ == "__main__":
    try:
        update_agents()
        sys.exit(0)
    except Exception as e:
        print(f"\nError updating agents: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure you're logged in: az login")
        print("2. Verify your .env file has all agent IDs configured")
        print("3. Check you have permissions to update agents in the project")
        sys.exit(1)

