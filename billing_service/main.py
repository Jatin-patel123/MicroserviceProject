from fastapi import FastAPI, Depends, Cookie
from sqlalchemy.orm import Session
from shared.database import SessionLocal

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/create-bill")
def create_bill(items: list, role: str = Cookie(None), db: Session = Depends(get_db)):

    if role != "seller":
        return {"error": "Unauthorized"}

    total = 0

    for item in items:
        product = db.execute(f"SELECT * FROM Products WHERE id={item['product_id']}").fetchone()

        cost = product.selling_price * item['quantity']
        total += cost

        # Reduce inventory
        db.execute(f"""
            UPDATE Products 
            SET quantity = quantity - {item['quantity']}
            WHERE id = {product.id}
        """)

    db.commit()

    return {"total_bill": total}