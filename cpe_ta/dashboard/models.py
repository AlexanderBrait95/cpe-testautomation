"""Pydantic v2 response models for the CPE Dashboard API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DomainStat(BaseModel):
    name: str
    passed: int
    failed: int
    skipped: int
    error: int
    total: int
    pass_rate: float  # 0.0..1.0


class LastRun(BaseModel):
    run_id: str
    timestamp: float
    duration_s: float
    git_sha: str


class OverviewModel(BaseModel):
    passed: int
    failed: int
    skipped: int
    error: int
    total: int
    last_run: LastRun | None
    domains: list[DomainStat]


class RunSummary(BaseModel):
    run_id: str
    timestamp: float
    duration_s: float
    passed: int
    failed: int
    skipped: int
    error: int
    total: int
    git_sha: str


class TestEntry(BaseModel):
    name: str
    domain: str
    status: str  # passed | failed | skipped | error
    duration_s: float
    message: str | None = None
    stacktrace: str | None = None
    params: dict[str, Any] | None = None


class RunDetail(BaseModel):
    run_id: str
    timestamp: float
    duration_s: float
    git_sha: str
    tests: list[TestEntry]


class DeviceStatus(BaseModel):
    name: str
    type: str
    connected: bool
    detail: str = ""


class TestbedStatus(BaseModel):
    dut: str
    hal_devices: list[DeviceStatus]
    services: list[str]
    source: str  # "sim" | "real" | "missing"


class RunStartRequest(BaseModel):
    markers: str


class RunProgress(BaseModel):
    status: str  # running | finished | failed | idle | cancelled
    run_id: str | None = None
    started: float | None = None
    lines_tail: list[str] = []
    counts: dict[str, int] = {}


# ---------------------------------------------------------------------------
# Help / Onboarding models (§15, AC-36..AC-39)
# ---------------------------------------------------------------------------


class HelpQuickstartStep(BaseModel):
    order: int
    title: str
    description: str
    command: str | None = None


class HelpDevice(BaseModel):
    name: str
    purpose: str
    connection: str
    sim_available: bool


class HelpService(BaseModel):
    key: str
    name: str
    purpose: str
    sim_available: bool
    note: str


class HelpContent(BaseModel):
    quickstart: list[HelpQuickstartStep]
    hardware: list[HelpDevice]
    infrastructure: list[HelpService]


# ---------------------------------------------------------------------------
# Inventory validation model (§15, AC-43)
# ---------------------------------------------------------------------------


class InventoryValidateResult(BaseModel):
    ok: bool
    errors: list[str]
