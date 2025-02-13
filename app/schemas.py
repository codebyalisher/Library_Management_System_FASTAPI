import re
from typing import Optional, List
from pydantic import BaseModel,validator

class UserOut(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None 
    role: Optional[str] = 'regular' 

    class Config:
        orm_mode = True
        from_attributes = True 

class UserAuth(BaseModel):
    username: str
    password: str
    email: str
    full_name: Optional[str] = None 
    role: Optional[str] = 'regular'   
    
    
    class Config:
        orm_mode = True 
        from_attributes = True

class TokenSchema(BaseModel):
    access_token: str
    token_type: str  

class TokenPayload(BaseModel): # for decoding the JWT token's payload
    sub: str  # Subject (e.g., user identifier)
    exp: Optional[int]  # Expiration time (optional, if you include exp in the JWT)

# SystemUser schema (used for system or user-related data)
class SystemUser(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: Optional[str] = 'regular'  # Default to 'regular' or whichever role you expect

    class Config:
        orm_mode = True  # Important for ORM (SQLAlchemy) compatibility
        from_attributes = True  # Important for ORM (SQLAlchemy) compatibility

class AssignRoleRequest(BaseModel):
    user_id: int  # ID of the user to assign the role
    role: str     # Role to assign (admin, staff, regular)
    
class AssignRoleResponse(BaseModel):
    message: str
    
class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class AuthorUpdate(AuthorBase):
    name: Optional[str] = None  # Optional fields for updates
    bio: Optional[str] = None
    
class AuthorOut(AuthorBase):
    id: int
    name: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class BookCreate(BaseModel):
    title: str
    isbn: str
    author_id:int
    published_date: str
    
    @validator("isbn")
    def validate_isbn(cls, v):
        if not re.match(r"^\d{10}(\d{3})?$", v):  # Basic ISBN-10/13 validation
            raise ValueError("Invalid ISBN format")
        return v
    class Config:
        orm_mode = True
        from_attributes = True
        
class BookUpdate(BookCreate):
    title: Optional[str] = None
    isbn: Optional[str] = None
    author_id: Optional[int] = None
    published_date: Optional[str] = None
    available: Optional[str] = None

    @validator("isbn")
    def validate_isbn(cls, v):
        if not re.match(r"^\d{10}(\d{3})?$", v):  # Basic ISBN-10/13 validation
            raise ValueError("Invalid ISBN format")
        return v

    class Config:
        orm_mode = True
        from_attributes = True
        
class BookOut(BaseModel):
    id: int
    title: Optional[str] = None
    isbn: Optional[str] = None
    author_id: Optional[int] = None  
    author_name: Optional[str] = None
    published_date: Optional[str] = None
    available: Optional[bool] = None

    @validator("isbn")
    def validate_isbn(cls, v):
        if not re.match(r"^\d{10}(\d{3})?$", v):  # Basic ISBN-10/13 validation
            raise ValueError("Invalid ISBN format")
        return v

    class Config:
        orm_mode = True
        from_attributes = True

class BookSearch(BaseModel):    
    title: Optional[str] = None
    isbn: Optional[str] = None
    author_id: Optional[int] = None  
    author_name: Optional[str] = None
    published_date: Optional[str] = None
    available: Optional[bool] = None
    class Config:
        orm_mode = True
        from_attributes = True
        
class BorrowerBase(BaseModel):
    user_id: int

class BorrowerOut(BorrowerBase):
    books_borrowed: List[BookOut]

    class Config:
        orm_mode = True
        from_attributes = True