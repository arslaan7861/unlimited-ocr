# AGENTS.md: Unlimited-OCR Microservice Guidance

Welcome to the Baidu Unlimited-OCR microservice codebase. This file serves as an index and quick-reference guide for autonomous AI coding agents and human engineers working on this repository.

---

## 1. Directory & Codebase Architecture

```text
unlimited-ocr/
├── .agents/
│   ├── rules/
│   │   ├── architecture.md       # Router, schema, service, and lifespan boundaries
│   │   ├── error-contract.md     # Unified JSON error response contract
│   │   ├── docstrings.md         # Mandatory Google Python docstring standard
│   │   └── token-efficiency.md   # Guidelines for agent tool calling & token efficiency
│   └── workflows/
│       ├── dev-workflow.md       # Dev server, setup, and model handling
│       └── test-and-verify.md    # Linting, compile, and pytest execution
├── AGENTS.md                     # This file
├── app/
│   ├── config/settings.py        # Pydantic Settings configuration
│   ├── core/                     # Exceptions, logging, and unified error handlers
│   ├── middlewares/              # X-Request-ID correlation tracking
│   ├── startup/lifespan.py       # Lifespan singleton model loader & semaphore
│   ├── schemas/                  # Pydantic v2 data models
│   ├── services/                 # ModelService, image OCR, and streaming PDF OCR
│   └── api/                      # Health and OCR v1 endpoints
├── models/unlimited-ocr/         # Local model weights directory (git-ignored)
└── tests/                        # Comprehensive unit & validation tests
```

---

## 2. Core Operational Rules for Agents

1. **Follow the Unified Error Contract**:
   Every error response must match `{ "success": false, "message": "...", "errors": [...] }`. See `.agents/rules/error-contract.md`.
2. **Never Load Models in Route Handlers**:
   Models are lifespan singletons in `app.state.model_service`. See `.agents/rules/architecture.md`.
3. **Async Safety & Concurrency Limits**:
   Wrap blocking inference with `asyncio.to_thread` and enforce `app.state.semaphore`.
4. **Mandatory Google-Style Docstrings**:
   Every module, class, method, endpoint, and helper requires complete Google docstrings. See `.agents/rules/docstrings.md`.
5. **Fast Offline Testing**:
   Unit tests must never download weights or require a GPU. Use the `mock_model_service` fixture in `tests/conftest.py`.

---

## 3. Workflows Quick Reference

- **Development Server**: `uv run uvicorn app.main:app --reload --port 8000`
- **Lint & Format**: `uv run ruff check .` and `uv run ruff format .`
- **Compile Verification**: `python3 -m compileall app tests`
- **Run Unit Tests**: `uv run pytest -v -m "not integration"`
- **Run Full Integration Tests**: `uv run pytest -v`
