# Workflow: Test & Verification

## 1. Syntax & Bytecode Compilation Check

Ensure all Python files compile cleanly without syntax errors:

```bash
python3 -m compileall app tests
```

## 2. Linting and Code Formatting (Ruff)

```bash
# Check for lint violations
uv run ruff check .

# Check formatting
uv run ruff format --check .

# Auto-apply fixes and formatting
uv run ruff check --fix .
uv run ruff format .
```

## 3. Automated Pytest Suite

Run offline unit and validation tests:

```bash
# Run unit test suite (fast, offline, uses mocked model)
uv run pytest -v -m "not integration"

# Run tests with coverage
uv run pytest --cov=app tests/

# Run integration tests (only when local model weights and hardware are available)
uv run pytest -v -m "integration"
```
