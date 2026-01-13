"""
Capa de persistencia con SQLite.
Maneja proyectos actuales, historial de cambios y estadísticas de corridas.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

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

