#this file is to define enpoints like controller -> here is the
#acutal put/post/update/delete logic

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..auth import verify_password, create_access_token, hash_password
from ..db import pool

router = APIRouter()

@router.post("/register")
async def register(email: str, password: str):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if user:
            raise HTTPException(status_code=400, detail="User already exists")
        hashed = hash_password(password)
        await conn.execute("INSERT INTO users (email, hashed_password) VALUES ($1, $2)", email, hashed)
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", form_data.username)
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}
