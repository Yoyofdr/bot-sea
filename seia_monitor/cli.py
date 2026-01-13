"""
Interfaz de línea de comandos (CLI) para el sistema SEIA Monitor.
Usa Typer para una experiencia moderna y amigable.
"""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from seia_monitor.config import Config
from seia_monitor.logger import get_logger, setup_logger
from seia_monitor.runner import run_monitoring
from seia_monitor.scheduler import start_scheduler
from seia_monitor.storage import SEIAStorage
from seia_monitor.notifier_teams import test_teams_webhook

# Inicializar app de Typer
app = typer.Typer(
    name="seia_monitor",
    help="Sistema de Monitoreo SEIA - Chile",
    add_completion=False
)

console = Console()
logger = get_logger("cli")


@app.command()
def run(
    once: bool = typer.Option(
        False,
        "--once",
        help="Ejecutar una sola vez y salir"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Modo de prueba (no guarda ni notifica)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Modo verbose (DEBUG)"
    )
):
    """
    Ejecuta el monitoreo del SEIA.
    
    Por defecto ejecuta una sola vez. Usa 'schedule' para ejecución continua.
    """
    # Configurar log level
    if verbose:
        setup_logger(level="DEBUG")
    
    # Validar configuración
    errors = Config.validate()
    if errors:
        console.print("[red]✗ Errores de configuración:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)
    
    # Ejecutar
    try:
        if dry_run:
            console.print("[yellow]⚠ Modo DRY RUN - No se guardarán cambios[/yellow]")
        
        console.print("[cyan]Iniciando monitoreo SEIA...[/cyan]")
        
        stats = run_monitoring(Config(), dry_run=dry_run)
        
        # Mostrar resultado
        if stats.success:
            console.print("\n[green]✓ Corrida completada exitosamente[/green]")
            console.print(f"  • Duración: {stats.duration_seconds:.1f}s")
            console.print(f"  • Proyectos: {stats.total_projects}")
            console.print(f"  • Páginas: {stats.pages_scraped}")
            console.print(f"  • Método: {stats.scrape_method}")
            console.print(f"  • Nuevos: {stats.nuevos_count}")
            console.print(f"  • Cambios relevantes: {stats.cambios_count}")
        else:
            console.print("\n[red]✗ Corrida falló[/red]")
            if stats.errors:
                console.print(f"  • Errores: {stats.errors}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrumpido por usuario[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        logger.error(f"Error en CLI: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def schedule(
    time: str = typer.Option(
        None,
        "--time", "-t",
        help="Hora de ejecución (HH:MM). Default: usar SCHEDULE_TIME del .env"
    )
):
    """
    Inicia el scheduler para ejecución automática diaria.
    
    El proceso correrá indefinidamente hasta ser interrumpido (Ctrl+C).
    """
    # Validar configuración
    errors = Config.validate()
    if errors:
        console.print("[red]✗ Errores de configuración:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)
    
    # Determinar hora
    schedule_time = time if time else Config.SCHEDULE_TIME
    
    console.print("[cyan]Iniciando scheduler...[/cyan]")
    console.print(f"  • Hora programada: {schedule_time}")
    console.print(f"  • Zona horaria: {Config.TIMEZONE}")
    console.print(f"  • Presiona Ctrl+C para detener\n")
    
    try:
        start_scheduler(Config(), schedule_time)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler detenido por usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        logger.error(f"Error en scheduler: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def status():
    """
    Muestra el estado de la última corrida y estadísticas generales.
    """
    try:
        storage = SEIAStorage()
        
        # Última corrida
        last_run = storage.get_last_run_stats()
        
        if not last_run:
            console.print("[yellow]No hay corridas registradas aún[/yellow]")
            return
        
        # Tabla de última corrida
        table = Table(title="Última Corrida", show_header=True)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")
        
        status_icon = "✓" if last_run.success else "✗"
        status_color = "green" if last_run.success else "red"
        
        table.add_row("Estado", f"[{status_color}]{status_icon} {'Exitosa' if last_run.success else 'Fallida'}[/{status_color}]")
        table.add_row("Fecha/Hora", last_run.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Duración", f"{last_run.duration_seconds:.1f}s")
        table.add_row("Proyectos", str(last_run.total_projects))
        table.add_row("Páginas", str(last_run.pages_scraped))
        table.add_row("Método", last_run.scrape_method)
        table.add_row("Nuevos", str(last_run.nuevos_count))
        table.add_row("Cambios", str(last_run.cambios_count))
        
        if last_run.errors:
            table.add_row("Errores", last_run.errors[:100])
        
        console.print(table)
        
        # Total de proyectos actuales
        current_projects = storage.get_current_projects()
        console.print(f"\n[cyan]Total de proyectos monitoreados: {len(current_projects)}[/cyan]")
    
    except Exception as e:
        console.print(f"[red]✗ Error obteniendo estado: {e}[/red]")
        sys.exit(1)


@app.command()
def test_teams():
    """
    Envía un mensaje de prueba al webhook de Teams.
    """
    if not Config.TEAMS_WEBHOOK_URL:
        console.print("[red]✗ No hay TEAMS_WEBHOOK_URL configurado en .env[/red]")
        sys.exit(1)
    
    console.print("[cyan]Enviando mensaje de prueba a Teams...[/cyan]")
    
    success = test_teams_webhook(Config.TEAMS_WEBHOOK_URL)
    
    if success:
        console.print("[green]✓ Webhook funciona correctamente[/green]")
        console.print("  Revisa el canal de Teams para ver el mensaje")
    else:
        console.print("[red]✗ Error enviando mensaje de prueba[/red]")
        console.print("  Revisa el webhook URL y los logs para más detalles")
        sys.exit(1)


@app.command()
def config_check():
    """
    Verifica la configuración del sistema.
    """
    console.print("[cyan]Verificando configuración...[/cyan]\n")
    
    # Validar
    errors = Config.validate()
    
    # Tabla de configuración
    table = Table(title="Configuración Actual", show_header=True)
    table.add_column("Variable", style="cyan")
    table.add_column("Valor", style="white")
    table.add_column("Estado", style="white")
    
    configs = [
        ("SEIA_BASE_URL", Config.SEIA_BASE_URL),
        ("FECHA_DESDE", Config.FECHA_DESDE),
        ("SCRAPE_MODE", Config.SCRAPE_MODE),
        ("TEAMS_WEBHOOK_URL", Config.TEAMS_WEBHOOK_URL[:50] + "..." if Config.TEAMS_WEBHOOK_URL else None),
        ("DB_PATH", str(Config.get_db_path())),
        ("LOG_LEVEL", Config.LOG_LEVEL),
        ("MAX_PAGES", str(Config.MAX_PAGES)),
        ("TIMEZONE", Config.TIMEZONE),
        ("SCHEDULE_TIME", Config.SCHEDULE_TIME),
    ]
    
    for name, value in configs:
        if value:
            table.add_row(name, str(value), "[green]✓[/green]")
        else:
            table.add_row(name, "[dim]no configurado[/dim]", "[yellow]⚠[/yellow]")
    
    console.print(table)
    
    # Errores
    if errors:
        console.print("\n[red]✗ Errores de validación:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)
    else:
        console.print("\n[green]✓ Configuración válida[/green]")


@app.command()
def version():
    """Muestra la versión del sistema."""
    from seia_monitor import __version__
    console.print(f"SEIA Monitor v{__version__}")


def main():
    """Punto de entrada principal"""
    app()


if __name__ == "__main__":
    main()


