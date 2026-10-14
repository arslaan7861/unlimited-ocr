# Rule: Architecture & Component Boundaries

## 1. Modular Separation of Concerns

The application strictly separates responsibilities across layers:
- `app/api/`: Routing and request ingestion. No business logic, OCR algorithms, or direct model calls.
- `app/schemas/`: Pydantic models for validation, request parsing, and response serialization.
- `app/services/`: Core logic:
  - `model_service.py`: Encapsulates model weight loading, device resolution, and raw inference.
  - `image_ocr.py`: Validates image magic bytes, runs PIL transformations, offloads to thread pool with semaphore.
  - `pdf_ocr.py`: Streams PDF pages one by one via PyMuPDF (`fitz`), prevents OOM, runs page-by-page inference.
- `app/startup/lifespan.py`: FastAPI lifespan context manager. Loads models once during server startup and assigns singletons to `app.state`.
- `app/core/`: Centralized domain exceptions, structured logging, and unified exception handlers.

## 2. Lifespan Model Management
- **Never initialize models inside route functions or request handlers.**
- The model must be loaded once on startup inside `app/startup/lifespan.py` and attached to `app.state.model_service`.
- Model path is read from `Settings.model_path` (supporting local directory and Hugging Face ID).
- Missing weights or hardware errors must NOT immediately crash the application; set `app.state.is_ready = False` so `/health/ready` signals 503 while allowing diagnosis.

## 3. Concurrency & Event Loop Protection
- PyTorch inference is synchronous and CPU/GPU-bound.
- Route handlers must always use `asyncio.to_thread` or thread pools to run inference.
- All inference calls must acquire `app.state.semaphore` (`MAX_CONCURRENT_INFERENCES`) to protect against RAM exhaustion.
