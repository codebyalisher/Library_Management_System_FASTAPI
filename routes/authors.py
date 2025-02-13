from typing import List
from database import get_db
from sqlalchemy.orm import Session
from app.models import Author, User
from fastapi.responses import JSONResponse
from app.deps import get_current_user,is_admin
from app.schemas import AuthorCreate,AuthorUpdate,AuthorOut
from fastapi import  Depends, HTTPException, status, APIRouter



router = APIRouter()

@router.post("/create-authors", response_model=AuthorOut)
def create_author(author_data: AuthorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        existing_author=db.query(Author).filter(Author.name == author_data.name).first()                
        if existing_author:
            return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST,"message": "Author already exists"}, status_code=status.HTTP_400_BAD_REQUEST)
        db_author = Author(**author_data.dict())
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
        
        author_out = AuthorOut(
            id=db_author.id,
            name=db_author.name,
            bio=db_author.bio
        )
        
        return JSONResponse(
            content={"status": status.HTTP_201_CREATED, "message": "Author created successfully", "data": author_out.dict()},
            status_code=status.HTTP_201_CREATED )
    else:
        return JSONResponse(content={"status":status.HTTP_401_UNAUTHORIZED,"message": "Only admin has the authority to create the author"}, status_code=status.HTTP_401_UNAUTHORIZED)

@router.get("/get-authors", response_model=list[AuthorOut])
def get_authors(db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    if not authors:
        return JSONResponse(
            content={"status": status.HTTP_404_NOT_FOUND, "message": "No authors found"},
            status_code=status.HTTP_404_NOT_FOUND
        )
    authors_data = [AuthorOut.from_orm(author) for author in authors]
    
    return JSONResponse( content={"status": status.HTTP_200_OK, "message": "Authors retrieved successfully", "data": [author.dict() for author in authors_data]},status_code=status.HTTP_200_OK )

@router.get("/get-authors-byId/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        return JSONResponse(content={"status": status.HTTP_404_NOT_FOUND, "message": "Author not found"}, status_code=status.HTTP_404_NOT_FOUND )
    author_out = AuthorOut.from_orm(author)
    
    return JSONResponse(content={"status": status.HTTP_200_OK, "message": "Author retrieved successfully", "data": author_out.dict()},status_code=status.HTTP_200_OK)

@router.put("/update-authors/{author_id}", response_model=AuthorOut)
def update_author(author_id: int, author: AuthorUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        db_author = db.query(Author).filter(Author.id == author_id).first()
        if not db_author:
            return JSONResponse(content={"status": status.HTTP_404_NOT_FOUND, "message": "Author not found"}, status_code=status.HTTP_404_NOT_FOUND)
        # for key, value in author.dict().items(): this method can be also used to update the author
        #     setattr(db_author, key, value)
        if author.name is not None:
            db_author.name = author.name
        if author.bio is not None:
            db_author.bio = author.bio
        existing_author=db.query(Author).filter(Author.name == author.name).first()                
        if existing_author:
            return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST,"message": "Author already Updated"}, status_code=status.HTTP_400_BAD_REQUEST)
        db.commit()
        db.refresh(db_author)
        updated_data = AuthorOut.from_orm(db_author)
        return JSONResponse(content={"status": status.HTTP_200_OK, "message": "Author updated successfully", "data": updated_data.dict()}, status_code=status.HTTP_200_OK)
    else:
       return JSONResponse(content={"status": status.HTTP_401_UNAUTHORIZED, "message": "Only admin has the authority to update the author"}, status_code=status.HTTP_401_UNAUTHORIZED)

@router.delete("/delete-authors/{author_id}")
def delete_author(author_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        db_author = db.query(Author).filter(Author.id == author_id).first()
        if not db_author:
            return JSONResponse(content={"status": status.HTTP_404_NOT_FOUND, "message": "Author not found"}, status_code=status.HTTP_404_NOT_FOUND)
        db.delete(db_author)
        db.commit()
        return JSONResponse(content={"status": status.HTTP_200_OK, "message": "Author deleted successfully"}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"status": status.HTTP_401_UNAUTHORIZED, "message": "Only admin has the authority to delete the author"}, status_code=status.HTTP_401_UNAUTHORIZED)

    
    