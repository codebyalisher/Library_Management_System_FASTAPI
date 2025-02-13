from uuid import uuid4
from app.models import User
from database import get_db
from sqlalchemy.orm import Session
from app.utils import get_hashed_password
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
from app.deps import get_current_user,is_admin,is_staff,is_regular
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from app.utils import get_hashed_password,create_access_token, create_refresh_token,verify_password
from app.schemas import UserOut, UserAuth, TokenSchema,SystemUser,TokenPayload,AssignRoleRequest,AssignRoleResponse


router=APIRouter()

@router.post('/signup', summary="Create new user", response_model=UserOut)
async def create_user(data: UserAuth, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        return JSONResponse(
            content={"status":status.HTTP_400_BAD_REQUEST, "message": "User with this email already exists"},
            status_code=status.HTTP_400_BAD_REQUEST,            
        )
    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        return JSONResponse(
            content={"status":status.HTTP_400_BAD_REQUEST, "message": "Username  already taken, please choose a different one"},
            status_code=status.HTTP_400_BAD_REQUEST,            
        )    
    hashed_password = get_hashed_password(data.password)  
    new_user = User(        
        username=data.username,
        hashed_password=hashed_password,
        email=data.email,
        full_name=data.full_name if data.full_name else None,
        is_active=True,
        role=data.role if data.role else 'regular', 
    )    
    db.add(new_user)  
    db.commit()  
    db.refresh(new_user) 
    user = UserOut.from_orm(new_user).dict()
    return JSONResponse(content={"status":status.HTTP_201_CREATED, "message": "User created successfully", "user": user}, status_code=status.HTTP_201_CREATED)

@router.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        return JSONResponse(
            content={"status":status.HTTP_404_NOT_FOUND, "message": "user not found"},
            status_code=status.HTTP_404_NOT_FOUND,            
        )    
    # Verifying the password
    if not verify_password(form_data.password, user.hashed_password):
        return JSONResponse(
            content={"status":status.HTTP_400_BAD_REQUEST, "message": "Incorrect email or password"},
            status_code=status.HTTP_400_BAD_REQUEST,            
        )    
    # Generating access and refresh tokens
    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    user=UserOut.from_orm(user).dict()#converting user object to dictionary using pydantic model for josn
    return JSONResponse(
        content={"status":status.HTTP_200_OK,
                 "message": "Login successful",
                 "user": user,
                 "access_token": access_token,
                 "refresh_token": refresh_token,},
                 status_code=status.HTTP_200_OK)
     
@router.get('/me', summary='Get details of currently logged-in user', response_model=SystemUser)
async def get_me(user:User = Depends(get_current_user)):
    if user is None:
        return JSONResponse(
            content={"status":status.HTTP_404_NOT_FOUND, "message": "User not found"},
            status_code=status.HTTP_404_NOT_FOUND
        )
    user=UserOut.from_orm(user).dict()
            
    return JSONResponse(content={"status":status.HTTP_200_OK, "message": "User details fetched successfully","user":user}, status_code=status.HTTP_200_OK)

@router.post("/assign-role", summary="Assign a role to a user", response_model=AssignRoleResponse)
async def assign_role(request: AssignRoleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)    
    user_to_update = db.query(User).filter(User.id == request.user_id).first()
    if not user_to_update:
        return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND, "message": "User not found"}, status_code=status.HTTP_404_NOT_FOUND)
    if request.role not in ["admin", "staff", "regular"]:
        return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST, "message": "Invalid role"}, status_code=status.HTTP_400_BAD_REQUEST)
    try:
        user_to_update.role = request.role
        db.commit()
        db.refresh(user_to_update)
    except Exception as e:
        db.rollback()
        return JSONResponse(content={"status":status.HTTP_500_INTERNAL_SERVER_ERROR, "message": "Failed to assign the role"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content= {"status":status.HTTP_200_OK, "message": f"Role '{request.role}' assigned to user '{user_to_update.username}'"},status_code=status.HTTP_200_OK)
