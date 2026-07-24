"""Inventory Service — manages parts stock levels."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from typing import List, Optional

from shared.database import Base, get_engine, get_session_factory, get_db, init_db
from shared.schemas import PartCreate, PartResponse, StockLevelResponse

app = FastAPI(title="Inventory Service", version="1.0.0")

DATABASE_URL = "sqlite:///./inventory.db"
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)


class Part(Base):
    __tablename__ = "part"
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    stock = relationship("StockLevel", back_populates="part", uselist=False)


class StockLevel(Base):
    __tablename__ = "stock_level"
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("part.id"), unique=True, nullable=False)
    quantity_available = Column(Integer, default=0)
    minimum_threshold = Column(Integer, default=10)
    warehouse_location = Column(String, nullable=False)
    part = relationship("Part", back_populates="stock")


init_db(engine)


def get_db_session():
    yield from get_db(SessionFactory)


def get_part_by_id(db: Session, part_id: int) -> Optional[Part]:
    """Fetch a part by its primary key."""
    return db.query(Part).filter(Part.id == part_id).first()


def get_part_by_number(db: Session, part_number: str) -> Optional[Part]:
    """Fetch a part by its part number."""
    return db.query(Part).filter(Part.part_number == part_number).first()


def list_parts(db: Session, skip: int = 0, limit: int = 100) -> List[Part]:
    """Return paginated list of all parts."""
    return db.query(Part).offset(skip).limit(limit).all()


def create_part(db: Session, part_data: PartCreate) -> Part:
    """Create a new part and initialize its stock level."""
    existing = get_part_by_number(db, part_data.part_number)
    if existing:
        raise ValueError(f"Part {part_data.part_number} already exists")
    db_part = Part(**part_data.model_dump())
    db.add(db_part)
    db.flush()
    stock = StockLevel(part_id=db_part.id, quantity_available=0, warehouse_location="WAREHOUSE-A")
    db.add(stock)
    db.commit()
    db.refresh(db_part)
    return db_part


def update_stock_level(db: Session, part_id: int, quantity_delta: int) -> StockLevel:
    """Adjust stock quantity by delta (positive = add, negative = remove)."""
    stock = db.query(StockLevel).filter(StockLevel.part_id == part_id).first()
    if not stock:
        raise ValueError(f"No stock record found for part {part_id}")
    stock.quantity_available += quantity_delta
    if stock.quantity_available < 0:
        raise ValueError("Stock cannot go below zero")
    db.commit()
    db.refresh(stock)
    return stock


def check_stock_availability(db: Session, part_id: int, quantity_needed: int) -> bool:
    """Check if sufficient stock is available for a given quantity."""
    stock = db.query(StockLevel).filter(StockLevel.part_id == part_id).first()
    if not stock:
        return False
    return stock.quantity_available >= quantity_needed


def get_low_stock_parts(db: Session) -> List[StockLevel]:
    """Return all parts where stock is below minimum threshold."""
    return db.query(StockLevel).filter(
        StockLevel.quantity_available < StockLevel.minimum_threshold
    ).all()


def reserve_parts_for_order(db: Session, items: list) -> bool:
    """Reserve parts for an order. Returns False if any item is out of stock."""
    for item in items:
        if not check_stock_availability(db, item["part_id"], item["quantity"]):
            return False
    for item in items:
        update_stock_level(db, item["part_id"], -item["quantity"])
    return True


@app.get("/parts", response_model=List[PartResponse])
def list_parts_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return list_parts(db, skip=skip, limit=limit)


@app.get("/parts/{part_id}", response_model=PartResponse)
def get_part_endpoint(part_id: int, db: Session = Depends(get_db_session)):
    part = get_part_by_id(db, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@app.post("/parts", response_model=PartResponse, status_code=201)
def create_part_endpoint(part: PartCreate, db: Session = Depends(get_db_session)):
    try:
        return create_part(db, part)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/parts/{part_id}/stock", response_model=StockLevelResponse)
def get_stock_endpoint(part_id: int, db: Session = Depends(get_db_session)):
    stock = db.query(StockLevel).filter(StockLevel.part_id == part_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    return stock


@app.post("/parts/{part_id}/stock/adjust")
def adjust_stock_endpoint(part_id: int, delta: int, db: Session = Depends(get_db_session)):
    try:
        return update_stock_level(db, part_id, delta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reserve")
def reserve_parts_endpoint(items: list, db: Session = Depends(get_db_session)):
    success = reserve_parts_for_order(db, items)
    if not success:
        raise HTTPException(status_code=409, detail="Insufficient stock for one or more parts")
    return {"reserved": True}


@app.get("/stock/low", response_model=List[StockLevelResponse])
def low_stock_endpoint(db: Session = Depends(get_db_session)):
    return get_low_stock_parts(db)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "inventory_service"}
