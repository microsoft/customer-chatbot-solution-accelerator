import argparse
import asyncio
import sys
from pathlib import Path

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchTool,
    AzureAISearchToolResource,
    ConnectionType,
    FunctionTool,
    PromptAgentDefinition,
)
from agent_framework.azure import AzureAIProjectAgentProvider
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from scenarios.scenario_loader import load_agent_instructions, load_manifest, resolve_scenario, catalog_tool_name, policy_tool_name

p = argparse.ArgumentParser()
p.add_argument("--ai_project_endpoint", required=True)
p.add_argument("--solution_name", required=True)
p.add_argument("--gpt_model_name", required=True)
p.add_argument("--ai_search_endpoint", required=True)
p.add_argument("--scenario", default=None)
args = p.parse_args()

ai_project_endpoint = args.ai_project_endpoint
solutionName = args.solution_name
gptModelName = args.gpt_model_name
ai_search_endpoint = args.ai_search_endpoint
scenario = resolve_scenario(args.scenario)
manifest = load_manifest(scenario)
catalog_index = manifest["search"]["catalogIndex"]
policies_index = manifest["search"]["policiesIndex"]
catalog_prefix = manifest["agents"]["catalogAgentPrefix"]
policy_prefix = manifest["agents"]["policyAgentPrefix"]
chat_prefix = manifest["agents"]["chatAgentPrefix"]
catalog_tool_name_val = catalog_tool_name(scenario)
policy_tool_name_val = policy_tool_name(scenario)


async def get_ai_search_connection_id(project_client: AIProjectClient) -> str:
    async for connection in project_client.connections.list():
        if connection.type == ConnectionType.AZURE_AI_SEARCH:
            if connection.target == ai_search_endpoint:
                return connection.id
    raise Exception(
        f"Could not find AI Search connection for {ai_search_endpoint}."
    )


async def create_agents():
    async with (
        AzureCliCredential() as credential,
        AIProjectClient(endpoint=ai_project_endpoint, credential=credential) as project_client,
        AzureAIProjectAgentProvider(
            project_client=project_client,
            credential=credential,
        ) as provider,
    ):
        ai_search_conn_id = await get_ai_search_connection_id(project_client)

        catalog_agent = await provider.create_agent(
            name=f"{catalog_prefix}-{solutionName}",
            model=gptModelName,
            instructions=load_agent_instructions(scenario, "catalog_agent"),
            tools={
                "type": "azure_ai_search",
                "azure_ai_search": {
                    "indexes": [
                        {
                            "project_connection_id": ai_search_conn_id,
                            "index_name": catalog_index,
                            "query_type": "vector_simple",
                            "top_k": 5,
                        }
                    ]
                },
            },
        )

        policy_agent = await provider.create_agent(
            name=f"{policy_prefix}-{solutionName}",
            model=gptModelName,
            instructions=load_agent_instructions(scenario, "policy_agent"),
            tools={
                "type": "azure_ai_search",
                "azure_ai_search": {
                    "indexes": [
                        {
                            "project_connection_id": ai_search_conn_id,
                            "index_name": policies_index,
                            "query_type": "vector_simple",
                            "top_k": 5,
                        }
                    ]
                },
            },
        )

        chat_agent = await provider.create_agent(
            name=f"{chat_prefix}-{solutionName}",
            model=gptModelName,
            instructions=load_agent_instructions(scenario, "chat_agent"),
            tools=[
                catalog_agent.as_tool(name=catalog_tool_name_val),
                policy_agent.as_tool(name=policy_tool_name_val),
            ],
        )

        return catalog_agent.name, policy_agent.name, chat_agent.name


product_agent_name, policy_agent_name, chat_agent_name = asyncio.run(create_agents())
print(f"chatAgentName={chat_agent_name}")
print(f"productAgentName={product_agent_name}")
print(f"policyAgentName={policy_agent_name}")
