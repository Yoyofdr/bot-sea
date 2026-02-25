"""
Capa de persistencia con SQLite.
Maneja proyectos actuales, historial de cambios y estadísticas de corridas.
"""

import re
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ChangeEvent, RunStats, ProjectDetails

logger = get_logger("storage")


class SEIAStorage:
    """Manejo de persistencia en SQLite"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta de la base de datos (usa Config si no se especifica)
        """
        if db_path is None:
            db_path = Config.get_db_path()
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar schema
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Crea una nueva conexión a la base de datos"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        """Crea las tablas si no existen"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla: projects_current
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects_current (
                    project_id TEXT PRIMARY KEY,
                    nombre_proyecto TEXT NOT NULL,
                    titular TEXT,
                    region TEXT,
                    tipo TEXT,
                    fecha_ingreso TEXT,
                    estado TEXT,
                    estado_normalizado TEXT,
                    url_detalle TEXT,
                    raw_row TEXT,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """)
            
            # Tabla: project_history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    estado_anterior TEXT,
                    estado_nuevo TEXT,
                    estado_anterior_normalizado TEXT,
                    estado_nuevo_normalizado TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_relevant BOOLEAN,
                    FOREIGN KEY (project_id) REFERENCES projects_current(project_id)
                )
            """)
            
            # Tabla: runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_seconds REAL,
                    total_projects INTEGER,
                    pages_scraped INTEGER,
                    scrape_method TEXT,
                    errors TEXT,
                    nuevos_count INTEGER,
                    cambios_count INTEGER,
                    success BOOLEAN
                )
            """)
            
            # Tabla: monitor_state (máquina de estados)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitor_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla: projects_staging (staging area para validación pre-commit)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects_staging (
                    project_id TEXT PRIMARY KEY,
                    nombre_proyecto TEXT NOT NULL,
                    titular TEXT,
                    region TEXT,
                    tipo TEXT,
                    fecha_ingreso TEXT,
                    estado TEXT,
                    estado_normalizado TEXT,
                    url_detalle TEXT,
                    raw_row TEXT,
                    first_seen TIMESTAMP,
                    last_updated TIMESTAMP
                )
            """)

            # Tabla: project_details (información detallada de proyectos aprobados)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_details (
                    project_id TEXT PRIMARY KEY,
                    nombre_completo TEXT,
                    tipo_proyecto TEXT,
                    monto_inversion TEXT,
                    descripcion_completa TEXT,
                    titular_nombre TEXT,
                    titular_domicilio TEXT,
                    titular_ciudad TEXT,
                    titular_telefono TEXT,
                    titular_fax TEXT,
                    titular_email TEXT,
                    rep_legal_nombre TEXT,
                    rep_legal_domicilio TEXT,
                    rep_legal_telefono TEXT,
                    rep_legal_fax TEXT,
                    rep_legal_email TEXT,
                    scraped_at TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_current(project_id)
                )
            """)

            # Tabla: lawyers (catálogo de abogados)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lawyers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    email TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabla: project_management (estado comercial interno)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_management (
                    project_id TEXT PRIMARY KEY,
                    pipeline_status TEXT NOT NULL DEFAULT 'contactado',
                    responsable_lawyer_id INTEGER,
                    prioridad TEXT NOT NULL DEFAULT 'media',
                    proxima_accion_at TIMESTAMP,
                    ultima_interaccion_at TIMESTAMP,
                    probabilidad_cierre INTEGER,
                    notas TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_current(project_id),
                    FOREIGN KEY (responsable_lawyer_id) REFERENCES lawyers(id),
                    CHECK (pipeline_status IN ('contactado', 'en_conversaciones', 'fallido', 'completado')),
                    CHECK (prioridad IN ('baja', 'media', 'alta')),
                    CHECK (probabilidad_cierre IS NULL OR (probabilidad_cierre >= 0 AND probabilidad_cierre <= 100))
                )
            """)

            # Tabla: project_activity (timeline interna)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL DEFAULT 'nota',
                    content TEXT NOT NULL,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects_current(project_id)
                )
            """)
            
            # Índices para mejorar performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_project 
                ON project_history(project_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_timestamp 
                ON project_history(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_timestamp 
                ON runs(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_management_status
                ON project_management(pipeline_status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_management_lawyer
                ON project_management(responsable_lawyer_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_project
                ON project_activity(project_id, created_at DESC)
            """)
            
            conn.commit()
            logger.debug("Schema inicializado correctamente")
    
    def get_current_projects(self) -> list[Project]:
        """
        Obtiene todos los proyectos actuales.
        
        Returns:
            Lista de proyectos
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects_current")
            rows = cursor.fetchall()
            
            projects = []
            for row in rows:
                project = Project(
                    project_id=row['project_id'],
                    nombre_proyecto=row['nombre_proyecto'],
                    titular=row['titular'],
                    region=row['region'],
                    tipo=row['tipo'],
                    fecha_ingreso=row['fecha_ingreso'],
                    estado=row['estado'],
                    estado_normalizado=row['estado_normalizado'],
                    url_detalle=row['url_detalle'],
                    raw_row=row['raw_row'],
                    first_seen=datetime.fromisoformat(row['first_seen']) if row['first_seen'] else None,
                    last_updated=datetime.fromisoformat(row['last_updated']) if row['last_updated'] else None
                )
                projects.append(project)
            
            logger.info(f"Cargados {len(projects)} proyectos actuales de la BD")
            return projects
    
    def save_projects(
        self,
        projects: list[Project],
        validate: bool = True
    ) -> None:
        """
        Guarda proyectos actuales (reemplaza todos).
        
        Estrategia:
        1. Mantiene first_seen de proyectos existentes
        2. Actualiza last_updated
        3. Usa transacción atómica
        
        Args:
            projects: Lista de proyectos a guardar
            validate: Si True, valida antes de guardar
        
        Raises:
            ValueError: Si la validación falla
        """
        if validate:
            self._validate_projects_to_save(projects)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Obtener first_seen de proyectos existentes
                cursor.execute("SELECT project_id, first_seen FROM projects_current")
                existing_first_seen = {
                    row['project_id']: row['first_seen']
                    for row in cursor.fetchall()
                }
                
                # Limpiar tabla actual
                cursor.execute("DELETE FROM projects_current")
                
                # Insertar proyectos
                for project in projects:
                    # Preservar first_seen si ya existía
                    if project.project_id in existing_first_seen:
                        first_seen = existing_first_seen[project.project_id]
                    else:
                        first_seen = datetime.now().isoformat()
                    
                    last_updated = datetime.now().isoformat()
                    
                    cursor.execute("""
                        INSERT INTO projects_current (
                            project_id, nombre_proyecto, titular, region, tipo,
                            fecha_ingreso, estado, estado_normalizado, url_detalle,
                            raw_row, first_seen, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project.project_id,
                        project.nombre_proyecto,
                        project.titular,
                        project.region,
                        project.tipo,
                        project.fecha_ingreso,
                        project.estado,
                        project.estado_normalizado,
                        project.url_detalle,
                        project.raw_row,
                        first_seen,
                        last_updated
                    ))
                
                conn.commit()
                logger.info(f"Guardados {len(projects)} proyectos en la BD")
            
            except Exception as e:
                conn.rollback()
                logger.error(f"Error guardando proyectos: {e}")
                raise
    
    def _validate_projects_to_save(self, projects: list[Project]):
        """
        Valida que los proyectos sean razonables antes de guardar.
        
        Evita corrupción por scraping fallido.
        """
        if len(projects) == 0:
            # Verificar última corrida
            last_stats = self.get_last_run_stats()
            if last_stats and last_stats.total_projects > 50:
                raise ValueError(
                    f"Intento de guardar 0 proyectos cuando la última corrida "
                    f"tenía {last_stats.total_projects}. Posible fallo de scraping."
                )
        
        # Verificar reducción sospechosa
        last_stats = self.get_last_run_stats()
        if last_stats and last_stats.total_projects > 0:
            reduction_ratio = len(projects) / last_stats.total_projects
            if reduction_ratio < 0.5:
                logger.warning(
                    f"Reducción sospechosa de proyectos: "
                    f"{last_stats.total_projects} → {len(projects)} "
                    f"({reduction_ratio:.1%})"
                )
                # No lanzar error, solo advertir
    
    def add_history_entries(self, changes: list[ChangeEvent]) -> None:
        """
        Agrega entradas al historial de cambios.
        
        Args:
            changes: Lista de eventos de cambio
        """
        if not changes:
            return
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for change in changes:
                timestamp = change.timestamp.isoformat() if change.timestamp else datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO project_history (
                        project_id, estado_anterior, estado_nuevo,
                        estado_anterior_normalizado, estado_nuevo_normalizado,
                        timestamp, is_relevant
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    change.project_id,
                    change.estado_anterior,
                    change.estado_nuevo,
                    change.estado_anterior_normalizado,
                    change.estado_nuevo_normalizado,
                    timestamp,
                    change.is_relevant
                ))
            
            conn.commit()
            logger.info(f"Guardados {len(changes)} cambios en el historial")
    
    def save_run_stats(self, stats: RunStats) -> None:
        """
        Guarda estadísticas de una corrida.
        
        Args:
            stats: Estadísticas de la corrida
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            errors_json = json.dumps(stats.errors) if stats.errors else None
            timestamp = stats.timestamp.isoformat()
            
            cursor.execute("""
                INSERT INTO runs (
                    timestamp, duration_seconds, total_projects,
                    pages_scraped, scrape_method, errors,
                    nuevos_count, cambios_count, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                stats.duration_seconds,
                stats.total_projects,
                stats.pages_scraped,
                stats.scrape_method,
                errors_json,
                stats.nuevos_count,
                stats.cambios_count,
                stats.success
            ))
            
            conn.commit()
            logger.debug("Estadísticas de corrida guardadas")
    
    def get_last_run_stats(self) -> Optional[RunStats]:
        """
        Obtiene las estadísticas de la última corrida.
        
        Returns:
            RunStats o None si no hay corridas previas
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM runs 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            errors = json.loads(row['errors']) if row['errors'] else None
            
            return RunStats(
                timestamp=datetime.fromisoformat(row['timestamp']),
                duration_seconds=row['duration_seconds'],
                total_projects=row['total_projects'],
                pages_scraped=row['pages_scraped'],
                scrape_method=row['scrape_method'],
                nuevos_count=row['nuevos_count'],
                cambios_count=row['cambios_count'],
                success=bool(row['success']),
                errors=errors
            )

    def get_last_two_run_timestamps(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        Retorna (previous_run_ts, latest_run_ts) para calcular novedades por corrida.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp
                FROM runs
                WHERE success = 1
                ORDER BY timestamp DESC
                LIMIT 2
            """)
            rows = cursor.fetchall()
            if not rows:
                return None, None
            latest = datetime.fromisoformat(rows[0]["timestamp"])
            previous = datetime.fromisoformat(rows[1]["timestamp"]) if len(rows) > 1 else None
            return previous, latest

    @staticmethod
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _compute_is_new(self, first_seen: Optional[str]) -> bool:
        """
        Define si un proyecto es "nuevo" en la última corrida exitosa.
        - Con 2 corridas: previous < first_seen <= latest
        - Con 1 corrida: first_seen <= latest (bootstrapping inicial)
        """
        first_seen_dt = self._parse_dt(first_seen)
        if not first_seen_dt:
            return False

        previous_run_ts, latest_run_ts = self.get_last_two_run_timestamps()
        if not latest_run_ts:
            return False
        if previous_run_ts is None:
            return first_seen_dt <= latest_run_ts
        return previous_run_ts < first_seen_dt <= latest_run_ts
    
    def get_project_history(
        self,
        project_id: str,
        limit: int = 10
    ) -> list[ChangeEvent]:
        """
        Obtiene el historial de cambios de un proyecto.
        
        Args:
            project_id: ID del proyecto
            limit: Número máximo de entradas
        
        Returns:
            Lista de cambios
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.*, p.nombre_proyecto, p.region, p.url_detalle
                FROM project_history h
                LEFT JOIN projects_current p ON h.project_id = p.project_id
                WHERE h.project_id = ?
                ORDER BY h.timestamp DESC
                LIMIT ?
            """, (project_id, limit))
            rows = cursor.fetchall()
            
            changes = []
            for row in rows:
                change = ChangeEvent(
                    project_id=row['project_id'],
                    nombre_proyecto=row['nombre_proyecto'] or "",
                    estado_anterior=row['estado_anterior'],
                    estado_nuevo=row['estado_nuevo'],
                    estado_anterior_normalizado=row['estado_anterior_normalizado'],
                    estado_nuevo_normalizado=row['estado_nuevo_normalizado'],
                    region=row['region'],
                    url_detalle=row['url_detalle'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    is_relevant=bool(row['is_relevant'])
                )
                changes.append(change)
            
            return changes
    
    def save_project_details(self, details: ProjectDetails) -> None:
        """
        Guarda o actualiza los detalles de un proyecto.
        
        Args:
            details: ProjectDetails a guardar
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            scraped_at = details.scraped_at.isoformat() if details.scraped_at else datetime.now().isoformat()
            
            # Usar INSERT OR REPLACE para actualizar si ya existe
            cursor.execute("""
                INSERT OR REPLACE INTO project_details (
                    project_id, nombre_completo, tipo_proyecto,
                    monto_inversion, descripcion_completa,
                    titular_nombre, titular_domicilio, titular_ciudad,
                    titular_telefono, titular_fax, titular_email,
                    rep_legal_nombre, rep_legal_domicilio, rep_legal_telefono,
                    rep_legal_fax, rep_legal_email,
                    scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                details.project_id,
                details.nombre_completo,
                details.tipo_proyecto,
                details.monto_inversion,
                details.descripcion_completa,
                details.titular_nombre,
                details.titular_domicilio,
                details.titular_ciudad,
                details.titular_telefono,
                details.titular_fax,
                details.titular_email,
                details.rep_legal_nombre,
                details.rep_legal_domicilio,
                details.rep_legal_telefono,
                details.rep_legal_fax,
                details.rep_legal_email,
                scraped_at
            ))
            
            conn.commit()
            logger.info(f"Detalles guardados para proyecto {details.project_id}")
    
    def get_project_details(self, project_id: str) -> Optional[ProjectDetails]:
        """
        Obtiene los detalles de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            ProjectDetails o None si no existen
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM project_details
                WHERE project_id = ?
            """, (project_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return ProjectDetails(
                project_id=row['project_id'],
                nombre_completo=row['nombre_completo'],
                tipo_proyecto=row['tipo_proyecto'],
                monto_inversion=row['monto_inversion'],
                descripcion_completa=row['descripcion_completa'],
                titular_nombre=row['titular_nombre'],
                titular_domicilio=row['titular_domicilio'],
                titular_ciudad=row['titular_ciudad'],
                titular_telefono=row['titular_telefono'],
                titular_fax=row['titular_fax'],
                titular_email=row['titular_email'],
                rep_legal_nombre=row['rep_legal_nombre'],
                rep_legal_domicilio=row['rep_legal_domicilio'],
                rep_legal_telefono=row['rep_legal_telefono'],
                rep_legal_fax=row['rep_legal_fax'],
                rep_legal_email=row['rep_legal_email'],
                scraped_at=datetime.fromisoformat(row['scraped_at']) if row['scraped_at'] else None
            )

    # ─── State Machine Methods ───────────────────────────────────────────

    def _set_state(self, key: str, value: str) -> None:
        """Upsert a key-value pair in monitor_state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monitor_state (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, (key, value, datetime.now().isoformat()))
            conn.commit()

    def get_monitor_mode(self) -> str:
        """Retorna el modo actual: BOOTSTRAP, NORMAL o QUARANTINE. Default BOOTSTRAP."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM monitor_state WHERE key = 'mode'")
            row = cursor.fetchone()
            return row['value'] if row else 'BOOTSTRAP'

    def set_monitor_mode(self, mode: str) -> None:
        """Establece el modo del monitor."""
        valid = ('BOOTSTRAP', 'NORMAL', 'QUARANTINE')
        if mode not in valid:
            raise ValueError(f"Modo invalido: {mode}. Debe ser uno de {valid}")
        self._set_state('mode', mode)
        logger.info(f"Monitor mode => {mode}")

    def get_consecutive_stable_runs(self) -> int:
        """Retorna el numero de corridas estables consecutivas."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM monitor_state WHERE key = 'consecutive_stable_runs'")
            row = cursor.fetchone()
            return int(row['value']) if row else 0

    def set_consecutive_stable_runs(self, count: int) -> None:
        self._set_state('consecutive_stable_runs', str(count))

    def get_all_state(self) -> dict:
        """Retorna todas las claves de monitor_state como dict."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, updated_at FROM monitor_state")
            return {
                row['key']: {'value': row['value'], 'updated_at': row['updated_at']}
                for row in cursor.fetchall()
            }

    # ─── Staging Methods ─────────────────────────────────────────────────

    def save_projects_to_staging(self, projects: list[Project]) -> None:
        """Guarda proyectos en la tabla de staging (DELETE ALL + INSERT)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM projects_staging")
                now = datetime.now().isoformat()
                for project in projects:
                    cursor.execute("""
                        INSERT INTO projects_staging (
                            project_id, nombre_proyecto, titular, region, tipo,
                            fecha_ingreso, estado, estado_normalizado, url_detalle,
                            raw_row, first_seen, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project.project_id, project.nombre_proyecto, project.titular,
                        project.region, project.tipo, project.fecha_ingreso,
                        project.estado, project.estado_normalizado, project.url_detalle,
                        project.raw_row, now, now
                    ))
                conn.commit()
                logger.info(f"Staging: {len(projects)} proyectos guardados")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error guardando en staging: {e}")
                raise

    def promote_staging_to_current(self) -> None:
        """Promueve staging a current atomicamente. Preserva first_seen de registros existentes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Obtener first_seen de registros existentes
                cursor.execute("SELECT project_id, first_seen FROM projects_current")
                existing_first_seen = {
                    row['project_id']: row['first_seen']
                    for row in cursor.fetchall()
                }

                # Limpiar current
                cursor.execute("DELETE FROM projects_current")

                # Copiar desde staging preservando first_seen
                cursor.execute("SELECT * FROM projects_staging")
                rows = cursor.fetchall()
                for row in rows:
                    first_seen = existing_first_seen.get(row['project_id'], row['first_seen'])
                    cursor.execute("""
                        INSERT INTO projects_current (
                            project_id, nombre_proyecto, titular, region, tipo,
                            fecha_ingreso, estado, estado_normalizado, url_detalle,
                            raw_row, first_seen, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['project_id'], row['nombre_proyecto'], row['titular'],
                        row['region'], row['tipo'], row['fecha_ingreso'],
                        row['estado'], row['estado_normalizado'], row['url_detalle'],
                        row['raw_row'], first_seen, row['last_updated']
                    ))

                # Limpiar staging
                cursor.execute("DELETE FROM projects_staging")
                conn.commit()
                logger.info(f"Staging promovido a current: {len(rows)} proyectos")
            except Exception as e:
                conn.rollback()
                logger.error(f"Error promoviendo staging: {e}")
                raise

    def discard_staging(self) -> None:
        """Descarta datos de staging sin afectar current."""
        with self._get_connection() as conn:
            conn.cursor().execute("DELETE FROM projects_staging")
            conn.commit()
            logger.info("Staging descartado")

    # ─── Panel Methods ───────────────────────────────────────────────────

    def _ensure_management_record(self, project_id: str) -> None:
        """Crea fila de gestión si no existe para el proyecto."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO project_management (project_id)
                VALUES (?)
            """, (project_id,))
            conn.commit()

    def upsert_lawyer(self, nombre: str, email: Optional[str] = None, active: bool = True) -> int:
        """Crea o actualiza un abogado y retorna su ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO lawyers (nombre, email, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(nombre) DO UPDATE SET
                    email = excluded.email,
                    active = excluded.active,
                    updated_at = excluded.updated_at
            """, (nombre, email, int(active), now, now))

            cursor.execute("SELECT id FROM lawyers WHERE nombre = ?", (nombre,))
            row = cursor.fetchone()
            conn.commit()
            return int(row["id"])

    def get_lawyers(self, only_active: bool = True) -> list[dict[str, Any]]:
        """Retorna abogados para selector de responsables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if only_active:
                cursor.execute("""
                    SELECT id, nombre, email, active
                    FROM lawyers
                    WHERE active = 1
                    ORDER BY nombre ASC
                """)
            else:
                cursor.execute("""
                    SELECT id, nombre, email, active
                    FROM lawyers
                    ORDER BY nombre ASC
                """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def list_projects_panel(
        self,
        search: Optional[str] = None,
        region: Optional[str] = None,
        pipeline_status: Optional[str] = None,
        responsable_lawyer_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista proyectos combinando datos SEIA y gestión interna."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    p.project_id,
                    p.nombre_proyecto,
                    p.titular,
                    p.region,
                    p.tipo,
                    p.fecha_ingreso,
                    p.estado,
                    p.estado_normalizado,
                    p.url_detalle,
                    p.first_seen,
                    p.last_updated,
                    COALESCE(pm.pipeline_status, 'contactado') AS pipeline_status,
                    pm.responsable_lawyer_id,
                    pm.prioridad,
                    pm.proxima_accion_at,
                    pm.ultima_interaccion_at,
                    pm.probabilidad_cierre,
                    l.nombre AS responsable_lawyer_nombre
                FROM projects_current p
                LEFT JOIN project_management pm ON pm.project_id = p.project_id
                LEFT JOIN lawyers l ON l.id = pm.responsable_lawyer_id
                WHERE p.estado_normalizado = 'aprobado'
            """
            params: list[Any] = []

            if search:
                query += " AND (p.nombre_proyecto LIKE ? OR p.titular LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term])

            if region:
                query += " AND p.region = ?"
                params.append(region)

            if pipeline_status:
                query += " AND COALESCE(pm.pipeline_status, 'contactado') = ?"
                params.append(pipeline_status)

            if responsable_lawyer_id is not None:
                query += " AND pm.responsable_lawyer_id = ?"
                params.append(responsable_lawyer_id)

            query += """
                ORDER BY p.last_updated DESC, p.first_seen DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            items = []
            for row in rows:
                item = dict(row)
                item["is_new"] = self._compute_is_new(item.get("first_seen"))
                items.append(item)
            return items

    def count_projects_panel(
        self,
        search: Optional[str] = None,
        region: Optional[str] = None,
        pipeline_status: Optional[str] = None,
        responsable_lawyer_id: Optional[int] = None
    ) -> int:
        """Cuenta proyectos con mismos filtros del listado."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT COUNT(1) AS total
                FROM projects_current p
                LEFT JOIN project_management pm ON pm.project_id = p.project_id
                WHERE p.estado_normalizado = 'aprobado'
            """
            params: list[Any] = []

            if search:
                query += " AND (p.nombre_proyecto LIKE ? OR p.titular LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term])
            if region:
                query += " AND p.region = ?"
                params.append(region)
            if pipeline_status:
                query += " AND COALESCE(pm.pipeline_status, 'contactado') = ?"
                params.append(pipeline_status)
            if responsable_lawyer_id is not None:
                query += " AND pm.responsable_lawyer_id = ?"
                params.append(responsable_lawyer_id)

            cursor.execute(query, params)
            row = cursor.fetchone()
            return int(row["total"]) if row else 0

    def get_project_panel_detail(self, project_id: str) -> Optional[dict[str, Any]]:
        """Retorna detalle combinado de un proyecto para el panel."""
        self._ensure_management_record(project_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.project_id,
                    p.nombre_proyecto,
                    p.titular,
                    p.region,
                    p.tipo,
                    p.fecha_ingreso,
                    p.estado,
                    p.estado_normalizado,
                    p.url_detalle,
                    p.first_seen,
                    p.last_updated,
                    pm.pipeline_status,
                    pm.responsable_lawyer_id,
                    pm.prioridad,
                    pm.proxima_accion_at,
                    pm.ultima_interaccion_at,
                    pm.probabilidad_cierre,
                    pm.notas,
                    l.nombre AS responsable_lawyer_nombre,
                    l.email AS responsable_lawyer_email
                FROM projects_current p
                LEFT JOIN project_management pm ON pm.project_id = p.project_id
                LEFT JOIN lawyers l ON l.id = pm.responsable_lawyer_id
                WHERE p.project_id = ?
                LIMIT 1
            """, (project_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["is_new"] = self._compute_is_new(item.get("first_seen"))
            return item

    def update_project_management(
        self,
        project_id: str,
        pipeline_status: Optional[str] = None,
        responsable_lawyer_id: Optional[int] = None,
        prioridad: Optional[str] = None,
        proxima_accion_at: Optional[str] = None,
        ultima_interaccion_at: Optional[str] = None,
        probabilidad_cierre: Optional[int] = None,
        notas: Optional[str] = None
    ) -> None:
        """Actualiza campos internos de gestión comercial/legal."""
        self._ensure_management_record(project_id)

        updates: list[str] = []
        params: list[Any] = []

        allowed_status = {"contactado", "en_conversaciones", "fallido", "completado"}
        if pipeline_status is not None:
            if pipeline_status not in allowed_status:
                raise ValueError(f"pipeline_status inválido: {pipeline_status}")
            updates.append("pipeline_status = ?")
            params.append(pipeline_status)

        if responsable_lawyer_id is not None:
            updates.append("responsable_lawyer_id = ?")
            params.append(responsable_lawyer_id)

        if prioridad is not None:
            if prioridad not in {"baja", "media", "alta"}:
                raise ValueError(f"prioridad inválida: {prioridad}")
            updates.append("prioridad = ?")
            params.append(prioridad)

        if proxima_accion_at is not None:
            updates.append("proxima_accion_at = ?")
            params.append(proxima_accion_at)

        if ultima_interaccion_at is not None:
            updates.append("ultima_interaccion_at = ?")
            params.append(ultima_interaccion_at)

        if probabilidad_cierre is not None:
            if probabilidad_cierre < 0 or probabilidad_cierre > 100:
                raise ValueError("probabilidad_cierre debe estar entre 0 y 100")
            updates.append("probabilidad_cierre = ?")
            params.append(probabilidad_cierre)

        if notas is not None:
            updates.append("notas = ?")
            params.append(notas)

        if not updates:
            return

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(project_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE project_management
                SET {", ".join(updates)}
                WHERE project_id = ?
            """, params)
            conn.commit()

    def add_project_activity(
        self,
        project_id: str,
        content: str,
        activity_type: str = "nota",
        created_by: Optional[str] = None
    ) -> int:
        """Agrega una actividad/note al proyecto y retorna ID creado."""
        self._ensure_management_record(project_id)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO project_activity (project_id, activity_type, content, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, activity_type, content, created_by, datetime.now().isoformat()))
            activity_id = int(cursor.lastrowid)
            conn.commit()
            return activity_id

    def get_project_activity(self, project_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Retorna la actividad interna ordenada descendente por fecha."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, project_id, activity_type, content, created_by, created_at
                FROM project_activity
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (project_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_dashboard_kpis(self) -> dict[str, Any]:
        """Retorna métricas principales para cabecera del panel."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(1) AS total
                FROM projects_current
                WHERE estado_normalizado = 'aprobado'
            """)
            total_projects = int(cursor.fetchone()["total"])

            cursor.execute("""
                SELECT COALESCE(pm.pipeline_status, 'contactado') AS pipeline_status, COUNT(1) AS total
                FROM projects_current p
                LEFT JOIN project_management pm ON pm.project_id = p.project_id
                WHERE p.estado_normalizado = 'aprobado'
                GROUP BY COALESCE(pm.pipeline_status, 'contactado')
            """)
            by_status = {row["pipeline_status"]: int(row["total"]) for row in cursor.fetchall()}

            cursor.execute("""
                SELECT COUNT(1) AS total
                FROM projects_current p
                LEFT JOIN project_management pm ON pm.project_id = p.project_id
                WHERE p.estado_normalizado = 'aprobado'
                  AND pm.responsable_lawyer_id IS NULL
            """)
            without_lawyer = int(cursor.fetchone()["total"])

            cursor.execute("""
                SELECT COUNT(1) AS total
                FROM project_management pm
                INNER JOIN projects_current p ON p.project_id = pm.project_id
                WHERE proxima_accion_at IS NOT NULL
                  AND p.estado_normalizado = 'aprobado'
                  AND datetime(proxima_accion_at) < datetime('now')
                  AND pm.pipeline_status NOT IN ('fallido', 'completado')
            """)
            overdue_followups = int(cursor.fetchone()["total"])

            return {
                "total_projects": total_projects,
                "by_pipeline_status": by_status,
                "without_lawyer": without_lawyer,
                "overdue_followups": overdue_followups,
            }

    # ─── Validation Methods ──────────────────────────────────────────────

    def compute_stability_metrics(
        self,
        staging_projects: list[Project],
        current_projects: list[Project]
    ) -> dict:
        """
        Calcula metricas de estabilidad entre staging y current.

        Retorna dict con intersection_ratio, count_ratio, is_stable.
        """
        staging_ids = {p.project_id for p in staging_projects}
        current_ids = {p.project_id for p in current_projects}

        if not current_ids:
            return {
                'intersection_ratio': 0.0,
                'count_ratio': 0.0,
                'is_stable': False,
                'reason': 'no baseline',
                'staging_count': len(staging_ids),
                'current_count': 0,
                'intersection_count': 0,
            }

        intersection = staging_ids & current_ids
        intersection_ratio = len(intersection) / len(current_ids)
        count_ratio = len(staging_ids) / len(current_ids)

        is_stable = (
            intersection_ratio >= Config.STABILITY_INTERSECTION_MIN
            and Config.STABILITY_COUNT_RATIO_MIN <= count_ratio <= Config.STABILITY_COUNT_RATIO_MAX
        )

        return {
            'intersection_ratio': intersection_ratio,
            'count_ratio': count_ratio,
            'is_stable': is_stable,
            'staging_count': len(staging_ids),
            'current_count': len(current_ids),
            'intersection_count': len(intersection),
        }

    @staticmethod
    def validate_project_id_schema(projects: list[Project]) -> bool:
        """
        Verifica que los project_id sigan el patron esperado seia_XXXXXXXXXX.

        Retorna True si todos los IDs son validos, False si hay anomalias.
        """
        pattern = re.compile(r'^seia_\d{7,15}$')
        invalid = [p.project_id for p in projects if not pattern.match(p.project_id)]
        if invalid:
            logger.warning(
                "IDs con formato inesperado: %d de %d. Muestra: %s",
                len(invalid), len(projects), invalid[:5]
            )
            return False
        return True


def clear_database(db_path: Optional[Path] = None) -> None:
    """
    Limpia completamente la base de datos eliminando el archivo.
    
    Útil para empezar de cero con la nueva estrategia de monitoreo.
    
    Args:
        db_path: Ruta de la base de datos (usa Config si no se especifica)
    """
    if db_path is None:
        db_path = Config.get_db_path()
    
    if db_path.exists():
        db_path.unlink()
        logger.info(f"Base de datos limpiada: {db_path}")
    else:
        logger.info("Base de datos no existe, no hay nada que limpiar")

