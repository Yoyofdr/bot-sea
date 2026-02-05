"""
Sistema de logging con rotación y niveles configurables.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from seia_monitor.config import Config


def setup_logger(
    name: str = "seia_monitor",
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configura y retorna un logger con rotación de archivos.
    
    Args:
        name: Nombre del logger
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log (usa Config si no se especifica)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicar handlers si ya está configurado
    if logger.handlers:
        return logger
    
    # Nivel de log
    log_level = level or Config.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formato de log
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    if log_file is None:
        log_file = Config.get_log_path()
    
    # Asegurar que el directorio existe
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotación: 10 MB por archivo, mantener 5 archivos
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# Logger por defecto del módulo
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo del logger principal.
    
    Args:
        name: Nombre del logger hijo
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(f"seia_monitor.{name}")









