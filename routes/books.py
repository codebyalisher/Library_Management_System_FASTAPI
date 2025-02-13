from database import get_db
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi_cache.decorator import cache
from fastapi.responses import JSONResponse
from app.models import Book, Borrower, User,Author
from app.schemas import BookCreate, BookUpdate,BookOut,BookSearch
from app.deps import get_current_user, is_staff,is_admin,is_author
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter


router = APIRouter()

@router.post("/create-books", response_model=BookOut)
def create_book(book: BookCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        
        author = db.query(Author).filter(Author.id == book.author_id).first()
        if not author:
            return JSONResponse(
                content={"status":status.HTTP_404_NOT_FOUND,"message":"Author Not Found"},
                status_code=status.HTTP_404_NOT_FOUND)    
                    
        existing_book = db.query(Book).filter(Book.isbn == book.isbn).first()
        if existing_book:
            return JSONResponse(
                content={"status": status.HTTP_400_BAD_REQUEST, "message": "A book with the same ISBN already exists."},
                status_code=status.HTTP_400_BAD_REQUEST)
            
        existing_book = db.query(Book).filter(            
            Book.title == book.title,            
            Book.published_date == book.published_date
        ).first()

        if existing_book:
            return JSONResponse(
                content={"status":status.HTTP_400_BAD_REQUEST,"message":"A book with the given records already exists."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        db_book = Book(
            title=book.title,
            isbn=book.isbn,
            author_id=author.id,
            published_date=book.published_date
        )
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        
        db_book=BookOut.from_orm(db_book).dict()      
        
        return JSONResponse(
            content={"status": status.HTTP_201_CREATED, "message": "Book created successfully", "data": db_book},
            status_code=status.HTTP_201_CREATED
        )
    else:
        return JSONResponse(
            content={"status": status.HTTP_403_FORBIDDEN, "message": "Only Admin has the authority To Create the Book"},
            status_code=status.HTTP_403_FORBIDDEN
        )
        
@cache(expire=60)
@router.get("/get-all-books", response_model=list[BookOut])
def get_books(db: Session = Depends(get_db)):
    books=db.query(Book, Author.name.label("author_name")).join(Author).all()  
    if not books:
        return JSONResponse(
            content={"status":status.HTTP_404_NOT_FOUND,"message":"Books  doesn't exists."},
            status_code=status.HTTP_404_NOT_FOUND
        )
    books_details = [
        BookOut(
            id=book.id,
            title=book.title,
            isbn=book.isbn,
            author_id=book.author_id,
            author_name=author_name,  # Use the author_name from the tuple
            published_date=book.published_date,
            available=book.available
        ) for book, author_name in books
    ]

    books_data = [book.dict() for book in books_details]
    return JSONResponse(
            content={"status":status.HTTP_200_OK,"message":"Detail's of books along with the author, title, and publish date here.","data":books_data},
            status_code=status.HTTP_200_OK,
        )

@router.get("/get-book-ById/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND,"message":"Book Not Found"},status_code=status.HTTP_404_NOT_FOUND)
    book=BookOut.from_orm(book).dict()
    return JSONResponse(content={"status":status.HTTP_200_OK,"message":"Book Found successfully","data":book},status_code=status.HTTP_200_OK)

@router.put("/update-book/{book_id}", response_model=BookCreate)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_admin(current_user)
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
       return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND,"message":"Book Not Found"},status_code=status.HTTP_404_NOT_FOUND)

    if book.isbn is not None:
        existing_book = db.query(Book).filter(Book.isbn == book.isbn, Book.id != book_id).first()
    if existing_book:
        return JSONResponse(
            content={"status": status.HTTP_400_BAD_REQUEST, "message": "A book with the same ISBN already exists."},
            status_code=status.HTTP_400_BAD_REQUEST)
        
    if book.title is not None:
        db_book.title = book.title
    if book.isbn is not None:
        db_book.isbn = book.isbn
    if book.author_id is not None:
        db_book.author_id = book.author_id
    if book.published_date is not None:
        db_book.published_date = book.published_date
        
         # for key, value in book.dict().items():
        #     setattr(db_book, key, value)
        
    db.commit()
    db.refresh(db_book)
    
    updated_book = db.query(Book, Author.name.label("author_name")).join(Author).filter(Book.id == book_id).first()
    if not updated_book:
        return JSONResponse(
            content={"status": status.HTTP_404_NOT_FOUND, "message": "Book Not Found"},
            status_code=status.HTTP_404_NOT_FOUND)
        
    book_out = BookOut(
        id=updated_book.Book.id,
        title=updated_book.Book.title,
        isbn=updated_book.Book.isbn,
        author_name=updated_book.author_name,
        published_date=updated_book.Book.published_date,
        available=updated_book.Book.available
    )
    return JSONResponse(content={"status":status.HTTP_200_OK,"message":"Book Updated successfully","data":book_out.dict()},status_code=status.HTTP_200_OK)

@router.delete("/delete-book/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_admin(current_user):
        db_book = db.query(Book).filter(Book.id == book_id).first()
        if not db_book:
            return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND,"message":"Book Not Found"},status_code=status.HTTP_404_NOT_FOUND)
        db.delete(db_book)
        db.commit()
        return JSONResponse(content={"status":status.HTTP_200_OK,"message":"Book Deleted successfully"},status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"status": status.HTTP_403_FORBIDDEN, "message": "Only Admin has the authority To Delete the Book"},status_code=status.HTTP_403_FORBIDDEN)     

@router.get("/search/", response_model=list[BookOut])
def search_books(title: str = None,author_name: str = None,available: bool = None,db: Session = Depends(get_db)):    
    query = db.query(Book).join(Author)    
    if author_name:
        query = query.filter(Author.name.ilike(f"%{author_name}%"))    
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))    
    if available is not None:
        query = query.filter(Book.available == available) 
    books = query.all()
    if not books:
        return JSONResponse(
            content={"status": status.HTTP_404_NOT_FOUND, "message": "No books found"},
            status_code=status.HTTP_404_NOT_FOUND
        )    
    
    books_data = [
        BookOut(  
            id=book.id,          
            title=book.title,
            isbn=book.isbn,
            author_name=book.author.name,
            published_date=book.published_date,
            available=book.available
        ) for book in books
    ]

    books_dict = [book.dict() for book in books_data]    
    return JSONResponse(
        content={"status": status.HTTP_200_OK, "message": "Books Found successfully", "data": books_dict},
        status_code=status.HTTP_200_OK
    )

@router.post("/borrow-book/{book_id}")
def borrow_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["regular"]:
        return JSONResponse(
            content={"status": status.HTTP_403_FORBIDDEN, "message": "Only regular users can borrow books"},status_code=status.HTTP_403_FORBIDDEN)
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND,"message":"Book Not Found"},status_code=status.HTTP_404_NOT_FOUND)
    if not book.available:
        return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST,"message":"Book is not available"},status_code=status.HTTP_400_BAD_REQUEST)
    
    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower:
        borrower = Borrower(user_id=current_user.id)
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
    
    if len(borrower.books_borrowed) >= 3:
        return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST,"message":"You cannot borrowed more than 3 books"},status_code=status.HTTP_400_BAD_REQUEST)
    
    borrower.books_borrowed.append(book)
    book.available = False
    book.last_borrowed_date = datetime.utcnow()  # Update last_borrowed_date
    db.commit()
    return JSONResponse(content={"status":status.HTTP_200_OK,"message":"Book borrowed successfully"},status_code=status.HTTP_200_OK)

@router.post("/return-book/{book_id}")
def return_book(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["regular"]:
        return JSONResponse(content={"status": status.HTTP_403_FORBIDDEN, "message": "Only regular users can return books"},status_code=status.HTTP_403_FORBIDDEN)
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return JSONResponse(content={"status":status.HTTP_404_NOT_FOUND,"message":"Book Not Found"},status_code=status.HTTP_404_NOT_FOUND)
    
    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower or book not in borrower.books_borrowed:
        return JSONResponse(content={"status":status.HTTP_400_BAD_REQUEST,"message":"You have not borrowed this book"},status_code=status.HTTP_400_BAD_REQUEST)
    
    borrower.books_borrowed.remove(book)
    book.available = True
    db.commit()
    return JSONResponse(content={"status":status.HTTP_200_OK,"message":"Book returned successfully"},status_code=status.HTTP_200_OK)

