import requests
from fastapi import FastAPI

app = FastAPI()

BILLING_URL = "http://127.0.0.1:8003"
RETURN_URL = "http://127.0.0.1:8004"

@app.get("/daily-report")
def report():

    sales_data = requests.get(f"{BILLING_URL}/daily-sales").json()
    returns_data = requests.get(f"{RETURN_URL}/daily-returns").json()

    sales_dict = {
        row["product_id"]: {
            "sold_qty": row["total_qty"],
            "sales": row["total_sales"]
        }
        for row in sales_data
    }

    returns_dict = {
        row["product_id"]: {
            "returned_qty": row["total_qty"],
            "returns": row["total_returns"]
        }
        for row in returns_data
    }

    all_products = set(sales_dict.keys()) | set(returns_dict.keys())

    report = []
    total_sales = 0
    total_returns = 0

    for pid in all_products:
        sold = sales_dict.get(pid, {"sold_qty": 0, "sales": 0})
        returned = returns_dict.get(pid, {"returned_qty": 0, "returns": 0})

        profit = sold["sales"] - returned["returns"]

        report.append({
            "product_id": pid,
            "sold_qty": sold["sold_qty"],
            "returned_qty": returned["returned_qty"],
            "sales": sold["sales"],
            "returns": returned["returns"],
            "profit": profit
        })

        total_sales += sold["sales"]
        total_returns += returned["returns"]

    return {
        "summary": {
            "total_sales": total_sales,
            "total_returns": total_returns,
            "total_profit": total_sales - total_returns
        },
        "products": report
    }