import httpx
from fastapi import FastAPI, Request, Response, HTTPException, Body, Cookie, Query
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="Store Management System Gateway")

# Configuration
SERVICES = {
    "auth": "http://127.0.0.1:8001",
    "product": "http://127.0.0.1:8002",
    "billing": "http://127.0.0.1:8003",
    "return": "http://127.0.0.1:8004",
    "report": "http://127.0.0.1:8005"
}

# --- Shared Models for Swagger ---
class BillItem(BaseModel):
    product_id: int
    quantity: int

# --- Universal Proxy Function ---
async def proxy_request(service: str, path: str, method: str, request: Request, json_data=None):
    url = f"{SERVICES[service]}{path}"
    
    # Extract cookies from the incoming gateway request
    incoming_cookies = request.cookies 

    async with httpx.AsyncClient() as client:
        try:
            proxy_res = await client.request(
                method=method,
                url=url,
                params=dict(request.query_params),
                json=json_data,  # This sends the List[Item]
                headers={k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]},
                cookies=incoming_cookies, # FORWARD THE AUTH COOKIES HERE
                timeout=10.0
            )
            
            # Create a Response object for the Gateway to return to you
            response = Response(content=proxy_res.content, status_code=proxy_res.status_code)
            
            # Ensure the Gateway returns any new cookies the service might set
            for name, value in proxy_res.cookies.items():
                response.set_cookie(key=name, value=value, httponly=True)
            return response
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Service {service} connection failed")

# ---------------- AUTH SERVICE ----------------
@app.post("/register", tags=["Auth"])
async def register(username: str, password: str, role: str, request: Request):
    return await proxy_request("auth", "/register", "POST", request)

@app.post("/login", tags=["Auth"])
async def login(username: str, password: str, request: Request):
    return await proxy_request("auth", "/login", "POST", request)

@app.get("/validate", tags=["Auth"])
async def validate(request: Request):
    return await proxy_request("auth", "/validate", "GET", request)

@app.post("/logout", tags=["Auth"])
async def logout(request: Request):
    return await proxy_request("auth", "/logout", "POST", request)

# ---------------- PRODUCT SERVICE ----------------
@app.post("/add-product", tags=["Product"])
async def add_product(name: str, buying_price: float, selling_price: float, quantity: int, qty_alert: int, request: Request):
    return await proxy_request("product", "/add-product", "POST", request)

@app.get("/get-product/{id}", tags=["Product"])
async def get_product(id: int, request: Request):
    return await proxy_request("product", f"/get-product/{id}", "GET", request)

@app.put("/update-product/{product_id}", tags=["Product"])
async def update_product(product_id: int, request: Request, name: str = None, buying_price: float = None, selling_price: float = None, quantity: int = None, qty_alert: int = None):
    return await proxy_request("product", f"/update-product/{product_id}", "PUT", request)

@app.delete("/delete-product/{product_id}", tags=["Product"])
async def delete_product(product_id: int, request: Request):
    return await proxy_request("product", f"/delete-product/{product_id}", "DELETE", request)

# ---------------- BILLING SERVICE ----------------
@app.post("/create-bill", tags=["Billing"])
async def create_bill(request: Request, items: List[BillItem] = Body(...)):
    # Convert Pydantic models to dict so httpx can send them as JSON
    data_to_send = [item.dict() for item in items]
    return await proxy_request("billing", "/create-bill", "POST", request, json_data=data_to_send)

@app.get("/daily-sales", tags=["Billing"])
async def daily_sales(request: Request):
    return await proxy_request("billing", "/daily-sales", "GET", request)

# ---------------- RETURN SERVICE ----------------
@app.post("/return-product", tags=["Return"])
async def return_product(product_id: int, quantity: int, request: Request):
    return await proxy_request("return", "/return-product", "POST", request)

@app.get("/daily-returns", tags=["Return"])
async def daily_returns(request: Request):
    return await proxy_request("return", "/daily-returns", "GET", request)

# ---------------- REPORT SERVICE ----------------
@app.get("/daily-report", tags=["Report"])
async def daily_report(request: Request):
    return await proxy_request("report", "/daily-report", "GET", request)
