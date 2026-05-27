.PHONY: install run test lint fmt clean

install:
	python -m pip install -e ".[dev]"

run:
	python -m circle_cycle

test:
	pytest --cov=src --cov-report=term-missing

lint:
	ruff check . && mypy src

fmt:
	ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov dist *.egg-info
