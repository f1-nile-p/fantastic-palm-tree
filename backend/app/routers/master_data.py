import csv
import io
import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, UOM
from app.schemas import (
    ItemCreate,
    ItemResponse,
    UOMCreate,
    UOMResponse,
)
from app.services import rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/master-data", tags=["master-data"])


# ─── Items ────────────────────────────────────────────────────────────────────

@router.post("/items/upload", response_model=List[ItemResponse], status_code=status.HTTP_201_CREATED)
async def upload_items_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV of items (code, description, unit_of_measure, unit_price, category)."""
    content = await file.read()
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}")

    created: List[Item] = []
    for row in reader:
        code = (row.get("code") or "").strip()
        description = (row.get("description") or "").strip()
        uom = (row.get("unit_of_measure") or "").strip()
        if not code or not description:
            continue

        try:
            unit_price = float(row.get("unit_price") or 0) or None
        except (ValueError, TypeError):
            unit_price = None

        existing = db.query(Item).filter(Item.code == code).first()
        if existing:
            existing.description = description
            existing.unit_of_measure = uom
            existing.unit_price = unit_price
            existing.category = (row.get("category") or "").strip() or None
            created.append(existing)
        else:
            item = Item(
                code=code,
                description=description,
                unit_of_measure=uom,
                unit_price=unit_price,
                category=(row.get("category") or "").strip() or None,
            )
            db.add(item)
            created.append(item)

    db.commit()
    for item in created:
        db.refresh(item)

    # Re-index all items
    try:
        all_items = db.query(Item).all()
        rag_service.index_items(all_items)
    except Exception as exc:
        logger.warning("Qdrant indexing failed after CSV upload: %s", exc)

    return created


@router.get("/items", response_model=List[ItemResponse])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    existing = db.query(Item).filter(Item.code == item_in.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Item with this code already exists")
    item = Item(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    try:
        rag_service.index_items([item])
    except Exception as exc:
        logger.warning("Qdrant indexing failed: %s", exc)

    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()


# ─── UOMs ─────────────────────────────────────────────────────────────────────

@router.post("/uoms/upload", response_model=List[UOMResponse], status_code=status.HTTP_201_CREATED)
async def upload_uoms_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV of UOMs (code, description, aliases as semicolon-separated)."""
    content = await file.read()
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}")

    created: List[UOM] = []
    for row in reader:
        code = (row.get("code") or "").strip()
        description = (row.get("description") or "").strip()
        if not code:
            continue

        raw_aliases = row.get("aliases") or ""
        aliases = [a.strip() for a in raw_aliases.split(";") if a.strip()]

        existing = db.query(UOM).filter(UOM.code == code).first()
        if existing:
            existing.description = description
            existing.aliases = aliases
            created.append(existing)
        else:
            uom = UOM(code=code, description=description, aliases=aliases)
            db.add(uom)
            created.append(uom)

    db.commit()
    for uom in created:
        db.refresh(uom)

    try:
        all_uoms = db.query(UOM).all()
        rag_service.index_uoms(all_uoms)
    except Exception as exc:
        logger.warning("Qdrant UOM indexing failed: %s", exc)

    return created


@router.get("/uoms", response_model=List[UOMResponse])
def list_uoms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(UOM).offset(skip).limit(limit).all()


@router.post("/uoms", response_model=UOMResponse, status_code=status.HTTP_201_CREATED)
def create_uom(uom_in: UOMCreate, db: Session = Depends(get_db)):
    existing = db.query(UOM).filter(UOM.code == uom_in.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="UOM with this code already exists")
    uom = UOM(**uom_in.model_dump())
    db.add(uom)
    db.commit()
    db.refresh(uom)

    try:
        rag_service.index_uoms([uom])
    except Exception as exc:
        logger.warning("Qdrant UOM indexing failed: %s", exc)

    return uom


@router.delete("/uoms/{uom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uom(uom_id: uuid.UUID, db: Session = Depends(get_db)):
    uom = db.query(UOM).filter(UOM.id == uom_id).first()
    if not uom:
        raise HTTPException(status_code=404, detail="UOM not found")
    db.delete(uom)
    db.commit()
