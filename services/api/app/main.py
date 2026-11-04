from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, get_db
from app.init_db import init_db
from app.models import InventoryItem, Project
from app.schemas import (
    InventoryCreate,
    InventoryRead,
    InventoryUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)
from app.security import require_api_token

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.validate_runtime()
    init_db()
    yield
    engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

DbSession = Annotated[Session, Depends(get_db)]
Authenticated = Annotated[None, Depends(require_api_token)]


def _save(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="The requested change violates a data constraint") from exc


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api", "environment": settings.environment}


@app.get("/ready", tags=["operations"])
def ready(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ready", "database": "ok"}


@app.get("/api/v1/inventory", response_model=list[InventoryRead], tags=["inventory"])
def list_inventory(
    db: DbSession,
    _: Authenticated,
    q: str | None = Query(default=None, min_length=1, max_length=160),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InventoryItem]:
    statement = select(InventoryItem)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(InventoryItem.name.ilike(f"%{escaped}%", escape="\\"))
    return list(db.scalars(statement.order_by(InventoryItem.created_at.desc()).offset(offset).limit(limit)).all())


@app.post("/api/v1/inventory", response_model=InventoryRead, status_code=status.HTTP_201_CREATED, tags=["inventory"])
def create_inventory(payload: InventoryCreate, db: DbSession, _: Authenticated) -> InventoryItem:
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    _save(db)
    db.refresh(item)
    return item


@app.get("/api/v1/inventory/{item_id}", response_model=InventoryRead, tags=["inventory"])
def get_inventory(item_id: str, db: DbSession, _: Authenticated) -> InventoryItem:
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@app.patch("/api/v1/inventory/{item_id}", response_model=InventoryRead, tags=["inventory"])
def update_inventory(item_id: str, payload: InventoryUpdate, db: DbSession, _: Authenticated) -> InventoryItem:
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    _save(db)
    db.refresh(item)
    return item


@app.delete("/api/v1/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["inventory"])
def delete_inventory(item_id: str, db: DbSession, _: Authenticated) -> Response:
    item = db.get(InventoryItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    db.delete(item)
    _save(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/v1/projects", response_model=list[ProjectRead], tags=["projects"])
def list_projects(
    db: DbSession,
    _: Authenticated,
    q: str | None = Query(default=None, min_length=1, max_length=160),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Project]:
    statement = select(Project)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(Project.name.ilike(f"%{escaped}%", escape="\\"))
    return list(db.scalars(statement.order_by(Project.created_at.desc()).offset(offset).limit(limit)).all())


@app.post("/api/v1/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, tags=["projects"])
def create_project(payload: ProjectCreate, db: DbSession, _: Authenticated) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    _save(db)
    db.refresh(project)
    return project


@app.get("/api/v1/projects/{project_id}", response_model=ProjectRead, tags=["projects"])
def get_project(project_id: str, db: DbSession, _: Authenticated) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.patch("/api/v1/projects/{project_id}", response_model=ProjectRead, tags=["projects"])
def update_project(project_id: str, payload: ProjectUpdate, db: DbSession, _: Authenticated) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    _save(db)
    db.refresh(project)
    return project


@app.delete("/api/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
def delete_project(project_id: str, db: DbSession, _: Authenticated) -> Response:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    _save(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
