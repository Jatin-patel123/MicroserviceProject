from fastapi import FastAPI, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.database import SessionLocal

app = FastAPI()

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔒 Role Check Helper
def check_owner(role):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Unauthorized")


# ✅ 1. ADD PRODUCT
@app.post("/add-product")
def add_product(
    name: str,
    buying_price: float,
    selling_price: float,
    quantity: int,
    qty_alert: int,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_owner(role)

    result = db.execute(text("""
        INSERT INTO Products (name, buying_price, selling_price, quantity, qty_alert)
        OUTPUT INSERTED.id
        VALUES (:name, :buying_price, :selling_price, :quantity, :qty_alert)
    """), {
        "name": name,
        "buying_price": buying_price,
        "selling_price": selling_price,
        "quantity": quantity,
        "qty_alert": qty_alert
    })

    product_id = result.fetchone()[0]
    db.commit()

    return {"message": "Product added", "product_id": product_id}


# ✅ 2. GET PRODUCT BY ID (Inventory Check)
@app.get("/get-product/{product_id}")
def get_product(
    product_id: int,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_owner(role)

    result = db.execute(text("""
        SELECT * FROM Products WHERE id = :id
    """), {"id": product_id}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": result.id,
        "name": result.name,
        "buying_price": result.buying_price,
        "selling_price": result.selling_price,
        "quantity": result.quantity,
        "qty_alert": result.qty_alert
    }


# ✅ 3. UPDATE PRODUCT
@app.put("/update-product/{product_id}")
def update_product(
    product_id: int,
    name: str = None,
    buying_price: float = None,
    selling_price: float = None,
    quantity: int = None,
    qty_alert: int = None,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_owner(role)

    # Check if product exists
    existing = db.execute(text("SELECT * FROM Products WHERE id = :id"), {"id": product_id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update only provided fields
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


# ✅ 4. DELETE PRODUCT
@app.delete("/delete-product/{product_id}")
def delete_product(
    product_id: int,
    role: str = Cookie(None),
    db: Session = Depends(get_db)
):
    check_owner(role)

    result = db.execute(text("""
        DELETE FROM Products WHERE id = :id
    """), {"id": product_id})

    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted"}