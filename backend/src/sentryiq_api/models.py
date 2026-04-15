from __future__ import annotations

from pydantic import BaseModel, Field


class StackItem(BaseModel):
    category: str
    name: str
    version: str | None = None
    internet_facing: bool = False
    notes: str | None = None


class StackAssessmentRequest(BaseModel):
    organization: str = Field(default="Demo SMB")
    stack: list[StackItem]


class VulnerabilityFinding(BaseModel):
    cve_id: str
    asset: str
    severity: str
    cvss: float
    epss: float
    kev: bool
    summary: str
    remediation: str


class ChainFinding(BaseModel):
    title: str
    severity: str
    summary: str
    patch_order: list[str]


class PriorityItem(BaseModel):
    rank: int
    title: str
    reason: str
    action: str
    score: float


class StackAssessmentResponse(BaseModel):
    headline: str
    summary: str
    findings: list[VulnerabilityFinding]
    chains: list[ChainFinding]
    priority_queue: list[PriorityItem]


class EmployeeRisk(BaseModel):
    employee: str
    role: str
    score: int
    risk_level: str
    coaching: str


class PhishingSimulationRequest(BaseModel):
    target_name: str
    target_role: str
    channel: str = "email"
    scenario: str = "credential reset"


class PhishingSimulationResponse(BaseModel):
    subject: str
    body: str
    warnings: list[str]
