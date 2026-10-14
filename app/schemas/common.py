"""Common API schemas including unified error contracts and health responses."""

from pydantic import BaseModel, ConfigDict, Field


class ErrorItem(BaseModel):
    """Specific field-level or contextual error issue.

    Attributes:
        field (str): Dot-notated path to the field or error source.
        message (str): Explanatory error detail.
    """

    model_config = ConfigDict(extra="forbid")

    field: str = Field(
        ...,
        description="Dot-notated field path or error source",
        examples=["file.size", "pages.0"],
    )
    message: str = Field(
        ...,
        description="Specific issue description",
        examples=["File exceeds maximum allowed size of 25MB"],
    )


class ErrorResponse(BaseModel):
    """Standard unified error response envelope.

    Attributes:
        success (bool): Always false for error responses.
        message (str): High-level human readable error summary.
        errors (list[ErrorItem]): List of specific error issues.
    """

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(default=False, description="Operation success indicator")
    message: str = Field(..., description="High-level human readable error summary")
    errors: list[ErrorItem] = Field(default_factory=list, description="Specific error details")


class HealthResponse(BaseModel):
    """Service liveness and model status response.

    Attributes:
        status (str): Service liveness state ('healthy').
        model_loaded (bool): Indicates if model weights are loaded and ready.
        device (str): Active compute device (e.g. 'cpu', 'cuda').
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="healthy", description="Service liveness state")
    model_loaded: bool = Field(..., description="Whether model is loaded into memory")
    device: str = Field(..., description="Active compute device")
