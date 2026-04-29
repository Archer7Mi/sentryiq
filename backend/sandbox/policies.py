"""Sandbox policies for SentryIQ agents.

Defines security policies for each agent type:
- NIM AI agents (CVE synthesis, chain analysis, phishing)
- Chain detection engine
- Risk scoring engine
- Ingestion workers
"""

from sandbox.nemoclaw import AgentCapability, SandboxLevel, SandboxPolicy


# NIM AI Agent - CVE Synthesis
NIM_CVE_SYNTHESIS_POLICY = SandboxPolicy(
    agent_name="nim-cve-synthesis",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.NIM_API_ACCESS,
        AgentCapability.DATABASE_READ,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.TEXT_PROCESSING,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=256,
    max_timeout_seconds=30,
    max_api_calls_per_minute=50,
    allowed_nim_models=["nvidia/nemotron-3-super-120b-a12b"],
    audit_enabled=True,
    description="Plain-English CVE synthesis using NIM Nemotron model",
)

# NIM AI Agent - Chain Analysis
NIM_CHAIN_ANALYSIS_POLICY = SandboxPolicy(
    agent_name="nim-chain-analysis",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.NIM_API_ACCESS,
        AgentCapability.DATABASE_READ,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.TEXT_PROCESSING,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=512,
    max_timeout_seconds=45,
    max_api_calls_per_minute=30,
    allowed_nim_models=["deepseek-ai/deepseek-r1"],
    audit_enabled=True,
    description="Vulnerability chain detection and reasoning using NIM DeepSeek R1",
)

# NIM AI Agent - Phishing Generation
NIM_PHISHING_GEN_POLICY = SandboxPolicy(
    agent_name="nim-phishing-generation",
    sandbox_level=SandboxLevel.RESTRICTED,
    allowed_capabilities=[
        AgentCapability.NIM_API_ACCESS,
        AgentCapability.DATABASE_READ,
        AgentCapability.DATABASE_WRITE,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.TEXT_PROCESSING,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=256,
    max_timeout_seconds=25,
    max_api_calls_per_minute=20,
    allowed_nim_models=["meta/llama-3.3-70b-instruct"],
    audit_enabled=True,
    description="Phishing simulation email generation (restricted for compliance)",
)

# Chain Detection Engine
CHAIN_DETECTION_POLICY = SandboxPolicy(
    agent_name="chain-detector",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.DATABASE_READ,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.CRYPTO_OPERATIONS,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=512,
    max_timeout_seconds=60,
    max_api_calls_per_minute=100,
    audit_enabled=True,
    description="CWE prerequisite graph traversal for chain detection",
)

# Risk Scoring Engine
RISK_SCORER_POLICY = SandboxPolicy(
    agent_name="human-risk-scorer",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.DATABASE_READ,
        AgentCapability.DATABASE_WRITE,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=256,
    max_timeout_seconds=15,
    max_api_calls_per_minute=100,
    audit_enabled=True,
    description="Human risk score calculation from phishing simulations",
)

# NVD Ingestion Worker
NVD_WORKER_POLICY = SandboxPolicy(
    agent_name="nvd-ingestion-worker",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.DATABASE_WRITE,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.LOG_WRITE,
        AgentCapability.CACHE_ACCESS,
    ],
    max_memory_mb=1024,
    max_timeout_seconds=300,
    max_api_calls_per_minute=10,
    audit_enabled=True,
    description="NVD API polling and CVE record ingestion",
)

# Compliance Mapper
COMPLIANCE_MAPPER_POLICY = SandboxPolicy(
    agent_name="compliance-mapper",
    sandbox_level=SandboxLevel.STANDARD,
    allowed_capabilities=[
        AgentCapability.DATABASE_READ,
        AgentCapability.DATABASE_WRITE,
        AgentCapability.JSON_PROCESSING,
        AgentCapability.LOG_WRITE,
    ],
    max_memory_mb=256,
    max_timeout_seconds=30,
    max_api_calls_per_minute=50,
    audit_enabled=True,
    description="CVE to compliance framework mapping (NDPA, POPIA, Kenya DPA, PCI-DSS)",
)


def get_all_policies() -> dict:
    """Get all predefined sandbox policies.

    Returns:
        Dictionary mapping agent names to policies
    """
    return {
        "nim-cve-synthesis": NIM_CVE_SYNTHESIS_POLICY,
        "nim-chain-analysis": NIM_CHAIN_ANALYSIS_POLICY,
        "nim-phishing-generation": NIM_PHISHING_GEN_POLICY,
        "chain-detector": CHAIN_DETECTION_POLICY,
        "human-risk-scorer": RISK_SCORER_POLICY,
        "nvd-ingestion-worker": NVD_WORKER_POLICY,
        "compliance-mapper": COMPLIANCE_MAPPER_POLICY,
    }
