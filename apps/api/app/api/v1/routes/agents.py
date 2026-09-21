from fastapi import APIRouter, Depends

from app.agents.registry import AGENTS
from app.agents.router import route as route_message
from app.ai.registry import ai_is_configured
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.chat import AgentInfo, AIStatus, RouteRequest, RoutingInfo

router = APIRouter()


@router.get("", response_model=list[AgentInfo])
def list_agents() -> list[AgentInfo]:
    return [
        AgentInfo(name=a.name, title=a.title, description=a.description) for a in AGENTS.values()
    ]


@router.post("/route", response_model=RoutingInfo)
def preview_routing(
    payload: RouteRequest, _user: User = Depends(get_current_user)
) -> RoutingInfo:
    """Show which agent would answer, and why. Useful for transparency in the UI."""
    decision = route_message(payload.message)
    return RoutingInfo(
        agent=decision.agent.name,
        title=decision.agent.title,
        confidence=decision.confidence,
        signals=list(decision.signals),
    )


@router.get("/status", response_model=AIStatus)
def ai_status(_user: User = Depends(get_current_user)) -> AIStatus:
    configured = ai_is_configured()
    return AIStatus(
        configured=configured,
        provider=settings.ai_provider,
        model=settings.ai_model or None,
        detail=(
            "AI provider configured and ready."
            if configured
            else "Set AI_BASE_URL, AI_MODEL and AI_API_KEY in the environment to enable answers."
        ),
    )
