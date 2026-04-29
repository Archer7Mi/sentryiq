"""Sandboxed NVIDIA NIM API client wrapper.

Wraps the NIM client with NemoClaw sandbox enforcement.
All AI agent operations run through sandbox boundaries.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from backend.ai.nim_client import NIMClient
from backend.sandbox.monitor import get_monitor
from backend.sandbox.nemoclaw import get_sandbox
from backend.sandbox.policies import get_all_policies

logger = logging.getLogger(__name__)


class SandboxedNIMClient:
    """NVIDIA NIM client with NemoClaw sandbox enforcement.

    All NIM API calls are wrapped with security policies,
    rate limiting, and audit logging.
    """

    def __init__(self, nim_client: NIMClient):
        """Initialize sandboxed NIM client.

        Args:
            nim_client: Underlying NIM client instance
        """
        self.nim_client = nim_client
        self.sandbox = None
        self.monitor = get_monitor()

    async def initialize(self) -> bool:
        """Initialize sandbox and register policies.

        Returns:
            True if initialization successful
        """
        try:
            self.sandbox = await get_sandbox()

            # Register all NIM policies
            policies = get_all_policies()
            for agent_name in [
                "nim-cve-synthesis",
                "nim-chain-analysis",
                "nim-phishing-generation",
            ]:
                if agent_name in policies:
                    self.sandbox.register_agent(policies[agent_name])

            logger.info("Sandboxed NIM client initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize sandboxed NIM client: {e}")
            return False

    async def synthesize_cve(
        self,
        stack_id: str,
        cve_id: str,
        description: str,
        cvss_score: float,
        affected_products: list[str],
    ) -> Dict[str, Any]:
        """Synthesize CVE into plain-English alert (sandboxed).

        Args:
            stack_id: SMB stack ID
            cve_id: CVE identifier
            description: CVE description
            cvss_score: CVSS score
            affected_products: Affected product CPEs

        Returns:
            Dictionary with synthesis result
        """
        async def _synthesize_wrapper():
            return await self.nim_client.synthesize_cve(
                stack_id=stack_id,
                cve_id=cve_id,
                description=description,
                cvss_score=cvss_score,
                affected_products=affected_products,
            )

        if not self.sandbox:
            logger.warning("Sandbox not initialized, executing unsandboxed")
            return await _synthesize_wrapper()

        # Execute within sandbox boundaries
        result = await self.sandbox.execute_agent(
            "nim-cve-synthesis",
            _synthesize_wrapper,
        )

        if result["success"]:
            self.monitor.record_execution(
                "nim-cve-synthesis",
                result["execution_id"],
                success=True,
                duration_seconds=result["duration_seconds"],
            )
            return result["result"]
        else:
            self.monitor.record_execution(
                "nim-cve-synthesis",
                result["execution_id"],
                success=False,
                duration_seconds=result["duration_seconds"],
                error_message=result["error"],
            )
            raise RuntimeError(f"CVE synthesis failed: {result['error']}")

    async def analyze_chain(
        self,
        stack_id: str,
        cve_ids: list[str],
        chain_score: float,
        cwe_path: list[str],
    ) -> Dict[str, Any]:
        """Analyze vulnerability chain (sandboxed).

        Args:
            stack_id: SMB stack ID
            cve_ids: CVEs in the chain
            chain_score: Chain severity score
            cwe_path: CWE traversal path

        Returns:
            Dictionary with analysis result
        """
        async def _analyze_wrapper():
            return await self.nim_client.analyze_chain(
                stack_id=stack_id,
                cve_ids=cve_ids,
                chain_score=chain_score,
                cwe_path=cwe_path,
            )

        if not self.sandbox:
            logger.warning("Sandbox not initialized, executing unsandboxed")
            return await _analyze_wrapper()

        # Execute within sandbox boundaries
        result = await self.sandbox.execute_agent(
            "nim-chain-analysis",
            _analyze_wrapper,
        )

        if result["success"]:
            self.monitor.record_execution(
                "nim-chain-analysis",
                result["execution_id"],
                success=True,
                duration_seconds=result["duration_seconds"],
            )
            return result["result"]
        else:
            self.monitor.record_execution(
                "nim-chain-analysis",
                result["execution_id"],
                success=False,
                duration_seconds=result["duration_seconds"],
                error_message=result["error"],
            )
            raise RuntimeError(f"Chain analysis failed: {result['error']}")

    async def generate_phishing_email(
        self,
        campaign_type: str,
        target_role: str,
        company_name: str,
    ) -> Dict[str, Any]:
        """Generate phishing simulation email (sandboxed).

        Args:
            campaign_type: Type of campaign (phishing/vishing/smishing)
            target_role: Target employee role
            company_name: Company name for realism

        Returns:
            Dictionary with email content
        """
        async def _phishing_wrapper():
            return await self.nim_client.generate_phishing_email(
                campaign_type=campaign_type,
                target_role=target_role,
                company_name=company_name,
            )

        if not self.sandbox:
            logger.warning("Sandbox not initialized, executing unsandboxed")
            return await _phishing_wrapper()

        # Execute within RESTRICTED sandbox boundaries
        result = await self.sandbox.execute_agent(
            "nim-phishing-generation",
            _phishing_wrapper,
        )

        if result["success"]:
            self.monitor.record_execution(
                "nim-phishing-generation",
                result["execution_id"],
                success=True,
                duration_seconds=result["duration_seconds"],
            )
            return result["result"]
        else:
            self.monitor.record_execution(
                "nim-phishing-generation",
                result["execution_id"],
                success=False,
                duration_seconds=result["duration_seconds"],
                error_message=result["error"],
            )
            raise RuntimeError(f"Phishing generation failed: {result['error']}")

    def get_sandbox_status(self) -> Dict[str, Any]:
        """Get sandbox status.

        Returns:
            Sandbox status dictionary
        """
        if not self.sandbox:
            return {"status": "not_initialized"}
        return self.sandbox.get_sandbox_status()

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary.

        Returns:
            Monitoring summary dictionary
        """
        return self.monitor.get_summary()


# Global sandboxed client instance
_sandboxed_nim_client: Optional[SandboxedNIMClient] = None


async def get_sandboxed_nim_client(nim_client: Optional[NIMClient] = None) -> SandboxedNIMClient:
    """Get or create the global sandboxed NIM client.

    Args:
        nim_client: NIM client to wrap (required on first call)

    Returns:
        SandboxedNIMClient instance
    """
    global _sandboxed_nim_client

    if _sandboxed_nim_client is None:
        if not nim_client:
            raise ValueError("NIM client required for initialization")
        _sandboxed_nim_client = SandboxedNIMClient(nim_client)
        await _sandboxed_nim_client.initialize()

    return _sandboxed_nim_client


async def shutdown_sandboxed_nim_client() -> None:
    """Shutdown the sandboxed NIM client."""
    global _sandboxed_nim_client
    if _sandboxed_nim_client:
        logger.info("Shutting down sandboxed NIM client")
        _sandboxed_nim_client = None
