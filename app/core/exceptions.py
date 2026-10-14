"""Domain exceptions for the Unlimited-OCR service."""


class AppException(Exception):
    """Base application exception for unified error handling.

    Attributes:
        status_code (int): HTTP status code.
        message (str): High-level human readable error summary.
        errors (list[dict[str, str]]): List of specific field issues.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        errors: list[dict[str, str]] | None = None,
        field: str | None = None,
    ) -> None:
        """Initialize AppException.

        Args:
            message (str): High-level human readable error summary.
            status_code (int): HTTP status code. Defaults to 500.
            errors (list[dict[str, str]] | None): Detailed errors list.
            field (str | None): Optional field name to auto-populate errors list.
        """
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        if errors is not None:
            self.errors = errors
        elif field is not None:
            self.errors = [{"field": field, "message": message}]
        else:
            self.errors = []


class BadRequestException(AppException):
    """Exception raised when a client sends an invalid request (HTTP 400)."""

    def __init__(
        self,
        message: str = "Bad Request",
        field: str = "request",
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        """Initialize BadRequestException.

        Args:
            message (str): Summary of bad request. Defaults to "Bad Request".
            field (str): Name of the invalid field. Defaults to "request".
            errors (list[dict[str, str]] | None): Optional list of errors.
        """
        super().__init__(
            message=message,
            status_code=400,
            errors=errors,
            field=field if errors is None else None,
        )


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found (HTTP 404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        field: str = "resource",
    ) -> None:
        """Initialize NotFoundException.

        Args:
            message (str): Error message. Defaults to "Resource not found".
            field (str): Resource identifier or field. Defaults to "resource".
        """
        super().__init__(
            message=message,
            status_code=404,
            errors=[{"field": field, "message": message}],
        )


class PayloadTooLargeException(AppException):
    """Exception raised when uploaded payload exceeds size constraints (HTTP 413)."""

    def __init__(
        self,
        message: str = "Payload exceeds maximum allowed size",
        field: str = "file.size",
    ) -> None:
        """Initialize PayloadTooLargeException.

        Args:
            message (str): Error message. Defaults to "Payload exceeds maximum allowed size".
            field (str): Field identifier. Defaults to "file.size".
        """
        super().__init__(
            message=message,
            status_code=413,
            errors=[{"field": field, "message": message}],
        )


class UnsupportedMediaTypeException(AppException):
    """Exception raised when uploaded file type is unsupported (HTTP 415)."""

    def __init__(
        self,
        message: str = "Unsupported media type",
        field: str = "file.content_type",
    ) -> None:
        """Initialize UnsupportedMediaTypeException.

        Args:
            message (str): Error message. Defaults to "Unsupported media type".
            field (str): Field identifier. Defaults to "file.content_type".
        """
        super().__init__(
            message=message,
            status_code=415,
            errors=[{"field": field, "message": message}],
        )


class InferenceException(AppException):
    """Exception raised when model inference fails or service is unready."""

    def __init__(
        self,
        message: str = "OCR model inference failed",
        status_code: int = 500,
        errors: list[dict[str, str]] | None = None,
        field: str = "model",
    ) -> None:
        """Initialize InferenceException.

        Args:
            message (str): Error message. Defaults to "OCR model inference failed".
            status_code (int): HTTP status code. Defaults to 500.
            errors (list[dict[str, str]] | None): Optional list of errors.
            field (str): Field identifier. Defaults to "model".
        """
        super().__init__(
            message=message,
            status_code=status_code,
            errors=errors,
            field=field if errors is None else None,
        )
