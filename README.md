# SentryIQ

**AI-Powered Unified Cybersecurity Platform for Small and Medium-Sized Businesses**

> Detect. Chain. Prioritize. Simulate. Defend.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14%2B-green.svg)](https://python.org)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)]()

---

## The Problem

SMBs face the same sophisticated cyberattacks as Fortune 500 companies — but with a fraction of the budget, staff, and expertise. In Africa alone, cybercrime caused over USD 3 billion in losses between 2019 and 2025. Meanwhile:

- 40,009 new CVEs were published in 2024 alone — 108 per day
- The median time to mass-exploit a vulnerability after disclosure: **0 days**
- 60% of all breaches involve a human action — phishing, vishing, deepfakes
- Only 11% of SMBs have adopted any AI security tool
- Over 80% of organizations have no protocol for handling deepfake attacks

Existing enterprise tools (Tenable, Qualys, Rapid7) are too expensive, too complex, and not built for African SMB realities.

---

## The Solution

SentryIQ is the first unified, open-source platform to address both the **technical** and **human** attack surfaces in a single, affordable, plain-English platform.

### Pillar 1 — Technical Shield
- **Automated CVE Intelligence** — continuous ingestion from NVD, CISA KEV, FIRST EPSS
- **Stack Fingerprinting** — maps your exact tech stack to affected vulnerabilities
- **Vulnerability Chain Detection** — finds dangerous CVE combinations that individual scores miss
- **AI-Prioritized Patch Queue** — plain-English action items powered by NVIDIA NIM

### Pillar 2 — Human Shield
- **Deepfake Social Engineering Simulation** — spear phishing, voice cloning, multi-channel attacks
- **Human Risk Scoring** — continuous employee risk tracking
- **Compliance Mapping** — NDPA, POPIA, Kenya DPA, PCI-DSS, ISO 27001

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Archer7Mi/sentryiq.git
cd sentryiq

# Copy environment template
cp .env.example .env
# Add your NVIDIA NIM API key (free at build.nvidia.com)

# Start with Docker
docker compose up -d

# Backend available at http://localhost:8000
# Frontend available at http://localhost:3000
# API docs at http://localhost:8000/docs
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14 + FastAPI |
| Database | PostgreSQL 16 + Redis 7 |
| AI Engine | NVIDIA NIM API (DeepSeek-R1, Nemotron, Llama 3.3) |
| Frontend | React 18 + Tailwind CSS |
| Agent Security | NVIDIA NemoClaw (Phase 3) |
| Infrastructure | Docker + AWS (af-south-1) |

---

## Data Sources

All vulnerability intelligence sources are **free and open** — no licensing costs:

- [NVD / NIST](https://nvd.nist.gov/) — CVE database
- [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) — Known exploited vulnerabilities
- [FIRST EPSS](https://www.first.org/epss/) — Exploit prediction scores
- [MITRE CWE](https://cwe.mitre.org/) — Weakness taxonomy
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Web application risks
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) — API risks

---

## Roadmap

- **Phase 1** (Current) — Data pipeline: CVE ingestion, stack matching, chain detection
- **Phase 2** — Voice/vishing simulation, OWASP API Top 10, advanced chains
- **Phase 3** — Deepfake video simulation, NemoClaw agent sandboxing, supply chain risk
- **Phase 4** — Agentic auto-remediation, African threat intel sharing network
- **Phase 5** — Multilingual output (French, Swahili, Hausa, Amharic, Portuguese)

---

## African Market Focus

SentryIQ is built with the African SMB in mind:

- Native compliance mapping for NDPA (Nigeria), POPIA (South Africa), Kenya DPA 2019
- Designed for bandwidth-constrained environments
- Plain-English output suitable for non-technical administrators
- Post-hackathon roadmap includes multilingual African language support
- AWS af-south-1 (Cape Town) deployment for data residency

---

## Contributing

Contributions welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a PR.

All contributors must agree that SentryIQ is a **defensive tool only**. No offensive security capabilities will be merged.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

Copyright 2026 Michael Ted

---

## Acknowledgements

Built for the Africa CyberFest 2026 Solutions Hackathon — Open Track.
Powered by NVIDIA NIM, FastAPI, and the open-source security community.
