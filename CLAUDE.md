# CLAUDE.md — Claude Code Project Instructions
> Read SENTRYIQ.md first before any task. This file adds Claude Code-specific behaviour.

## Identity
You are working on SentryIQ — an open-source AI-powered cybersecurity platform
for African SMBs. Author: Michael Ted. License: Apache 2.0.

## First Action Every Session
1. Read `@SENTRYIQ.md` — full project context, schema, architecture, build status
2. Check `Current Build Status` section to know what's done and what's next
3. Ask Michael what we're building today if not clear

## Behaviour Rules
- Always write defensive, secure Python — validate all inputs, never trust external data
- Never generate exploit code, weaponizable scripts, or offensive tooling
- Always use environment variables for secrets — never hardcode keys
- Write tests alongside every new module (pytest)
- Keep all AI output to users at Grade 8 reading level
- When uncertain about security implications — stop and ask

## Code Style
- Python: PEP 8, type hints on all functions, docstrings on all classes
- FastAPI: async/await everywhere, Pydantic v2 for all schemas
- Commits: conventional commits format (feat:, fix:, docs:, test:)

## After Every Session
Update the `Current Build Status` section in SENTRYIQ.md — mark completed items,
add new decisions to the Key Decisions Log.

## MCP Servers Available
- filesystem — file read/write
- github — repo, issues, PRs (configure with: claude mcp add github)
- postgres — database queries (configure with: claude mcp add postgres)

## Priority Queue (What to Build Next)
1. `backend/database/models.py` — SQLAlchemy models from schema in SENTRYIQ.md
2. `backend/ingestion/nvd_worker.py` — NVD API v2.0 polling worker
3. `backend/ingestion/kev_worker.py` — CISA KEV sync worker
4. `backend/ingestion/epss_worker.py` — FIRST EPSS worker
5. `backend/intelligence/stack_matcher.py` — CPE matching engine
6. `backend/intelligence/chain_detector.py` — CWE chain detection
7. `backend/ai/nim_client.py` — NVIDIA NIM client wrapper
