"""NVIDIA NIM API client wrapper.

OpenAI-compatible interface to NVIDIA NIM models for CVE analysis,
chain reasoning, and alert synthesis.
"""

import json
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Model routing
MODEL_CHAIN_REASONING = "deepseek-ai/deepseek-r1"  # Best for complex multi-step logic
MODEL_CVE_SYNTHESIS = "nvidia/nemotron-3-super-120b-a12b"  # CVE explanation
MODEL_PHISHING_GEN = "meta/llama-3.3-70b-instruct"  # Phishing simulation


class NIMClient:
    """NVIDIA NIM API client.
    
    Uses OpenAI-compatible API to call NVIDIA NIM models for:
    - CVE chain reasoning (DeepSeek-R1)
    - CVE synthesis (Nemotron)
    - Phishing content generation (Llama)
    """

    def __init__(
        self,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        api_key: Optional[str] = None,
    ):
        """Initialize NIM client.
        
        Args:
            base_url: NIM API base URL. Defaults to NVIDIA's endpoint.
                      Can be overridden for testing or OpenRouter.
            api_key: API key for authentication. Defaults to NVIDIA_API_KEY env var.
        """
        self.base_url = base_url or os.getenv(
            "NIM_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY not found. Set via env var or constructor."
            )

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def synthesize_cve(
        self,
        cve_id: str,
        description: str,
        cvss_score: Optional[float],
        affected_systems: list[str],
    ) -> dict:
        """Generate plain-English CVE alert.
        
        Uses Nemotron to create Grade-8-level explanation of a CVE
        and its impact on an organization.
        
        Args:
            cve_id: CVE identifier
            description: Technical CVE description from NVD
            cvss_score: CVSS v3.1 base score
            affected_systems: List of affected system/product names
            
        Returns:
            Dict with keys:
                - alert: Plain-English alert text
                - remediation: Patch/mitigation steps
                - urgency: How urgent (Critical/High/Medium/Low)
        """
        logger.info(f"Synthesizing alert for {cve_id}")

        prompt = f"""You are a cybersecurity expert explaining vulnerabilities to business owners.

CVE: {cve_id}
Technical Description: {description}
Severity (CVSS): {cvss_score or 'Unknown'}/10
Affects: {', '.join(affected_systems)}

Generate a brief, non-technical explanation of:
1. What this vulnerability is
2. Why it matters to this organization
3. What action to take

Use simple language (Grade 8 reading level). Keep each section to 2-3 sentences.
Format your response as valid JSON with keys: "alert", "remediation", "urgency"
"""

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": MODEL_CVE_SYNTHESIS,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Try to parse JSON from response
        try:
            # Extract JSON from response (may have markdown code blocks)
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse NIM response: {e}")
            result = {
                "alert": content[:500],
                "remediation": "Contact your IT team.",
                "urgency": "Medium",
            }

        return result

    async def analyze_chain(
        self,
        cve_ids: list[str],
        cwe_path: list[str],
        attack_description: str,
    ) -> dict:
        """Analyze vulnerability chain using chain-of-thought reasoning.
        
        Uses DeepSeek-R1 to reason through how multiple CVEs combine
        into a more severe attack vector.
        
        Args:
            cve_ids: List of CVE IDs in chain
            cwe_path: List of CWE weaknesses in attack path
            attack_description: High-level description of the attack
            
        Returns:
            Dict with keys:
                - narrative: Plain-English chain explanation
                - attack_steps: Numbered steps attacker would take
                - impact: Expected outcome if chain is exploited
        """
        logger.info(f"Analyzing chain: {' → '.join(cve_ids)}")

        prompt = f"""You are analyzing an attack chain in a business network.

Attack Chain: {' → '.join(cve_ids)}
CWE Weaknesses: {' → '.join(cwe_path)}
Context: {attack_description}

Explain in simple terms:
1. How these vulnerabilities work together
2. The steps an attacker would take
3. What damage could result

Keep it brief and non-technical. Format as JSON with keys: 
"narrative", "attack_steps", "impact"
"""

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": MODEL_CHAIN_REASONING,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": 800,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse chain analysis: {e}")
            result = {
                "narrative": content[:500],
                "attack_steps": ["Contact IT team for remediation"],
                "impact": "Potential system compromise",
            }

        return result

    async def generate_phishing_email(
        self,
        target_role: str,
        company_context: str,
    ) -> dict:
        """Generate phishing simulation email.
        
        Uses Llama to create realistic-but-educational phishing content
        for human risk assessment simulations.
        
        Args:
            target_role: Job role being targeted (e.g., "finance", "admin")
            company_context: Brief org context for personalization
            
        Returns:
            Dict with keys:
                - subject: Email subject line
                - body: Email body
                - sender_identity: What the email claims to be from
        """
        logger.info(f"Generating phishing simulation for {target_role}")

        prompt = f"""Create a realistic phishing email for security training.

Target: {target_role} employee
Organization Context: {company_context}

Generate a plausible phishing email that would be used in a security awareness 
simulation. It should be convincing but not malicious. Use common phishing tactics.

Format as JSON with keys: "subject", "body", "sender_identity"
Keep the body under 200 words.
"""

        response = await self.client.post(
            "/chat/completions",
            json={
                "model": MODEL_PHISHING_GEN,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 500,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse phishing email: {e}")
            result = {
                "subject": "[Training] Security Update Required",
                "body": "Please update your security settings. Click here to continue.",
                "sender_identity": "IT Security Team",
            }

        return result
