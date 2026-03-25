from fastapi import FastAPI, Depends, Response
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from passlib.context import CryptContext

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/login")
def login(username: str, password: str, response: Response, db: Session = Depends(get_db)):
    user = db.execute(f"SELECT * FROM Users WHERE username='{username}'").fetchone()

    if not user:
        return {"error": "User not found"}

    if not pwd_context.verify(password, user.password):
        return {"error": "Wrong password"}

    # Set cookie (SESSION)
    response.set_cookie(key="user_id", value=str(user.id))
    response.set_cookie(key="role", value=user.role)

    return {"message": "Login success", "role": user.role}