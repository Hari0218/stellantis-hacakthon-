"""Order Service — creates and manages work orders for vehicles."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from typing import List, Optional
import httpx

from shared.database import Base, get_engine, get_session_factory, get_db, init_db
from shared.schemas import OrderCreate, OrderResponse

app = FastAPI(title="Order Service", version="1.0.0")

DATABASE_URL = "sqlite:///./order_service.db"
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)

INVENTORY_SERVICE_URL = "http://localhost:8002"
NOTIFICATION_SERVICE_URL = "http://localhost:8004"
VEHICLE_CATALOG_URL = "http://localhost:8001"


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, nullable=False)
    customer_email = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    status = Column(String, default="pending")
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_item"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    part_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")


init_db(engine)


def get_db_session():
    yield from get_db(SessionFactory)


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    """Fetch an order by its primary key."""
    return db.query(Order).filter(Order.id == order_id).first()


def list_orders(db: Session, skip: int = 0, limit: int = 100) -> List[Order]:
    """Return a paginated list of all orders."""
    return db.query(Order).offset(skip).limit(limit).all()


def list_orders_by_vehicle(db: Session, vehicle_id: int) -> List[Order]:
    """Return all orders associated with a specific vehicle."""
    return db.query(Order).filter(Order.vehicle_id == vehicle_id).all()


def check_vehicle_exists(vehicle_id: int) -> bool:
    """Call vehicle_catalog service to verify the vehicle exists."""
    try:
        resp = httpx.get(f"{VEHICLE_CATALOG_URL}/vehicles/{vehicle_id}", timeout=5.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


def reserve_inventory_for_order(items: list) -> bool:
    """Call inventory_service to reserve parts for this order."""
    try:
        payload = [{"part_id": i["part_id"], "quantity": i["quantity"]} for i in items]
        resp = httpx.post(f"{INVENTORY_SERVICE_URL}/reserve", json=payload, timeout=5.0)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


def notify_order_created(order_id: int, customer_email: str, user_id: int) -> None:
    """Call notification_service to send order confirmation."""
    try:
        httpx.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications/order-confirmation",
            params={"order_id": order_id, "customer_email": customer_email, "user_id": user_id},
            timeout=5.0,
        )
    except httpx.RequestError:
        pass  # Non-blocking: order creation succeeds even if notification fails


def create_order(db: Session, order_data: OrderCreate) -> Order:
    """Create a new work order and reserve inventory."""
    items_dicts = [item.model_dump() for item in order_data.items]
    reserved = reserve_inventory_for_order(items_dicts)
    if not reserved:
        raise ValueError("Could not reserve parts: insufficient inventory")
    total = sum(item["quantity"] * item["unit_price"] for item in items_dicts)
    db_order = Order(
        vehicle_id=order_data.vehicle_id,
        customer_email=order_data.customer_email,
        notes=order_data.notes,
        status="confirmed",
        total_amount=total,
    )
    db.add(db_order)
    db.flush()
    for item in items_dicts:
        db_item = OrderItem(order_id=db_order.id, **item)
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    notify_order_created(db_order.id, db_order.customer_email, user_id=1)
    return db_order


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    """Update the status of an existing order."""
    order = get_order_by_id(db, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    valid_statuses = ["pending", "confirmed", "in_progress", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")
    order.status = new_status
    db.commit()
    db.refresh(order)
    # Notify customer of status change
    try:
        httpx.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications/order-status",
            params={"order_id": order_id, "customer_email": order.customer_email, "new_status": new_status},
            timeout=5.0,
        )
    except httpx.RequestError:
        pass
    return order


def cancel_order(db: Session, order_id: int) -> bool:
    """Cancel an order if it's still pending or confirmed."""
    order = get_order_by_id(db, order_id)
    if not order:
        return False
    if order.status not in ("pending", "confirmed"):
        raise ValueError("Only pending or confirmed orders can be cancelled")
    order.status = "cancelled"
    db.commit()
    return True


def calculate_order_total(db: Session, order_id: int) -> float:
    """Recalculate the total amount from order items."""
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return sum(item.quantity * item.unit_price for item in items)


@app.get("/orders", response_model=List[OrderResponse])
def list_orders_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    return list_orders(db, skip=skip, limit=limit)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order_endpoint(order: OrderCreate, db: Session = Depends(get_db_session)):
    try:
        return create_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/orders/{order_id}/status")
def update_status_endpoint(order_id: int, new_status: str, db: Session = Depends(get_db_session)):
    try:
        return update_order_status(db, order_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/orders/{order_id}")
def cancel_order_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    try:
        success = cancel_order(db, order_id)
        if not success:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"cancelled": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/orders/vehicle/{vehicle_id}", response_model=List[OrderResponse])
def orders_by_vehicle_endpoint(vehicle_id: int, db: Session = Depends(get_db_session)):
    return list_orders_by_vehicle(db, vehicle_id)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "order_service"}
