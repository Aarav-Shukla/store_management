from jose import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import connect_db, close_db, get_pool
from typing import List
import os
import bcrypt
JWT_SECRET = os.getenv("JWT_SECRET")

class ProductCreate(BaseModel):
    barcode: str
    name: str
    price: float
    quantity_on_hand: int = 0
    
class LoginRequest(BaseModel):
    username: str
    password: str
    
class CartItem(BaseModel):
    product_id: int
    quantity: int
    
class CheckoutRequest(BaseModel):
    items: list[CartItem]
    
class RestockRequest(BaseModel):
    amount: int
    
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()

@app.get("/health")
async def health_check():
    return {"status" : "ok"}

@app.post("/products")
async def create_product(data: ProductCreate):
    pool = get_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO products (barcode, name, price, quantity_on_hand) VALUES ($1, $2, $3, $4)",
            data.barcode, data.name, data.price, data.quantity_on_hand
        )
    return {"message": "Product created successfully"}

@app.get("/products")
async def view_products():
    pool = get_pool();
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM products")
    return rows

@app.get("/products/{barcode}")
async def get_product_by_barcode(barcode: str):
    pool = get_pool();
    async with pool.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM products WHERE barcode = $1", barcode)
        if row is None:
            return None
    return row

@app.post("/auth/login")
async def login(data: LoginRequest):
    pool = get_pool()
    async with pool.acquire() as connection:
        user = await connection.fetchrow("SELECT * FROM users WHERE username = $1", data.username)
        if user is None:
            return {"error": "No User Found"}
        if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
            return {"error": "Invalid credentials"}
        token  = create_access_token({"username": data.username, "role": user["role"], "id": user["id"]})
        return {"access_token": token, "token_type": "bearer", "role": user["role"]}
    
@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"message": "authenticated", "user": current_user}

@app.post("/transactions")
async def checkout(data: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            total = 0
            prices = {}
            for item in data.items:
                product = await connection.fetchrow("SELECT * FROM products WHERE id = $1 FOR UPDATE", item.product_id)
                if product is None:
                    raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
                if product["quantity_on_hand"] < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for product {item.product_id}")
                total += product["price"] * item.quantity
                prices[item.product_id] = product["price"]
                await connection.execute(
                    "UPDATE products SET quantity_on_hand = quantity_on_hand - $1 WHERE id = $2",
                    item.quantity, item.product_id
                )
            transaction_id = await connection.fetchval(
                "INSERT INTO transactions (cashier_id, total) VALUES ($1, $2) RETURNING id",
                current_user["id"], total
            )
            for item in data.items:
                await connection.execute(
                    "INSERT INTO transaction_items (transaction_id, product_id, quantity, price_at_sale) VALUES ($1, $2, $3, $4)",
                    transaction_id, item.product_id, item.quantity, prices[item.product_id]
                )
                await connection.execute(
                    "INSERT INTO inventory_log (product_id, change_amount, reason) VALUES ($1, $2, $3)",
                    item.product_id, -item.quantity, 'sale'
                )
            return {"message": "Checkout successful", "transaction_id": transaction_id, "total": total}
        
@app.get("/products/low-stock")
async def low_stock():
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM products WHERE quantity_on_hand < reorder_threshold")
    return rows

@app.post("/products/{id}/restock")
async def restock_product(id: int, data: RestockRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "region_manager"]:
        raise HTTPException(status_code=403, detail="Access Denied")
    pool = get_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            "UPDATE products SET quantity_on_hand = quantity_on_hand + $1 WHERE id = $2",
            data.amount, id
        )
        await connection.execute(
            "INSERT INTO inventory_log (product_id, change_amount, reason) VALUES ($1, $2, $3)",
            id, data.amount, 'restock'
        )
    return {"message": "Restock successful", "product_id": id, "amount_added": data.amount}