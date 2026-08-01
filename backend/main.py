from jose import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import connect_db, close_db, get_pool
from typing import List, Optional
import os
import bcrypt
JWT_SECRET = os.getenv("JWT_SECRET")

class ProductCreate(BaseModel):
    store_id: int
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

@app.post("/auth/login")
async def login(data: LoginRequest):
    pool = get_pool()
    async with pool.acquire() as connection:
        user = await connection.fetchrow("SELECT * FROM users WHERE username = $1", data.username)
        if user is None:
            return {"error": "No User Found"}
        if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
            return {"error": "Invalid credentials"}

        if user["role"] == "region_manager":
            store_rows = await connection.fetch(
                "SELECT store_id FROM region_manager_stores WHERE region_manager_id = $1", user["id"]
            )
            store_ids = [row["store_id"] for row in store_rows]
        else:
            store_ids = [user["store_id"]]

        token = create_access_token({
            "username": data.username,
            "role": user["role"],
            "id": user["id"],
            "store_ids": store_ids
        })
        return {"access_token": token, "token_type": "bearer", "role": user["role"], "store_ids": store_ids}

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"message": "authenticated", "user": current_user}

@app.post("/products")
async def create_product(data: ProductCreate, current_user: dict = Depends(get_current_user)):
    if data.store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        await connection.execute(
            "INSERT INTO products (store_id, barcode, name, price, quantity_on_hand) VALUES ($1, $2, $3, $4, $5)",
            data.store_id, data.barcode, data.name, data.price, data.quantity_on_hand
        )
    return {"message": "Product created successfully"}

@app.get("/products")
async def view_products(store_id: Optional[int] = Query(None), current_user: dict = Depends(get_current_user)):
    if store_id is None:
        if len(current_user["store_ids"]) == 1:
            store_id = current_user["store_ids"][0]
        else:
            raise HTTPException(status_code=400, detail="store_id is required for users with access to multiple stores")
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM products WHERE store_id = $1", store_id)
    return rows

@app.get("/products/{store_id}/{barcode}")
async def get_product_by_barcode(store_id: int, barcode: str, current_user: dict = Depends(get_current_user)):
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT * FROM products WHERE store_id = $1 AND barcode = $2", store_id, barcode
        )
        if row is None:
            return None
    return row

@app.post("/transactions")
async def checkout(data: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    if len(current_user["store_ids"]) != 1:
        raise HTTPException(status_code=400, detail="Checkout requires a single-store user (employee or manager)")
    store_id = current_user["store_ids"][0]

    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            total = 0
            prices = {}
            for item in data.items:
                product = await connection.fetchrow(
                    "SELECT * FROM products WHERE id = $1 AND store_id = $2 FOR UPDATE",
                    item.product_id, store_id
                )
                if product is None:
                    raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found in your store")
                if product["quantity_on_hand"] < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for product {item.product_id}")
                total += product["price"] * item.quantity
                prices[item.product_id] = product["price"]
                await connection.execute(
                    "UPDATE products SET quantity_on_hand = quantity_on_hand - $1 WHERE id = $2",
                    item.quantity, item.product_id
                )
            transaction_id = await connection.fetchval(
                "INSERT INTO transactions (store_id, cashier_id, total) VALUES ($1, $2, $3) RETURNING id",
                store_id, current_user["id"], total
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
async def low_stock(store_id: Optional[int] = Query(None), current_user: dict = Depends(get_current_user)):
    if store_id is None:
        if len(current_user["store_ids"]) == 1:
            store_id = current_user["store_ids"][0]
        else:
            raise HTTPException(status_code=400, detail="store_id is required for users with access to multiple stores")
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch(
            "SELECT * FROM products WHERE store_id = $1 AND quantity_on_hand < reorder_threshold", store_id
        )
    return rows

@app.post("/products/{id}/restock")
async def restock_product(id: int, data: RestockRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["manager", "region_manager"]:
        raise HTTPException(status_code=403, detail="Access Denied")
    pool = get_pool()
    async with pool.acquire() as connection:
        product = await connection.fetchrow("SELECT * FROM products WHERE id = $1", id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if product["store_id"] not in current_user["store_ids"]:
            raise HTTPException(status_code=403, detail="You do not have access to this store")
        await connection.execute(
            "UPDATE products SET quantity_on_hand = quantity_on_hand + $1 WHERE id = $2",
            data.amount, id
        )
        await connection.execute(
            "INSERT INTO inventory_log (product_id, change_amount, reason) VALUES ($1, $2, $3)",
            id, data.amount, 'restock'
        )
    return {"message": "Restock successful", "product_id": id, "amount_added": data.amount}

@app.get("/stores")
async def get_my_stores(current_user: dict = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM stores WHERE id = ANY($1)", current_user["store_ids"])
    return rows