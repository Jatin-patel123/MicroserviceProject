from fastapi import FastAPI, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.ReturnDatabase import SessionLocal
import requests

app = FastAPI()

PRODUCT_URL = "http://127.0.0.1:8002"
AUTH_URL = "http://127.0.0.1:8001"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate(user_id, role):
    res = requests.get(
        f"{AUTH_URL}/validate",
        cookies={"user_id": str(user_id), "role": role} 
    )
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/return-product")
def return_product(
    product_id: int,
    quantity: int,
    user_id: int = Cookie(None),
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    validate(user_id, role)

    response = requests.get(
        f"{PRODUCT_URL}/get-product/{product_id}",
        cookies={"user_id": str(user_id), "role": role} 
    )

    if response.status_code != 200:
        raise HTTPException(404, detail="Product not found")

    product = response.json()

    refund = product["selling_price"] * quantity

    stock_res = requests.put(
        f"{PRODUCT_URL}/increase-stock/{product_id}",
        params={"quantity": quantity},
        cookies={"user_id": str(user_id), "role": role}  
    )

    if stock_res.status_code != 200:
        raise HTTPException(400, detail="Stock update failed")

    db.execute(text("""
        INSERT INTO Returns (product_id, quantity, refund_amount)
        VALUES (:p, :q, :r)
    """), {
        "p": product_id,
        "q": quantity,
        "r": refund
    })

    db.commit()

    return {
        "message": "Product returned successfully",
        "refund": refund
    }

@app.get("/daily-returns")
def daily_returns(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT product_id, SUM(quantity) as total_qty, SUM(refund_amount) as total_returns
        FROM Returns
        WHERE CAST(created_at AS DATE) = CAST(GETDATE() AS DATE)
        GROUP BY product_id
    """)).fetchall()

    return [dict(row._mapping) for row in result]