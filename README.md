# Library_Management_System_FASTAPI
A FastAPI Based Library Management System API to manage books, authors, and borrowers with role-based permissions.
## Project Overview

This project is a simplified Library Management System API built with Django. The API allows users to perform CRUD operations on Books, Authors, and Borrowers. User authentication is implemented to restrict certain operations based on user roles (admin, staff, regular user).

## Table of Contents

- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Routes](#routes)
- [Systematic Breakdown of Requirements](#systematic-breakdown-of-requirements)
  - [Models](#models)
  - [Views and API Endpoints](#views-and-api-endpoints)
  - [Authentication and Permissions](#authentication-and-permissions)
  - [Data Validation](#data-validation)
  - [Unit Testing](#unit-testing)
  - [Bonus Features](#bonus-features)
  - [Final Checklist](#final-checklist)

## Directory Structure

| Directory/File          | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| LMSFastA/               | Root directory of the project.                                              |
| ├── app/                | Contains the core application modules.                                      |
| │   ├── __init__.py     | Initialization file for the app package.                                    |
| │   ├── models.py       | Defines the database models.                                                |
| │   ├── schemas.py      | Defines the Pydantic schemas for data validation.                           |
| │   ├── deps.py         | Contains dependency functions for FastAPI.                                  |
| │   ├── database.py     | Manages database connections and sessions.                                  |
| │   └── main.py         | Entry point of the FastAPI application.                                     |
| ├── routes/             | Contains route handlers for different endpoints.                            |
| │   ├── __init__.py     | Initialization file for the routes package.                                 |
| │   ├── books.py        | Route handlers for book-related endpoints.                                  |
| │   ├── authors.py      | Route handlers for author-related endpoints.                                |
| │   ├── users.py        | Route handlers for user-related endpoints.                                  |
| │   └── borrow.py       | Route handlers for borrowing-related endpoints.                             |      
| ├── README.md           | Project documentation and setup instructions.                               |
| └── requirements.txt    | Lists all the dependencies required to run the project.                     |

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/LMSFastA.git
    cd LMSFastA
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database**:
    ```bash
    # Run the database migrations
    alembic upgrade head
    ```

## Usage

1. **Run the application**:
    ```bash
    uvicorn app.main:app --reload
    ```

2. **Access the API documentation**:
    - Open your browser and go to `http://127.0.0.1:8000/docs` for the Swagger UI documentation.
    - Alternatively, go to `http://127.0.0.1:8000/redoc` for the ReDoc documentation.

## Routes

### User Management

- **Sign Up**: `POST /api/v1/users/signup`
- **Login**: `POST /api/v1/users/login`
- **Get Current User**: `GET /api/v1/users/me`
- **Assign Role**: `POST /api/v1/users/assign-role`

### Author Management

- **Create Author**: `POST /api/v1/authors/create-authors`
- **Get All Authors**: `GET /api/v1/authors/get-all-authors`
- **Get Author by ID**: `GET /api/v1/authors/get-byId`
- **Update Author**: `PUT /api/v1/authors/update-authors`
- **Delete Author**: `DELETE /api/v1/authors/delete-authors`

### Book Management

- **Create Book**: `POST /api/v1/books/create-books`
- **Get All Books**: `GET /api/v1/books/get-all-books`
- **Get Book by ID**: `GET /api/v1/books/get-byId`
- **Update Book**: `PUT /api/v1/books/update-books`
- **Delete Book**: `DELETE /api/v1/books/delete-books`

### Borrowing Books

- **Borrow Book**: `POST /api/v1/borrow/{book_id}`
- **Return Book**: `POST /api/v1/return/{book_id}`

## Systematic Breakdown of Requirements

### Models

#### User Model

Attributes:
- `id`: Primary key (Integer).
- `username`: Unique, indexed (String).
- `email`: Unique, indexed (String).
- `hashed_password`: Hashed password (String).
- `full_name`: Optional (String).
- `is_active`: Boolean (default: True).
- `role`: String (values: admin, staff, regular).

Relationships:
- One-to-one with Borrower.
- One-to-many with Token.

#### Token Model

Attributes:
- `id`: Primary key (Integer).
- `user_id`: Foreign key to User (Integer).
- `access_token`: JWT token (String).
- `token_type`: Token type (String, default: Bearer).

Relationships:
- Many-to-one with User.

#### Author Model

Attributes:
- `id`: Primary key (Integer).
- `name`: Unique, indexed (String).
- `bio`: Optional (Text).

Relationships:
- One-to-many with Book.

#### Book Model

Attributes:
- `id`: Primary key (Integer).
- `title`: Indexed (String).
- `isbn`: Unique, indexed (String).
- `author_id`: Foreign key to Author (Integer).
- `published_date`: Date (Date).
- `available`: Boolean (default: True).

Relationships:
- Many-to-one with Author.
- Many-to-many with Borrower via borrowed_books.

#### Borrower Model

Attributes:
- `id`: Primary key (Integer).
- `user_id`: Foreign key to User (Integer).

Relationships:
- Many-to-many with Book via borrowed_books.

#### Borrowed Books (Junction Table)

Attributes:
- `borrower_id`: Foreign key to Borrower (Integer).
- `book_id`: Foreign key to Book (Integer).

### Views and API Endpoints

#### Author Management

- **Create Author**:
  - Method: POST `/api/v1/authors/create-authors`
  - Permissions: Staff and Admin only.
  - Response: Created author with status 201.

- **Get All Authors**:
  - Method: GET `/api/v1/authors/get-all-authors`
  - Permissions: Anyone (authenticated or not).
  - Response: List of authors.

- **Get Author by ID**:
  - Method: GET `/api/v1/authors/get-byId`
  - Permissions: Anyone.
  - Response: Author details.

- **Update Author**:
  - Method: PUT `/api/v1/authors/update-authors`
  - Permissions: Staff and Admin only.
  - Response: Updated author.

- **Delete Author**:
  - Method: DELETE `/api/v1/authors/delete-authors`
  - Permissions: Staff and Admin only.
  - Response: Status 204.

#### Book Management

- **Create Book**:
  - Method: POST `/api/v1/books/create-books`
  - Permissions: Staff and Admin only.
  - Validation: Ensure ISBN is unique and valid.
  - Response: Created book with status 201.

- **Get All Books**:
  - Method: GET `/api/v1/books/get-all-books`
  - Permissions: Anyone.
  - Response: List of books.

- **Get Book by ID**:
  - Method: GET `/api/v1/books/get-byId`
  - Permissions: Anyone.
  - Response: Book details.

- **Update Book**:
  - Method: PUT `/api/v1/books/update-books`
  - Permissions: Staff and Admin only.
  - Response: Updated book.

- **Delete Book**:
  - Method: DELETE `/api/v1/books/delete-books`
  - Permissions: Staff and Admin only.
  - Response: Status 204.

#### Borrowing Books

- **Borrow Book**:
  - Method: POST `/api/v1/borrow/{book_id}`
  - Permissions: Regular users only.
  - Validation:
    - Book must be available.
    - User cannot borrow more than 3 books.
  - Response: Borrowed book details.

- **Return Book**:
  - Method: POST `/api/v1/return/{book_id}`
  - Permissions: Regular users only.
  - Response: Returned book details.

### Authentication and Permissions

#### JWT Authentication

- Use OAuth2PasswordBearer for JWT token handling.
- Users log in with username and password to receive a JWT token.
- Token includes user role information for role-based access control.

#### Role-Based Access Control (RBAC)

- **Admin**:
  - Full access to all endpoints (users, books, authors, borrow records).

- **Staff**:
  - Can manage books and authors.
  - Cannot manage users or assign roles.

- **Regular Users**:
  - Can borrow and return books.
  - Cannot create, update, or delete books/authors.

#### Permissions

- Use `Depends` in FastAPI to enforce role-based access.

Example:
```python
def is_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
```
# Book Management System Documentation

## Data Validation

### ISBN Validation
- **Ensure ISBN is unique.**
- **Validate ISBN format** (e.g., ISBN-10 or ISBN-13).

### Borrowing Limit
- **Ensure a user cannot borrow more than 3 books at a time.**
- **Implement this in the borrow_book endpoint.**

### User Registration Validation
- **Ensure username and email are unique.**
- **Validate password strength** (e.g., minimum length, special characters).

## Unit Testing

### Test Cases

#### Borrowing Limit:
- **Ensure users cannot borrow more than 3 books.**

#### Permissions:
- **Ensure only authorized users (admin, staff) can create, update, or delete authors/books.**

#### Borrowing and Returning Logic:
- **Ensure borrowing a book updates its availability status.**
- **Ensure returning a book makes it available again.**

#### ISBN Uniqueness:
- **Ensure duplicate ISBNs return an error.**

#### User Role Restrictions:
- **Ensure regular users cannot modify authors or books.**

### Example Test
```python
# Example unit test for borrowing limit
def test_borrowing_limit():
    user = create_user()  # Create a user
    books = [create_book() for _ in range(4)]  # Create 4 books

    for book in books[:3]:
        borrow_book(user, book)  # Borrow 3 books
    with pytest.raises(HTTPException):
        borrow_book(user, books[3])  # Ensure cannot borrow more than 3 books
```
# Bonus Features

### Caching
- **Cache frequently accessed book lists** using Redis or FastAPI's caching system to improve performance and reduce database load.
  
Example setup:
```python
  from fastapi import FastAPI
  from fastapi_cache import FastAPICache
  from fastapi_cache.backends.redis import RedisBackend
  from redis import Redis

  app = FastAPI()

  # Setup Redis cache
  redis = Redis(host="localhost", port=6379, db=0)
  FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

  @app.get("/books")
  async def get_books():
      # This endpoint will cache the result for subsequent calls
      return {"books": books}
```
# Project Documentation

## Search and Filtering
Add search by title and filter by author/availability:
- Example: Search by title=Python and filter by author_name=John.

## Signals
Use FastAPI signals to update `last_borrowed_date` when a book is borrowed.

## Error Handling
Handle errors like borrowing unavailable books or exceeding borrowing limits.

## Final Checklist

### Code Structure and Organization
Follow FastAPI best practices:
- Separate models, schemas, views, and authentication into modules.
- Use dependency injection for database sessions and authentication.

### Correctness
Ensure models, views, permissions, and validations are implemented correctly.

### Authentication and Authorization
Use JWT authentication and role-based permissions effectively.

### Efficiency
Optimize database queries (e.g., use eager loading for relationships).

### Testing
Write comprehensive unit tests for all critical paths.

### Documentation
- Include docstrings for all endpoints and models.
- Provide a README file with setup instructions and API usage examples.

## Contributing
1. Fork the repository.
2. Create a new branch:
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. Make your changes.
4. Commit your changes:
    ```bash
    git commit -m 'Add some feature'
    ```
5. Push to the branch:
    ```bash
    git push origin feature/your-feature-name
    ```
6. Open a pull request.

## Acknowledgements
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- vbnet
  
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
This `README.md` file provides a comprehensive and professional overview of the LMSFastA project, including its directory structure, installation instructions, usage, routes, and detailed requirements. It is suitable for GitHub purposes and provides clear instructions and details for setting up and using the project.
