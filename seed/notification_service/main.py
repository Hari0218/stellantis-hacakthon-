"""Notification Service — sends email/SMS alerts for order events."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from typing import Optional, List
import httpx

from shared.database import Base, get_engine, get_session_factory, get_db, init_db
from shared.schemas import NotificationCreate, NotificationResponse
from shared.auth_utils import decode_token

app = FastAPI(title="Notification Service", version="1.0.0")

DATABASE_URL = "sqlite:///./notification.db"
engine = get_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)

AUTH_SERVICE_URL = "http://localhost:8003"


class Notification(Base):
    __tablename__ = "notification"
    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    notification_type = Column(String, nullable=False)
    order_id = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")


init_db(engine)


def get_db_session():
    yield from get_db(SessionFactory)


def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
    """Fetch a notification record by ID."""
    return db.query(Notification).filter(Notification.id == notification_id).first()


def list_notifications_for_order(db: Session, order_id: int) -> List[Notification]:
    """Fetch all notifications sent for a specific order."""
    return db.query(Notification).filter(Notification.order_id == order_id).all()


def create_notification(db: Session, notif_data: NotificationCreate) -> Notification:
    """Persist a new notification record."""
    db_notif = Notification(**notif_data.model_dump())
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif


def mark_notification_sent(db: Session, notification_id: int) -> Notification:
    """Mark a notification as sent with current timestamp."""
    notif = get_notification_by_id(db, notification_id)
    if not notif:
        raise ValueError(f"Notification {notification_id} not found")
    notif.status = "sent"
    notif.sent_at = func.now()
    db.commit()
    db.refresh(notif)
    return notif


def get_user_from_auth_service(user_id: int) -> Optional[dict]:
    """Call auth_service to retrieve user info (inter-service call)."""
    try:
        response = httpx.get(f"{AUTH_SERVICE_URL}/users/{user_id}", timeout=5.0)
        if response.status_code == 200:
            return response.json()
        return None
    except httpx.RequestError:
        return None


def send_order_confirmation(db: Session, order_id: int, customer_email: str, user_id: int) -> Notification:
    """Create and send an order confirmation notification."""
    user_info = get_user_from_auth_service(user_id)
    username = user_info["username"] if user_info else "Customer"
    notif_data = NotificationCreate(
        recipient_email=customer_email,
        subject=f"Order #{order_id} Confirmed",
        body=f"Dear {username}, your work order #{order_id} has been confirmed.",
        notification_type="order_confirmation",
        order_id=order_id,
    )
    notif = create_notification(db, notif_data)
    # Simulate sending (in production, this would call an SMTP/SMS gateway)
    return mark_notification_sent(db, notif.id)


def send_order_status_update(db: Session, order_id: int, customer_email: str, new_status: str) -> Notification:
    """Notify a customer that their order status has changed."""
    notif_data = NotificationCreate(
        recipient_email=customer_email,
        subject=f"Order #{order_id} Status Updated",
        body=f"Your work order #{order_id} is now: {new_status}.",
        notification_type="status_update",
        order_id=order_id,
    )
    notif = create_notification(db, notif_data)
    return mark_notification_sent(db, notif.id)


def send_low_stock_alert(db: Session, part_name: str, quantity: int) -> Notification:
    """Send an alert to the warehouse team about low stock."""
    notif_data = NotificationCreate(
        recipient_email="warehouse@autoshop.internal",
        subject=f"Low Stock Alert: {part_name}",
        body=f"Part '{part_name}' has dropped to {quantity} units. Please reorder.",
        notification_type="low_stock_alert",
    )
    notif = create_notification(db, notif_data)
    return mark_notification_sent(db, notif.id)


@app.post("/notifications", response_model=NotificationResponse, status_code=201)
def create_notification_endpoint(notif: NotificationCreate, db: Session = Depends(get_db_session)):
    return create_notification(db, notif)


@app.post("/notifications/order-confirmation")
def order_confirmation_endpoint(order_id: int, customer_email: str, user_id: int, db: Session = Depends(get_db_session)):
    notif = send_order_confirmation(db, order_id, customer_email, user_id)
    return notif


@app.post("/notifications/order-status")
def order_status_endpoint(order_id: int, customer_email: str, new_status: str, db: Session = Depends(get_db_session)):
    return send_order_status_update(db, order_id, customer_email, new_status)


@app.post("/notifications/low-stock")
def low_stock_endpoint(part_name: str, quantity: int, db: Session = Depends(get_db_session)):
    return send_low_stock_alert(db, part_name, quantity)


@app.get("/notifications/order/{order_id}", response_model=List[NotificationResponse])
def get_order_notifications_endpoint(order_id: int, db: Session = Depends(get_db_session)):
    return list_notifications_for_order(db, order_id)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "notification_service"}
