#!/usr/bin/env python3
"""
List all assistants in Azure AI Foundry project
"""
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)


async def list_assistants():
    print("Listing assistants in Azure AI Foundry project...")

    try:
        from foundry_client import get_foundry_client, init_foundry_client

        # Initialize Foundry client
        print("Initializing Foundry client...")
        await init_foundry_client()
        client = get_foundry_client()

        # Get OpenAI client
        print("Getting OpenAI client...")
        from config import settings

        openai_client = await client.get_openai_client(  # type: ignore
            api_version=settings.azure_openai_api_version
        )

        # List all assistants
        print("Fetching assistants...")
        assistants = await openai_client.beta.assistants.list(limit=100)

        print(f"\n✅ Found {len(assistants.data)} assistants:")
        for assistant in assistants.data:
            print(f"   - ID: {assistant.id}")
            print(f"     Name: {assistant.name or 'No name'}")
            print(f"     Description: {assistant.description or 'No description'}")
            print(f"     Model: {assistant.model}")
            print(f"     Created: {assistant.created_at}")
            print()

        return assistants.data

    except Exception as e:
        print(f"❌ Failed to list assistants: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    asyncio.run(list_assistants())
