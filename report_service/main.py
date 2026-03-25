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

@app.get("/daily-report")
def report(db: Session = Depends(get_db)):

    sales = db.execute("SELECT SUM(price) FROM BillItems").fetchone()[0]
    returns = db.execute("SELECT SUM(refund_amount) FROM Returns").fetchone()[0]

    profit = sales - returns

    return {
        "total_sales": sales,
        "returns": returns,
        "profit": profit
    }