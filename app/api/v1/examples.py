"""The original teaching endpoints, kept working (now at ``/api/v1/...``).

This is where the first lessons live: a path parameter, a query parameter, a
request body with validation, and a 201 status code. They are grouped in their
own router precisely because they are examples, not a real resource.
"""

from fastapi import APIRouter

from app.schemas.course import Course

router = APIRouter(tags=["examples"])


@router.get("/items/{item_id}", summary="Path + query parameters")
def read_item(item_id: int, q: str | None = None) -> dict:
    """Try ``/api/v1/items/42?q=hello``.

    ``item_id`` comes from the path (and must be an integer), ``q`` is optional
    query string.
    """
    return {"item_id": item_id, "q": q}


@router.get("/courses", summary="Example list endpoint")
def list_courses() -> dict:
    """A placeholder that shows how a list endpoint looks."""
    return {"courses": "Get different course details here and learn more."}


@router.post("/courses", status_code=201, summary="Example POST with validation")
def create_course(course: Course) -> dict:
    """Send a JSON body and get automatic validation for free.

    A missing field or a URL that is not http(s) returns a 422 that says exactly
    what was wrong — no validation code written by hand.
    """
    return {"message": "Course created successfully", "course": course}
