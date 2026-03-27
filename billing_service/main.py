from fastapi import FastAPI, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.BillingDatabase import SessionLocal
import requests
from pydantic import BaseModel
from typing import List

app = FastAPI()

PRODUCT_URL = "http://127.0.0.1:8002"
AUTH_URL = "http://127.0.0.1:8001"

# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- AUTH ----------------
def validate(user_id, role):
    if not user_id or not role:
        raise HTTPException(status_code=401, detail="Missing auth")

    res = requests.get(
        f"{AUTH_URL}/validate",
        cookies={"user_id": str(user_id), "role": role},
        timeout=3
    )

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------------- MODEL ----------------
class Item(BaseModel):
    product_id: int
    quantity: int

# ---------------- BILLING ----------------
@app.post("/create-bill")
def create_bill(
    items: List[Item],
    user_id: int = Cookie(None),
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    validate(user_id, role)

    if role != "seller":
        raise HTTPException(status_code=403, detail="Only seller allowed")

    try:
        # ✅ safer bill_id generation (still manual but safer)
        result = db.execute(text("""
            SELECT ISNULL(MAX(bill_id), 0) + 1 AS new_id FROM BillItems WITH (UPDLOCK, HOLDLOCK)
        """))
        bill_id = result.scalar()

        total = 0
        bill_items = []

        for item in items:
            # ✅ Get product
            response = requests.get(
                f"{PRODUCT_URL}/get-product/{item.product_id}",
                cookies={"user_id": str(user_id), "role": role},
                timeout=3
            )

            if response.status_code != 200:
                raise HTTPException(404, detail=f"Product {item.product_id} not found")

            product = response.json()

            # ✅ Calculate cost
            cost = product["selling_price"] * item.quantity
            total += cost

            # ✅ Reduce stock
            reduce = requests.put(
                f"{PRODUCT_URL}/reduce-stock/{item.product_id}",
                params={"quantity": item.quantity},
                cookies={"user_id": str(user_id), "role": role},
                timeout=3
            )

            if reduce.status_code != 200:
                raise HTTPException(400, detail="Stock issue")

            # ✅ Insert
            db.execute(text("""
                INSERT INTO BillItems (bill_id, product_id, quantity, price)
                VALUES (:b, :p, :q, :price)
            """), {
                "b": bill_id,
                "p": item.product_id,
                "q": item.quantity,
                "price": cost
            })

            bill_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": cost
            })

        db.commit()

        return {
            "message": "Bill created successfully",
            "bill_id": bill_id,
            "total": total,
            "items": bill_items
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- DAILY SALES ----------------
@app.get("/daily-sales")
def daily_sales(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT product_id, 
               SUM(quantity) as total_qty, 
               SUM(price) as total_sales
        FROM BillItems
        WHERE CAST(created_at AS DATE) = CAST(GETDATE() AS DATE)
        GROUP BY product_id
    """)).fetchall()

    return [dict(row._mapping) for row in result]