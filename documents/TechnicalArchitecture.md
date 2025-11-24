## Technical Architecture

This section outlines the components and interactions that power the intelligent customer chatbot solution. The architecture combines Azure AI Foundry's agent framework with enterprise data services to deliver conversational customer support.

![image](./Images/solution-architecture.png)

### Azure AI Foundry Agent Framework
Orchestrates multi-agent workflows with an intelligent orchestrator agent that uses automatic tool selection to route customer queries to specialized agents. The orchestrator analyzes user intent and invokes the appropriate specialist agent (Product Lookup or Policy/Knowledge) to handle each query, ensuring accurate and contextual responses.

### Specialized AI Agents
- **Product Lookup Agent**: Searches product catalogs using Azure AI Search to help customers discover products through natural language queries and provide personalized recommendations
- **Policy/Knowledge Agent**: Retrieves information from policy documents and knowledge bases to answer customer support questions about warranties, returns, and company policies

### Azure OpenAI Service  
Provides large language model (LLM) capabilities using GPT-4o-mini to power natural language understanding and conversational responses across all AI agents.

### Azure AI Search
Provides hybrid search capabilities combining semantic and keyword search across product catalogs and policy documents. Enables fast, accurate retrieval of relevant information for specialized agents.

### Azure Cosmos DB
Stores product catalogs, customer orders, and chat conversation history with high availability and global distribution. Maintains session context to enable continuous conversations and retrieve past customer interactions.

### App Service  
Hosts the React frontend application and FastAPI backend service. The backend orchestrates AI agent interactions, manages data access, and provides REST APIs for the frontend.

### Container Registry  
Stores and serves containerized deployments of the frontend and backend applications.

### Web Front-End  
A modern React/TypeScript application featuring dual-panel layout with product browsing and integrated AI chat assistant. Enables customers to shop and receive support through natural language conversations.