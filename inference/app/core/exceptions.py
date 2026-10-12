"""Custom typed domain exceptions for the AI Inference Service."""


class InferenceException(Exception):
    """Base exception for all inference service errors."""

    def __init__(self, message: str, error_code: str = "INFERENCE_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ModelNotApprovedError(InferenceException):
    """Raised when attempting to load or execute a model failing the license gate."""

    def __init__(self, model_id: str, reason: str):
        super().__init__(
            message=f"Model '{model_id}' is not approved for production: {reason}",
            error_code="MODEL_LICENSE_NOT_APPROVED",
            status_code=403,
        )


class ModelNotFoundError(InferenceException):
    """Raised when requested model ID is not registered."""

    def __init__(self, model_id: str):
        super().__init__(
            message=f"Model '{model_id}' is not found in the model registry.",
            error_code="MODEL_NOT_FOUND",
            status_code=404,
        )


class ConcurrencyLimitExceededError(InferenceException):
    """Raised when GPU concurrency limit is saturated."""

    def __init__(
        self, message: str = "GPU inference service is currently busy. Please retry shortly."
    ):
        super().__init__(
            message=message,
            error_code="GPU_CONCURRENCY_EXCEEDED",
            status_code=503,
        )


class InvalidAudioReferenceError(InferenceException):
    """Raised when the uploaded reference voice does not meet quality/duration criteria."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Reference audio is invalid: {reason}",
            error_code="INVALID_REFERENCE_AUDIO",
            status_code=400,
        )


class TextNormalizationError(InferenceException):
    """Raised when input text cannot be normalized or is empty."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Text normalization error: {reason}",
            error_code="INVALID_INPUT_TEXT",
            status_code=400,
        )
