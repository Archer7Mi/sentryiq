from __future__ import annotations

from fastapi import APIRouter

from .models import (
    PhishingSimulationRequest,
    PhishingSimulationResponse,
    StackAssessmentRequest,
    StackAssessmentResponse,
)
from .services import assess_stack, generate_phishing_template, sample_human_risk

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "sentryiq-api"}


@router.get("/human-risk/sample")
def human_risk_sample() -> list[dict[str, object]]:
    return [risk.model_dump() for risk in sample_human_risk()]


@router.post("/stack/assess", response_model=StackAssessmentResponse)
def stack_assessment(payload: StackAssessmentRequest) -> StackAssessmentResponse:
    return assess_stack(payload)


@router.post("/simulations/phishing", response_model=PhishingSimulationResponse)
def phishing_simulation(payload: PhishingSimulationRequest) -> PhishingSimulationResponse:
    return generate_phishing_template(payload)
