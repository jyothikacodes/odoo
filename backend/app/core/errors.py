from typing import Any, Optional

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=[{"field": field, "message": message}]
        )

class PasswordPolicyError(AppError):
    def __init__(self, failures: list):
        details = [{"field": "password", "rule": f.rule, "message": f.message} for f in failures]
        super().__init__(
            code="PASSWORD_POLICY",
            message="Password does not satisfy policy requirements",
            status_code=422,
            details=details
        )

class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource", message: Optional[str] = None):
        super().__init__(
            code="NOT_FOUND",
            message=message or f"{resource} not found",
            status_code=404
        )

class InvalidTransitionError(AppError):
    def __init__(self, action: str, current_status: str, allowed: list):
        super().__init__(
            code="INVALID_TRANSITION",
            message=f"Cannot perform action '{action}' on status '{current_status}'",
            status_code=409,
            details={"current_status": current_status, "allowed_actions": allowed}
        )

class PlanFlagDisallowsError(AppError):
    def __init__(self, message: str):
        super().__init__(
            code="PLAN_FLAG_DISALLOWS",
            message=message,
            status_code=409
        )

class PaymentExceedsDueError(AppError):
    def __init__(self, due: Any):
        super().__init__(
            code="PAYMENT_EXCEEDS_DUE",
            message=f"Payment amount exceeds amount due ({due})",
            status_code=422,
            details={"amount_due": str(due)}
        )

class InvoiceNotPayableError(AppError):
    def __init__(self, status: str):
        super().__init__(
            code="INVOICE_NOT_PAYABLE",
            message=f"Invoice in status '{status}' cannot accept payments",
            status_code=409
        )

class EmailTakenError(AppError):
    def __init__(self):
        super().__init__(
            code="EMAIL_TAKEN",
            message="An account with this email already exists",
            status_code=409
        )
