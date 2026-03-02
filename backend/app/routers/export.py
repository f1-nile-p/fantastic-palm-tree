import uuid
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PurchaseOrder

router = APIRouter(prefix="/api/export", tags=["export"])


def _prettify(element: Element) -> str:
    """Return a pretty-printed XML string for the given Element."""
    raw = tostring(element, encoding="unicode")
    reparsed = minidom.parseString(raw)
    return reparsed.toprettyxml(indent="  ")


@router.get("/orders/{po_id}/xml")
def export_po_xml(po_id: uuid.UUID, db: Session = Depends(get_db)):
    """Generate ERP-compatible XML for an approved purchase order."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    extracted = po.extracted_data or {}

    # Build XML tree
    root = Element("PurchaseOrder")

    header = SubElement(root, "Header")
    _sub(header, "PONumber", extracted.get("po_number") or str(po.id))
    _sub(header, "Vendor", extracted.get("vendor_name") or "")
    _sub(header, "Date", extracted.get("date") or str(po.created_at.date()))
    _sub(header, "Status", po.status)
    _sub(header, "Filename", po.filename)
    _sub(header, "ConfidenceScore", f"{po.confidence_score:.4f}" if po.confidence_score is not None else "")

    lines_el = SubElement(root, "Lines")
    for line in sorted(po.lines, key=lambda l: l.line_number):
        line_el = SubElement(lines_el, "Line")
        _sub(line_el, "LineNumber", str(line.line_number))
        _sub(line_el, "Description", line.raw_description or "")
        _sub(line_el, "ItemCode", line.matched_item_code or "")
        _sub(line_el, "ItemDescription", line.matched_item_description or "")
        _sub(line_el, "Quantity", str(line.quantity) if line.quantity is not None else "")
        _sub(line_el, "UOM", line.matched_uom_code or line.uom_raw or "")
        _sub(line_el, "UnitPrice", str(line.unit_price) if line.unit_price is not None else "")
        _sub(line_el, "TotalPrice", str(line.total_price) if line.total_price is not None else "")
        _sub(line_el, "Notes", line.notes or "")

    xml_content = _prettify(root)

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="po_{po_id}.xml"'},
    )


def _sub(parent: Element, tag: str, text: str) -> Element:
    el = SubElement(parent, tag)
    el.text = text
    return el
