from __future__ import annotations


class ProviderRequestError(RuntimeError):
    def __init__(self, *, stage: str, reason: str, message: str) -> None:
        super().__init__(message)
        self.stage = stage
        self.reason = reason
        self.message = message
