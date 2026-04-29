# Cline Instructions — Build NVIDIA NIM Integration for SentryIQ

## Project Context

**SentryIQ** — Open-source AI-powered cybersecurity platform for African SMBs
- **Author:** Michael Ted
- **Repo:** https://github.com/Archer7Mi/sentryiq
- **License:** Apache 2.0
- **Status:** 8 phases complete (data pipeline, intelligence, testing, Docker). NOW: Implement NIM integration.

**Earlier Conversation:** https://claude.ai/share/2a1475c0-0453-445a-a390-b61e21634ddd
- Covers project genesis, architecture decisions, full design rationale
- Includes Phase 0-8 roadmap and completed phases
- Reference this for context on why we chose NIM, NemoClaw, and plain-English output

---

## What You're Building: NIM Client Integration (Missing from Phase 3)

SentryIQ currently has NO NIM integration code. The documentation describes it, but the actual implementation is missing.

### What NIM Is Used For
- **CVE Synthesis** — Nemotron-3-Super-120B-A12B generates plain-English CVE explanations (Grade 8 level)
- **Chain Analysis** — DeepSeek-R1 reasons through vulnerability chains to find attack paths
- **Phishing Generation** — Llama 3.3 70B creates realistic phishing simulation emails

### NIM API Details
- **Base URL:** `https://integrate.api.nvidia.com/v1`
- **Auth:** Environment variable `NVIDIA_API_KEY` (free tier, 5,000 credits)
- **API Type:** OpenAI-compatible (use `openai` Python library with custom base_url)

---

## Your Task: Build 3 Files

### 1. `backend/src/sentryiq_api/ai/nim_client.py` (NEW)

**Purpose:** Wrapper around NVIDIA NIM API

**Must include:**
- `NIMClient` class with async methods
- `synthesize_cve(cve_data)` → uses Nemotron-3-Super for plain-English CVE summary
- `analyze_chain(chain_cves, cwe_graph)` → uses DeepSeek-R1 for chain reasoning
- `generate_phishing_email(target_role, organization_context)` → uses Llama 3.3 for email generation
- Error handling, retry logic, rate limiting awareness
- Type hints, docstrings on all methods
- Pydantic schemas for all input/output

**Key Requirements:**
- Async/await throughout (FastAPI compatibility)
- Plain-English output calibrated to Grade 8 reading level
- NEVER expose API keys in logs or responses
- All AI output must be defensive (no exploit suggestions)

### 2. `backend/src/sentryiq_api/ai/prompts.py` (NEW)

**Purpose:** Centralized prompt templates for NIM calls

**Must include:**
- `CVE_SYNTHESIS_PROMPT` — template for Nemotron to explain a CVE
- `CHAIN_ANALYSIS_PROMPT` — template for DeepSeek-R1 to analyze chains
- `PHISHING_EMAIL_PROMPT` — template for Llama to generate phishing campaign content

**Prompt Guidelines:**
- CVE synthesis: Explain what the vulnerability is, who is affected, what the patch is, in plain English
- Chain analysis: Analyze the prerequisites, attack path, and business impact
- Phishing generation: Create realistic but clearly for-testing emails (must say "TEST CAMPAIGN" in header)

### 3. Update `backend/src/sentryiq_api/main.py` (EXISTING)

**Add:**
- Import NIMClient
- Initialize NIMClient on FastAPI startup
- Make it available to routes via dependency injection
- Add endpoints that call NIM:
  - `POST /api/ai/vulnerabilities/{stack_id}/synthesize` — synthesize all CVEs for a stack
  - `POST /api/ai/chains/{stack_id}/analyze` — analyze detected chains for a stack
  - `POST /api/ai/simulations/{campaign_id}/generate-email` — generate phishing email for campaign

---

## Files to Reference

Read these FIRST for context:

1. **`SENTRYIQ.md`** — Master project file with full architecture
2. **`backend/src/sentryiq_api/models.py`** — Data models for CVE, Chain, Stack
3. **`backend/src/sentryiq_api/routes.py`** — Existing route structure
4. **`docker-compose.yml`** — Service configuration
5. **`.env.example`** — Environment variables including `NVIDIA_API_KEY`

---

## Code Standards (MUST FOLLOW)

- **Python:** PEP 8, type hints required, docstrings on all classes/methods
- **FastAPI:** async/await everywhere, Pydantic v2 schemas for all inputs/outputs
- **Security:** 
  - NEVER hardcode API keys
  - NEVER log sensitive data
  - Validate all external API inputs before processing
  - This is a DEFENSIVE tool only — no exploit suggestions
- **AI Output:** Plain English, Grade 8 reading level, non-technical SMB admin audience
- **Testing:** Add pytest tests for each NIM method (mock the API calls)

---

## Exact Steps

1. **Read** `SENTRYIQ.md` sections on "NIM API Integration Pattern" and "Chain Detection Algorithm"
2. **Create** `backend/src/sentryiq_api/ai/__init__.py` (empty package marker)
3. **Create** `backend/src/sentryiq_api/ai/nim_client.py` with NIMClient class
4. **Create** `backend/src/sentryiq_api/ai/prompts.py` with prompt templates
5. **Update** `backend/src/sentryiq_api/main.py` to initialize NIMClient and add endpoints
6. **Test** the 3 NIM methods locally (mock calls if needed, don't burn real credits yet)
7. **Commit** with message: `feat: Add NVIDIA NIM integration for CVE synthesis, chain analysis, and phishing generation`

---

## When You Get Stuck

- Check the earlier conversation: https://claude.ai/share/2a1475c0-0453-445a-a390-b61e21634ddd
- Reference Phase 3 section in SENTRYIQ.md for expected behavior
- Remember: NIM is OpenAI-compatible, so use the `openai` Python library
- Ask me (Claude via claude.ai) if logic is unclear

---

## Success Criteria

✅ `nim_client.py` exists with 3 async methods  
✅ All methods type-hinted and documented  
✅ Prompts are in `prompts.py` not hardcoded  
✅ Main.py initializes NIMClient on startup  
✅ 3 new API endpoints added  
✅ No API keys in code or logs  
✅ Tests written (even if mocked)  
✅ Commit pushed to GitHub  

**Go.**
