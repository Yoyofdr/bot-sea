"""
Motor de detección de cambios entre snapshots de proyectos.
Identifica proyectos nuevos y cambios relevantes de estado.
"""

from datetime import datetime
from typing import Set

from seia_monitor.models import Project, ChangeEvent, ChangeResult
from seia_monitor.logger import get_logger

logger = get_logger("diff")


# Transiciones relevantes que se notificarán
# SOLO detectamos cuando un proyecto pasa de "En Calificación" a "Aprobado"
RELEVANT_TRANSITIONS = [
    # (estado_anterior_normalizado, estado_nuevo_normalizado)
    ("en_calificacion_activo", "aprobado"),
]


def is_relevant_transition(
    estado_anterior_norm: str,
    estado_nuevo_norm: str
) -> bool:
    """
    Determina si una transición de estado es relevante para notificación.
    
    Actualmente SOLO detecta: "En Calificación (Activo)" → "Aprobado"
    
    Args:
        estado_anterior_norm: Estado anterior normalizado
        estado_nuevo_norm: Estado nuevo normalizado
    
    Returns:
        True si la transición es relevante
    """
    return (estado_anterior_norm, estado_nuevo_norm) in RELEVANT_TRANSITIONS


def detect_changes(
    previous: list[Project],
    current: list[Project]
) -> ChangeResult:
    """
    Detecta cambios entre dos snapshots de proyectos.
    
    Identifica:
    - Proyectos nuevos (no existían en previous)
    - Cambios de estado (mismo project_id, diferente estado)
    - Filtra solo transiciones relevantes para notificación
    
    Args:
        previous: Lista de proyectos del snapshot anterior
        current: Lista de proyectos del snapshot actual
    
    Returns:
        ChangeResult con nuevos, cambios relevantes y todos los cambios
    """
    timestamp = datetime.now()
    
    # Crear índices por project_id
    previous_dict = {p.project_id: p for p in previous}
    current_dict = {p.project_id: p for p in current}
    
    # IDs
    previous_ids: Set[str] = set(previous_dict.keys())
    current_ids: Set[str] = set(current_dict.keys())
    
    # 1. Proyectos nuevos (están en current pero no en previous)
    new_ids = current_ids - previous_ids
    nuevos = [current_dict[pid] for pid in new_ids]
    
    logger.info(f"Detectados {len(nuevos)} proyectos nuevos")
    
    # 2. Proyectos que continúan (en ambos)
    continuing_ids = current_ids & previous_ids
    
    # 3. Detectar cambios de estado
    todos_los_cambios = []
    cambios_relevantes = []
    
    for pid in continuing_ids:
        prev_project = previous_dict[pid]
        curr_project = current_dict[pid]
        
        # Comparar estados normalizados
        if prev_project.estado_normalizado != curr_project.estado_normalizado:
            # Crear evento de cambio
            change = ChangeEvent(
                project_id=pid,
                nombre_proyecto=curr_project.nombre_proyecto,
                estado_anterior=prev_project.estado,
                estado_nuevo=curr_project.estado,
                estado_anterior_normalizado=prev_project.estado_normalizado,
                estado_nuevo_normalizado=curr_project.estado_normalizado,
                region=curr_project.region,
                url_detalle=curr_project.url_detalle,
                timestamp=timestamp,
                is_relevant=False  # Se determinará abajo
            )
            
            # Verificar si es relevante
            if is_relevant_transition(
                prev_project.estado_normalizado,
                curr_project.estado_normalizado
            ):
                change.is_relevant = True
                cambios_relevantes.append(change)
                logger.info(
                    f"Cambio relevante: {curr_project.nombre_proyecto[:50]} - "
                    f"{prev_project.estado_normalizado} → {curr_project.estado_normalizado}"
                )
            
            todos_los_cambios.append(change)
    
    logger.info(
        f"Detectados {len(todos_los_cambios)} cambios de estado "
        f"({len(cambios_relevantes)} relevantes)"
    )
    
    # 4. Proyectos eliminados (opcional, no se usan por ahora)
    removed_ids = previous_ids - current_ids
    if removed_ids:
        logger.info(f"Proyectos ya no presentes: {len(removed_ids)}")
    
    result = ChangeResult(
        nuevos=nuevos,
        cambios_relevantes=cambios_relevantes,
        todos_los_cambios=todos_los_cambios
    )
    
    logger.info(f"Resultado: {result}")
    
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

