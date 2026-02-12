"""
Motor de detección de cambios entre snapshots de proyectos.
Identifica solo proyectos nuevos aprobados.
"""

from datetime import datetime
from typing import Set

from seia_monitor.models import Project, ChangeEvent, ChangeResult
from seia_monitor.logger import get_logger

logger = get_logger("diff")


def detect_changes(
    previous: list[Project],
    current: list[Project]
) -> ChangeResult:
    """
    Detecta proyectos nuevos aprobados entre dos snapshots.
    
    Estrategia simplificada: Solo identifica proyectos con estado normalizado
    "aprobado" que no existían en el snapshot anterior. Ya no detectamos
    cambios de estado.
    
    Args:
        previous: Lista de proyectos del snapshot anterior
        current: Lista de proyectos del snapshot actual
    
    Returns:
        ChangeResult con nuevos proyectos (cambios_relevantes y todos_los_cambios vacíos)
    """
    # Crear conjuntos de IDs
    previous_ids: Set[str] = {p.project_id for p in previous}
    current_ids: Set[str] = {p.project_id for p in current}
    
    # Proyectos nuevos (están en current pero no en previous)
    new_ids = current_ids - previous_ids
    nuevos = [
        p for p in current
        if p.project_id in new_ids and p.estado_normalizado == "aprobado"
    ]
    nuevos_descartados_no_aprobados = sum(
        1
        for p in current
        if p.project_id in new_ids and p.estado_normalizado != "aprobado"
    )
    
    logger.info(f"Detectados {len(nuevos)} proyectos aprobados nuevos")
    if nuevos_descartados_no_aprobados:
        logger.warning(
            "Descartados %s proyectos nuevos no aprobados",
            nuevos_descartados_no_aprobados
        )
    
    # Proyectos eliminados (opcional, solo para logging)
    removed_ids = previous_ids - current_ids
    if removed_ids:
        logger.info(f"Proyectos ya no presentes: {len(removed_ids)}")
    
    result = ChangeResult(
        nuevos=nuevos,
        cambios_relevantes=[],  # Ya no detectamos cambios de estado
        todos_los_cambios=[]
    )
    
    logger.info(f"Resultado: Nuevos: {len(nuevos)}, Cambios relevantes: 0")
    
    return result


def deduplicate_changes(changes: list[ChangeEvent]) -> list[ChangeEvent]:
    """
    Deduplica cambios por project_id.
    
    Si hay múltiples cambios para el mismo proyecto, mantiene el último.
    
    Args:
        changes: Lista de cambios potencialmente con duplicados
    
    Returns:
        Lista sin duplicados
    """
    seen = {}
    
    for change in changes:
        # Mantener el último (más reciente)
        seen[change.project_id] = change
    
    unique = list(seen.values())
    
    if len(unique) < len(changes):
        logger.info(f"Deduplicados {len(changes) - len(unique)} cambios")
    
    return unique

