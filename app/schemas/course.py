"""The original teaching example, kept so the first lessons still work.

``POST /api/v1/courses`` validates the body against this model, which is how
the README explains request validation: a bad URL or a missing field comes back
as a clear 422 error, with no validation code written by hand.
"""

from pydantic import BaseModel, HttpUrl


class Course(BaseModel):
    """Request body for ``POST /api/v1/courses``."""

    name: str
    instructor: str
    website: HttpUrl  # must be a valid http/https URL
    duration: float  # hours, e.g. 2.5
