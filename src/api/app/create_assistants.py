#!/usr/bin/env python3
"""
Create Azure AI Foundry assistants programmatically
"""
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)


async def create_assistants():
    print("Creating assistants in Azure AI Foundry project...")

    try:
        from config import settings
        from foundry_client import get_foundry_client, init_foundry_client

        # Initialize Foundry client
        print("Initializing Foundry client...")
        await init_foundry_client()
        client = get_foundry_client()

        # Get OpenAI client
        print("Getting OpenAI client...")
        openai_client = await client.get_openai_client(  # type: ignore
            api_version=settings.azure_openai_api_version
        )

        # Define assistants to create
        assistants_to_create = [
            {
                "name": "Orchestrator Agent",
                "description": "Main orchestrator that routes customer inquiries to specialized agents for product searches, order tracking, and policy questions.",
                "instructions": """You are the main orchestrator for Contoso Paints e-commerce customer service. Your role is to:

1. Analyze customer inquiries and route them to appropriate specialists
2. Handle general questions and greetings
3. Provide comprehensive assistance using available tools
4. Maintain a helpful, professional tone

You have access to tools for:
- Product search and recommendations
- Order tracking and management
- Policy and FAQ information

Always aim to provide accurate, helpful responses while maintaining excellent customer service.""",
                "model": "gpt-4o-mini",
            },
            {
                "name": "Product Lookup Agent",
                "description": "Specialized agent for product searches, recommendations, and catalog inquiries.",
                "instructions": """You are a product specialist for Contoso Paints e-commerce. Your expertise includes:

1. Product search and discovery
2. Product recommendations based on customer needs
3. Pricing and availability information
4. Product specifications and details
5. Category browsing and filtering

Always help customers find the right products for their needs. Use the product search tools to provide accurate, up-to-date information.""",
                "model": "gpt-4o-mini",
            },
            {
                "name": "Order Status Agent",
                "description": "Specialized agent for order tracking, status updates, and order management.",
                "instructions": """You are an order specialist for Contoso Paints e-commerce. You help customers with:

1. Order status and tracking
2. Order history and details
3. Return and refund requests
4. Shipping information
5. Order modifications when possible

Always provide accurate order information and help resolve any order-related concerns professionally.""",
                "model": "gpt-4o-mini",
            },
            {
                "name": "Knowledge Agent",
                "description": "Specialized agent for policies, FAQs, warranties, and general support information.",
                "instructions": """You are a knowledge specialist for Contoso Paints e-commerce. You provide information about:

1. Return and refund policies
2. Warranty information
3. Shipping policies
4. FAQs and general questions
5. Company policies and procedures

Always provide accurate, helpful information from official policies and documentation.""",
                "model": "gpt-4o-mini",
            },
        ]

        created_assistants = []

        for assistant_config in assistants_to_create:
            print(f"\nCreating {assistant_config['name']}...")

            try:
                # Create assistant
                assistant = await openai_client.beta.assistants.create(
                    name=assistant_config["name"],
                    description=assistant_config["description"],
                    instructions=assistant_config["instructions"],
                    model=assistant_config["model"],
                    tools=[],  # We'll add tools later through plugins
                )

                print(f"✅ Created {assistant.name}")
                print(f"   ID: {assistant.id}")
                print(f"   Model: {assistant.model}")

                created_assistants.append(
                    {
                        "name": assistant_config["name"],
                        "id": assistant.id,
                        "role": assistant_config["name"].lower().replace(" ", "_"),
                    }
                )

            except Exception as e:
                print(f"❌ Failed to create {assistant_config['name']}: {e}")

        # Print environment variable updates
        if created_assistants:
            print("\n🎯 Update your .env file with these new assistant IDs:")
            print("=" * 60)

            env_mapping = {
                "orchestrator_agent": "FOUNDRY_ORCHESTRATOR_AGENT_ID",
                "product_lookup_agent": "FOUNDRY_PRODUCT_AGENT_ID",
                "order_status_agent": "FOUNDRY_ORDER_AGENT_ID",
                "knowledge_agent": "FOUNDRY_KNOWLEDGE_AGENT_ID",
            }

            for assistant in created_assistants:
                role = assistant["role"]
                if role in env_mapping:
                    env_var = env_mapping[role]
                    print(f'{env_var}="{assistant["id"]}"')

            print("=" * 60)

        return created_assistants

    except Exception as e:
        print(f"❌ Failed to create assistants: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    asyncio.run(create_assistants())
