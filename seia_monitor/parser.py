"""
Parser HTML para extraer proyectos del SEIA.
Implementa fuzzy column matching para ser robusto ante cambios de estructura.
"""

from bs4 import BeautifulSoup, Tag
from typing import Optional
from datetime import datetime

from seia_monitor.models import Project
from seia_monitor.normalizer import (
    normalize_string,
    normalize_estado,
    extract_id_from_url,
    generate_project_id_hash,
    fuzzy_match_column
)
from seia_monitor.logger import get_logger
from seia_monitor.config import Config

logger = get_logger("parser")


class ColumnMapper:
    """Mapea columnas de la tabla HTML por contenido del header"""
    
    def __init__(self):
        self.nombre_idx: Optional[int] = None
        self.titular_idx: Optional[int] = None
        self.region_idx: Optional[int] = None
        self.tipo_idx: Optional[int] = None
        self.fecha_idx: Optional[int] = None
        self.estado_idx: Optional[int] = None
        
    def map_headers(self, headers: list[str]) -> bool:
        """
        Mapea headers de columnas usando fuzzy matching.
        
        Args:
            headers: Lista de textos de headers
        
        Returns:
            True si se encontraron las columnas mínimas requeridas
        """
        for idx, header in enumerate(headers):
            header_norm = normalize_string(header)
            
            # Estado (PRIMERO para evitar ambigüedades con "proyecto")
            if "estado" in header_norm and self.estado_idx is None:
                self.estado_idx = idx
                logger.debug(f"Columna 'estado' mapeada a índice {idx}")
            
            # Nombre del proyecto
            elif fuzzy_match_column(header, ["nombre"]) and self.nombre_idx is None:
                self.nombre_idx = idx
                logger.debug(f"Columna 'nombre' mapeada a índice {idx}")
            
            # Titular
            elif fuzzy_match_column(header, ["titular", "empresa", "responsable"]) and self.titular_idx is None:
                self.titular_idx = idx
                logger.debug(f"Columna 'titular' mapeada a índice {idx}")
            
            # Región
            elif fuzzy_match_column(header, ["region", "zona"]) and self.region_idx is None:
                self.region_idx = idx
                logger.debug(f"Columna 'region' mapeada a índice {idx}")
            
            # Tipo/Tipología
            elif fuzzy_match_column(header, ["tipo", "tipologia", "categoria"]) and self.tipo_idx is None:
                self.tipo_idx = idx
                logger.debug(f"Columna 'tipo' mapeada a índice {idx}")
            
            # Fecha de ingreso
            elif fuzzy_match_column(header, ["fecha", "ingreso", "presentacion"]) and self.fecha_idx is None:
                self.fecha_idx = idx
                logger.debug(f"Columna 'fecha' mapeada a índice {idx}")
        
        # Validar que tenemos las columnas mínimas
        if self.nombre_idx is None:
            logger.warning("No se encontró columna 'nombre'")
            return False
        
        if self.estado_idx is None:
            logger.warning("No se encontró columna 'estado'")
            return False
        
        return True
    
    def get_value(self, cells: list, idx: Optional[int]) -> Optional[str]:
        """Obtiene el valor de una celda de forma segura"""
        if idx is None or idx >= len(cells):
            return None
        
        cell = cells[idx]
        if isinstance(cell, Tag):
            # Extraer texto, eliminando tags HTML
            text = cell.get_text(separator=" ", strip=True)
            return text if text else None
        elif isinstance(cell, str):
            return cell.strip() if cell.strip() else None
        
        return None


def parse_projects_from_html(html: str) -> list[Project]:
    """
    Parsea proyectos desde HTML usando BeautifulSoup.
    
    Args:
        html: HTML de la página de resultados
    
    Returns:
        Lista de proyectos parseados
    """
    soup = BeautifulSoup(html, 'lxml')
    projects = []
    
    # Intentar encontrar la tabla de resultados
    # Probar diferentes selectores (en orden de prioridad)
    table = None
    possible_selectors = [
        'table#datatable-proyectos',  # ID específico del SEIA
        'table.tabla_resultados',
        'table#resultados',
        'table[class*="result"]',
        'table[id*="result"]',
        'div.resultados table',
    ]
    
    for selector in possible_selectors:
        table = soup.select_one(selector)
        if table:
            logger.debug(f"Tabla encontrada con selector: {selector}")
            break
    
    # Si no encontró con selectores, buscar la tabla con más datos en tbody
    if not table:
        logger.debug("Buscando tabla con tbody con datos...")
        all_tables = soup.find_all('table')
        for t in all_tables:
            tbody = t.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                if len(rows) > 0:
                    table = t
                    logger.debug(f"Tabla encontrada con {len(rows)} filas en tbody")
                    break
    
    if not table:
        logger.error("No se encontró tabla de resultados en el HTML")
        return projects
    
    # Extraer headers
    headers = []
    header_row = table.find('thead')
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    else:
        # Si no hay thead, usar primera fila
        first_row = table.find('tr')
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
    
    if not headers:
        logger.error("No se encontraron headers en la tabla")
        return projects
    
    logger.info(f"Headers encontrados: {headers}")
    
    # Mapear columnas
    mapper = ColumnMapper()
    if not mapper.map_headers(headers):
        logger.error("No se pudieron mapear las columnas mínimas requeridas")
        return projects
    
    # Extraer filas de datos (tbody o todas las tr excepto la primera)
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        # Saltar la fila de headers
        rows = table.find_all('tr')[1:]
    
    logger.info(f"Procesando {len(rows)} filas")
    
    # Procesar cada fila
    for row_idx, row in enumerate(rows):
        try:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 2:  # Fila vacía o de separación
                continue
            
            # Extraer valores
            nombre = mapper.get_value(cells, mapper.nombre_idx)
            titular = mapper.get_value(cells, mapper.titular_idx)
            region = mapper.get_value(cells, mapper.region_idx)
            tipo = mapper.get_value(cells, mapper.tipo_idx)
            fecha_ingreso = mapper.get_value(cells, mapper.fecha_idx)
            estado = mapper.get_value(cells, mapper.estado_idx)
            
            # Validar que tenemos datos mínimos
            if not nombre or not estado:
                logger.warning(f"Fila {row_idx}: falta nombre o estado, omitiendo")
                continue
            
            # Extraer URL de detalle (buscar en la celda del nombre)
            url_detalle = None
            if mapper.nombre_idx is not None and mapper.nombre_idx < len(cells):
                nombre_cell = cells[mapper.nombre_idx]
                link = nombre_cell.find('a')
                if link and link.get('href'):
                    url_detalle = link['href']
                    # Si es relativa, completar con base URL
                    if url_detalle and not url_detalle.startswith('http'):
                        # Construir URL completa con el dominio del SEIA
                        # Base SEIA: https://seia.sea.gob.cl
                        if url_detalle.startswith('/'):
                            url_detalle = f"https://seia.sea.gob.cl{url_detalle}"
                        else:
                            # Si no empieza con /, usar la ruta relativa del base URL
                            base_url = Config.SEIA_BASE_URL.rsplit('/', 1)[0]
                            url_detalle = f"{base_url}/{url_detalle}"
                    
                    logger.debug(f"URL detalle extraída: {url_detalle[:80]}")
            
            # Determinar project_id
            project_id = None
            if url_detalle:
                project_id = extract_id_from_url(url_detalle)
            
            if not project_id:
                # Generar hash como fallback
                project_id = generate_project_id_hash(
                    nombre=nombre,
                    region=region,
                    titular=titular,
                    fecha_ingreso=fecha_ingreso
                )
                logger.debug(f"ID generado por hash para: {nombre[:50]}")
            
            # Normalizar estado
            estado_normalizado = normalize_estado(estado)
            
            # Crear proyecto
            project = Project(
                project_id=project_id,
                nombre_proyecto=nombre,
                titular=titular,
                region=region,
                tipo=tipo,
                fecha_ingreso=fecha_ingreso,
                estado=estado,
                estado_normalizado=estado_normalizado,
                url_detalle=url_detalle,
                raw_row=str(row)[:500],  # Guardar primeros 500 chars para debug
                last_updated=datetime.now()
            )
            
            projects.append(project)
            
            # Límite de seguridad
            if len(projects) >= Config.MAX_PROJECTS_PER_RUN:
                logger.warning(f"Alcanzado límite de {Config.MAX_PROJECTS_PER_RUN} proyectos")
                break
        
        except Exception as e:
            logger.error(f"Error procesando fila {row_idx}: {e}")
            continue
    
    logger.info(f"Parseados {len(projects)} proyectos del HTML")
    return projects


def validate_html_has_results(html: str) -> bool:
    """
    Valida que el HTML contenga tabla de resultados.
    
    Args:
        html: HTML a validar
    
    Returns:
        True si se detecta tabla de resultados
    """
    if not html or len(html) < 100:
        return False
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Buscar tabla específica del SEIA
    table = soup.select_one('table#datatable-proyectos')
    
    # Si no la encuentra, buscar cualquier tabla con tbody con datos
    if not table:
        all_tables = soup.find_all('table')
        for t in all_tables:
            tbody = t.find('tbody')
            if tbody:
                data_rows = tbody.find_all('tr')
                if len(data_rows) >= 1:
                    return True
        return False
    
    # Verificar que tenga filas en tbody
    tbody = table.find('tbody')
    if tbody:
        data_rows = tbody.find_all('tr')
        if len(data_rows) >= 1:
            return True
    
    return False


def deduplicate_projects(projects: list[Project]) -> list[Project]:
    """
    Deduplica proyectos por project_id.
    
    Args:
        projects: Lista de proyectos potencialmente con duplicados
    
    Returns:
        Lista sin duplicados (mantiene el primero)
    """
    seen = set()
    unique = []
    duplicates = 0
    
    for project in projects:
        if project.project_id not in seen:
            seen.add(project.project_id)
            unique.append(project)
        else:
            duplicates += 1
            logger.warning(f"Duplicado encontrado: {project.nombre_proyecto} ({project.project_id})")
    
    if duplicates > 0:
        logger.info(f"Eliminados {duplicates} proyectos duplicados")
    
    return unique

