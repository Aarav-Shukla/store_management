import asyncio
import asyncpg
import os
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

PRODUCTS = [
    ("MILK-001", "Milk 1 Gallon", 3.99),
    ("BREAD-001", "Bread Loaf", 2.49),
    ("EGGS-001", "Eggs Dozen", 4.29),
    ("BANANA-001", "Bananas Bunch", 1.99),
    ("TOWEL-001", "Paper Towels 6-Pack", 8.99),
    ("CHICK-001", "Chicken Breast 1lb", 5.49),
    ("RICE-001", "White Rice 5lb", 6.99),
    ("PASTA-001", "Spaghetti 1lb", 1.79),
    ("CHEESE-001", "Cheddar Cheese 8oz", 3.49),
    ("YOGURT-001", "Greek Yogurt 32oz", 4.99),
    ("APPLE-001", "Apples 3lb Bag", 4.49),
    ("COFFEE-001", "Ground Coffee 12oz", 7.99),
    ("CEREAL-001", "Cereal Box", 3.99),
    ("BUTTER-001", "Butter 1lb", 4.29),
    ("OJ-001", "Orange Juice 64oz", 4.79),
    ("SOUP-001", "Canned Soup", 1.99),
    ("PEANUT-001", "Peanut Butter 16oz", 3.29),
    ("TOMATO-001", "Canned Tomatoes", 1.49),
    ("ONION-001", "Onions 3lb Bag", 2.99),
    ("POTATO-001", "Potatoes 5lb Bag", 3.99),
    ("SODA-001", "Soda 12-Pack", 5.99),
    ("CHIPS-001", "Potato Chips", 3.49),
    ("COOKIE-001", "Cookies Pack", 3.29),
    ("DETERGENT-001", "Laundry Detergent", 9.99),
    ("TOILETPAPER-001", "Toilet Paper 12-Pack", 7.49),
]

async def seed_transactions(conn):
    print("Generating transactions...")
    stores = await conn.fetch("SELECT id FROM stores")

    for store in stores:
        store_id = store["id"]
        products = await conn.fetch("SELECT id, price FROM products WHERE store_id = $1", store_id)

        num_transactions = random.randint(60, 100)

        for _ in range(num_transactions):
            days_ago = random.randint(0, 60)
            created_at = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0, 23))

            num_items = random.randint(1, 5)
            chosen_products = random.sample(products, min(num_items, len(products)))

            total = 0
            line_items = []
            for product in chosen_products:
                quantity = random.randint(1, 3)
                price = float(product["price"])
                total += price * quantity
                line_items.append((product["id"], quantity, price))

            transaction_id = await conn.fetchval(
                "INSERT INTO transactions (store_id, cashier_id, total, created_at) VALUES ($1, $2, $3, $4) RETURNING id",
                store_id, None, round(total, 2), created_at
            )

            for product_id, quantity, price in line_items:
                await conn.execute(
                    "INSERT INTO transaction_items (transaction_id, product_id, quantity, price_at_sale) VALUES ($1, $2, $3, $4)",
                    transaction_id, product_id, quantity, price
                )

    print("Done generating transactions.")

async def seed():
    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)

    print("Clearing existing data...")
    await conn.execute("DELETE FROM inventory_log")
    await conn.execute("DELETE FROM transaction_items")
    await conn.execute("DELETE FROM transactions")
    await conn.execute("DELETE FROM products")

    stores = await conn.fetch("SELECT id FROM stores")

    print(f"Seeding {len(PRODUCTS)} products across {len(stores)} stores...")
    for store in stores:
        store_id = store["id"]
        for index, (sku, name, price) in enumerate(PRODUCTS):
            barcode = f"{store_id}{index:04d}"
            quantity = random.randint(5, 50)
            await conn.execute(
                """
                INSERT INTO products (store_id, barcode, sku, name, price, quantity_on_hand, reorder_threshold)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                store_id, barcode, sku, name, price, quantity, 10
            )

    print("Done seeding products.")

    await seed_transactions(conn)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed())