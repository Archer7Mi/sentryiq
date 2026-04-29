# SentryIQ — GitHub Copilot Instructions
# This file provides always-on context for every Copilot session.
# Read SENTRYIQ.md for the full architecture before any task.

## Project Identity
- Name: SentryIQ
- Author: Michael Ted
- License: Apache 2.0
- Repo: https://github.com/Archer7Mi/sentryiq
- Purpose: Open-source AI-powered cybersecurity platform for African SMBs

## Stack
- Backend: Python 3.14.2 + FastAPI (async) + PostgreSQL + Redis
- Frontend: React 18 + Tailwind CSS
- AI: NVIDIA NIM API (OpenAI-compatible, base_url=https://integrate.api.nvidia.com/v1)
- Containers: Docker 29.1.3
- CI/CD: GitHub Actions

## Critical Rules — Never Violate
- NEVER generate exploit code or offensive security tooling
- NEVER hardcode API keys — always use environment variables
- NEVER store sensitive data unencrypted
- ALL external API inputs must be validated before processing
- ALL user-facing text must be plain English (Grade 8 level)
- This is a DEFENSIVE security tool only

## Code Standards
- Python: PEP 8, type hints required, docstrings on all classes and public methods
- FastAPI: async/await everywhere, Pydantic v2 schemas for all request/response models
- Tests: pytest, write tests alongside every new module
- Commits: conventional commits (feat:, fix:, docs:, test:, chore:)

## Architecture Context
- CVE data flows: NVD API → ingestion workers → PostgreSQL → stack matcher → chain detector → NIM AI → plain-English alerts
- Chain detection uses CWE prerequisite graph traversal (see SENTRYIQ.md for algorithm)
- NIM API is OpenAI-compatible — use the openai Python library with custom base_url
- All agents will be sandboxed with NVIDIA NemoClaw in Phase 3

## What We Are Building Now
Phase 1 — Data Pipeline:
- NVD REST API v2.0 polling worker (APScheduler, every 2 hours)
- CISA KEV JSON sync worker (every 6 hours)
- FIRST EPSS score worker (daily)
- SQLAlchemy models matching the schema in SENTRYIQ.md

## NIM Client Pattern
```python
from openai import OpenAI
import os

nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)
# Chain reasoning: deepseek-ai/deepseek-r1
# CVE synthesis: nvidia/nemotron-3-super-120b-a12b  
# Phishing gen: meta/llama-3.3-70b-instruct
```
