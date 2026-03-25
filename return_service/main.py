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

@app.post("/return-product")
def return_product(product_id: int, quantity: int, db: Session = Depends(get_db)):

    product = db.execute(f"SELECT * FROM Products WHERE id={product_id}").fetchone()

    refund = product.selling_price * quantity

    # Add back to inventory
    db.execute(f"""
        UPDATE Products 
        SET quantity = quantity + {quantity}
        WHERE id = {product_id}
    """)

    db.execute(f"""
        INSERT INTO Returns (product_id, quantity, refund_amount)
        VALUES ({product_id}, {quantity}, {refund})
    """)

    db.commit()

    return {"refund": refund}