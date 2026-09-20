from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session, select

from src.database import create_db_and_tables, get_session
from src.models import User, UserCreate, UserRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# This one line creates your web application.
# The title shows up in the automatic API docs (see below).
app = FastAPI(title="AIQuest API", lifespan=lifespan)


# --- Request body schema -----------------------------------------------
# A Pydantic model defines the shape of the data your API accepts.
# FastAPI uses it to validate incoming JSON automatically:
# if someone sends a missing field or a wrong type, they get a clear 422 error.
class Course(BaseModel):
    name: str
    instructor: str
    website: HttpUrl  # must be a valid http/https URL
    duration: float   # hours, e.g. 2.5


# --- Routes -------------------------------------------------------------
# Each "decorator" (@app.get / @app.post) turns the function below it
# into an endpoint that responds to HTTP requests.

@app.get("/")
def read_root():
    """The home page of your API."""
    return {"message": "Welcome to AIQuest!"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    """
    Path parameter: {item_id} in the URL (must be an int).
    Query parameter: optional ?q=... after the URL.
    Try it: /items/42?q=hello
    """
    return {"item_id": item_id, "q": q}


@app.get("/courses")
def list_courses():
    """Get all courses (for now, just a placeholder message)."""
    return {"courses": "Get different course details here and learn more."}


@app.post("/courses", status_code=201)
def create_course(course: Course):
    """
    Create a new course. FastAPI reads the JSON body,
    validates it against the Course model, and gives you a Course object.
    """
    return {"message": "Course created successfully", "course": course}


@app.post("/users", response_model=UserRead, status_code=201)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """
    Create a new user and save it to the database.

    - Reads the JSON body and validates it against `UserCreate`.
    - Converts it into a `User` table row.
    - Commits it to the database, which assigns it an `id`.
    - Returns the saved user (including its new `id`) as `UserRead`.
    """
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)  # loads the auto-generated `id` from the DB
    return db_user


@app.get("/users", response_model=list[UserRead])
def list_users(session: Session = Depends(get_session)):
    """Get all users currently stored in the database."""
    users = session.exec(select(User)).all()
    return users


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    """
    Get info for one specific user by id.
    Returns 404 if no user with that id exists.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
