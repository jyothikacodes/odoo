from decimal import Decimal
from typing import List, Any
from app.core.money import q2, ZERO
from app.core.errors import ValidationError

def unit_price(product: Any, variants: List[Any]) -> Decimal:
    """product.sales_price + sum(variant.extra_price). Variants must belong to product and have distinct attribute_id."""
    attr_ids = [getattr(v, "attribute_id", None) for v in variants]
    if len(set(attr_ids)) != len(attr_ids):
        raise ValidationError("variant_ids", "One value per attribute")
    
    prod_id = getattr(product, "id", None)
    if any(getattr(v, "product_id", None) != prod_id for v in variants):
        raise ValidationError("variant_ids", "Variant does not belong to product")
        
    extra = sum((getattr(v, "extra_price", ZERO) for v in variants), ZERO)
    sales = getattr(product, "sales_price", ZERO)
    return q2(sales + extra)

def line_description(product: Any, variants: List[Any]) -> str:
    base_name = getattr(product, "name", "Product")
    if not variants:
        return base_name
    var_strs = []
    for v in variants:
        attr_name = getattr(getattr(v, "attribute", None), "name", "Option")
        val = getattr(v, "value", "")
        var_strs.append(f"{attr_name}: {val}")
    return f"{base_name} ({', '.join(var_strs)})"
