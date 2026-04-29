"""SQLAlchemy ORM models for SentryIQ.

Core data models representing CVE records, SMB stacks, vulnerability chains,
and simulation campaigns. All models use PostgreSQL and timezone-aware datetimes.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    Numeric,
    String,
    Text,
    UUID,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class CVERecord(Base):
    """CVE record ingested from NVD API.
    
    Represents a single Common Vulnerabilities and Exposures entry with CVSS,
    EPSS, CWE associations, and CPE product impact data.
    """

    __tablename__ = "cve_records"

    cve_id: str = Column(String(30), primary_key=True, index=True)
    """CVE identifier (e.g., CVE-2024-12345)."""

    description: str = Column(Text, nullable=False)
    """Vulnerability description from NVD."""

    cvss_score: Optional[float] = Column(Numeric(3, 1), nullable=True)
    """CVSS v3.1 base score (0-10)."""

    cvss_vector: Optional[str] = Column(String(255), nullable=True)
    """CVSS v3.1 vector string (e.g., CVSS:3.1/AV:N/AC:L...)."""

    cwe_ids: list[str] = Column(JSON, default=list, nullable=False)
    """Associated CWE weakness IDs extracted from CVE record."""

    affected_cpes: list[str] = Column(JSON, default=list, nullable=False)
    """CPE product strings affected by this CVE."""

    is_kev: bool = Column(Boolean, default=False, index=True)
    """True if in CISA Known Exploited Vulnerabilities list."""

    epss_score: Optional[float] = Column(Numeric(5, 4), nullable=True)
    """FIRST EPSS exploit probability score (0-1)."""

    epss_percentile: Optional[float] = Column(Numeric(5, 4), nullable=True)
    """EPSS percentile ranking relative to other CVEs (0-1)."""

    published_date: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    """CVE publication date from NVD."""

    modified_date: datetime = Column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )
    """Last modification date from NVD."""

    patch_available: bool = Column(Boolean, default=False, index=True)
    """True if patch/update is available from vendor."""

    created_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    """Record insertion time."""

    updated_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    """Record last update time."""

    # Relationships
    stack_vulnerabilities = relationship(
        "StackVulnerability",
        back_populates="cve_record",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_cve_is_kev_epss", "is_kev", "epss_score"),
        Index("idx_cve_published", "published_date"),
        Index("idx_cve_modified", "modified_date"),
    )


class SMBStack(Base):
    """Registered tech stack for an SMB organization.
    
    Represents a single SMB customer and their declared software/infrastructure
    inventory using CPE product identifiers.
    """

    __tablename__ = "smb_stacks"

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """Unique stack identifier."""

    org_name: str = Column(String(255), nullable=False, index=True)
    """Organization/company name."""

    cpe_identifiers: list[str] = Column(JSON, default=list, nullable=False)
    """All declared CPE product strings in stack."""

    internet_facing_cpes: list[str] = Column(JSON, default=list, nullable=False)
    """Subset of CPEs exposed to internet (higher risk)."""

    compliance_frameworks: list[str] = Column(
        JSON, default=list, nullable=False
    )
    """Applicable compliance frameworks (e.g., ['NDPA', 'POPIA', 'PCI-DSS'])."""

    created_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    """Stack registration time."""

    updated_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    """Last stack update time."""

    # Relationships
    stack_vulnerabilities = relationship(
        "StackVulnerability",
        back_populates="stack",
        cascade="all, delete-orphan",
    )
    vuln_chains = relationship(
        "VulnChain", back_populates="stack", cascade="all, delete-orphan"
    )
    simulation_campaigns = relationship(
        "SimulationCampaign",
        back_populates="stack",
        cascade="all, delete-orphan",
    )
    employee_risk_scores = relationship(
        "EmployeeRiskScore",
        back_populates="stack",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("idx_stack_org", "org_name"),)


class StackVulnerability(Base):
    """CVE matched to a specific SMB stack with priority scoring.
    
    Represents the intersection of a detected CVE and an SMB's registered stack.
    Includes composite priority scoring and AI-generated remediation guidance.
    """

    __tablename__ = "stack_vulnerabilities"

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """Unique record identifier."""

    stack_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey("smb_stacks.id"),
        nullable=False,
        index=True,
    )
    """Reference to SMB stack."""

    cve_id: str = Column(
        String(30), ForeignKey("cve_records.cve_id"), nullable=False, index=True
    )
    """Reference to CVE record."""

    priority_score: float = Column(Numeric(5, 2), nullable=False, index=True)
    """Composite SentryIQ priority score (0-100)."""

    priority_label: str = Column(
        String(20), nullable=False, index=True
    )  # CRITICAL, HIGH, MEDIUM, LOW
    """Human-readable priority label."""

    chain_id: Optional[str] = Column(
        UUID(as_uuid=True),
        ForeignKey("vuln_chains.id"),
        nullable=True,
        index=True,
    )
    """Reference to chain if this CVE is part of a detected chain."""

    plain_english_alert: Optional[str] = Column(Text, nullable=True)
    """Claude-generated plain-English alert (Grade 8 reading level)."""

    remediation_steps: Optional[str] = Column(Text, nullable=True)
    """Claude-generated fix/patch instructions."""

    is_resolved: bool = Column(Boolean, default=False, index=True)
    """True if patch has been applied or vulnerability mitigated."""

    detected_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    """Detection/match time."""

    resolved_at: Optional[datetime] = Column(TIMESTAMP(timezone=True), nullable=True)
    """Resolution time if is_resolved is True."""

    # Relationships
    stack = relationship("SMBStack", back_populates="stack_vulnerabilities")
    cve_record = relationship("CVERecord", back_populates="stack_vulnerabilities")
    chain = relationship("VulnChain", back_populates="vulnerabilities")

    __table_args__ = (
        Index("idx_stk_vuln_priority", "stack_id", "priority_score"),
        Index("idx_stk_vuln_resolved", "stack_id", "is_resolved"),
    )


class VulnChain(Base):
    """Detected vulnerability chain for an SMB stack.
    
    Represents a multi-hop attack path where combining multiple CVEs creates
    a more severe attack vector than any individual CVE alone.
    """

    __tablename__ = "vuln_chains"

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """Unique chain identifier."""

    stack_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey("smb_stacks.id"),
        nullable=False,
        index=True,
    )
    """Reference to SMB stack."""

    cve_ids: list[str] = Column(JSON, default=list, nullable=False)
    """CVE identifiers that form this chain."""

    cwe_path: list[str] = Column(JSON, default=list, nullable=False)
    """CWE weakness IDs in traversal order."""

    chain_score: float = Column(Numeric(5, 2), nullable=False, index=True)
    """Composite chain risk score with amplification."""

    attack_outcome: str = Column(String(50), nullable=False)
    """Expected attack outcome (e.g., RCE, PRIVESC, EXFIL)."""

    chain_narrative: Optional[str] = Column(Text, nullable=True)
    """Claude-generated explanation of attack chain."""

    detected_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    """Chain detection time."""

    # Relationships
    stack = relationship("SMBStack", back_populates="vuln_chains")
    vulnerabilities = relationship(
        "StackVulnerability",
        back_populates="chain",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_chain_score", "stack_id", "chain_score"),
        Index("idx_chain_outcome", "attack_outcome"),
    )


class SimulationCampaign(Base):
    """Phishing/vishing simulation campaign for an SMB stack.
    
    Represents a single targeted human risk assessment simulation campaign
    (phishing email, vishing call, etc.) with engagement metrics.
    """

    __tablename__ = "simulation_campaigns"

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """Unique campaign identifier."""

    stack_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey("smb_stacks.id"),
        nullable=False,
        index=True,
    )
    """Reference to SMB stack."""

    campaign_type: str = Column(String(50), nullable=False)
    """Type: 'phishing', 'vishing', 'smishing', 'deepfake'."""

    target_employee_role: Optional[str] = Column(String(100), nullable=True)
    """Job role targeted (e.g., 'finance', 'admin') for segmentation."""

    email_content: Optional[str] = Column(Text, nullable=True)
    """Generated phishing email body (if campaign_type='phishing')."""

    status: str = Column(String(50), default="pending", index=True)
    """Campaign status: pending, sent, in-progress, completed."""

    human_risk_delta: Optional[float] = Column(Numeric(4, 2), nullable=True)
    """Change in Human Risk Score after campaign completion."""

    launched_at: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    """Campaign launch time."""

    completed_at: Optional[datetime] = Column(TIMESTAMP(timezone=True), nullable=True)
    """Campaign completion time (when status='completed')."""

    # Relationships
    stack = relationship("SMBStack", back_populates="simulation_campaigns")

    __table_args__ = (
        Index("idx_campaign_status", "stack_id", "status"),
        Index("idx_campaign_type", "campaign_type"),
    )


class EmployeeRiskScore(Base):
    """Individual employee human risk score within an SMB stack.
    
    Tracks human risk assessment for each employee based on simulation
    engagement: clicks, reports, and other behavioral indicators.
    """

    __tablename__ = "employee_risk_scores"

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    """Unique record identifier."""

    stack_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey("smb_stacks.id"),
        nullable=False,
        index=True,
    )
    """Reference to SMB stack."""

    employee_identifier: str = Column(String(255), nullable=False, index=True)
    """Hashed/anonymized employee identifier (never plain email)."""

    risk_score: float = Column(Numeric(5, 2), default=50.0, nullable=False, index=True)
    """Human risk score 0-100 (higher = more risky behavior)."""

    simulations_sent: int = Column(Numeric, default=0, nullable=False)
    """Count of simulations sent to this employee."""

    simulations_clicked: int = Column(Numeric, default=0, nullable=False)
    """Count of simulations where employee clicked malicious link."""

    simulations_reported: int = Column(Numeric, default=0, nullable=False)
    """Count of simulations where employee reported/flagged as suspicious."""

    last_updated: datetime = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    """Last risk score update time."""

    # Relationships
    stack = relationship("SMBStack", back_populates="employee_risk_scores")

    __table_args__ = (
        Index("idx_employee_risk", "stack_id", "risk_score"),
    )
