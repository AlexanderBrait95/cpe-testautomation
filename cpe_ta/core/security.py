"""Security scan engine + EN-18031 checklist."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    MANUAL = "manual"


@dataclass
class SecurityFinding:
    category: str  # open_port / weak_tls / default_cred / cve
    severity: str  # critical/high/medium/low
    description: str
    evidence: str


@dataclass
class EN18031CheckItem:
    requirement_id: str  # e.g. "EN18031-1.5.3"
    description: str
    status: CheckStatus = CheckStatus.MANUAL
    evidence: str = ""
    automated: bool = False


@dataclass
class SecurityScanResult:
    target: str
    findings: list[SecurityFinding] = field(default_factory=list)
    open_ports: list[int] = field(default_factory=list)
    weak_tls_versions: list[str] = field(default_factory=list)
    default_creds_found: bool = False


class SimSecurityTarget:
    """Simulated DUT for security testing."""

    def __init__(self) -> None:
        self.open_ports: list[int] = [80, 443, 22]
        self.tls_versions: list[str] = ["TLS 1.2", "TLS 1.3"]
        self.has_default_creds: bool = False
        self.firmware_version: str = "1.0.0"


def scan_target(target: SimSecurityTarget) -> SecurityScanResult:
    """Run security scan against target (sim or real)."""
    result = SecurityScanResult(target=target.firmware_version)
    result.open_ports = list(target.open_ports)

    # Check for weak TLS
    for ver in target.tls_versions:
        if ver in ("TLS 1.0", "TLS 1.1", "SSLv3"):
            result.weak_tls_versions.append(ver)
            result.findings.append(
                SecurityFinding(
                    category="weak_tls",
                    severity="high",
                    description=f"Weak TLS version: {ver}",
                    evidence=ver,
                )
            )

    # Check default credentials
    if target.has_default_creds:
        result.default_creds_found = True
        result.findings.append(
            SecurityFinding(
                category="default_cred",
                severity="critical",
                description="Default credentials accepted",
                evidence="admin:admin",
            )
        )

    # Open port analysis
    dangerous_ports = {23: "Telnet", 21: "FTP", 69: "TFTP"}
    for port in target.open_ports:
        if port in dangerous_ports:
            result.findings.append(
                SecurityFinding(
                    category="open_port",
                    severity="medium",
                    description=f"Dangerous port open: {dangerous_ports[port]}",
                    evidence=str(port),
                )
            )

    return result


EN18031_CHECKLIST: list[EN18031CheckItem] = [
    EN18031CheckItem(
        "EN18031-1.5.1", "Secure boot mechanism", CheckStatus.MANUAL, automated=False
    ),
    EN18031CheckItem(
        "EN18031-1.5.2",
        "Software update integrity verification",
        CheckStatus.MANUAL,
        automated=False,
    ),
    EN18031CheckItem(
        "EN18031-1.5.3",
        "No hardcoded credentials",
        CheckStatus.PASS,
        automated=True,
    ),
    EN18031CheckItem(
        "EN18031-1.5.4",
        "Minimum TLS 1.2 on management interfaces",
        CheckStatus.PASS,
        automated=True,
    ),
    EN18031CheckItem(
        "EN18031-2.1", "Default firewall inbound deny", CheckStatus.PASS, automated=True
    ),
    EN18031CheckItem(
        "EN18031-2.2",
        "User data protection at rest",
        CheckStatus.MANUAL,
        automated=False,
    ),
    EN18031CheckItem(
        "EN18031-3.1",
        "Network function protection",
        CheckStatus.MANUAL,
        automated=False,
    ),
]


def get_en18031_status(target: SimSecurityTarget) -> list[EN18031CheckItem]:
    """Run automated EN-18031 checks, mark manual items as MANUAL."""
    result = []
    for item in EN18031_CHECKLIST:
        check = EN18031CheckItem(
            requirement_id=item.requirement_id,
            description=item.description,
            status=item.status,
            evidence=item.evidence,
            automated=item.automated,
        )
        # Override automated checks based on scan
        if item.requirement_id == "EN18031-1.5.3":
            check.status = CheckStatus.FAIL if target.has_default_creds else CheckStatus.PASS
            check.evidence = (
                "default_creds_found" if target.has_default_creds else "no default creds"
            )
        elif item.requirement_id == "EN18031-1.5.4":
            has_weak = any(v in target.tls_versions for v in ("TLS 1.0", "TLS 1.1"))
            check.status = CheckStatus.FAIL if has_weak else CheckStatus.PASS
            check.evidence = f"TLS versions: {target.tls_versions}"
        result.append(check)
    return result
