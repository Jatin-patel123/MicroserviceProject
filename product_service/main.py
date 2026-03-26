from fastapi import FastAPI, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.ProductDatabase import SessionLocal
import requests

app = FastAPI()
AUTH_URL = "http://127.0.0.1:8001"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate(user_id, role):
    res = requests.get(f"{AUTH_URL}/validate", cookies={"user_id": str(user_id), "role": role})
    if res.status_code != 200:
        raise HTTPException(401, "Unauthorized")
    return res.json()
def check_access(role):
    if role not in ["owner", "seller"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
# ADD PRODUCT

@app.post("/add-product")
def add_product(
    name: str,
    buying_price: float,
    selling_price: float,
    quantity: int,
    qty_alert: int,
    user_id: int = Cookie(None),
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):

    validate(user_id, role)

    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner allowed")

    # ✅ Insert product
    db.execute(text("""
        INSERT INTO Products (name, buying_price, selling_price, quantity, qty_alert)
        VALUES (:n, :b, :s, :q, :a)
    """), {
        "n": name,
        "b": buying_price,
        "s": selling_price,
        "q": quantity,
        "a": qty_alert
    })

    db.commit()

    # ✅ Get latest inserted ID
    result = db.execute(text("SELECT TOP 1 id FROM Products ORDER BY id DESC"))
    product_id = result.fetchone()[0]

    return {
        "message": "Product added successfully",
        "product_id": product_id
    }
# GET PRODUCT
@app.get("/get-product/{id}")
def get_product(id: int, user_id: int = Cookie(None), role: str = Cookie(None), db: Session = Depends(get_db)):
    validate(user_id, role)

    product = db.execute(text("SELECT * FROM Products WHERE id=:id"), {"id": id}).fetchone()
    if not product:
        raise HTTPException(404, "Not found")

    return dict(product._mapping)

# ✅ UPDATE PRODUCT
@app.put("/update-product/{product_id}")
def update_product(
    product_id: int,
    name: str = None,
    buying_price: float = None,
    selling_price: float = None,
    quantity: int = None,
    qty_alert: int = None,
    user_id: int = Cookie(None),
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    validate(user_id, role)
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner allowed")
    existing = db.execute(text("SELECT * FROM Products WHERE id=:id"),
                          {"id": product_id}).fetchone()
    

    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    db.execute(text("""
        UPDATE Products
        SET 
            name = COALESCE(:name, name),
            buying_price = COALESCE(:buying_price, buying_price),
            selling_price = COALESCE(:selling_price, selling_price),
            quantity = COALESCE(:quantity, quantity),
            qty_alert = COALESCE(:qty_alert, qty_alert)
        WHERE id = :id
    """), {
        "name": name,
        "buying_price": buying_price,
        "selling_price": selling_price,
        "quantity": quantity,
        "qty_alert": qty_alert,
        "id": product_id
    })

    db.commit()
    return {"message": "Product updated"}


# ✅ DELETE PRODUCT
@app.delete("/delete-product/{product_id}")
def delete_product(
    product_id: int,
    user_id: int = Cookie(None),
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    validate(user_id, role)
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only owner allowed")

    result = db.execute(text("DELETE FROM Products WHERE id=:id"),
                        {"id": product_id})

    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted"}


@app.put("/reduce-stock/{product_id}")
def reduce_stock(
    product_id: int,
    quantity: int,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_access(role)

    product = db.execute(text("SELECT * FROM Products WHERE id=:id"),
                         {"id": product_id}).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.quantity < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    db.execute(text("""
        UPDATE Products
        SET quantity = quantity - :qty
        WHERE id = :id
    """), {"qty": quantity, "id": product_id})

    db.commit()

    return {"message": "Stock reduced"}


# 🔥 INCREASE STOCK (USED BY RETURNS)
@app.put("/increase-stock/{product_id}")
def increase_stock(
    product_id: int,
    quantity: int,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_access(role)

    db.execute(text("""
        UPDATE Products
        SET quantity = quantity + :qty
        WHERE id = :id
    """), {"qty": quantity, "id": product_id})

    db.commit()

    return {"message": "Stock increased"}