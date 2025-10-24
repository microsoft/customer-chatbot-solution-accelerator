#!/usr/bin/env python3
"""
Test script to check orchestrator agent configuration
"""
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_orchestrator():
    print("Testing orchestrator configuration...")
    
    try:
        from simple_foundry_orchestrator import get_simple_foundry_orchestrator
        
        # Get the orchestrator
        print("Initializing orchestrator...")
        orch = await get_simple_foundry_orchestrator()
        
        print(f"✅ Orchestrator configured: {orch.is_configured}")
        print(f"✅ Number of agents: {len(orch.agents)}")
        print(f"✅ Agent names: {list(orch.agents.keys())}")
        
        for name, agent in orch.agents.items():
            agent_id = getattr(agent, 'id', getattr(agent, 'assistant_id', 'unknown'))
            print(f"   - {name}: {type(agent).__name__} (ID: {agent_id})")
        
        # Test routing for different queries
        test_queries = [
            "Hello",
            "What products do you have?", 
            "Show me laptops",
            "What's your return policy?",
            "Track my order"
        ]
        
        print("\n🔍 Testing routing logic:")
        for query in test_queries:
            try:
                agent_name = orch._determine_target_agent(query)
                print(f"   '{query}' -> {agent_name}")
            except Exception as e:
                print(f"   '{query}' -> ERROR: {e}")
        
        return orch
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_orchestrator())