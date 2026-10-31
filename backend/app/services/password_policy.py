import re
from dataclasses import dataclass
from typing import Optional, List
from app.core.errors import PasswordPolicyError

MIN_LEN = 9            # "more than eight characters"
MAX_LEN = 128

@dataclass(frozen=True)
class RuleFailure:
    rule: str          # "min_length" | "uppercase" | "lowercase" | "special" | "max_length" | "common" | "contains_identity"
    message: str

COMMON = {"password", "password1", "123456789", "qwertyuiop", "abcdefghi", "welcome123", "admin12345"}

def validate_password(pw: str, *, email: Optional[str] = None, name: Optional[str] = None) -> List[RuleFailure]:
    f: List[RuleFailure] = []
    if len(pw) < MIN_LEN:
        f.append(RuleFailure("min_length", "Must be more than 8 characters"))
    if len(pw) > MAX_LEN:
        f.append(RuleFailure("max_length", "Must be at most 128 characters"))
    if not re.search(r"[A-Z]", pw):
        f.append(RuleFailure("uppercase", "Must contain an uppercase letter"))
    if not re.search(r"[a-z]", pw):
        f.append(RuleFailure("lowercase", "Must contain a lowercase letter"))
    if not re.search(r"[^A-Za-z0-9]", pw):
        f.append(RuleFailure("special", "Must contain a special character"))
    if pw.lower() in COMMON:
        f.append(RuleFailure("common", "Password is too common"))
    local = (email or "").split("@")[0].lower()
    if local and len(local) >= 4 and local in pw.lower():
        f.append(RuleFailure("contains_identity", "Must not contain your email name"))
    return f

def check_password_or_raise(pw: str, email: Optional[str] = None, name: Optional[str] = None) -> None:
    failures = validate_password(pw, email=email, name=name)
    if failures:
        raise PasswordPolicyError(failures)
