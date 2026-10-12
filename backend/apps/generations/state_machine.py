"""State machine validating job lifecycle transitions."""


class InvalidStateTransitionError(Exception):
    """Raised when an illegal status change is attempted on a GenerationJob."""

    def __init__(self, from_state: str, to_state: str):
        super().__init__(f"Cannot transition GenerationJob from '{from_state}' to '{to_state}'.")
        self.from_state = from_state
        self.to_state = to_state


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"RUNNING", "CANCELLED"},
    "RUNNING": {"SUCCEEDED", "FAILED", "CANCELLED"},
    "SUCCEEDED": set(),  # Terminal state
    "FAILED": {"PENDING"},  # Allow retry
    "CANCELLED": set(),  # Terminal state
}


def validate_transition(current_state: str, next_state: str) -> None:
    """Validate that transition from current_state to next_state is legal."""
    valid_targets = ALLOWED_TRANSITIONS.get(current_state, set())
    if next_state not in valid_targets:
        raise InvalidStateTransitionError(current_state, next_state)
