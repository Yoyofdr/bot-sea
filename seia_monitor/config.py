"""
Configuración del sistema SEIA Monitor.
Carga variables de entorno y valida configuración.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración centralizada del sistema"""
    
    # Directorio base del proyecto
    BASE_DIR = Path(__file__).parent.parent
    
    # SEIA Configuration
    SEIA_BASE_URL: str = os.getenv(
        "SEIA_BASE_URL",
        "https://seia.sea.gob.cl/busqueda/buscarProyectoResumen.php"
    )
    SCRAPE_MODE: str = os.getenv("SCRAPE_MODE", "auto")  # auto|requests|playwright
    
    # Teams Notification
    TEAMS_WEBHOOK_URL: Optional[str] = os.getenv("TEAMS_WEBHOOK_URL")
    
    # Database
    DB_PATH: str = os.getenv("DB_PATH", "data/seia_monitor.db")
    
    # Scraping Config
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "1"))
    MAX_PROJECTS_PER_RUN: int = int(os.getenv("MAX_PROJECTS_PER_RUN", "10000"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Scheduler
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Santiago")
    SCHEDULE_TIME: str = os.getenv("SCHEDULE_TIME", "08:00")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/seia_monitor.log")
    
    # Retry configuration
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    RETRY_INITIAL_DELAY: float = 1.0
    
    # Rate limiting
    RATE_LIMIT_DELAY: float = 2.5  # segundos entre páginas
    
    @classmethod
    def validate(cls) -> list[str]:
        """Valida la configuración y retorna lista de errores"""
        errors = []
        
        if not cls.SEIA_BASE_URL:
            errors.append("SEIA_BASE_URL es requerido")
            
        if cls.SCRAPE_MODE not in ["auto", "requests", "playwright"]:
            errors.append(f"SCRAPE_MODE inválido: {cls.SCRAPE_MODE}")
            
        if cls.TEAMS_WEBHOOK_URL and not cls.TEAMS_WEBHOOK_URL.startswith("https://"):
            errors.append("TEAMS_WEBHOOK_URL debe ser una URL HTTPS válida")
            
        if cls.MAX_PAGES < 1:
            errors.append("MAX_PAGES debe ser >= 1")
            
        if cls.REQUEST_TIMEOUT < 1:
            errors.append("REQUEST_TIMEOUT debe ser >= 1")
            
        return errors
    
    @classmethod
    def get_db_path(cls) -> Path:
        """Retorna la ruta absoluta de la base de datos"""
        if Path(cls.DB_PATH).is_absolute():
            return Path(cls.DB_PATH)
        return cls.BASE_DIR / cls.DB_PATH
    
    @classmethod
    def get_log_path(cls) -> Path:
        """Retorna la ruta absoluta del archivo de log"""
        if Path(cls.LOG_FILE).is_absolute():
            return Path(cls.LOG_FILE)
        return cls.BASE_DIR / cls.LOG_FILE
    
    @classmethod
    def ensure_directories(cls):
        """Crea los directorios necesarios si no existen"""
        # Directorio de base de datos
        db_path = cls.get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Directorio de logs
        log_path = cls.get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Directorio de debug
        debug_dir = cls.BASE_DIR / "data" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)


# Validar configuración al importar
config_errors = Config.validate()
if config_errors:
    import warnings
    for error in config_errors:
        warnings.warn(f"Error de configuración: {error}")

