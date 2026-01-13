"""
Modelos de datos (dataclasses) para el sistema SEIA Monitor.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """Representa un proyecto del SEIA"""
    project_id: str
    nombre_proyecto: str
    titular: Optional[str] = None
    region: Optional[str] = None
    tipo: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    estado: str = ""
    estado_normalizado: str = ""
    url_detalle: Optional[str] = None
    raw_row: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def __hash__(self):
        return hash(self.project_id)
    
    def __eq__(self, other):
        if not isinstance(other, Project):
            return False
        return self.project_id == other.project_id


@dataclass
class ProjectDetails:
    """Información detallada de un proyecto aprobado"""
    project_id: str
    nombre_completo: str
    tipo_proyecto: str
    monto_inversion: Optional[str] = None  # Ej: "19,8000 Millones de Dólares"
    descripcion_completa: Optional[str] = None
    
    # Titular
    titular_nombre: Optional[str] = None
    titular_domicilio: Optional[str] = None
    titular_ciudad: Optional[str] = None
    titular_telefono: Optional[str] = None
    titular_fax: Optional[str] = None
    titular_email: Optional[str] = None
    
    # Representante Legal
    rep_legal_nombre: Optional[str] = None
    rep_legal_domicilio: Optional[str] = None
    rep_legal_telefono: Optional[str] = None
    rep_legal_fax: Optional[str] = None
    rep_legal_email: Optional[str] = None
    
    scraped_at: Optional[datetime] = None


@dataclass
class ChangeEvent:
    """Representa un cambio de estado de un proyecto"""
    project_id: str
    nombre_proyecto: str
    estado_anterior: str
    estado_nuevo: str
    estado_anterior_normalizado: str
    estado_nuevo_normalizado: str
    region: Optional[str] = None
    url_detalle: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_relevant: bool = False
    details: Optional['ProjectDetails'] = None  # Detalles adicionales si están disponibles
    
    def __str__(self):
        return f"{self.nombre_proyecto}: {self.estado_anterior} → {self.estado_nuevo}"


@dataclass
class ScrapeMeta:
    """Metadata de una operación de scraping"""
    method: str  # 'requests' o 'playwright'
    pages_scraped: int
    total_projects: int
    duration_seconds: float
    errors: list[str] = field(default_factory=list)
    success: bool = True


@dataclass
class RunStats:
    """Estadísticas de una corrida del monitor"""
    timestamp: datetime
    duration_seconds: float
    total_projects: int
    pages_scraped: int
    scrape_method: str
    nuevos_count: int
    cambios_count: int
    success: bool
    errors: Optional[str] = None


@dataclass
class ChangeResult:
    """Resultado de la detección de cambios"""
    nuevos: list[Project] = field(default_factory=list)
    cambios_relevantes: list[ChangeEvent] = field(default_factory=list)
    todos_los_cambios: list[ChangeEvent] = field(default_factory=list)
    
    def has_changes(self) -> bool:
        """Retorna True si hay cambios relevantes o nuevos proyectos"""
        return len(self.nuevos) > 0 or len(self.cambios_relevantes) > 0
    
    def __str__(self):
        return f"Nuevos: {len(self.nuevos)}, Cambios relevantes: {len(self.cambios_relevantes)}"

