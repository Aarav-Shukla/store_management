from fastapi import FastAPI
from pydantic import BaseModel
from database import connect_db, close_db, get_pool

class ProductCreate(BaseModel):
    barcode: str
    name: str
    price: float
    quantity_on_hand: int = 0


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