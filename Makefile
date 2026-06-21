.PHONY: install lint typecheck test verify clean

# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------
install:
	pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# lint  (ruff)
# ---------------------------------------------------------------------------
lint:
	ruff check cpe_ta tests

# ---------------------------------------------------------------------------
# typecheck  (mypy --strict on core + hal base)
# ---------------------------------------------------------------------------
typecheck:
	mypy --strict cpe_ta/core cpe_ta/hal/base.py 2>/dev/null || mypy --strict cpe_ta/core
	mypy --strict cpe_ta/dashboard/data.py cpe_ta/dashboard/models.py

# ---------------------------------------------------------------------------
# test  (all tests, no coverage)
# ---------------------------------------------------------------------------
test:
	pytest tests -v

# ---------------------------------------------------------------------------
# verify  (= lint + typecheck + headless-suite with coverage + junitxml)
# ---------------------------------------------------------------------------
verify: lint typecheck
	pytest -m "not hardware" -n auto --junitxml=test-results.xml \
	    --cov=cpe_ta --cov-report=term-missing -q
	@echo "=== Verify Gate PASSED ==="

# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f test-results.xml .coverage
	rm -rf htmlcov .mypy_cache .ruff_cache
