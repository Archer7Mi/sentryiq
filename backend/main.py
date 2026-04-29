"""SentryIQ FastAPI application entrypoint.

Initializes the FastAPI app with database connection, NIM client,
and all API routes.
"""

import logging
import os

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.intelligence_routes import (
    init_nim_client,
    router as intelligence_router,
    shutdown_nim_client,
)
from backend.api.sandbox_routes import router as sandbox_router
from backend.api.simulation_routes import (
    init_phishing_engine,
    init_risk_scorer,
    router as simulation_router,
)
from backend.database.connection import get_engine, init_db
from backend.sandbox.nemoclaw import shutdown_sandbox
from backend.sandbox.nim_sandboxed import (
    get_sandboxed_nim_client,
    shutdown_sandboxed_nim_client,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SentryIQ",
    description="AI-powered cybersecurity platform for SMBs",
    version="0.1.0",
)

# Include routers
app.include_router(intelligence_router)
app.include_router(simulation_router)
app.include_router(sandbox_router)


@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    logger.info("SentryIQ starting up...")

    try:
        # Initialize database
        engine = await get_engine()
        await init_db(engine)
        logger.info("Database initialized")

        # Initialize sandbox
        from backend.sandbox.nemoclaw import get_sandbox
        from backend.sandbox.policies import get_all_policies

        sandbox = await get_sandbox()
        policies = get_all_policies()
        for agent_name, policy in policies.items():
            sandbox.register_agent(policy)
        logger.info("NemoClaw sandbox initialized with %d policies", len(policies))

        # Initialize NIM client
        from backend.api.intelligence_routes import get_nim_client
        await init_nim_client()
        nim_client = get_nim_client()
        logger.info("NIM client initialized")

        # Initialize sandboxed NIM client
        sandboxed_nim_client = await get_sandboxed_nim_client(nim_client)
        logger.info("Sandboxed NIM client initialized")

        # Initialize phishing engine (with sandboxed NIM)
        await init_phishing_engine(sandboxed_nim_client)
        logger.info("Phishing engine initialized with sandboxed NIM")

        # Initialize risk scorer
        await init_risk_scorer()
        logger.info("Risk scorer initialized")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("SentryIQ shutting down...")
    await shutdown_nim_client()
    await shutdown_sandboxed_nim_client()
    await shutdown_sandbox()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SentryIQ"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
