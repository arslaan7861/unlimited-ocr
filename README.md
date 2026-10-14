# Baidu Unlimited-OCR FastAPI Microservice

Production-ready, modular FastAPI service powered by [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) for high-accuracy text extraction from images and scanned PDF documents.

---

## Features
- **Standalone Microservice**: Clean FastAPI architecture with lifespan management and Pydantic v2 validation.
- **Image & PDF Ingestion**: Supports `image/png`, `image/jpeg`, `image/webp`, and multi-page `application/pdf`.
- **Memory-Safe PDF Streaming**: Streams and renders PDF pages one at a time via PyMuPDF (`fitz`) to prevent memory ballooning and OOM errors on large documents.
- **Async Concurrency Throttling**: Synchronous PyTorch model inference is offloaded to worker threads and throttled via an `asyncio.Semaphore` to safeguard 16 GB RAM / CPU instances.
- **Unified Error Contract**: All errors (400, 404, 413, 415, 422, 500, 503) strictly follow `{ "success": false, "message": "...", "errors": [...] }`.
- **Request Correlation & Structured Logging**: Every request is assigned an `X-Request-ID` correlation ID, tracked in logs via `contextvars`, and returned in response headers.
- **Health & Readiness Probes**: `/health` (liveness) and `/health/ready` (readiness) for automated orchestrators and document pipelines.
- **Autonomous Agent Guidelines**: Complete `.agents/` directory containing rules and verification workflows.

---

## Technology Stack
- **Manager**: `uv`
- **Framework**: FastAPI + Uvicorn
- **OCR Engine**: Baidu Unlimited-OCR (PyTorch / Transformers / Hugging Face)
- **Document Processing**: Pillow (Images) & PyMuPDF (PDFs)
- **Settings & Validation**: `pydantic-settings` & `pydantic` v2
- **Testing & Quality**: `pytest`, `pytest-asyncio`, `httpx`, `ruff`

---

## Directory Structure

```text
unlimited-ocr/
├── .agents/                  # Autonomous agent rules and workflows
│   ├── rules/
│   │   ├── architecture.md
│   │   ├── error-contract.md
│   │   ├── docstrings.md
│   │   └── token-efficiency.md
│   └── workflows/
│       ├── dev-workflow.md
│       └── test-and-verify.md
├── AGENTS.md                 # Agent and developer index
├── app/
│   ├── main.py               # Application factory & entrypoint
│   ├── config/settings.py    # Environment configuration
│   ├── core/                 # Logger, exceptions, and error handlers
│   ├── middlewares/          # Request correlation middleware
│   ├── startup/lifespan.py   # Model loading and resource initialization
│   ├── schemas/              # Common and OCR Pydantic schemas
│   ├── services/             # ModelService, image_ocr, and pdf_ocr
│   └── api/                  # Routes (/health, /api/v1/ocr)
├── models/
│   └── unlimited-ocr/        # Local model weights directory (git-ignored)
├── tests/                    # Offline unit, mock, and validation tests
├── .env.example              # Environment variables template
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Quickstart

### 1. Installation
Install dependencies using `uv`:
```bash
uv sync
```

### 2. Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```

Key environment variables:
| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `models/unlimited-ocr` | Local weight directory or Hugging Face repo ID |
| `DEVICE` | `cpu` | Compute device (`cpu`, `cuda`, `auto`) |
| `TORCH_DTYPE` | `bfloat16` | PyTorch weight precision |
| `MAX_UPLOAD_SIZE_MB` | `25` | Max upload size in megabytes |
| `MAX_PDF_PAGES` | `50` | Maximum allowed pages per PDF |
| `MAX_CONCURRENT_INFERENCES` | `2` | Max concurrent model inference calls |
| `PDF_DPI` | `300` | Rasterization resolution for PDF pages |

### 3. Run Development Server
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs are available at `http://localhost:8000/docs`.

---

## API Reference

### 1. Health Probe
```bash
curl -X GET http://localhost:8000/health
```
Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu"
}
```

### 2. Readiness Probe
```bash
curl -X GET http://localhost:8000/health/ready
```
Returns `HTTP 200` when the model is initialized, or `HTTP 503` if weights are missing or unready.

### 3. Image OCR
```bash
curl -X POST http://localhost:8000/api/v1/ocr/image \
  -F "file=@document.png"
```
Response:
```json
{
  "success": true,
  "filename": "document.png",
  "text": "Extracted text content...",
  "processing_time_seconds": 0.85,
  "metadata": {
    "format": "PNG",
    "width": 1200,
    "height": 1600
  }
}
```

### 4. Scanned PDF OCR
```bash
curl -X POST http://localhost:8000/api/v1/ocr/pdf \
  -F "file=@invoice.pdf"
```
Response:
```json
{
  "success": true,
  "filename": "invoice.pdf",
  "page_count": 2,
  "pages": [
    { "page_number": 1, "text": "Invoice Number: INV-1024" },
    { "page_number": 2, "text": "Total Amount: INR 12500" }
  ],
  "text": "Invoice Number: INV-1024\n\nTotal Amount: INR 12500",
  "processing_time_seconds": 3.42
}
```

---

## Testing & Quality

```bash
# Verify Python bytecode compilation
python3 -m compileall app tests

# Run Ruff linter and formatter
uv run ruff check .
uv run ruff format --check .

# Run offline unit and validation test suite
uv run pytest -v -m "not integration"
```
