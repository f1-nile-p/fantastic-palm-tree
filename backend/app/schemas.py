from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


# ---------- Item ----------

class ItemBase(BaseModel):
    code: str
    description: str
    unit_of_measure: str
    unit_price: Optional[float] = None
    category: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[float] = None
    category: Optional[str] = None


class ItemResponse(ItemBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- UOM ----------

class UOMBase(BaseModel):
    code: str
    description: str
    aliases: Optional[List[str]] = []


class UOMCreate(UOMBase):
    pass


class UOMUpdate(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None


class UOMResponse(UOMBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ---------- POLine ----------

class POLineBase(BaseModel):
    line_number: int
    raw_description: Optional[str] = None
    matched_item_id: Optional[uuid.UUID] = None
    matched_item_code: Optional[str] = None
    matched_item_description: Optional[str] = None
    quantity: Optional[float] = None
    uom_raw: Optional[str] = None
    matched_uom_code: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    confidence_score: Optional[float] = None
    notes: Optional[str] = None


class POLineCreate(POLineBase):
    pass


class POLineUpdate(BaseModel):
    matched_item_code: Optional[str] = None
    matched_item_description: Optional[str] = None
    matched_item_id: Optional[uuid.UUID] = None
    quantity: Optional[float] = None
    uom_raw: Optional[str] = None
    matched_uom_code: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    notes: Optional[str] = None


class POLineResponse(POLineBase):
    id: uuid.UUID
    po_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ---------- PurchaseOrder ----------

class PurchaseOrderBase(BaseModel):
    filename: str
    status: str = "pending"
    raw_text: Optional[str] = None
    extracted_data: Optional[Any] = None
    confidence_score: Optional[float] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    extracted_data: Optional[Any] = None
    confidence_score: Optional[float] = None


class PurchaseOrderSummary(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(PurchaseOrderBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    lines: List[POLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
