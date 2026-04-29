"""Pytest configuration and shared fixtures for SentryIQ tests."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.ai.nim_client import NIMClient
from backend.database.models import Base
from backend.sandbox.nemoclaw import NemoclawSandbox
from backend.sandbox.policies import get_all_policies
from backend.simulation.phishing import PhishingSimulationEngine
from backend.simulation.scoring import HumanRiskScorer


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"timeout": 30},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async test database session."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
def mock_nim_client() -> NIMClient:
    """Create mock NIM client for testing."""
    client = NIMClient(api_key="test-key-123")
    # Mock responses in individual tests
    return client


@pytest_asyncio.fixture
async def test_sandbox() -> NemoclawSandbox:
    """Create test sandbox instance."""
    sandbox = NemoclawSandbox("test-sandbox")
    await sandbox.initialize()

    # Register policies
    policies = get_all_policies()
    for agent_name, policy in policies.items():
        sandbox.register_agent(policy)

    return sandbox


@pytest_asyncio.fixture
async def phishing_engine(mock_nim_client) -> PhishingSimulationEngine:
    """Create phishing simulation engine for testing."""
    return PhishingSimulationEngine(mock_nim_client)


@pytest.fixture
def risk_scorer() -> HumanRiskScorer:
    """Create human risk scorer for testing."""
    return HumanRiskScorer()


@pytest.fixture
def sample_cve_data():
    """Sample CVE data for tests."""
    return {
        "cve_id": "CVE-2024-12345",
        "description": "Critical vulnerability in example software",
        "cvss_score": 9.5,
        "cwe_ids": ["CWE-79", "CWE-89"],
        "affected_cpes": ["cpe:2.3:a:vendor:product:1.0:*:*:*:*:*:*:*"],
        "epss_score": 0.95,
        "is_kev": True,
    }


@pytest.fixture
def sample_stack_data():
    """Sample SMB stack data for tests."""
    return {
        "org_name": "Test SMB Inc",
        "cpe_identifiers": [
            "cpe:2.3:a:microsoft:windows:11:*:*:*:*:*:*:*",
            "cpe:2.3:a:oracle:java:17:*:*:*:*:*:*:*",
        ],
        "internet_facing_cpes": [
            "cpe:2.3:a:microsoft:windows:11:*:*:*:*:*:*:*",
        ],
        "compliance_frameworks": ["NDPA", "POPIA"],
    }


@pytest.fixture
def sample_cwe_graph():
    """Sample CWE prerequisite graph for tests."""
    return {
        "CWE-79": {"name": "Improper Neutralization of Input During Web Page Generation", "children": []},
        "CWE-89": {"name": "SQL Injection", "children": ["CWE-200"]},
        "CWE-200": {"name": "Exposure of Sensitive Information", "children": []},
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "sandbox: mark test as a sandbox test")
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables between tests."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
