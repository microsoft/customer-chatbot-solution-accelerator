from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, ProductListResponse
from .services import sql
import os
from .agents import Orchestrator
from .handoff import HandoffChatOrchestrator
from .config import settings

app = FastAPI(title="Shop+Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("USE_HANDOFF_DEMO", "false").lower() == "true":
    orch = HandoffChatOrchestrator()
else:
    orch = Orchestrator()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/products", response_model=ProductListResponse)
def list_products(limit: int = 50):
    items = sql.fetch_products(limit=limit)
    return {"items": items}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await orch.respond(req.message, history=[m.model_dump() for m in (req.history or [])])
    return ChatResponse(**result)
