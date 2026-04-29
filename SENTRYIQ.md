# SentryIQ — Master Context File
> This file is the single source of truth for all AI tools working on this project.
> Claude Code: read this file at the start of every session via `@SENTRYIQ.md`
> GitHub Copilot: this file is referenced in `.github/copilot-instructions.md`
> Last updated: April 2026

---

## What Is SentryIQ

SentryIQ is an open-source, AI-powered unified cybersecurity platform built specifically
for small and medium-sized businesses (SMBs). It is the first platform to combine:

1. **Technical Shield** — Automated CVE/CWE ingestion, vulnerability chain detection,
   and AI-prioritized patch queues
2. **Human Shield** — Deepfake social engineering simulation, human risk scoring,
   and compliance mapping

It is designed for non-technical SMB administrators — all AI output is plain English,
calibrated to Grade 8 reading level. It has a specific focus on the African SMB market
and includes native compliance mapping for NDPA (Nigeria), POPIA (South Africa),
and Kenya Data Protection Act 2019.

**Author:** Michael Ted
**License:** Apache License 2.0
**Repository:** https://github.com/Archer7Mi/sentryiq
**Status:** Active development — Hackathon build phase

---

## Absolute Rules (Never Violate)

- NEVER generate exploit code, weaponizable scripts, or offensive security tooling
- NEVER store SMB stack data unencrypted
- NEVER log API keys, credentials, or sensitive stack information
- ALL simulation features require explicit organizational administrator consent
- ALL AI output targeting non-technical users must be plain English (Grade 8 level)
- ALL agents must operate within NemoClaw sandbox boundaries when implemented
- This is a DEFENSIVE tool only

---

## Tech Stack

### Backend
- **Language:** Python 3.14.2
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL 16
- **Cache/Queue:** Redis 7
- **Task Scheduler:** APScheduler
- **Package Manager:** pip + requirements.txt

### Frontend
- **Framework:** React 18
- **Styling:** Tailwind CSS
- **State:** Zustand
- **HTTP Client:** Axios

### AI/ML Layer
- **Primary Reasoning:** NVIDIA NIM API (free tier)
  - Chain detection: `deepseek-ai/deepseek-r1` via NIM
  - CVE synthesis: `nvidia/nemotron-3-super-120b-a12b` via NIM
  - Phishing generation: `meta/llama-3.3-70b-instruct` via NIM
- **Fallback/Design:** Anthropic Claude (claude.ai — architecture sessions only)
- **NIM Base URL:** `https://integrate.api.nvidia.com/v1`
- **NIM Key Env Var:** `NVIDIA_API_KEY`

### Agent Security (Phase 3)
- **Framework:** NVIDIA NemoClaw (alpha)
- **Purpose:** Kernel-level sandboxing of SentryIQ's internal agents

### Infrastructure
- **Containers:** Docker 29.1.3
- **Cloud Target:** AWS (af-south-1 — Cape Town region)
- **CI/CD:** GitHub Actions

### Data Sources (all free, no licensing)
- NVD REST API v2.0 — CVE database
- CISA KEV JSON — Known Exploited Vulnerabilities
- FIRST EPSS API — Exploit prediction scores
- MITRE CWE XML — Weakness taxonomy
- OWASP Top 10 (2021) — Web app risk categories
- OWASP API Security Top 10 (2023) — API risk categories
- NVD CPE Dictionary — Product enumeration

---

## Repository Structure

```
sentryiq/
├── SENTRYIQ.md                    # This file — master context
├── CLAUDE.md                      # Claude Code specific instructions
├── README.md                      # Public-facing project README
├── LICENSE                        # Apache 2.0
├── docker-compose.yml             # Local development environment
├── .github/
│   ├── copilot-instructions.md    # Copilot always-on context
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI pipeline
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python dependencies
│   ├── config.py                  # Environment config (pydantic-settings)
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── schemas.py             # Pydantic schemas
│   │   └── connection.py          # DB connection pool
│   ├── ingestion/
│   │   ├── nvd_worker.py          # NVD API polling worker
│   │   ├── kev_worker.py          # CISA KEV sync worker
│   │   └── epss_worker.py         # FIRST EPSS score worker
│   ├── intelligence/
│   │   ├── stack_matcher.py       # CPE-based CVE-to-stack matching
│   │   ├── chain_detector.py      # CWE graph chain detection engine
│   │   └── prioritizer.py        # Composite priority scoring
│   ├── ai/
│   │   ├── nim_client.py          # NVIDIA NIM API client
│   │   ├── synthesizer.py         # Plain-English alert generation
│   │   └── prompts/
│   │       ├── chain_analysis.py  # Chain detection prompts
│   │       ├── cve_synthesis.py   # CVE plain-English prompts
│   │       └── phishing_gen.py    # Phishing simulation prompts
│   ├── simulation/
│   │   ├── phishing.py            # Phishing campaign engine
│   │   ├── vishing.py             # Voice simulation (Phase 2)
│   │   └── scoring.py             # Human Risk Score calculator
│   ├── compliance/
│   │   └── mapper.py              # CVE → compliance framework mapping
│   └── api/
│       ├── routes/
│       │   ├── stacks.py          # Stack management endpoints
│       │   ├── vulnerabilities.py # CVE/alert endpoints
│       │   ├── simulations.py     # Simulation management endpoints
│       │   └── compliance.py      # Compliance report endpoints
│       └── middleware.py          # Auth, rate limiting, logging
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Dashboard/
│   │   │   ├── AlertQueue/
│   │   │   ├── StackWizard/
│   │   │   ├── SimulationCenter/
│   │   │   └── ComplianceMap/
│   │   └── store/
│   │       └── index.js
│   └── public/
├── data/
│   ├── cwe_graph/                 # CWE prerequisite relationship definitions
│   ├── owasp_mappings/            # OWASP Top 10 → CWE mappings
│   └── compliance_frameworks/    # NDPA, POPIA, Kenya DPA rule sets
├── tests/
│   ├── test_ingestion.py
│   ├── test_chain_detection.py
│   └── test_stack_matching.py
├── docs/
│   ├── architecture/              # Architecture decision records (ADRs)
│   ├── api/                       # API documentation
│   └── ai-sessions/               # Exported claude.ai session context
└── infra/
    ├── docker-compose.yml
    └── aws/                       # AWS CDK infrastructure code
```

---

## Database Schema (Core Tables)

```sql
-- CVE records ingested from NVD
cve_records (
  cve_id VARCHAR PRIMARY KEY,       -- e.g. CVE-2024-12345
  description TEXT,
  cvss_score DECIMAL(3,1),
  cvss_vector VARCHAR,
  cwe_ids TEXT[],                   -- Associated CWE weakness IDs
  affected_cpes TEXT[],             -- CPE product strings
  is_kev BOOLEAN DEFAULT FALSE,     -- CISA KEV membership
  epss_score DECIMAL(5,4),          -- FIRST EPSS probability
  epss_percentile DECIMAL(5,4),
  published_date TIMESTAMP,
  modified_date TIMESTAMP,
  patch_available BOOLEAN
)

-- SMB registered stacks
smb_stacks (
  id UUID PRIMARY KEY,
  org_name VARCHAR,
  cpe_identifiers TEXT[],           -- Declared CPE product strings
  internet_facing_cpes TEXT[],      -- Subset exposed to internet
  compliance_frameworks TEXT[],     -- e.g. ['NDPA', 'PCI-DSS']
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- CVEs matched to a specific SMB stack
stack_vulnerabilities (
  id UUID PRIMARY KEY,
  stack_id UUID REFERENCES smb_stacks,
  cve_id VARCHAR REFERENCES cve_records,
  priority_score DECIMAL(5,2),      -- Composite SentryIQ score
  priority_label VARCHAR,           -- CRITICAL/HIGH/MEDIUM/LOW
  chain_id UUID,                    -- NULL if standalone vuln
  plain_english_alert TEXT,         -- Claude-generated explanation
  remediation_steps TEXT,           -- Claude-generated fix steps
  is_resolved BOOLEAN DEFAULT FALSE,
  detected_at TIMESTAMP,
  resolved_at TIMESTAMP
)

-- Detected vulnerability chains
vuln_chains (
  id UUID PRIMARY KEY,
  stack_id UUID REFERENCES smb_stacks,
  cve_ids TEXT[],                   -- CVEs in this chain
  cwe_path TEXT[],                  -- CWE traversal path
  chain_score DECIMAL(5,2),
  attack_outcome VARCHAR,           -- e.g. 'RCE', 'PRIVESC', 'EXFIL'
  chain_narrative TEXT,             -- Claude-generated chain explanation
  detected_at TIMESTAMP
)

-- Phishing simulation campaigns
simulation_campaigns (
  id UUID PRIMARY KEY,
  stack_id UUID REFERENCES smb_stacks,
  campaign_type VARCHAR,            -- 'phishing','vishing','smishing'
  target_employee_role VARCHAR,
  email_content TEXT,
  status VARCHAR,                   -- 'pending','sent','clicked','reported'
  human_risk_delta DECIMAL(4,2),    -- HRS change after simulation
  launched_at TIMESTAMP,
  completed_at TIMESTAMP
)

-- Employee human risk scores
employee_risk_scores (
  id UUID PRIMARY KEY,
  stack_id UUID REFERENCES smb_stacks,
  employee_identifier VARCHAR,      -- Hashed, never plain email
  risk_score DECIMAL(5,2),          -- 0-100
  simulations_sent INTEGER DEFAULT 0,
  simulations_clicked INTEGER DEFAULT 0,
  simulations_reported INTEGER DEFAULT 0,
  last_updated TIMESTAMP
)
```

---

## Chain Detection Algorithm

The chain detection engine builds a directed attack graph using CWE prerequisite
relationships. Here is the core logic:

```
1. For each CVE matched to the SMB stack:
   - Extract associated CWE IDs
   - Look up CWE in prerequisite graph (cwe_graph/)

2. Build directed graph:
   - Nodes = CWE weakness categories
   - Edges = prerequisite relationships (CWE-A enables CWE-B)

3. Traverse graph depth-first from each node:
   - Find paths of length >= 2 where ALL component CVEs exist in stack
   - Record complete path + CVEs involved

4. Score each chain:
   Chain Score = max(individual CVSS) 
               × chain_amplification_factor    # 1.5x for 2-hop, 2.0x for 3+hop
               × max(EPSS scores in chain)
               × KEV_bonus                     # 1.3x if any CVE is in KEV

5. Flag chains above threshold as CRITICAL regardless of individual scores
```

---

## NIM API Integration Pattern

```python
from openai import OpenAI

nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

# Model routing per task:
# Chain detection/reasoning → deepseek-ai/deepseek-r1
# CVE plain-English synthesis → nvidia/nemotron-3-super-120b-a12b
# Phishing generation → meta/llama-3.3-70b-instruct
```

---

## Current Build Status

### ✅ Completed
- Project documentation (v2.0 Industry Edition)
- Database schema design
- Repository structure design
- Chain detection algorithm design
- NIM API integration pattern
- Development environment (Python 3.14.2, Docker 29.1.3)
- **Phase 1 Database Layer**: SQLAlchemy 2.0 async models (6 core tables)
- **Phase 1 DB Connection**: Async engine with connection pooling
- **Phase 1 Ingestion Config**: Environment-based settings (Pydantic)
- **Phase 1 NVD Worker**: NVD API v2.0 polling (async, paginated, hourly)
- **Phase 1 KEV Worker**: CISA KEV catalog sync (6-hourly)
- **Phase 1 EPSS Worker**: FIRST EPSS score fetching (daily)
- **Requirements.txt**: All Phase 1 dependencies pinned
- **docker-compose.yml**: PostgreSQL 16 + Redis 7 configured

### 🔄 In Progress
- Phase 2: Stack matcher + chain detection engine

### ⏳ Not Started
- Stack fingerprinting wizard
- CVE-to-stack matching implementation
- Chain detection algorithm implementation
- NIM AI integration (Claude API synthesis prompts)
- React dashboard
- Phishing simulation engine
- NemoClaw agent sandboxing

---

## Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| AI provider | NVIDIA NIM (free tier) | Cost — Claude API too expensive for student budget |
| License | Apache 2.0 | Patent protection + digital sovereignty alignment |
| Primary language | Python | Security library ecosystem, NVD API compatibility |
| DB | PostgreSQL | Relational CVE/stack mapping, chain graph storage |
| African compliance | NDPA + POPIA + Kenya DPA | Africa CyberFest mission, target market |
| Model for chain reasoning | DeepSeek-R1 via NIM | Best open model for multi-step logical reasoning |
| Agent security | NemoClaw (Phase 3) | Kernel-level sandboxing for agent trust architecture |

---

## Environment Variables Required

```bash
# AI
NVIDIA_API_KEY=nvapi-...           # NVIDIA NIM free tier key

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=...                     # JWT signing key
ENCRYPTION_KEY=...                 # Stack data encryption

# External APIs (all free)
NVD_API_KEY=...                    # Optional — increases NVD rate limit
HIBP_API_KEY=...                   # HaveIBeenPwned (Phase 2)
```

---

## Compliance Framework Mappings

| Framework | Jurisdiction | Key Articles Mapped |
|---|---|---|
| NDPA 2023 | Nigeria | Art. 24 (security), Art. 25 (breach notification) |
| POPIA | South Africa | Section 19 (security safeguards) |
| Kenya DPA 2019 | Kenya | Section 25 (security obligations) |
| PCI-DSS v4.0 | Global | Req. 6 (vuln management), Req. 11 (testing) |
| ISO 27001:2022 | Global | A.8.8 (vuln management), A.8.29 (secure dev) |
