"""FastAPI application factory for the CPE Dashboard."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cpe_ta.dashboard import data as _data
from cpe_ta.dashboard.models import (
    DomainStat,
    OverviewModel,
    RunDetail,
    RunProgress,
    RunStartRequest,
    RunSummary,
    TestbedStatus,
)
from cpe_ta.dashboard.runner import DashboardRunner

_STATIC_DIR = Path(__file__).parent / "static"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


def create_app(
    results_path: str = "test-results.xml",
    db_path: str | None = None,
    runner: DashboardRunner | None = None,
    testbed_path: str | None = None,
) -> FastAPI:
    """Create and configure the FastAPI dashboard application."""
    app = FastAPI(title="CPE Test-Automation Dashboard", version="1.0.0")

    _runner = runner or DashboardRunner()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_entries_and_runs() -> tuple[list, list[RunSummary]]:
        entries, xml_summaries = _data.load_results(results_path)
        db_summaries = _data.get_run_summaries(db_path)
        # Merge: DB runs first (authoritative), then XML import if no DB runs
        summaries = db_summaries if db_summaries else xml_summaries
        return entries, summaries

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.get("/api/overview", response_model=OverviewModel)
    def api_overview() -> OverviewModel:
        entries, summaries = _load_entries_and_runs()
        return _data.overview(entries, summaries)

    @app.get("/api/domains", response_model=list[DomainStat])
    def api_domains() -> list[DomainStat]:
        entries, _ = _load_entries_and_runs()
        return _data.domain_stats(entries)

    @app.get("/api/runs", response_model=list[RunSummary])
    def api_runs() -> list[RunSummary]:
        _, summaries = _load_entries_and_runs()
        return summaries

    @app.get("/api/runs/active/progress", response_model=RunProgress)
    def api_progress() -> RunProgress:
        return _runner.progress()

    @app.get("/api/runs/{run_id}", response_model=RunDetail)
    def api_run_detail(run_id: str) -> RunDetail:
        detail = _data.get_run_detail(db_path, run_id)
        if detail is None:
            # Fallback: check if it's the XML import run
            entries, summaries = _load_entries_and_runs()
            for s in summaries:
                if s.run_id == run_id:
                    return RunDetail(
                        run_id=run_id,
                        timestamp=s.timestamp,
                        duration_s=s.duration_s,
                        git_sha=s.git_sha,
                        tests=entries,
                    )
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        return detail

    @app.get("/api/testbed", response_model=TestbedStatus)
    def api_testbed() -> TestbedStatus:
        return _data.get_testbed_status(testbed_path)

    @app.post("/api/runs", status_code=202)
    def api_start_run(req: RunStartRequest) -> dict:
        from cpe_ta.dashboard.runner import validate_marker  # noqa: PLC0415

        try:
            validate_marker(req.markers)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if _runner.is_busy():
            raise HTTPException(status_code=409, detail="A run is already in progress")

        try:
            run_id = _runner.start(req.markers)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        return {"run_id": run_id, "status": "running"}

    # ------------------------------------------------------------------
    # Static frontend
    # ------------------------------------------------------------------

    if _STATIC_DIR.exists() and any(_STATIC_DIR.iterdir()):
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(str(_STATIC_DIR / "index.html"))

    return app
