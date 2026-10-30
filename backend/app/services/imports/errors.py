from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
