"""
Orquestador principal del sistema de monitoreo SEIA.
Coordina scraping, detección de cambios, persistencia y notificaciones.
"""

import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import RunStats, ChangeResult
from seia_monitor.scraper import scrape_seia
from seia_monitor.storage import SEIAStorage
from seia_monitor.diff import detect_changes
from seia_monitor.notifier_email import send_email_notification
from seia_monitor.scraper_detail import scrape_project_details

logger = get_logger("runner")


class MonitoringRunner:
    """Orquestador de corridas de monitoreo"""
    
    def __init__(self, config: Config):
        self.config = config
        self.storage = SEIAStorage()
        self.debug_dir = config.BASE_DIR / "data" / "debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_debug_html(self, html: str, prefix: str = "error"):
        """Guarda HTML para debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = self.debug_dir / f"{prefix}_{timestamp}.html"
        
        try:
            debug_path.write_text(html, encoding='utf-8')
            logger.info(f"HTML de debug guardado: {debug_path}")
        except Exception as e:
            logger.error(f"Error guardando HTML de debug: {e}")
    
    def run(self, dry_run: bool = False) -> RunStats:
        """
        Ejecuta una corrida completa del monitoreo.
        
        Pasos:
        1. Scraping (con fallback automático)
        2. Cargar snapshot anterior
        3. Detectar cambios
        4. Guardar a BD (si no dry_run y exitoso)
        5. Enviar notificación por Email (si hay cambios)
        6. Log de estadísticas
        
        Args:
            dry_run: Si True, no guarda cambios ni envía notificaciones
        
        Returns:
            RunStats con el resultado de la corrida
        """
        start_time = time.time()
        success = False
        errors = []
        
        logger.info("=" * 60)
        logger.info(f"Iniciando corrida de monitoreo SEIA")
        logger.info(f"Modo: {'DRY RUN' if dry_run else 'PRODUCCIÓN'}")
        logger.info(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        try:
            # Asegurar directorios
            Config.ensure_directories()
            
            # 1. SCRAPING
            logger.info("Paso 1: Scraping de proyectos")
            try:
                projects, scrape_meta = scrape_seia(self.config)
                
                logger.info(
                    f"✓ Scraping completado: {scrape_meta.total_projects} proyectos, "
                    f"{scrape_meta.pages_scraped} páginas, "
                    f"método: {scrape_meta.method}, "
                    f"duración: {scrape_meta.duration_seconds:.1f}s"
                )
                
                if scrape_meta.errors:
                    errors.extend(scrape_meta.errors)
                
                if not scrape_meta.success or len(projects) == 0:
                    raise Exception(
                        f"Scraping no exitoso o sin resultados: "
                        f"{len(projects)} proyectos"
                    )
            
            except Exception as e:
                error_msg = f"Error en scraping: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                raise
            
            # 2. CARGAR SNAPSHOT ANTERIOR
            logger.info("Paso 2: Cargando snapshot anterior")
            try:
                previous_projects = self.storage.get_current_projects()
                logger.info(f"✓ Snapshot anterior: {len(previous_projects)} proyectos")
            except Exception as e:
                logger.warning(f"No se pudo cargar snapshot anterior: {e}")
                previous_projects = []
            
            # 3. DETECTAR CAMBIOS
            logger.info("Paso 3: Detectando cambios")
            try:
                changes = detect_changes(previous_projects, projects)
                logger.info(
                    f"✓ Cambios detectados: {len(changes.nuevos)} nuevos, "
                    f"{len(changes.cambios_relevantes)} cambios relevantes, "
                    f"{len(changes.todos_los_cambios)} cambios totales"
                )
            except Exception as e:
                error_msg = f"Error detectando cambios: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                # Continuar con changes vacío
                changes = ChangeResult()
            
            # 3.5. EXTRAER DETALLES DE PROYECTOS APROBADOS
            if changes.cambios_relevantes:
                logger.info("Paso 3.5: Extrayendo detalles de proyectos aprobados")
                detalles_extraidos = 0
                
                for change in changes.cambios_relevantes:
                    # Solo extraer detalles si el proyecto pasó a "aprobado"
                    if change.estado_nuevo_normalizado == "aprobado" and change.url_detalle:
                        try:
                            logger.info(f"  Extrayendo detalles: {change.nombre_proyecto[:50]}...")
                            details = scrape_project_details(change.url_detalle)
                            change.details = details
                            detalles_extraidos += 1
                            logger.info(f"  ✓ Detalles extraídos: {change.nombre_proyecto[:50]}")
                            
                            # Pequeño delay para no saturar el servidor
                            time.sleep(2)
                        
                        except Exception as e:
                            logger.error(
                                f"  ✗ Error extrayendo detalles de {change.nombre_proyecto[:50]}: {e}"
                            )
                            # Continuar con el resto
                
                logger.info(f"✓ Detalles extraídos de {detalles_extraidos}/{len(changes.cambios_relevantes)} proyectos")
            
            # 4. GUARDAR A BASE DE DATOS
            if not dry_run:
                logger.info("Paso 4: Guardando a base de datos")
                try:
                    # Guardar proyectos actuales
                    self.storage.save_projects(projects, validate=True)
                    
                    # Guardar historial de cambios
                    if changes.todos_los_cambios:
                        self.storage.add_history_entries(changes.todos_los_cambios)
                    
                    # Guardar detalles de proyectos aprobados
                    detalles_guardados = 0
                    for change in changes.cambios_relevantes:
                        if change.details:
                            try:
                                self.storage.save_project_details(change.details)
                                detalles_guardados += 1
                            except Exception as e:
                                logger.error(f"Error guardando detalles de {change.project_id}: {e}")
                    
                    if detalles_guardados > 0:
                        logger.info(f"✓ Guardados detalles de {detalles_guardados} proyectos")
                    
                    logger.info("✓ Datos guardados exitosamente")
                except Exception as e:
                    error_msg = f"Error guardando a BD: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # No lanzar error, continuar para intentar notificar
            else:
                logger.info("Paso 4: Omitido (dry run)")
            
            # 5. NOTIFICAR POR EMAIL
            if not dry_run and self.config.EMAIL_ENABLED and changes.nuevos:
                logger.info("Paso 5: Enviando notificación por Email")
                try:
                    logger.info(f"Enviando {len(changes.nuevos)} proyecto(s) nuevo(s) por email")
                    
                    notification_sent = send_email_notification(
                        changes.nuevos,
                        self.config
                    )
                    
                    if notification_sent:
                        logger.info("✓ Notificación enviada por email")
                    else:
                        logger.warning("⚠ No se pudo enviar notificación por email")
                
                except Exception as e:
                    error_msg = f"Error enviando notificación: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    # No fallar la corrida por esto
            else:
                if dry_run:
                    logger.info("Paso 5: Omitido (dry run)")
                elif not self.config.EMAIL_ENABLED:
                    logger.info("Paso 5: Omitido (no hay email configurado)")
                else:
                    logger.info("Paso 5: Omitido (no hay proyectos nuevos)")
            
            # Corrida exitosa
            success = True
            duration = time.time() - start_time
            
            logger.info("=" * 60)
            logger.info(f"✓ Corrida completada exitosamente en {duration:.1f}s")
            logger.info("=" * 60)
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 60)
            logger.error(f"✗ Corrida FALLIDA: {e}")
            logger.error("=" * 60)
            
            if 'scrape_meta' not in locals():
                # Scraping falló completamente
                scrape_meta = type('obj', (object,), {
                    'method': 'unknown',
                    'pages_scraped': 0,
                    'total_projects': 0
                })
                projects = []
                changes = ChangeResult()
        
        # Crear estadísticas de corrida
        duration = time.time() - start_time
        
        run_stats = RunStats(
            timestamp=datetime.now(),
            duration_seconds=duration,
            total_projects=len(projects) if 'projects' in locals() else 0,
            pages_scraped=scrape_meta.pages_scraped if 'scrape_meta' in locals() else 0,
            scrape_method=scrape_meta.method if 'scrape_meta' in locals() else 'unknown',
            nuevos_count=len(changes.nuevos) if 'changes' in locals() else 0,
            cambios_count=len(changes.cambios_relevantes) if 'changes' in locals() else 0,
            success=success,
            errors="; ".join(errors) if errors else None
        )
        
        # Guardar estadísticas de corrida (incluso si falló)
        if not dry_run:
            try:
                self.storage.save_run_stats(run_stats)
            except Exception as e:
                logger.error(f"Error guardando estadísticas: {e}")
        
        return run_stats


def run_monitoring(
    config: Optional[Config] = None,
    dry_run: bool = False
) -> RunStats:
    """
    Función de entrada para ejecutar una corrida de monitoreo.
    
    Args:
        config: Configuración (usa Config global si no se especifica)
        dry_run: Si True, no guarda cambios ni envía notificaciones
    
    Returns:
        RunStats con el resultado
    """
    if config is None:
        config = Config()
    
    runner = MonitoringRunner(config)
    return runner.run(dry_run=dry_run)

