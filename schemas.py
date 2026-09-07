from typing import Optional, List
from pydantic import BaseModel, EmailStr

# User Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True


# Category Schemas
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# Product Schemas
class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: float
    stock: int
    image_url: Optional[str] = None
    is_available: bool
    category: Optional[CategoryOut] = None

    class Config:
        from_attributes = True


# Cart Schemas
class CartAdd(BaseModel):
    product_id: int
    quantity: int = 1

class CartUpdate(BaseModel):
    quantity: int

class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductOut
    subtotal: float

    class Config:
        from_attributes = True

class CartSummaryOut(BaseModel):
    items: List[CartItemOut]
    subtotal: float
    shipping: float
    tax: float
    grand_total: float
    total_count: int


# Checkout & Order Schemas
class CheckoutIn(BaseModel):
    full_name: str
    email: EmailStr
    address: str
    city: str
    postal_code: str
    country: str = "USA"

class OrderItemOut(BaseModel):
    id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    full_name: str
    email: str
    address: str
    city: str
    postal_code: str
    country: str
    total_price: float
    status: str
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
