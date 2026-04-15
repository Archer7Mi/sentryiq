from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import (
    ChainFinding,
    EmployeeRisk,
    PhishingSimulationRequest,
    PhishingSimulationResponse,
    PriorityItem,
    StackAssessmentRequest,
    StackAssessmentResponse,
    VulnerabilityFinding,
)


@dataclass(frozen=True)
class Rule:
    keywords: tuple[str, ...]
    cve_id: str
    asset_label: str
    severity: str
    cvss: float
    epss: float
    kev: bool
    summary: str
    remediation: str


RULES: tuple[Rule, ...] = (
    Rule(
        keywords=("apache", "http server"),
        cve_id="CVE-2025-24017",
        asset_label="Apache HTTP Server",
        severity="high",
        cvss=8.8,
        epss=0.73,
        kev=True,
        summary="Internet-facing web servers with this build are exposed to remote execution and request smuggling patterns.",
        remediation="Patch Apache immediately and schedule a restart window for the web tier.",
    ),
    Rule(
        keywords=("openssl",),
        cve_id="CVE-2025-23451",
        asset_label="OpenSSL",
        severity="medium",
        cvss=7.5,
        epss=0.41,
        kev=False,
        summary="Older OpenSSL releases can weaken TLS handling and create a pivot for chained exploitation.",
        remediation="Upgrade OpenSSL in the base image or OS package set before the next release.",
    ),
    Rule(
        keywords=("windows server", "domain controller"),
        cve_id="CVE-2025-34560",
        asset_label="Windows Server",
        severity="critical",
        cvss=9.8,
        epss=0.87,
        kev=True,
        summary="This server role is a high-value target when exposed with other workstation or web-tier weaknesses.",
        remediation="Prioritize the domain controller patch and validate lateral-movement controls.",
    ),
    Rule(
        keywords=("mssql", "sql server"),
        cve_id="CVE-2025-19771",
        asset_label="Microsoft SQL Server",
        severity="high",
        cvss=8.1,
        epss=0.54,
        kev=False,
        summary="Database services with this version can be abused after credential theft or web-tier compromise.",
        remediation="Patch the database host and review service account privilege boundaries.",
    ),
)


def _matches(item_text: str, rule: Rule) -> bool:
    normalized = item_text.lower()
    return any(keyword in normalized for keyword in rule.keywords)


def _score_finding(finding: VulnerabilityFinding, internet_facing: bool) -> float:
    base_score = finding.cvss * 10
    base_score += finding.epss * 100
    if finding.kev:
        base_score += 15
    if internet_facing:
        base_score += 10
    return round(base_score, 1)


def assess_stack(payload: StackAssessmentRequest) -> StackAssessmentResponse:
    stack_text = " ".join(
        " ".join(
            part for part in [item.category, item.name, item.version or "", item.notes or ""] if part
        )
        for item in payload.stack
    ).lower()

    findings: list[VulnerabilityFinding] = []
    queue: list[PriorityItem] = []

    for rule in RULES:
        if _matches(stack_text, rule):
            internet_facing = any(
                _matches(" ".join(filter(None, [item.name, item.notes or ""])), rule)
                and item.internet_facing
                for item in payload.stack
            )
            finding = VulnerabilityFinding(
                cve_id=rule.cve_id,
                asset=rule.asset_label,
                severity=rule.severity,
                cvss=rule.cvss,
                epss=rule.epss,
                kev=rule.kev,
                summary=rule.summary,
                remediation=rule.remediation,
            )
            findings.append(finding)
            queue.append(
                PriorityItem(
                    rank=0,
                    title=finding.cve_id,
                    reason=finding.summary,
                    action=finding.remediation,
                    score=_score_finding(finding, internet_facing),
                )
            )

    chains: list[ChainFinding] = []
    if "apache" in stack_text and "openssl" in stack_text:
        chains.append(
            ChainFinding(
                title="Apache + OpenSSL public-web chain",
                severity="critical",
                summary=(
                    "The web server and TLS library together create a path from an internet-facing edge to code execution."
                ),
                patch_order=["Patch OpenSSL", "Patch Apache", "Restart the web tier"],
            )
        )
        queue.append(
            PriorityItem(
                rank=0,
                title="Critical chain: Apache + OpenSSL",
                reason="Two individually manageable issues combine into a remote execution path on the edge tier.",
                action="Break the chain by patching OpenSSL first, then Apache.",
                score=97.5,
            )
        )

    if "windows server" in stack_text and "mssql" in stack_text:
        chains.append(
            ChainFinding(
                title="Windows Server + SQL pivot chain",
                severity="high",
                summary="Credential or service compromise on the database host can pivot into the Windows core services layer.",
                patch_order=["Patch Windows Server", "Patch SQL Server", "Review service account permissions"],
            )
        )
        queue.append(
            PriorityItem(
                rank=0,
                title="High chain: Windows Server + SQL Server",
                reason="The database and Windows layers reinforce each other and increase blast radius.",
                action="Close the privilege gap and patch the Windows host before database hardening.",
                score=89.0,
            )
        )

    queue = sorted(queue, key=lambda item: item.score, reverse=True)
    for index, item in enumerate(queue, start=1):
        queue[index - 1] = item.model_copy(update={"rank": index})

    if not findings:
        headline = f"No known high-confidence matches found for {payload.organization}."
        summary = "The current demo catalog does not match this stack yet. Add more stack fingerprints or ingest live feeds."
    else:
        headline = f"{payload.organization} has {len(findings)} matched vulnerability signal(s)."
        summary = "SentryIQ prioritized the matched issues using severity, exploit likelihood, and chain risk."

    return StackAssessmentResponse(
        headline=headline,
        summary=summary,
        findings=findings,
        chains=chains,
        priority_queue=queue,
    )


def sample_human_risk() -> list[EmployeeRisk]:
    return [
        EmployeeRisk(
            employee="Maya Okafor",
            role="Finance Manager",
            score=82,
            risk_level="high",
            coaching="Pause before opening urgent payment requests and verify any change by phone.",
        ),
        EmployeeRisk(
            employee="Jordan Lee",
            role="Operations Lead",
            score=54,
            risk_level="medium",
            coaching="Report unexpected MFA prompts and avoid approving logins from unrecognized devices.",
        ),
        EmployeeRisk(
            employee="Sam Patel",
            role="Support Specialist",
            score=21,
            risk_level="low",
            coaching="Keep reporting suspicious messages; your behavior is helping the team build resistance.",
        ),
    ]


def generate_phishing_template(payload: PhishingSimulationRequest) -> PhishingSimulationResponse:
    subject = f"Action required: {payload.scenario.title()} review for {payload.target_name}"
    body = (
        f"Hi {payload.target_name},\n\n"
        f"This is a {payload.channel} simulation for the {payload.target_role} role. "
        f"Please review the request labeled '{payload.scenario}' and decide whether it should be escalated, "
        "reported, or blocked.\n\n"
        "The goal of the simulation is to test verification habits, not collect credentials."
    )
    warnings = [
        "Use only with organizational consent.",
        "Do not collect real credentials.",
        "Replace placeholder identity data before production use.",
    ]
    return PhishingSimulationResponse(subject=subject, body=body, warnings=warnings)
