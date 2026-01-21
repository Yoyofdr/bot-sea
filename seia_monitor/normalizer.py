"""
Normalización de strings y estados para comparación robusta.
"""

import hashlib
import re
import unicodedata
from typing import Optional


def normalize_string(text: Optional[str]) -> str:
    """
    Normaliza un string para comparación robusta.
    
    - Elimina espacios al inicio/final
    - Colapsa múltiples espacios en uno
    - Convierte a minúsculas
    - Normaliza tildes (NFD)
    - Elimina caracteres invisibles
    
    Args:
        text: String a normalizar
    
    Returns:
        String normalizado
    """
    if not text:
        return ""
    
    # Trim y colapsar espacios
    normalized = " ".join(text.strip().split())
    
    # Minúsculas
    normalized = normalized.lower()
    
    # Normalizar unicode (NFD - descomponer tildes)
    normalized = unicodedata.normalize('NFD', normalized)
    
    # Eliminar caracteres de combinación (tildes separadas)
    normalized = ''.join(
        char for char in normalized
        if unicodedata.category(char) != 'Mn'
    )
    
    # Eliminar caracteres invisibles y de control
    normalized = ''.join(
        char for char in normalized
        if unicodedata.category(char)[0] != 'C'
    )
    
    return normalized


def normalize_estado(estado: Optional[str]) -> str:
    """
    Normaliza un estado del SEIA a un valor estándar.
    
    Estados reconocidos:
    - en_admision
    - en_calificacion_activo
    - aprobado
    - rechazado
    - desistido
    - otro (catch-all)
    
    Args:
        estado: Estado original del proyecto
    
    Returns:
        Estado normalizado
    """
    if not estado:
        return "otro"
    
    # Normalizar el string primero
    estado_norm = normalize_string(estado)
    
    # Patrones de estados conocidos
    if "admision" in estado_norm:
        return "en_admision"
    
    if "calificacion" in estado_norm:
        # Distinguir activo vs pausado/suspendido
        if "activo" in estado_norm or "en calificacion" == estado_norm:
            return "en_calificacion_activo"
        else:
            return "en_calificacion_suspendido"
    
    if "aprobado" in estado_norm or "favorable" in estado_norm:
        return "aprobado"
    
    if "rechazado" in estado_norm or "desfavorable" in estado_norm:
        return "rechazado"
    
    if "desistido" in estado_norm or "desiste" in estado_norm:
        return "desistido"
    
    if "no admitido" in estado_norm:
        return "no_admitido"
    
    # Otros estados
    return "otro"


def generate_project_id_hash(
    nombre: str,
    region: Optional[str] = None,
    titular: Optional[str] = None,
    fecha_ingreso: Optional[str] = None
) -> str:
    """
    Genera un ID hash estable para un proyecto basado en sus campos clave.
    
    Se usa como fallback cuando no hay ID oficial disponible.
    
    Args:
        nombre: Nombre del proyecto (normalizado)
        region: Región del proyecto
        titular: Titular del proyecto
        fecha_ingreso: Fecha de ingreso
    
    Returns:
        Hash SHA256 (primeros 16 caracteres)
    """
    # Normalizar todos los campos
    nombre_norm = normalize_string(nombre)
    region_norm = normalize_string(region) if region else ""
    titular_norm = normalize_string(titular) if titular else ""
    fecha_norm = normalize_string(fecha_ingreso) if fecha_ingreso else ""
    
    # Concatenar con separador
    combined = f"{nombre_norm}|{region_norm}|{titular_norm}|{fecha_norm}"
    
    # Generar hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Retornar primeros 16 caracteres con prefijo
    return f"hash_{hash_hex[:16]}"


def extract_id_from_url(url: Optional[str]) -> Optional[str]:
    """
    Extrae el ID del proyecto desde una URL de detalle.
    
    Patrones soportados:
    - id_expediente=12345
    - proyecto/12345
    - expediente/12345
    
    Args:
        url: URL de detalle del proyecto
    
    Returns:
        ID extraído o None si no se encuentra
    """
    if not url:
        return None
    
    # Intentar diferentes patrones
    patterns = [
        r'id_expediente[=:](\d+)',
        r'proyecto[/:](\d+)',
        r'expediente[/:](\d+)',
        r'id[=:](\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return f"seia_{match.group(1)}"
    
    return None


def fuzzy_match_column(header: str, keywords: list[str]) -> bool:
    """
    Hace matching difuso de un header de columna contra keywords.
    
    Args:
        header: Texto del header de la columna
        keywords: Lista de keywords a buscar
    
    Returns:
        True si algún keyword coincide
    """
    header_norm = normalize_string(header)
    
    for keyword in keywords:
        keyword_norm = normalize_string(keyword)
        if keyword_norm in header_norm:
            return True
    
    return False







