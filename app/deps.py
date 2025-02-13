from jose import jwt 
from database import get_db  # Make sure to import your DB session provider
from app.models import User
from typing import Union, Any
from datetime import datetime
from sqlalchemy.orm import Session  
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from .utils import ALGORITHM, JWT_SECRET_KEY
from app.schemas import TokenPayload, SystemUser
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)

async def get_current_user(token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)      
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            return JSONResponse(content={"status":status.HTTP_401_UNAUTHORIZED, "message": "Token expired"},
                status_code=status.HTTP_401_UNAUTHORIZED,                
                headers={"WWW-Authenticate": "Bearer"})            
    except (jwt.JWTError, ValidationError):
        return JSONResponse(content={"status":status.HTTP_403_FORBIDDEN, "message": "Could not validate credentials"},
            status_code=status.HTTP_403_FORBIDDEN,           
            headers={"WWW-Authenticate": "Bearer"})
    user = db.query(User).filter(User.email== token_data.sub).first() 
    if user is None:
        return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND, "message": "User not found"},status_code=status.HTTP_404_NOT_FOUND)    
      
    return user  

def is_admin(user: User):
    if user.role != "admin":
        return JSONResponse(content={"status":status.HTTP_403_FORBIDDEN, "message": "Admin access required"},       status_code=status.HTTP_403_FORBIDDEN,)
        
def is_staff(user: User):
    if user.role not in ["admin", "staff"]:
        return JSONResponse(content={"status":status.HTTP_403_FORBIDDEN, "message": "Staff access required"},status_code=status.HTTP_403_FORBIDDEN)
            
def is_regular(user: User):
    if user.role != "regular":
        return JSONResponse(content={"status":status.HTTP_403_FORBIDDEN, "message": "Regular user access required"},status_code=status.HTTP_403_FORBIDDEN)
        
def is_author(user: User):
    if user.role != "author":
        return JSONResponse(content={"status":status.HTTP_403_FORBIDDEN, "message": "Author user access required"},status_code=status.HTTP_403_FORBIDDEN)