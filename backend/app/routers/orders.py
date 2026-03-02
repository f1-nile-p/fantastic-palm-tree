import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PurchaseOrder, POLine
from app.schemas import (
    PurchaseOrderResponse,
    PurchaseOrderSummary,
    PurchaseOrderUpdate,
    POLineResponse,
    POLineUpdate,
)
from app.services.document_parser import parse_document
from app.services.llm_service import extract_po_data
from app.services import rag_service, confidence_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/upload", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
async def upload_po(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and process a purchase order document."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # 1. Parse document text
    raw_text = parse_document(file_bytes, file.filename or "upload")

    # 2. Extract structured data via LLM
    extracted_data = {}
    if raw_text:
        try:
            extracted_data = await extract_po_data(raw_text)
        except Exception as exc:
            logger.warning("LLM extraction failed: %s", exc)

    # 3. Build PO record
    po = PurchaseOrder(
        filename=file.filename or "upload",
        status="under_review",
        raw_text=raw_text,
        extracted_data=extracted_data,
    )
    db.add(po)
    db.flush()  # get po.id before adding lines

    # 4. Match line items via RAG
    line_dicts: List[dict] = []
    for idx, raw_line in enumerate(extracted_data.get("line_items", []), start=1):
        description = raw_line.get("description") or ""
        uom_raw = raw_line.get("unit") or ""
        quantity = raw_line.get("quantity")
        unit_price = raw_line.get("unit_price")

        item_matches = []
        uom_matches = []
        best_item: dict = {}
        best_uom: dict = {}

        try:
            if description:
                item_matches = rag_service.match_item(description, limit=3)
                best_item = item_matches[0] if item_matches else {}
        except Exception as exc:
            logger.warning("Item RAG match failed: %s", exc)

        try:
            if uom_raw:
                uom_matches = rag_service.match_uom(uom_raw, limit=3)
                best_uom = uom_matches[0] if uom_matches else {}
        except Exception as exc:
            logger.warning("UOM RAG match failed: %s", exc)

        # Compute total price
        total_price: Optional[float] = None
        if quantity is not None and unit_price is not None:
            try:
                total_price = round(float(quantity) * float(unit_price), 4)
            except (TypeError, ValueError):
                pass

        line_data = {
            "quantity": quantity,
            "unit_price": unit_price,
        }
        line_conf = confidence_service.score_po_line(line_data, best_item, best_uom)

        po_line = POLine(
            po_id=po.id,
            line_number=idx,
            raw_description=description,
            matched_item_id=uuid.UUID(str(best_item["id"])) if best_item.get("id") else None,
            matched_item_code=best_item.get("code"),
            matched_item_description=best_item.get("description"),
            quantity=quantity,
            uom_raw=uom_raw,
            matched_uom_code=best_uom.get("code"),
            unit_price=unit_price,
            total_price=total_price,
            confidence_score=line_conf,
        )
        db.add(po_line)
        line_dicts.append({"confidence_score": line_conf})

    # 5. Score overall PO
    po.confidence_score = confidence_service.score_po(line_dicts)
    db.commit()
    db.refresh(po)
    return po


@router.get("/", response_model=List[PurchaseOrderSummary])
def list_orders(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return (
        db.query(PurchaseOrder)
        .order_by(PurchaseOrder.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_order(po_id: uuid.UUID, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.patch("/{po_id}", response_model=PurchaseOrderResponse)
def update_order(
    po_id: uuid.UUID,
    update: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(po, key, value)
    po.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    return po


@router.patch("/{po_id}/lines/{line_id}", response_model=POLineResponse)
def update_po_line(
    po_id: uuid.UUID,
    line_id: uuid.UUID,
    update: POLineUpdate,
    db: Session = Depends(get_db),
):
    line = (
        db.query(POLine)
        .filter(POLine.id == line_id, POLine.po_id == po_id)
        .first()
    )
    if not line:
        raise HTTPException(status_code=404, detail="PO line not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(line, key, value)

    # Recompute total price if qty/price changed
    if line.quantity is not None and line.unit_price is not None:
        line.total_price = round(line.quantity * line.unit_price, 4)

    db.commit()
    db.refresh(line)
    return line


@router.post("/{po_id}/approve", response_model=PurchaseOrderResponse)
def approve_order(po_id: uuid.UUID, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = "approved"
    po.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/reject", response_model=PurchaseOrderResponse)
def reject_order(po_id: uuid.UUID, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = "rejected"
    po.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(po)
    return po
