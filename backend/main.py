from jose import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import connect_db, close_db, get_pool
from typing import List, Optional
import os
import bcrypt
import math

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

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth's radius in miles
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

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
    allow_origins=[
        "http://localhost:5173",
        "https://store-management-f1775amzu-aarav-shukla1.vercel.app"
    ],
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
            "store_ids": store_ids,
            "name": user["name"]
        })
        return {"access_token": token, "token_type": "bearer", "role": user["role"], "store_ids": store_ids, "name": user["name"]}

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"message": "authenticated", "user": current_user}

@app.get("/stores")
async def get_my_stores(current_user: dict = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM stores WHERE id = ANY($1)", current_user["store_ids"])
    return rows

# ==========================================
# PRODUCT ROUTES (Specific paths first)
# ==========================================

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

@app.get("/products/availability/{barcode}")
async def check_availability(barcode: str, store_id: int, current_user: dict = Depends(get_current_user)):
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")

    pool = get_pool()
    async with pool.acquire() as connection:
        origin_store = await connection.fetchrow("SELECT * FROM stores WHERE id = $1", store_id)
        if origin_store is None:
            raise HTTPException(status_code=404, detail="Store not found")

        origin_product = await connection.fetchrow(
            "SELECT * FROM products WHERE barcode = $1 AND store_id = $2", barcode, store_id
        )
        if origin_product is None:
            raise HTTPException(status_code=404, detail="Product not found at your store")

        rows = await connection.fetch(
            """
            SELECT products.quantity_on_hand, stores.id AS store_id, stores.name AS store_name, stores.latitude, stores.longitude
            FROM products
            JOIN stores ON products.store_id = stores.id
            WHERE products.sku = $1 AND products.store_id != $2 AND products.quantity_on_hand > 0
            """,
            origin_product["sku"], store_id
        )

        results = []
        for row in rows:
            distance = calculate_distance(
                origin_store["latitude"], origin_store["longitude"],
                row["latitude"], row["longitude"]
            )
            results.append({
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "quantity_on_hand": row["quantity_on_hand"],
                "distance_miles": round(distance, 1)
            })

        results.sort(key=lambda r: r["distance_miles"])

    return {"product_name": origin_product["name"], "availability": results}

@app.get("/products")
async def view_products(store_id: Optional[int] = Query(None), search: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    if store_id is None:
        if len(current_user["store_ids"]) == 1:
            store_id = current_user["store_ids"][0]
        else:
            raise HTTPException(status_code=400, detail="store_id is required for users with access to multiple stores")
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        if search:
            rows = await connection.fetch(
                "SELECT * FROM products WHERE store_id = $1 AND (name ILIKE $2 OR sku ILIKE $2)",
                store_id, f"%{search}%"
            )
        else:
            rows = await connection.fetch("SELECT * FROM products WHERE store_id = $1", store_id)
    return rows

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

# ==========================================
# TRANSACTION ROUTES (Specific paths first)
# ==========================================

@app.get("/transactions/history")
async def get_transaction_history(store_id: int, search: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")
    pool = get_pool()
    async with pool.acquire() as connection:
        if search:
            rows = await connection.fetch(
                "SELECT id, total, created_at FROM transactions WHERE store_id = $1 AND id::text = $2 ORDER BY created_at DESC LIMIT 20",
                store_id, search
            )
        else:
            rows = await connection.fetch(
                "SELECT id, total, created_at FROM transactions WHERE store_id = $1 ORDER BY created_at DESC LIMIT 20",
                store_id
            )
    return rows

@app.get("/transactions/{id}/items")
async def get_transaction_items(id: int, current_user: dict = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as connection:
        transaction = await connection.fetchrow("SELECT * FROM transactions WHERE id = $1", id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        if transaction["store_id"] not in current_user["store_ids"]:
            raise HTTPException(status_code=403, detail="You do not have access to this transaction")

        rows = await connection.fetch(
            """
            SELECT transaction_items.quantity, transaction_items.price_at_sale, products.name
            FROM transaction_items
            JOIN products ON transaction_items.product_id = products.id
            WHERE transaction_items.transaction_id = $1
            """,
            id
        )
    return rows

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
        
# ==========================================
# ANALYTICS ROUTES
# ==========================================

@app.get("/analytics/summary")
async def get_analytics_summary(store_id: int, current_user: dict = Depends(get_current_user)):
    if store_id not in current_user["store_ids"]:
        raise HTTPException(status_code=403, detail="You do not have access to this store")

    pool = get_pool()
    async with pool.acquire() as connection:
        summary = await connection.fetchrow(
            """
            SELECT COUNT(*) AS transaction_count, COALESCE(SUM(total), 0) AS total_revenue
            FROM transactions
            WHERE store_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
            """,
            store_id
        )

        daily = await connection.fetch(
            """
            SELECT DATE(created_at) AS day, SUM(total) AS revenue
            FROM transactions
            WHERE store_id = $1 AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY day
            """,
            store_id
        )

        top_products = await connection.fetch(
            """
            SELECT products.name, SUM(transaction_items.quantity) AS total_sold
            FROM transaction_items
            JOIN transactions ON transaction_items.transaction_id = transactions.id
            JOIN products ON transaction_items.product_id = products.id
            WHERE transactions.store_id = $1 AND transactions.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY products.name
            ORDER BY total_sold DESC
            LIMIT 5
            """,
            store_id
        )

    avg_transaction = (summary["total_revenue"] / summary["transaction_count"]) if summary["transaction_count"] > 0 else 0

    return {
        "total_revenue": round(float(summary["total_revenue"]), 2),
        "transaction_count": summary["transaction_count"],
        "average_transaction": round(float(avg_transaction), 2),
        "daily_revenue": [{"day": str(row["day"]), "revenue": round(float(row["revenue"]), 2)} for row in daily],
        "top_products": [{"name": row["name"], "quantity_sold": row["total_sold"]} for row in top_products]
    }