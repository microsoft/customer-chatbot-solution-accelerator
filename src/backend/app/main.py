from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ChatRequest, ProductListResponse  # ChatResponse not needed here
from .services import sql
from .config import settings
from .foundry_client import init_foundry_client, shutdown_foundry_client
from .handoff import HandoffChatOrchestrator
# from .agents import Orchestrator  # <- remove old orchestrator import

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) init shared Foundry client (safe even if no Foundry agents are used)
    await init_foundry_client(settings.azure_foundry_endpoint)

    # 2) build orchestrator via async factory and stash on app.state
    app.state.orch = await HandoffChatOrchestrator.create()
    try:
        yield
    finally:
        # 3) clean shutdown
        await app.state.orch.shutdown()
        await shutdown_foundry_client()

# IMPORTANT: pass lifespan=lifespan so startup/shutdown actually run
app = FastAPI(title="Shop+Chat API", lifespan=lifespan)

# CORS — normalize to a list in case settings.cors_origins is a string
allow_origins = settings.cors_origins if isinstance(settings.cors_origins, list) else [settings.cors_origins]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/products", response_model=ProductListResponse)
def list_products(limit: int = 50):
    items = sql.fetch_products(limit=limit)
    return {"items": items}

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    # If startup somehow didn't run (e.g., a test), lazily init to avoid AttributeError
    orch: HandoffChatOrchestrator | None = getattr(request.app.state, "orch", None)
    if orch is None:
        await init_foundry_client(settings.azure_foundry_endpoint)
        request.app.state.orch = await HandoffChatOrchestrator.create()
        orch = request.app.state.orch

    # Fold history into the prompt (or extend orchestrator to accept history natively)
    if req.history:
        hist_lines = []
        for m in req.history:
            role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
            if role and content:
                hist_lines.append(f"{role.capitalize()}: {content}")
        user_text = "Previous messages:\n" + "\n".join(hist_lines) + "\n\n" + req.message
    else:
        user_text = req.message

    try:
        result = await orch.respond(user_text)
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Chat failed: {ex}")