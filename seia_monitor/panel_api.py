"""
API del panel de monitoreo (FastAPI).
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from seia_monitor.config import Config
from seia_monitor.storage import SEIAStorage

ALLOWED_PIPELINE_STATUS = {"contactado", "en_conversaciones", "fallido", "completado"}
ALLOWED_PRIORIDAD = {"baja", "media", "alta"}


class ManagementPatch(BaseModel):
    pipeline_status: Optional[str] = None
    responsable_lawyer_id: Optional[int] = None
    prioridad: Optional[str] = None
    proxima_accion_at: Optional[str] = None
    ultima_interaccion_at: Optional[str] = None
    probabilidad_cierre: Optional[int] = Field(default=None, ge=0, le=100)
    notas: Optional[str] = None


class ActivityCreate(BaseModel):
    content: str = Field(min_length=1)
    activity_type: str = "nota"
    created_by: Optional[str] = None


class LawyerCreate(BaseModel):
    nombre: str = Field(min_length=1)
    email: Optional[str] = None
    active: bool = True


def create_app() -> FastAPI:
    app = FastAPI(title="SEIA Panel API", version="1.0.0")
    storage = SEIAStorage(db_path=Config.get_panel_db_path())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/projects")
    def list_projects(
        search: Optional[str] = Query(default=None),
        region: Optional[str] = Query(default=None),
        pipeline_status: Optional[str] = Query(default=None),
        responsable_lawyer_id: Optional[int] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        if pipeline_status and pipeline_status not in ALLOWED_PIPELINE_STATUS:
            raise HTTPException(status_code=400, detail="pipeline_status inválido")

        items = storage.list_projects_panel(
            search=search,
            region=region,
            pipeline_status=pipeline_status,
            responsable_lawyer_id=responsable_lawyer_id,
            limit=limit,
            offset=offset,
        )
        total = storage.count_projects_panel(
            search=search,
            region=region,
            pipeline_status=pipeline_status,
            responsable_lawyer_id=responsable_lawyer_id,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        project = storage.get_project_panel_detail(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return project

    @app.patch("/api/projects/{project_id}/management")
    def patch_management(project_id: str, payload: ManagementPatch) -> dict:
        if payload.pipeline_status and payload.pipeline_status not in ALLOWED_PIPELINE_STATUS:
            raise HTTPException(status_code=400, detail="pipeline_status inválido")
        if payload.prioridad and payload.prioridad not in ALLOWED_PRIORIDAD:
            raise HTTPException(status_code=400, detail="prioridad inválida")

        try:
            storage.update_project_management(
                project_id=project_id,
                pipeline_status=payload.pipeline_status,
                responsable_lawyer_id=payload.responsable_lawyer_id,
                prioridad=payload.prioridad,
                proxima_accion_at=payload.proxima_accion_at,
                ultima_interaccion_at=payload.ultima_interaccion_at,
                probabilidad_cierre=payload.probabilidad_cierre,
                notas=payload.notas,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        project = storage.get_project_panel_detail(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return project

    @app.get("/api/projects/{project_id}/activity")
    def get_activity(project_id: str, limit: int = Query(default=50, ge=1, le=200)) -> dict:
        return {"items": storage.get_project_activity(project_id, limit=limit)}

    @app.post("/api/projects/{project_id}/activity")
    def create_activity(project_id: str, payload: ActivityCreate) -> dict:
        activity_id = storage.add_project_activity(
            project_id=project_id,
            content=payload.content,
            activity_type=payload.activity_type,
            created_by=payload.created_by,
        )
        return {"id": activity_id}

    @app.get("/api/dashboard/kpis")
    def dashboard_kpis() -> dict:
        return storage.get_dashboard_kpis()

    @app.get("/api/lawyers")
    def list_lawyers(only_active: bool = Query(default=True)) -> dict:
        return {"items": storage.get_lawyers(only_active=only_active)}

    @app.post("/api/lawyers")
    def create_lawyer(payload: LawyerCreate) -> dict:
        lawyer_id = storage.upsert_lawyer(
            nombre=payload.nombre,
            email=payload.email,
            active=payload.active,
        )
        return {"id": lawyer_id}

    static_dir = Path(__file__).parent / "panel_static"
    app.mount("/panel_static", StaticFiles(directory=static_dir), name="panel_static")

    @app.get("/")
    def panel_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    return app
