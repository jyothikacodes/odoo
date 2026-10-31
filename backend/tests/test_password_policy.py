import pytest
from app.services.password_policy import validate_password

def test_password_policy_golden_vectors():
    # Abcdefg!1 (9 chars) -> none
    assert len(validate_password("Abcdefg!1")) == 0

    # Abcdef!1 (8 chars) -> min_length
    res = validate_password("Abcdef!1")
    assert any(f.rule == "min_length" for f in res)

    # abcdefgh!1 -> uppercase
    res = validate_password("abcdefgh!1")
    assert any(f.rule == "uppercase" for f in res)

    # ABCDEFGH!1 -> lowercase
    res = validate_password("ABCDEFGH!1")
    assert any(f.rule == "lowercase" for f in res)

    # Abcdefghi1 -> special
    res = validate_password("Abcdefghi1")
    assert any(f.rule == "special" for f in res)

    # abcdefgh (8 chars) -> min_length, uppercase, special
    res = validate_password("abcdefgh")
    rules = {f.rule for f in res}
    assert {"min_length", "uppercase", "special"}.issubset(rules)

    # 129 * 'A' + 'a!' -> max_length
    res = validate_password("A" * 129 + "a!")
    assert any(f.rule == "max_length" for f in res)

    # Passw0rd!x with email passw0rd@x.com -> contains_identity
    res = validate_password("Passw0rd!x", email="passw0rd@x.com")
    assert any(f.rule == "contains_identity" for f in res)
