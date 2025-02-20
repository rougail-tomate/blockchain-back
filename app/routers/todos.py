from fastapi import APIRouter, HTTPException
from app.schemas.todo import Todo

router = APIRouter(
    prefix="/todo",
    tags=["todo"],
)
todo_list = []

@router.get("/")
async def read_todo():
    return {"Todo": todo_list}

@router.get("/{id}")
async def read_todo_by_id(id: int):
    if id >= len(todo_list):
        raise HTTPException(status_code=404, detail="Todo not found")
    else:
        return {"Todo": todo_list[id]}

@router.post("/")
async def create_todo(Todo: Todo):
    Todo.id = len(todo_list) + 1
    todo_list.append(Todo)
    print(todo_list)
    return {"message": "Todo created", "data": Todo.dict()}

@router.put("/{id}")
async def update_todo(id: int, Todo: Todo):
    if id > len(todo_list):
        raise HTTPException(status_code=404, detail="Todo not found")
    else:
        todo_list[id] = Todo
    return {"message": "Todo updated", "data": Todo.dict()}