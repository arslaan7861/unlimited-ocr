# Workflow: Development Setup & Execution

## 1. Environment Setup

The project uses `uv` for fast, deterministic dependency management.

```bash
# Initialize / sync dependencies
uv sync

# Activate virtual environment (if working in terminal)
source .venv/bin/activate
```

## 2. Model Checkpoint Management

Model weights can be located locally under `models/unlimited-ocr/` or loaded directly from Hugging Face:

```bash
# Model directory is ignored by Git. Weights can be downloaded via huggingface-cli:
uv run huggingface-cli download baidu/Unlimited-OCR --local-dir models/unlimited-ocr
```

## 3. Launching Development Server

```bash
# Run server with live reload on port 8000
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. API Endpoints

- Health check: `GET http://localhost:8000/health`
- Readiness check: `GET http://localhost:8000/health/ready`
- Interactive Swagger docs: `http://localhost:8000/docs`
- Image OCR: `POST http://localhost:8000/api/v1/ocr/image`
- PDF OCR: `POST http://localhost:8000/api/v1/ocr/pdf`
