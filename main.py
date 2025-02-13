from fastapi import FastAPI, Request
from routes.authors import router as authors_router
from routes.books import router as books_router
from routes.users import router as user_router
from database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LMS with FastAPI", description="Learning Management System", version="1.0.0")

app.include_router(user_router, prefix="/api/v1/users")
app.include_router(authors_router, prefix="/api/v1/authors")
app.include_router(books_router, prefix="/api/v1/books")

