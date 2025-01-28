from fastapi import FastAPI, HTTPException, Depends, APIRouter, Query, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import Optional, List
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_403_FORBIDDEN,
    HTTP_200_OK,
)
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Fetch the API Key from the environment
API_KEY = os.getenv("LAB4_API_KEY")
if not API_KEY:
    raise RuntimeError("API Key not set in the environment variables")

# Initialize FastAPI app
app = FastAPI()

# Dependency for API Key validation
api_key_header = APIKeyHeader(name="X-API-Key")

async def api_key_query(api_key: str = Query(None, alias="api-key")):
    return api_key

def validate_api_key(
    header_api_key: str = Depends(api_key_header),
    query_api_key: str = Depends(api_key_query),
):
    # Check if either the header or query parameter contains the valid API key
    api_key = header_api_key or query_api_key
    if api_key != API_KEY:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail={"error": "Invalid API Key"}
        )
    return api_key

# In-memory database for tasks
task_db = [
    {
        "task_id": 1,
        "task_title": "Laboratory Activity",
        "task_desc": "Create Lab Act 2",
        "is_finished": False,
    }
]

class TaskCreate(BaseModel):
    task_title: str
    task_desc: str
    is_finished: Optional[bool] = False

class TaskUpdate(BaseModel):
    task_title: Optional[str]
    task_desc: Optional[str]
    is_finished: Optional[bool]

def find_task_by_id(task_id: int):
    for task in task_db:
        if task["task_id"] == task_id:
            return task
    return None

# Define APIRouters for versioning
apiv1_router = APIRouter(
    prefix="/apiv1",
    dependencies=[Depends(validate_api_key)],
    tags=["API v1"],
)

apiv2_router = APIRouter(
    prefix="/apiv2",
    dependencies=[Depends(validate_api_key)],
    tags=["API v2"],
)

# --- APIV1 Endpoints ---
@apiv1_router.get("/tasks/{task_id}", status_code=HTTP_200_OK)
def get_task_v1(task_id: int):
    task = find_task_by_id(task_id)
    if task:
        return {"status": "ok", "data": task}
    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND, detail={"error": "Task not found"}
    )

# --- APIV2 Endpoints ---
@apiv2_router.get("/tasks/{task_id}", status_code=HTTP_200_OK)
def get_task_v2(task_id: int):
    task = find_task_by_id(task_id)
    if task:
        return {"status": "ok", "data": task}
    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND, detail={"error": "Task not found"}
    )

@apiv2_router.post("/tasks", status_code=HTTP_201_CREATED)
def create_task_v2(task: TaskCreate):
    if not task.task_title.strip() or not task.task_desc.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task title and description cannot be empty"},
        )
    
    new_task_id = max([t["task_id"] for t in task_db]) + 1 if task_db else 1
    new_task = {
        "task_id": new_task_id,
        "task_title": task.task_title,
        "task_desc": task.task_desc,
        "is_finished": task.is_finished,
    }
    task_db.append(new_task)
    return {"status": "ok", "data": new_task}

@apiv2_router.patch("/tasks/{task_id}", status_code=HTTP_200_OK)
def update_task_v2(task_id: int, task: TaskUpdate):
    existing_task = find_task_by_id(task_id)
    if not existing_task:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail={"error": "Task not found"}
        )
    
    if task.task_title is not None:
        if not task.task_title.strip():
            raise HTTPException(
                status_code=400, detail={"error": "Task title cannot be empty"}
            )
        existing_task["task_title"] = task.task_title
    if task.task_desc is not None:
        if not task.task_desc.strip():
            raise HTTPException(
                status_code=400, detail={"error": "Task description cannot be empty"}
            )
        existing_task["task_desc"] = task.task_desc
    if task.is_finished is not None:
        existing_task["is_finished"] = task.is_finished

    return {"status": "ok", "data": existing_task}

@apiv2_router.delete("/tasks/{task_id}", status_code=HTTP_204_NO_CONTENT)
def delete_task_v2(task_id: int):
    task = find_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail={"error": "Task not found"}
        )
    
    task_db.remove(task)
    return None

@apiv2_router.get("/tasks", status_code=HTTP_200_OK)
def get_all_tasks_v2():
    if not task_db:
        return {"status": "ok", "data": [], "message": "No tasks available"}
    return {"status": "ok", "data": task_db}

# Include the routers in the main app
app.include_router(apiv1_router)
app.include_router(apiv2_router)
