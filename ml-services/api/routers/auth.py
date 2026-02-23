from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from api.auth_utils import create_access_token, get_password_hash, verify_password, Token, ACCESS_TOKEN_EXPIRE_MINUTES
from data_pipeline.db_connector import DBConnector
from api.security import limiter
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from utils.audit_logger import audit_logger
import pandas as pd

router = APIRouter()

@router.post("/auth/register")
@limiter.limit("5/minute")
def register(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        hashed_password = get_password_hash(form_data.password)
        
        # Check if user exists
        # Note: We need a 'users' table. Assuming it exists or we mock it.
        # For MVP/Simulated Env without DB, we might fail here if table missing.
        
        query_check = "SELECT * FROM users WHERE username = %s"
        query_insert = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        
        with DBConnector.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query_check, (form_data.username,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Username already registered")
                
                cur.execute(query_insert, (form_data.username, hashed_password))
                conn.commit()
                
        return {"status": "User created"}
    except Exception as e:
        # Handle Table Not Found gracefully for MVP
        if "relation \"users\" does not exist" in str(e):
             raise HTTPException(status_code=500, detail="Users table missing. Please run migration.")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        query = "SELECT username, password_hash FROM users WHERE username = %s"
        
        with DBConnector() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (form_data.username,))
                result = cur.fetchone()
                
        if not result or not verify_password(form_data.password, result[1]):
            audit_logger.log_event(
                event_type="LOGIN_ATTEMPT",
                user_id=form_data.username,
                status="FAILURE",
                ip_address=request.client.host if request.client else "unknown",
                details={"reason": "Invalid credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": result[0]}, expires_delta=access_token_expires
        )
        
        audit_logger.log_event(
            event_type="LOGIN_ATTEMPT",
            user_id=result[0],
            status="SUCCESS",
            ip_address=request.client.host if request.client else "unknown"
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except RateLimitExceeded:
        raise
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_event(
            event_type="LOGIN_ERROR",
            user_id=form_data.username,
            status="ERROR",
            details={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=str(e))
