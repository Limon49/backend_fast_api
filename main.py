from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

# This one line creates your web application.
# The title shows up in the automatic API docs (see below).
app = FastAPI(title="AIQuest API")


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
