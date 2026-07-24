"""Vehicle Catalog Service — manages vehicle and model data."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from typing import List

from shared.database import Base, get_engine, get_session_factory, get_db, init_db
from shared.schemas import VehicleCreate, VehicleResponse

app = FastAPI(title="Vehicle Catalog Service", version="1.0.0")

DATABASE_URL = "sqlite:///./vehicle_catalog.db"
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)


class Vehicle(Base):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    vin = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VehicleModel(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, nullable=False)
    name = Column(String, nullable=False)
    year_start = Column(Integer, nullable=False)
    year_end = Column(Integer, nullable=True)
    base_price = Column(Float, nullable=False)


init_db(engine)


def get_db_session():
    yield from get_db(SessionFactory)


def get_vehicle_by_vin(db: Session, vin: str) -> Vehicle:
    """Look up a vehicle by its VIN number."""
    return db.query(Vehicle).filter(Vehicle.vin == vin).first()


def get_vehicle_by_id(db: Session, vehicle_id: int) -> Vehicle:
    """Look up a vehicle by primary key."""
    return db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()


def list_vehicles(db: Session, skip: int = 0, limit: int = 100) -> List[Vehicle]:
    """Return a paginated list of all vehicles."""
    return db.query(Vehicle).offset(skip).limit(limit).all()


def create_vehicle(db: Session, vehicle_data: VehicleCreate) -> Vehicle:
    """Create and persist a new vehicle record."""
    existing = get_vehicle_by_vin(db, vehicle_data.vin)
    if existing:
        raise ValueError(f"Vehicle with VIN {vehicle_data.vin} already exists")
    db_vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def update_vehicle_make(db: Session, vehicle_id: int, new_make: str) -> Vehicle:
    """Update the make field of a vehicle."""
    vehicle = get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        raise ValueError(f"Vehicle {vehicle_id} not found")
    vehicle.make = new_make
    db.commit()
    db.refresh(vehicle)
    return vehicle


def delete_vehicle(db: Session, vehicle_id: int) -> bool:
    """Delete a vehicle by ID. Returns True if deleted."""
    vehicle = get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        return False
    db.delete(vehicle)
    db.commit()
    return True


def list_models_by_make(db: Session, make: str) -> List[VehicleModel]:
    """Return all vehicle models for a given manufacturer."""
    return db.query(VehicleModel).filter(VehicleModel.make == make).all()


@app.get("/vehicles", response_model=List[VehicleResponse])
def list_vehicles_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return list_vehicles(db, skip=skip, limit=limit)


@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle_endpoint(vehicle_id: int, db: Session = Depends(get_db_session)):
    vehicle = get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@app.post("/vehicles", response_model=VehicleResponse, status_code=201)
def create_vehicle_endpoint(vehicle: VehicleCreate, db: Session = Depends(get_db_session)):
    try:
        return create_vehicle(db, vehicle)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.put("/vehicles/{vehicle_id}/make", response_model=VehicleResponse)
def update_make_endpoint(vehicle_id: int, new_make: str, db: Session = Depends(get_db_session)):
    try:
        return update_vehicle_make(db, vehicle_id, new_make)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/vehicles/{vehicle_id}", status_code=204)
def delete_vehicle_endpoint(vehicle_id: int, db: Session = Depends(get_db_session)):
    deleted = delete_vehicle(db, vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle not found")


@app.get("/models/{make}")
def list_models_endpoint(make: str, db: Session = Depends(get_db_session)):
    return list_models_by_make(db, make)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "vehicle_catalog"}
