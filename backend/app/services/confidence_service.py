def score_po_line(line: dict, item_match: dict, uom_match: dict) -> float:
    """
    Score a single PO line 0.0–1.0.

    Weights:
    - item match score  : 0.4
    - uom match score   : 0.3
    - quantity + price  : 0.3
    """
    item_score = float(item_match.get("score", 0.0)) if item_match else 0.0
    uom_score = float(uom_match.get("score", 0.0)) if uom_match else 0.0

    has_quantity = 1.0 if line.get("quantity") not in (None, 0) else 0.0
    has_price = 1.0 if line.get("unit_price") not in (None, 0) else 0.0
    presence_score = (has_quantity + has_price) / 2.0

    return round(
        item_score * 0.4 + uom_score * 0.3 + presence_score * 0.3,
        4,
    )


def score_po(lines: list[dict]) -> float:
    """Return the average confidence score across all lines."""
    if not lines:
        return 0.0
    total = sum(line.get("confidence_score", 0.0) or 0.0 for line in lines)
    return round(total / len(lines), 4)
