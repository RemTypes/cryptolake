.PHONY: install dev lint type-check test serve ingest status clean

# ── Setup ────────────────────────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# ── Code Quality ─────────────────────────────────────────────────────────
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

lint-fix:
	ruff check --fix src/ tests/
	ruff format src/ tests/

type-check:
	mypy src/cryptolake

test:
	pytest tests/ -v --cov=src/cryptolake --cov-report=term-missing

# ── Application ──────────────────────────────────────────────────────────
serve:
	cryptolake serve --reload

ingest:
	cryptolake ingest --exchange binance --exchange coingecko

status:
	cryptolake status

# ── Cleanup ──────────────────────────────────────────────────────────────
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
