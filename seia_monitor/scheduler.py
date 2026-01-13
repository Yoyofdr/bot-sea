"""
Scheduler interno usando APScheduler.
Ejecuta el monitoreo automáticamente a una hora fija.
"""

import signal
import sys
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.runner import run_monitoring

logger = get_logger("scheduler")


class SEIAScheduler:
    """Scheduler para ejecuciones automáticas"""
    
    def __init__(self, config: Config, schedule_time: str = "08:00"):
        """
        Inicializa el scheduler.
        
        Args:
            config: Configuración del sistema
            schedule_time: Hora de ejecución en formato HH:MM (24h)
        """
        self.config = config
        self.schedule_time = schedule_time
        self.scheduler = BlockingScheduler(timezone=config.TIMEZONE)
        
        # Parsear hora
        try:
            hour, minute = map(int, schedule_time.split(':'))
            self.hour = hour
            self.minute = minute
        except (ValueError, IndexError):
            logger.error(f"Formato de hora inválido: {schedule_time}")
            raise ValueError(f"schedule_time debe estar en formato HH:MM")
        
        # Setup signal handlers para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación"""
        logger.info(f"Señal {signum} recibida, deteniendo scheduler...")
        self.stop()
        sys.exit(0)
    
    def _job_wrapper(self):
        """Wrapper del job para manejo de errores"""
        try:
            logger.info("=" * 60)
            logger.info(f"Ejecución programada iniciada a las {datetime.now()}")
            logger.info("=" * 60)
            
            stats = run_monitoring(self.config, dry_run=False)
            
            if stats.success:
                logger.info(
                    f"✓ Ejecución programada completada exitosamente. "
                    f"Nuevos: {stats.nuevos_count}, Cambios: {stats.cambios_count}"
                )
            else:
                logger.error(
                    f"✗ Ejecución programada falló. Errores: {stats.errors}"
                )
        
        except Exception as e:
            logger.error(f"Error en ejecución programada: {e}", exc_info=True)
    
    def start(self):
        """
        Inicia el scheduler en modo daemon.
        
        El proceso correrá indefinidamente hasta recibir señal de terminación.
        """
        # Configurar timezone
        tz = pytz.timezone(self.config.TIMEZONE)
        
        # Agregar job con cron trigger
        trigger = CronTrigger(
            hour=self.hour,
            minute=self.minute,
            timezone=tz
        )
        
        self.scheduler.add_job(
            self._job_wrapper,
            trigger=trigger,
            id='seia_monitor_job',
            name='SEIA Monitoring Job',
            replace_existing=True
        )
        
        logger.info("=" * 60)
        logger.info(f"Scheduler iniciado")
        logger.info(f"Zona horaria: {self.config.TIMEZONE}")
        logger.info(f"Hora programada: {self.schedule_time} diariamente")
        logger.info(f"Próxima ejecución: {self.scheduler.get_jobs()[0].next_run_time}")
        logger.info("Presiona Ctrl+C para detener")
        logger.info("=" * 60)
        
        # Iniciar scheduler (bloqueante)
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler detenido por usuario")
    
    def stop(self):
        """Detiene el scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler detenido")


def start_scheduler(
    config: Optional[Config] = None,
    schedule_time: Optional[str] = None
):
    """
    Inicia el scheduler en modo daemon.
    
    Args:
        config: Configuración (usa Config global si no se especifica)
        schedule_time: Hora de ejecución (usa Config.SCHEDULE_TIME si no se especifica)
    """
    if config is None:
        config = Config()
    
    if schedule_time is None:
        schedule_time = config.SCHEDULE_TIME
    
    scheduler = SEIAScheduler(config, schedule_time)
    scheduler.start()


# Permitir ejecución directa
if __name__ == "__main__":
    start_scheduler()

