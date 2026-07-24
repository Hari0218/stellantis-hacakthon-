"""Shared Pydantic schemas used across all AutoShop services."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class VehicleBase(BaseModel):
    make: str
    model: str
    year: int
    vin: str


class VehicleCreate(VehicleBase):
    pass


class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PartBase(BaseModel):
    part_number: str
    name: str
    description: Optional[str] = None
    unit_price: float


class PartCreate(PartBase):
    pass


class PartResponse(PartBase):
    id: int

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    part_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    vehicle_id: int
    customer_email: str
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: int
    status: str
    total_amount: float
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: str
    role: str = "technician"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class NotificationBase(BaseModel):
    recipient_email: str
    subject: str
    body: str
    notification_type: str


class NotificationCreate(NotificationBase):
    order_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    id: int
    sent_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class StockLevelResponse(BaseModel):
    part_id: int
    quantity_available: int
    minimum_threshold: int
    warehouse_location: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    detail: str
    code: str
