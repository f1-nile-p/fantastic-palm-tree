import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    unit_of_measure = Column(String, nullable=False)
    unit_price = Column(Float, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UOM(Base):
    __tablename__ = "uoms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    aliases = Column(JSON, default=list)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending/under_review/approved/rejected
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("POLine", back_populates="purchase_order", cascade="all, delete-orphan")


class POLine(Base):
    __tablename__ = "po_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    raw_description = Column(String, nullable=True)
    matched_item_id = Column(UUID(as_uuid=True), nullable=True)
    matched_item_code = Column(String, nullable=True)
    matched_item_description = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    uom_raw = Column(String, nullable=True)
    matched_uom_code = Column(String, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    notes = Column(String, nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
