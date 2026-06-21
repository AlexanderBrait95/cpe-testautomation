"""FastAPI application factory for the CPE Dashboard."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from cpe_ta.dashboard import data as _data
from cpe_ta.dashboard.help import get_help_content
from cpe_ta.dashboard.models import (
    DomainStat,
    HelpContent,
    InventoryValidateResult,
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
        summaries = db_summaries if db_summaries else xml_summaries
        return entries, summaries

    def _get_run_detail_or_404(run_id: str) -> RunDetail:
        detail = _data.get_run_detail(db_path, run_id)
        if detail is None:
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
    def api_runs(
        status: str | None = Query(default=None),
        domain: str | None = Query(default=None),
        q: str | None = Query(default=None),
        sort: str | None = Query(default=None),
    ) -> list[RunSummary]:
        _, summaries = _load_entries_and_runs()
        filtered = _data.filter_runs(summaries, q=q)
        return _data.sort_runs(filtered, sort=sort)

    @app.get("/api/runs/active/progress", response_model=RunProgress)
    def api_progress() -> RunProgress:
        return _runner.progress()

    @app.post("/api/runs/active/cancel")
    def api_cancel_run() -> dict[str, str]:
        cancelled = _runner.cancel()
        if not cancelled:
            raise HTTPException(status_code=409, detail="No active run to cancel")
        return {"status": "cancelled"}

    @app.get("/api/runs/{run_id}/export")
    def api_export_run(run_id: str, format: str = Query(default="junit")) -> Response:
        detail = _get_run_detail_or_404(run_id)
        if format == "junit":
            content = _data.run_junit_bytes(detail)
            return Response(
                content=content,
                media_type="application/xml",
                headers={"Content-Disposition": f'attachment; filename="run-{run_id}.xml"'},
            )
        if format == "html":
            html = _data.render_run_html(detail)
            return Response(
                content=html.encode("utf-8"),
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="run-{run_id}.html"'},
            )
        raise HTTPException(status_code=422, detail=f"Unknown format {format!r}. Use 'junit' or 'html'.")

    @app.get("/api/runs/{run_id}", response_model=RunDetail)
    def api_run_detail(
        run_id: str,
        status: str | None = Query(default=None),
        domain: str | None = Query(default=None),
        q: str | None = Query(default=None),
    ) -> RunDetail:
        detail = _get_run_detail_or_404(run_id)
        if status or domain or q:
            filtered_tests = _data.filter_entries(detail.tests, status=status, domain=domain, q=q)
            return RunDetail(
                run_id=detail.run_id,
                timestamp=detail.timestamp,
                duration_s=detail.duration_s,
                git_sha=detail.git_sha,
                tests=filtered_tests,
            )
        return detail

    @app.get("/api/testbed", response_model=TestbedStatus)
    def api_testbed() -> TestbedStatus:
        return _data.get_testbed_status(testbed_path)

    @app.get("/api/help", response_model=HelpContent)
    def api_help() -> HelpContent:
        return get_help_content()

    @app.post("/api/inventory/validate", response_model=InventoryValidateResult)
    def api_inventory_validate(
        path: str | None = Query(default=None),
    ) -> InventoryValidateResult:
        from cpe_ta.core.config import ConfigError, load_testbed  # noqa: PLC0415
        from cpe_ta.core.inventory import validate_wiring_map  # noqa: PLC0415

        yaml_path = path or testbed_path or "testbed.yaml"
        p = Path(yaml_path)
        if not p.exists():
            return InventoryValidateResult(ok=False, errors=[f"File not found: {yaml_path}"])
        try:
            tb = load_testbed(str(p))
        except ConfigError as exc:
            return InventoryValidateResult(ok=False, errors=[str(exc)])
        except Exception as exc:  # noqa: BLE001
            return InventoryValidateResult(ok=False, errors=[f"Unexpected error: {exc}"])
        wiring_errors = validate_wiring_map(tb.wiring_map)
        if wiring_errors:
            return InventoryValidateResult(ok=False, errors=wiring_errors)
        return InventoryValidateResult(ok=True, errors=[])

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
