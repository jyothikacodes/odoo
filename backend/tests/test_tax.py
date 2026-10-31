from decimal import Decimal
import pytest
from app.services.tax_service import TaxRule, compute_line_tax
from app.core.money import D

def test_tax_golden_vectors():
    t18_excl = TaxRule(id=1, name="GST 18%", kind="percentage", rate=Decimal("18"), price_included=False)
    t10_excl = TaxRule(id=2, name="Tax 10%", kind="percentage", rate=Decimal("10"), price_included=False)
    t18_incl = TaxRule(id=3, name="GST 18% incl.", kind="percentage", rate=Decimal("18"), price_included=True)
    t9_incl_1 = TaxRule(id=4, name="CGST 9% incl.", kind="percentage", rate=Decimal("9"), price_included=True)
    t9_incl_2 = TaxRule(id=5, name="SGST 9% incl.", kind="percentage", rate=Decimal("9"), price_included=True)
    tfixed_10 = TaxRule(id=6, name="Fixed Fee", kind="fixed", rate=Decimal("10.00"), price_included=False)

    # 1560.00 GST 18% excl -> 1560.00 / 280.80 / 1840.80
    r = compute_line_tax(D("1560.00"), 1, [t18_excl])
    assert r.net == D("1560.00")
    assert r.tax_total == D("280.80")
    assert r.line_total == D("1840.80")

    # 33.33 18% excl -> 33.33 / 6.00 / 39.33 (5.9994 rounds to 6.00)
    r = compute_line_tax(D("33.33"), 1, [t18_excl])
    assert r.net == D("33.33")
    assert r.tax_total == D("6.00")
    assert r.line_total == D("39.33")

    # 0.05 10% excl -> 0.05 / 0.01 / 0.06 (0.005 rounds to 0.01)
    r = compute_line_tax(D("0.05"), 1, [t10_excl])
    assert r.net == D("0.05")
    assert r.tax_total == D("0.01")
    assert r.line_total == D("0.06")

    # 1180.00 18% incl -> 1000.00 / 180.00 / 1180.00
    r = compute_line_tax(D("1180.00"), 1, [t18_incl])
    assert r.net == D("1000.00")
    assert r.tax_total == D("180.00")
    assert r.line_total == D("1180.00")

    # 1180.00 9% incl + 9% incl -> 1000.00 / 180.00 (90.00 + 90.00) / 1180.00
    r = compute_line_tax(D("1180.00"), 1, [t9_incl_1, t9_incl_2])
    assert r.net == D("1000.00")
    assert r.tax_total == D("180.00")
    assert r.line_total == D("1180.00")
    assert len(r.breakdown) == 2
    assert r.breakdown[0]["amount"] == "90.00"
    assert r.breakdown[1]["amount"] == "90.00"

    # 300.00 qty 3, fixed 10.00 excl -> 300.00 / 30.00 / 330.00
    r = compute_line_tax(D("300.00"), 3, [tfixed_10])
    assert r.net == D("300.00")
    assert r.tax_total == D("30.00")
    assert r.line_total == D("330.00")

    # 500.00 none -> 500.00 / 0.00 / 500.00
    r = compute_line_tax(D("500.00"), 1, [])
    assert r.net == D("500.00")
    assert r.tax_total == D("0.00")
    assert r.line_total == D("500.00")

    # 500.00 customer_exempt=True -> 500.00 / 0.00 / 500.00
    r = compute_line_tax(D("500.00"), 1, [t18_excl], customer_exempt=True)
    assert r.net == D("500.00")
    assert r.tax_total == D("0.00")
    assert r.line_total == D("500.00")

    # Mixing inclusive and exclusive must raise ValueError
    with pytest.raises(ValueError):
        compute_line_tax(D("100.00"), 1, [t18_excl, t18_incl])
