from fastapi import APIRouter, Depends

from ..auth import get_current_authenticated_user
from ..config import settings
from ..scenario_config import compliance_banner, current_scenario, welcome_config

router = APIRouter(
    prefix="/api/chat",
    tags=["chat-config"],
    dependencies=[Depends(get_current_authenticated_user)],
)


@router.get("/config")
async def get_chat_config():
    welcome = welcome_config()
    return {
        "scenario": current_scenario(),
        "welcomeTitle": welcome["title"],
        "welcomeSubtitle": welcome["subtitle"],
        "welcomeHint": welcome["hint"],
        "complianceBanner": compliance_banner(),
        "agentConfigured": bool(settings.foundry_chat_agent and settings.foundry_policy_agent),
    }
