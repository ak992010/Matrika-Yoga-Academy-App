from __future__ import annotations

from fastapi import FastAPI, HTTPException
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from track2_location_agent.agent import build_agent
from track2_location_agent.config import APP_NAME, DATASET_NAME, MODEL_NAME, PROJECT_ID
from track2_location_agent.tools import AgentConfigurationError, runtime_diagnostics

app = FastAPI(
    title="Track 2 ADK MCP Location Intelligence Agent",
    version="1.0.0",
    description=(
        "A Google ADK agent that combines BigQuery and Google Maps MCP servers "
        "for location intelligence workflows."
    ),
)

session_service = InMemorySessionService()


class LocationIntelligenceRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=1200)
    city: str = Field(default="Los Angeles", min_length=2, max_length=80)
    business_type: str = Field(
        default="high-end sourdough bakery",
        min_length=3,
        max_length=120,
    )


class LocationIntelligenceResponse(BaseModel):
    answer: str
    session_id: str
    model: str
    dataset: str


def _extract_text_from_event(event) -> str:
    if not getattr(event, "content", None) or not event.content.parts:
        return ""

    pieces: list[str] = []
    for part in event.content.parts:
        text = getattr(part, "text", None)
        if text:
            pieces.append(text)
    return "".join(pieces).strip()


def _build_prompt(payload: LocationIntelligenceRequest) -> str:
    return (
        "Use the available MCP tools to answer the location intelligence "
        "question below. Use BigQuery for macro market analysis and Google Maps "
        "for real-world location validation whenever it matters. Keep the "
        "answer practical and decision-oriented.\n\n"
        f"BUSINESS TYPE: {payload.business_type}\n"
        f"TARGET CITY: {payload.city}\n"
        f"QUESTION: {payload.question}\n\n"
        "In your answer, summarize the strongest evidence, the most promising "
        "area if one emerges, and any important caveats."
    )


async def _run_agent(prompt: str) -> LocationIntelligenceResponse:
    try:
        agent = build_agent(strict=True)
    except AgentConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
    )

    user_id = "track2-location-intelligence-api-user"
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    final_text = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part.from_text(text=prompt)]),
    ):
        if event.is_final_response():
            final_text = _extract_text_from_event(event) or final_text

    if not final_text:
        raise HTTPException(status_code=502, detail="The agent returned an empty response.")

    return LocationIntelligenceResponse(
        answer=final_text,
        session_id=session.id,
        model=MODEL_NAME,
        dataset=f"{PROJECT_ID or '<project>'}.{DATASET_NAME}",
    )


@app.get("/healthz")
async def healthz() -> dict[str, object]:
    return {
        "status": "ok",
        "service": APP_NAME,
        "model": MODEL_NAME,
        "dataset": f"{PROJECT_ID or '<project>'}.{DATASET_NAME}",
        "checks": runtime_diagnostics(),
    }


@app.post("/location-intelligence", response_model=LocationIntelligenceResponse)
async def location_intelligence(
    payload: LocationIntelligenceRequest,
) -> LocationIntelligenceResponse:
    return await _run_agent(_build_prompt(payload))

