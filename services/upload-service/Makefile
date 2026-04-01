format:
	uv run ruff format src/ tests/

typecheck:
	uv run ty check src/

lint:
	uv run ruff check --fix src/ tests/

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

pre-commit:
	uv run pre-commit run --all-files

quality:
	uv run ruff format src/ tests/
	uv run ruff check src/ tests/
	uv run ty check src/
	uv run pytest --cov=src --cov-report=term-missing
