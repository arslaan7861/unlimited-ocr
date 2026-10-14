# Rule: Mandatory Google Python Style Docstrings

Every Python module, class, public/private method, route handler, and utility function in this repository MUST have complete Google-style docstrings.

## Format Specification

```python
"""Short single-line summary of functionality.

Optional extended explanation describing behavior, side effects,
or relevant algorithms.

Args:
    param1 (type): Description of param1.
    param2 (type, optional): Description of param2. Defaults to value.

Returns:
    return_type: Description of returned value.

Raises:
    ExceptionType: Circumstances under which this error is raised.
"""
```

## Guidelines
- Write docstrings for all modules (top of file).
- Include class-level docstrings listing primary attributes.
- Accurately document all arguments and return types matching Python type annotations.
- Document domain exceptions in the `Raises:` section.
