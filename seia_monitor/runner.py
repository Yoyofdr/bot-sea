"""
Orquestador principal del sistema de monitoreo SEIA.
Coordina scraping, deteccion de cambios, persistencia y notificaciones.
Implementa maquina de estados: BOOTSTRAP -> NORMAL, con fallback a QUARANTINE.
"""

import os
import time
from datetime import datetime
from typing import Optional

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import RunStats, ChangeResult
from seia_monitor.scraper import scrape_seia
from seia_monitor.storage import SEIAStorage
from seia_monitor.diff import detect_changes
from seia_monitor.notifier_email import (
    send_email_notification,
    send_anomaly_alert_notification,
    send_quarantine_alert_notification
)
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

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _extract_details_for_changes(self, changes: ChangeResult):
        """Extrae detalles de proyectos nuevos/cambios relevantes."""
        skip_details = os.getenv("SKIP_DETAILS", "false").lower() == "true"

        if changes.cambios_relevantes and not skip_details:
            logger.info("Extrayendo detalles de proyectos con cambios relevantes")
            detalles_extraidos = 0
            for change in changes.cambios_relevantes:
                if change.estado_nuevo_normalizado == "aprobado" and change.url_detalle:
                    try:
                        logger.info(f"  Extrayendo detalles: {change.nombre_proyecto[:50]}...")
                        details = scrape_project_details(change.url_detalle)
                        change.details = details
                        detalles_extraidos += 1
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"  Error extrayendo detalles de {change.nombre_proyecto[:50]}: {e}")
            logger.info(f"Detalles extraidos de {detalles_extraidos}/{len(changes.cambios_relevantes)} cambios")

        if changes.nuevos and not skip_details:
            logger.info("Extrayendo detalles de proyectos nuevos")
            detalles_extraidos = 0
            for project in changes.nuevos:
                if project.url_detalle:
                    try:
                        logger.info(f"  Extrayendo detalles: {project.nombre_proyecto[:50]}...")
                        details = scrape_project_details(project.url_detalle)
                        project.details = details
                        detalles_extraidos += 1
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"  Error extrayendo detalles de '{project.nombre_proyecto[:30]}...': {e}")
                        project.details = None
            logger.info(f"Detalles extraidos de {detalles_extraidos}/{len(changes.nuevos)} nuevos")

    def _save_details(self, changes: ChangeResult):
        """Persiste detalles extraidos a BD."""
        detalles_guardados = 0
        for change in changes.cambios_relevantes:
            if change.details:
                try:
                    self.storage.save_project_details(change.details)
                    detalles_guardados += 1
                except Exception as e:
                    logger.error(f"Error guardando detalles de {change.project_id}: {e}")
        for project in changes.nuevos:
            if project.details:
                try:
                    self.storage.save_project_details(project.details)
                    detalles_guardados += 1
                except Exception as e:
                    logger.error(f"Error guardando detalles de {project.project_id}: {e}")
        if detalles_guardados > 0:
            logger.info(f"Guardados detalles de {detalles_guardados} proyectos")

    def _build_stats(self, success, projects, scrape_meta, changes, errors, start_time):
        """Construye RunStats."""
        duration = time.time() - start_time
        return RunStats(
            timestamp=datetime.now(),
            duration_seconds=duration,
            total_projects=len(projects) if projects else 0,
            pages_scraped=scrape_meta.pages_scraped if scrape_meta else 0,
            scrape_method=scrape_meta.method if scrape_meta else 'unknown',
            nuevos_count=len(changes.nuevos) if changes else 0,
            cambios_count=len(changes.cambios_relevantes) if changes else 0,
            success=success,
            errors="; ".join(errors) if errors else None
        )

    # ─── Mode Handlers ───────────────────────────────────────────────────

    def _handle_bootstrap(self, projects, previous_projects, stability,
                          scrape_meta, dry_run, id_schema_ok, approved_ratio,
                          errors, start_time):
        """BOOTSTRAP: Establece baseline validada sin notificaciones."""
        logger.info("=== MODO BOOTSTRAP ===")

        # Validar ratio de aprobados
        if approved_ratio < self.config.APPROVED_MIN_RATIO:
            reason = (
                f"Ratio de aprobados {approved_ratio:.1%} < umbral "
                f"{self.config.APPROVED_MIN_RATIO:.1%}"
            )
            logger.error(f"Bootstrap rechazado: {reason}")
            self.storage.discard_staging()
            self.storage.set_monitor_mode('QUARANTINE')
            if self.config.EMAIL_ENABLED and not dry_run:
                send_quarantine_alert_notification(
                    reason=reason,
                    total_scraped=len(projects),
                    stability_metrics=stability,
                    config=self.config
                )
            errors.append(reason)
            stats = self._build_stats(False, projects, scrape_meta, ChangeResult(), errors, start_time)
            if not dry_run:
                self.storage.save_run_stats(stats)
            return stats

        # Validar esquema de IDs
        if not id_schema_ok:
            reason = "Esquema de project_id inconsistente"
            logger.error(f"Bootstrap rechazado: {reason}")
            self.storage.discard_staging()
            self.storage.set_monitor_mode('QUARANTINE')
            if self.config.EMAIL_ENABLED and not dry_run:
                send_quarantine_alert_notification(
                    reason=reason,
                    total_scraped=len(projects),
                    stability_metrics=stability,
                    config=self.config
                )
            errors.append(reason)
            stats = self._build_stats(False, projects, scrape_meta, ChangeResult(), errors, start_time)
            if not dry_run:
                self.storage.save_run_stats(stats)
            return stats

        if not dry_run:
            # Promover staging a current
            self.storage.promote_staging_to_current()

            # Evaluar estabilidad para transicion BOOTSTRAP -> NORMAL
            if previous_projects:
                consecutive = self.storage.get_consecutive_stable_runs()
                if stability['is_stable']:
                    consecutive += 1
                    self.storage.set_consecutive_stable_runs(consecutive)
                    logger.info(f"Corrida estable #{consecutive} en BOOTSTRAP")

                    required = self.config.BOOTSTRAP_STABLE_RUNS_REQUIRED
                    if consecutive >= required:
                        self.storage.set_monitor_mode('NORMAL')
                        logger.info("*** TRANSICION A MODO NORMAL ***")
                else:
                    self.storage.set_consecutive_stable_runs(0)
                    logger.info(
                        "Corrida inestable (intersection=%.1f%%, count_ratio=%.1f%%), "
                        "contador reiniciado",
                        stability['intersection_ratio'] * 100,
                        stability['count_ratio'] * 100
                    )
            else:
                logger.info("Primera corrida bootstrap - baseline establecida")
                self.storage.set_consecutive_stable_runs(0)
        else:
            logger.info("Dry run: staging no promovido")

        logger.info("Bootstrap: SIN notificaciones (establecimiento de baseline)")

        stats = self._build_stats(True, projects, scrape_meta, ChangeResult(), errors, start_time)
        if not dry_run:
            self.storage.save_run_stats(stats)
        return stats

    def _handle_normal(self, projects, previous_projects, stability,
                       scrape_meta, dry_run, id_schema_ok, approved_ratio,
                       errors, start_time):
        """NORMAL: Operacion regular con diff y notificaciones."""
        logger.info("=== MODO NORMAL ===")

        # Validaciones de integridad
        validation_failed = False
        reason = ""

        if approved_ratio < self.config.APPROVED_MIN_RATIO:
            reason = f"Ratio de aprobados {approved_ratio:.1%} < umbral {self.config.APPROVED_MIN_RATIO:.1%}"
            validation_failed = True
        elif not id_schema_ok:
            reason = "Esquema de project_id inconsistente"
            validation_failed = True
        elif stability['intersection_ratio'] < 0.50:
            reason = (
                f"Interseccion critica: {stability['intersection_ratio']:.1%} < 50%%. "
                f"Posible contaminacion de datos"
            )
            validation_failed = True

        if validation_failed:
            logger.warning(f"Validacion fallida: {reason}")
            logger.warning("*** TRANSICION A QUARANTINE - baseline preservada ***")
            self.storage.discard_staging()
            self.storage.set_monitor_mode('QUARANTINE')
            if self.config.EMAIL_ENABLED and not dry_run:
                send_quarantine_alert_notification(
                    reason=reason,
                    total_scraped=len(projects),
                    stability_metrics=stability,
                    config=self.config
                )
            errors.append(reason)
            stats = self._build_stats(False, projects, scrape_meta, ChangeResult(), errors, start_time)
            if not dry_run:
                self.storage.save_run_stats(stats)
            return stats

        # Detectar cambios
        changes = detect_changes(previous_projects, projects)
        logger.info(
            f"Cambios detectados: {len(changes.nuevos)} nuevos, "
            f"{len(changes.cambios_relevantes)} cambios relevantes"
        )

        # Circuit breaker por volumen anomalo
        anomaly_threshold = self.config.ALERT_NEW_APPROVED_THRESHOLD
        if len(changes.nuevos) > anomaly_threshold:
            logger.warning(
                "Volumen anomalo: %s nuevos > umbral %s. "
                "Staging descartado, baseline preservada.",
                len(changes.nuevos), anomaly_threshold
            )
            self.storage.discard_staging()
            if self.config.EMAIL_ENABLED and not dry_run:
                send_anomaly_alert_notification(
                    nuevos_count=len(changes.nuevos),
                    total_scraped=len(projects),
                    threshold=anomaly_threshold,
                    config=self.config
                )
            stats = self._build_stats(True, projects, scrape_meta, changes, errors, start_time)
            if not dry_run:
                self.storage.save_run_stats(stats)
            return stats

        if not dry_run:
            # Extraer detalles
            self._extract_details_for_changes(changes)

            # Promover staging a current
            self.storage.promote_staging_to_current()

            # Guardar historial
            if changes.todos_los_cambios:
                self.storage.add_history_entries(changes.todos_los_cambios)

            # Guardar detalles
            self._save_details(changes)

            # Notificar por email
            if self.config.EMAIL_ENABLED:
                try:
                    if changes.nuevos:
                        logger.info(f"Enviando {len(changes.nuevos)} proyecto(s) nuevo(s) por email")
                    else:
                        logger.info("Enviando email de confirmacion (sin proyectos nuevos)")

                    notification_sent = send_email_notification(changes.nuevos, self.config)
                    if notification_sent:
                        logger.info("Notificacion enviada por email")
                    else:
                        logger.warning("No se pudo enviar notificacion por email")
                except Exception as e:
                    error_msg = f"Error enviando notificacion: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
        else:
            logger.info("Dry run: omitiendo persistencia y notificaciones")
            # En dry run igual detectamos cambios para mostrar
            changes = detect_changes(previous_projects, projects)

        stats = self._build_stats(True, projects, scrape_meta, changes, errors, start_time)
        if not dry_run:
            self.storage.save_run_stats(stats)
        return stats

    def _handle_quarantine(self, projects, previous_projects, stability,
                           scrape_meta, dry_run, id_schema_ok, approved_ratio,
                           errors, start_time):
        """QUARANTINE: No actualizar baseline ni enviar email normal. Solo alerta."""
        logger.info("=== MODO QUARANTINE ===")
        logger.warning("En CUARENTENA: la baseline NO sera actualizada")

        # Siempre descartar staging en cuarentena
        self.storage.discard_staging()

        if self.config.EMAIL_ENABLED and not dry_run:
            send_quarantine_alert_notification(
                reason="Sistema en cuarentena. Ejecutar 'python -m seia_monitor bootstrap' para recuperar.",
                total_scraped=len(projects),
                stability_metrics=stability,
                config=self.config
            )

        logger.info("Para salir de QUARANTINE: python -m seia_monitor bootstrap")

        stats = self._build_stats(True, projects, scrape_meta, ChangeResult(), errors, start_time)
        if not dry_run:
            self.storage.save_run_stats(stats)
        return stats

    # ─── Main Pipeline ───────────────────────────────────────────────────

    def run(self, dry_run: bool = False, force_bootstrap: bool = False) -> RunStats:
        """
        Ejecuta una corrida completa del monitoreo.

        Pipeline:
        1. Leer modo actual (BOOTSTRAP / NORMAL / QUARANTINE)
        2. Scraping
        3. Guardar en staging
        4. Validar (IDs, approved ratio)
        5. Cargar baseline actual
        6. Computar metricas de estabilidad
        7. Delegar a handler segun modo

        Args:
            dry_run: Si True, no guarda cambios ni envia notificaciones
            force_bootstrap: Si True, fuerza modo BOOTSTRAP

        Returns:
            RunStats con el resultado de la corrida
        """
        start_time = time.time()
        errors = []
        projects = []
        scrape_meta = None
        changes = ChangeResult()

        # Leer y/o forzar modo
        current_mode = self.storage.get_monitor_mode()
        if force_bootstrap:
            current_mode = 'BOOTSTRAP'
            self.storage.set_monitor_mode('BOOTSTRAP')
            self.storage.set_consecutive_stable_runs(0)

        logger.info("=" * 60)
        logger.info("Iniciando corrida de monitoreo SEIA")
        logger.info(f"Modo monitor: {current_mode}")
        logger.info(f"Ejecucion: {'DRY RUN' if dry_run else 'PRODUCCION'}")
        logger.info(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        try:
            Config.ensure_directories()

            # 1. SCRAPING
            logger.info("Paso 1: Scraping de proyectos")
            try:
                projects, scrape_meta = scrape_seia(self.config)
                logger.info(
                    f"Scraping completado: {scrape_meta.total_projects} proyectos, "
                    f"{scrape_meta.pages_scraped} paginas, "
                    f"metodo: {scrape_meta.method}, "
                    f"duracion: {scrape_meta.duration_seconds:.1f}s"
                )
                if scrape_meta.errors:
                    errors.extend(scrape_meta.errors)
                if not scrape_meta.success or len(projects) == 0:
                    raise Exception(
                        f"Scraping no exitoso o sin resultados: {len(projects)} proyectos"
                    )
            except Exception as e:
                error_msg = f"Error en scraping: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                raise

            # 2. GUARDAR EN STAGING
            logger.info("Paso 2: Guardando en staging")
            self.storage.save_projects_to_staging(projects)

            # 3. VALIDACIONES
            logger.info("Paso 3: Validaciones")
            id_schema_ok = self.storage.validate_project_id_schema(projects)
            if not id_schema_ok:
                logger.warning("Esquema de project_id con anomalias")

            approved_count = sum(1 for p in projects if p.estado_normalizado == "aprobado")
            approved_ratio = approved_count / len(projects) if projects else 0
            logger.info(f"Ratio de aprobados: {approved_count}/{len(projects)} ({approved_ratio:.1%})")

            # 4. CARGAR BASELINE
            logger.info("Paso 4: Cargando baseline actual")
            try:
                previous_projects = self.storage.get_current_projects()
                logger.info(f"Baseline actual: {len(previous_projects)} proyectos")
            except Exception as e:
                logger.warning(f"No se pudo cargar baseline: {e}")
                previous_projects = []

            # 5. METRICAS DE ESTABILIDAD
            stability = self.storage.compute_stability_metrics(projects, previous_projects)
            logger.info(
                "Estabilidad: intersection=%.1f%%, count_ratio=%.1f%%, estable=%s",
                stability['intersection_ratio'] * 100,
                stability['count_ratio'] * 100,
                stability['is_stable']
            )

            # 6. DELEGAR A HANDLER SEGUN MODO
            if current_mode == 'BOOTSTRAP':
                return self._handle_bootstrap(
                    projects, previous_projects, stability,
                    scrape_meta, dry_run, id_schema_ok, approved_ratio,
                    errors, start_time
                )
            elif current_mode == 'NORMAL':
                return self._handle_normal(
                    projects, previous_projects, stability,
                    scrape_meta, dry_run, id_schema_ok, approved_ratio,
                    errors, start_time
                )
            elif current_mode == 'QUARANTINE':
                return self._handle_quarantine(
                    projects, previous_projects, stability,
                    scrape_meta, dry_run, id_schema_ok, approved_ratio,
                    errors, start_time
                )
            else:
                logger.error(f"Modo desconocido: {current_mode}, tratando como QUARANTINE")
                return self._handle_quarantine(
                    projects, previous_projects, stability,
                    scrape_meta, dry_run, id_schema_ok, approved_ratio,
                    errors, start_time
                )

        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 60)
            logger.error(f"Corrida FALLIDA: {e}")
            logger.error("=" * 60)

            # Descartar staging si quedo algo
            try:
                self.storage.discard_staging()
            except Exception:
                pass

            stats = self._build_stats(False, projects, scrape_meta, changes, errors, start_time)

            if not dry_run:
                try:
                    self.storage.save_run_stats(stats)
                except Exception as save_err:
                    logger.error(f"Error guardando estadisticas: {save_err}")

            return stats


def run_monitoring(
    config: Optional[Config] = None,
    dry_run: bool = False
) -> RunStats:
    """
    Funcion de entrada para ejecutar una corrida de monitoreo.

    Args:
        config: Configuracion (usa Config global si no se especifica)
        dry_run: Si True, no guarda cambios ni envia notificaciones

    Returns:
        RunStats con el resultado
    """
    if config is None:
        config = Config()

    runner = MonitoringRunner(config)
    return runner.run(dry_run=dry_run)
