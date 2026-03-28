from fastapi import FastAPI, Depends, Response, HTTPException, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import text
from shared.AuthDatabase import SessionLocal
from passlib.context import CryptContext
import hashlib

app = FastAPI()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(sha256_hash)

def verify_password(password: str, hashed: str):
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.verify(sha256_hash, hashed)

@app.post("/register")
def register(username: str, password: str, role: str, db: Session = Depends(get_db)):
    if role not in ["owner", "seller"]:
        raise HTTPException(400, "Invalid role")

    existing = db.execute(text("SELECT * FROM Users WHERE username=:u"), {"u": username}).fetchone()
    if existing:
        raise HTTPException(400, "User exists")

    db.execute(text("""
        INSERT INTO Users (username, password, role)
        VALUES (:u, :p, :r)
    """), {"u": username, "p": hash_password(password), "r": role})

    db.commit()
    return {"message": "Registered"}

@app.post("/login")
def login(username: str, password: str, response: Response, db: Session = Depends(get_db)):
    user = db.execute(text("SELECT * FROM Users WHERE username=:u"), {"u": username}).fetchone()

    if not user or not verify_password(password, user.password):
        raise HTTPException(401, "Invalid credentials")

    response.set_cookie("user_id", str(user.id), httponly=True)
    response.set_cookie("role", user.role, httponly=True)

    return {"message": "Login success"}

@app.get("/validate")
def validate(user_id: int = Cookie(None), role: str = Cookie(None), db: Session = Depends(get_db)):
    if not user_id or not role:
        raise HTTPException(401, "Not logged in")

    user = db.execute(text("SELECT * FROM Users WHERE id=:id"), {"id": user_id}).fetchone()

    if not user or user.role != role:
        raise HTTPException(403, "Invalid session")

    return {"user_id": user.id, "role": user.role}

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("user_id")
    response.delete_cookie("role")
    return {"message": "Logged out"}