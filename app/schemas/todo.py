from pydantic import BaseModel
from datetime import datetime

class Todo(BaseModel):
    id: int | None
    title: str
    description: str | None
    is_done: bool
    deadline: datetime | str | None
