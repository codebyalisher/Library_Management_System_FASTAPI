from database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,Table,DateTime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # Store the hashed password (never the plain one)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String)  
    borrower = relationship("Borrower", back_populates="user", uselist=False)

class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # Reference to the User model
    access_token = Column(String, unique=True)
    token_type = Column(String, default='bearer')
    user = relationship('User', back_populates="tokens")

User.tokens = relationship("Token", back_populates="user")

class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bio = Column(String)
    books = relationship("Book", back_populates="author") # Define the reverse relationship in the Author model
    
class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    isbn = Column(String, unique=True)
    author_id = Column(Integer, ForeignKey('authors.id'))
    published_date = Column(String)
    available = Column(Boolean, default=False)
    author = relationship("Author", back_populates="books")
    last_borrowed_date = Column(DateTime, nullable=True)
    
class Borrower(Base):
    __tablename__ = 'borrowers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    books_borrowed = relationship("Book", secondary="borrowed_books")
    user = relationship("User", back_populates="borrower")

borrowed_books = Table('borrowed_books', Base.metadata, # Many to Many relationship
    Column('borrower_id', Integer, ForeignKey('borrowers.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True)
)

