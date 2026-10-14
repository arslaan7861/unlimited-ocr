# Rule: Unified JSON Error Response Contract

## 1. Specification

All error responses returned by the API (HTTP 400, 404, 413, 415, 422, 500, 503) MUST strictly conform to the following schema:

```json
{
  "success": false,
  "message": "<High-level human readable error summary>",
  "errors": [
    {
      "field": "<dot.notated.field.path_or_unknown>",
      "message": "<Specific issue description>"
    }
  ]
}
```

## 2. Requirements

- `success`: Always `false` in error envelopes.
- `message`: High-level summary of the error condition.
- `errors`: Non-null array of objects containing `field` and `message`.
- Validation error locations from Pydantic or FastAPI must be normalized into dot notation:
  - `('body', 'file')` -> `"file"`
  - `('body', 'pages', 0)` -> `"pages.0"`
  - Empty or unspecified locations default to `"unknown"` or `"request"`.
- 500 internal server errors must log the full traceback internally but return a safe, sanitized generic message to clients.
