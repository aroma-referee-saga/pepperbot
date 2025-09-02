from __future__ import annotations

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Shopping List schemas
class ShoppingListBase(BaseModel):
    title: str
    description: Optional[str] = None


class ShoppingListCreate(ShoppingListBase):
    pass


class ShoppingListUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ShoppingList(ShoppingListBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List Item schemas
class ListItemBase(BaseModel):
    name: str
    quantity: float = 1.0
    unit: Optional[str] = None
    is_completed: bool = False


class ListItemCreate(ListItemBase):
    pass


class ListItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    is_completed: Optional[bool] = None


class ListItem(ListItemBase):
    id: int
    shopping_list_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Filter schemas
class FilterBase(BaseModel):
    name: str
    criteria: str  # JSON string
    is_active: bool = True


class FilterCreate(FilterBase):
    pass


class FilterUpdate(BaseModel):
    name: Optional[str] = None
    criteria: Optional[str] = None
    is_active: Optional[bool] = None


class Filter(FilterBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Discount schemas
class DiscountBase(BaseModel):
    title: str
    description: Optional[str] = None
    store: str
    original_price: Optional[float] = None
    discount_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    valid_until: Optional[datetime] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    store: Optional[str] = None
    original_price: Optional[float] = None
    discount_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    valid_until: Optional[datetime] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class Discount(DiscountBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Notification schemas
class NotificationBase(BaseModel):
    title: str
    message: str
    type: str


class NotificationCreate(NotificationBase):
    user_id: int
    discount_id: Optional[int] = None


class Notification(NotificationBase):
    id: int
    user_id: int
    discount_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Telegram webhook schemas
class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None


# Response schemas
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None