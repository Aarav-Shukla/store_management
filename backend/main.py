from jose import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from database import connect_db, close_db, get_pool
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
        token  = create_access_token({"username": data.username, "role": user["role"]})
        return {"access_token": token, "token_type": "bearer"}
    
@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"message": "authenticated", "user": current_user}