import os
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqladmin import Admin

from database import engine, get_db, Base
import models
import schemas
from auth import get_password_hash, verify_password, create_access_token, get_current_user, get_optional_user
from admin_panel import UserAdmin, CategoryAdmin, ProductAdmin, OrderAdmin, OrderItemAdmin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CodeAlpha E-Commerce FastAPI Backend", version="2.0")

# Setup SQLAdmin single-server portal at /admin
admin = Admin(app, engine, title="CodeAlpha Admin Portal")
admin.add_view(UserAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(ProductAdmin)
admin.add_view(OrderAdmin)
admin.add_view(OrderItemAdmin)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend" / "static" if (BASE_DIR / "frontend" / "static").exists() else BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates" if (BASE_DIR / "frontend" / "templates").exists() else BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get("store_session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        response.set_cookie("store_session_id", session_id, max_age=60*60*24*30)
    return session_id


# =========================================================================
# REST API ENDPOINTS
# =========================================================================

@app.post("/api/auth/register", response_model=schemas.Token)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.username == user_in.username) | (models.User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username})
    return {"access_token": token, "token_type": "bearer", "username": new_user.username}


@app.post("/api/auth/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.get("/api/auth/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/api/categories", response_model=List[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()


@app.get("/api/products", response_model=List[schemas.ProductOut])
def get_products(q: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Product).filter(models.Product.is_available == True)
    if q:
        query = query.filter(models.Product.name.ilike(f"%{q}%") | models.Product.description.ilike(f"%{q}%"))
    if category:
        cat_obj = db.query(models.Category).filter(models.Category.slug == category).first()
        if cat_obj:
            query = query.filter(models.Product.category_id == cat_obj.id)
    return query.all()


@app.get("/api/products/{slug_or_id}", response_model=schemas.ProductOut)
def get_product(slug_or_id: str, db: Session = Depends(get_db)):
    if slug_or_id.isdigit():
        prod = db.query(models.Product).filter(models.Product.id == int(slug_or_id)).first()
    else:
        prod = db.query(models.Product).filter(models.Product.slug == slug_or_id).first()
    
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@app.get("/api/cart", response_model=schemas.CartSummaryOut)
def get_cart(request: Request, response: Response, db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_optional_user)):
    session_id = get_session_id(request, response)

    if user:
        items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    else:
        items = db.query(models.CartItem).filter(models.CartItem.session_id == session_id, models.CartItem.user_id == None).all()

    subtotal = round(sum(item.subtotal for item in items), 2)
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00
    tax = round(subtotal * 0.08, 2)
    grand_total = round(subtotal + shipping + tax, 2)
    total_count = sum(item.quantity for item in items)

    return {
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
        "total_count": total_count,
    }


@app.post("/api/cart/add")
def add_to_cart(payload: schemas.CartAdd, request: Request, response: Response, db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_optional_user)):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product or not product.is_available:
        raise HTTPException(status_code=404, detail="Product not available")

    session_id = get_session_id(request, response)

    if user:
        cart_item = db.query(models.CartItem).filter(models.CartItem.user_id == user.id, models.CartItem.product_id == product.id).first()
    else:
        cart_item = db.query(models.CartItem).filter(models.CartItem.session_id == session_id, models.CartItem.user_id == None, models.CartItem.product_id == product.id).first()

    qty = max(1, payload.quantity)
    if cart_item:
        cart_item.quantity += qty
    else:
        cart_item = models.CartItem(
            user_id=user.id if user else None,
            session_id=session_id if not user else None,
            product_id=product.id,
            quantity=qty
        )
        db.add(cart_item)

    db.commit()

    if user:
        all_items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    else:
        all_items = db.query(models.CartItem).filter(models.CartItem.session_id == session_id, models.CartItem.user_id == None).all()
    
    total_count = sum(i.quantity for i in all_items)
    return {"success": True, "message": f'"{product.name}" added to cart!', "cart_total_count": total_count}


@app.put("/api/cart/update/{item_id}")
def update_cart_item(item_id: int, payload: schemas.CartUpdate, db: Session = Depends(get_db)):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if payload.quantity <= 0:
        db.delete(cart_item)
    else:
        cart_item.quantity = payload.quantity
    db.commit()
    return {"success": True}


@app.delete("/api/cart/remove/{item_id}")
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if cart_item:
        db.delete(cart_item)
        db.commit()
    return {"success": True}


@app.post("/api/checkout", response_model=schemas.OrderOut)
def checkout(payload: schemas.CheckoutIn, request: Request, response: Response, db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_optional_user)):
    session_id = get_session_id(request, response)
    
    if user:
        cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == user.id).all()
    else:
        cart_items = db.query(models.CartItem).filter(models.CartItem.session_id == session_id, models.CartItem.user_id == None).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(item.subtotal for item in cart_items)
    shipping = 10.00 if subtotal > 0 and subtotal < 100 else 0.00
    tax = round(subtotal * 0.08, 2)
    grand_total = round(subtotal + shipping + tax, 2)

    order = models.Order(
        user_id=user.id if user else None,
        full_name=payload.full_name,
        email=payload.email,
        address=payload.address,
        city=payload.city,
        postal_code=payload.postal_code,
        country=payload.country,
        total_price=grand_total,
        status="Completed"
    )
    db.add(order)
    db.flush()

    for item in cart_items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )
        db.add(order_item)
        if item.product.stock >= item.quantity:
            item.product.stock -= item.quantity

    for item in cart_items:
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order


# =========================================================================
# HTML PAGES ROUTING
# =========================================================================

@app.get("/", response_class=HTMLResponse)
def page_index(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.is_available == True).all()
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("store/index.html", {"request": request, "products": products, "categories": categories})

@app.get("/product/{slug}", response_class=HTMLResponse)
def page_product_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug).first()
    if not product:
        return RedirectResponse("/")
    related_products = db.query(models.Product).filter(models.Product.category_id == product.category_id, models.Product.id != product.id).limit(4).all()
    return templates.TemplateResponse("store/product_detail.html", {"request": request, "product": product, "related_products": related_products})

@app.get("/cart", response_class=HTMLResponse)
def page_cart(request: Request):
    return templates.TemplateResponse("store/cart.html", {"request": request})

@app.get("/checkout", response_class=HTMLResponse)
def page_checkout(request: Request):
    return templates.TemplateResponse("store/checkout.html", {"request": request})

@app.get("/order-success/{order_id}", response_class=HTMLResponse)
def page_order_success(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    return templates.TemplateResponse("store/order_success.html", {"request": request, "order": order})

@app.get("/register", response_class=HTMLResponse)
def page_register(request: Request):
    return templates.TemplateResponse("store/register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    return templates.TemplateResponse("store/login.html", {"request": request})
