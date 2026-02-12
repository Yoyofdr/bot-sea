"""
Interfaz de linea de comandos (CLI) para el sistema SEIA Monitor.
Usa Typer para una experiencia moderna y amigable.
"""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from seia_monitor.config import Config
from seia_monitor.logger import get_logger, setup_logger
from seia_monitor.runner import MonitoringRunner, run_monitoring
from seia_monitor.scheduler import start_scheduler
from seia_monitor.storage import SEIAStorage

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

    Por defecto ejecuta una sola vez. Usa 'schedule' para ejecucion continua.
    """
    # Configurar log level
    if verbose:
        setup_logger(level="DEBUG")

    # Validar configuracion
    errors = Config.validate()
    if errors:
        console.print("[red]Errores de configuracion:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    # Ejecutar
    try:
        if dry_run:
            console.print("[yellow]Modo DRY RUN - No se guardaran cambios[/yellow]")

        console.print("[cyan]Iniciando monitoreo SEIA...[/cyan]")

        stats = run_monitoring(Config(), dry_run=dry_run)

        # Mostrar resultado
        if stats.success:
            console.print("\n[green]Corrida completada exitosamente[/green]")
            console.print(f"  - Duracion: {stats.duration_seconds:.1f}s")
            console.print(f"  - Proyectos: {stats.total_projects}")
            console.print(f"  - Paginas: {stats.pages_scraped}")
            console.print(f"  - Metodo: {stats.scrape_method}")
            console.print(f"  - Nuevos: {stats.nuevos_count}")
            console.print(f"  - Cambios relevantes: {stats.cambios_count}")
        else:
            console.print("\n[red]Corrida fallo[/red]")
            if stats.errors:
                console.print(f"  - Errores: {stats.errors}")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrumpido por usuario[/yellow]")
        sys.exit(0)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Error en CLI: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def bootstrap(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simular sin guardar cambios"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Modo verbose (DEBUG)"
    )
):
    """
    Entra en modo BOOTSTRAP y establece una baseline limpia.

    Pasos:
    1. Fuerza modo BOOTSTRAP
    2. Ejecuta scraping y validacion
    3. Guarda snapshot validado SIN enviar notificaciones
    4. Tras 2 corridas estables consecutivas, transiciona a NORMAL

    Usar para recuperar de baseline contaminada o inicializar el sistema.
    """
    if verbose:
        setup_logger(level="DEBUG")

    errors = Config.validate()
    if errors:
        console.print("[red]Errores de configuracion:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    console.print("[cyan]Entrando en modo BOOTSTRAP...[/cyan]")
    console.print("[yellow]Las notificaciones seran suprimidas hasta que la baseline sea estable[/yellow]")

    try:
        config = Config()
        runner = MonitoringRunner(config)
        stats = runner.run(dry_run=dry_run, force_bootstrap=True)

        if stats.success:
            mode = runner.storage.get_monitor_mode()
            stable_runs = runner.storage.get_consecutive_stable_runs()
            required = config.BOOTSTRAP_STABLE_RUNS_REQUIRED

            console.print(f"\n[green]Bootstrap completado[/green]")
            console.print(f"  - Modo actual: {mode}")
            console.print(f"  - Corridas estables: {stable_runs}/{required}")
            console.print(f"  - Proyectos en baseline: {stats.total_projects}")

            if mode == 'NORMAL':
                console.print("\n[green]Sistema transiciono a modo NORMAL[/green]")
            elif mode == 'BOOTSTRAP':
                needed = max(0, required - stable_runs)
                console.print(f"\n[yellow]Ejecutar bootstrap {needed} vez/veces mas para confirmar estabilidad[/yellow]")
            elif mode == 'QUARANTINE':
                console.print("\n[red]Validacion fallo - entro en QUARANTINE[/red]")
                console.print("Revisar logs y ejecutar bootstrap nuevamente")
        else:
            console.print(f"\n[red]Bootstrap fallo: {stats.errors}[/red]")
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrumpido por usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Error en bootstrap: {e}", exc_info=True)
        sys.exit(1)


@app.command(name="quarantine-status")
def quarantine_status():
    """
    Muestra el estado actual del monitor y que se necesita para transicionar.
    """
    try:
        storage = SEIAStorage()
        state = storage.get_all_state()
        current_projects = storage.get_current_projects()
        last_run = storage.get_last_run_stats()

        mode = state.get('mode', {}).get('value', 'BOOTSTRAP (default)')
        stable_runs = state.get('consecutive_stable_runs', {}).get('value', '0')

        table = Table(title="Estado del Monitor", show_header=True)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

        # Color segun modo
        mode_color = {"NORMAL": "green", "BOOTSTRAP": "yellow", "QUARANTINE": "red"}.get(mode, "white")
        table.add_row("Modo", f"[{mode_color}]{mode}[/{mode_color}]")
        table.add_row("Corridas estables consecutivas", stable_runs)
        table.add_row("Proyectos en baseline", str(len(current_projects)))

        if last_run:
            status_icon = "[green]OK[/green]" if last_run.success else "[red]FALLO[/red]"
            table.add_row("Ultima corrida", last_run.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("Resultado ultima corrida", status_icon)
            table.add_row("Proyectos ultima corrida", str(last_run.total_projects))

        for key, info in state.items():
            if key not in ('mode', 'consecutive_stable_runs'):
                table.add_row(key, info['value'])

        console.print(table)

        # Indicaciones segun modo
        if mode == 'QUARANTINE':
            console.print("\n[red]Sistema en CUARENTENA[/red]")
            console.print("Para salir: [cyan]python -m seia_monitor bootstrap[/cyan]")
        elif mode == 'BOOTSTRAP' or mode == 'BOOTSTRAP (default)':
            required = Config.BOOTSTRAP_STABLE_RUNS_REQUIRED
            needed = max(0, required - int(stable_runs))
            console.print(f"\n[yellow]Faltan {needed} corrida(s) estable(s) para llegar a NORMAL[/yellow]")
            console.print("Ejecutar: [cyan]python -m seia_monitor bootstrap[/cyan]")
        elif mode == 'NORMAL':
            console.print("\n[green]Sistema operando normalmente[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def schedule(
    time: str = typer.Option(
        None,
        "--time", "-t",
        help="Hora de ejecucion (HH:MM). Default: usar SCHEDULE_TIME del .env"
    )
):
    """
    Inicia el scheduler para ejecucion automatica diaria.

    El proceso correra indefinidamente hasta ser interrumpido (Ctrl+C).
    """
    # Validar configuracion
    errors = Config.validate()
    if errors:
        console.print("[red]Errores de configuracion:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

    # Determinar hora
    schedule_time = time if time else Config.SCHEDULE_TIME

    console.print("[cyan]Iniciando scheduler...[/cyan]")
    console.print(f"  - Hora programada: {schedule_time}")
    console.print(f"  - Zona horaria: {Config.TIMEZONE}")
    console.print(f"  - Presiona Ctrl+C para detener\n")

    try:
        start_scheduler(Config(), schedule_time)
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler detenido por usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.error(f"Error en scheduler: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def status():
    """
    Muestra el estado de la ultima corrida y estadisticas generales.
    """
    try:
        storage = SEIAStorage()

        # Modo actual
        mode = storage.get_monitor_mode()
        mode_color = {"NORMAL": "green", "BOOTSTRAP": "yellow", "QUARANTINE": "red"}.get(mode, "white")
        console.print(f"Modo monitor: [{mode_color}]{mode}[/{mode_color}]")

        # Ultima corrida
        last_run = storage.get_last_run_stats()

        if not last_run:
            console.print("[yellow]No hay corridas registradas aun[/yellow]")
            return

        # Tabla de ultima corrida
        table = Table(title="Ultima Corrida", show_header=True)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

        status_color = "green" if last_run.success else "red"
        status_text = "Exitosa" if last_run.success else "Fallida"

        table.add_row("Estado", f"[{status_color}]{status_text}[/{status_color}]")
        table.add_row("Fecha/Hora", last_run.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Duracion", f"{last_run.duration_seconds:.1f}s")
        table.add_row("Proyectos", str(last_run.total_projects))
        table.add_row("Paginas", str(last_run.pages_scraped))
        table.add_row("Metodo", last_run.scrape_method)
        table.add_row("Nuevos", str(last_run.nuevos_count))
        table.add_row("Cambios", str(last_run.cambios_count))

        if last_run.errors:
            table.add_row("Errores", last_run.errors[:100])

        console.print(table)

        # Total de proyectos actuales
        current_projects = storage.get_current_projects()
        console.print(f"\n[cyan]Total de proyectos monitoreados: {len(current_projects)}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error obteniendo estado: {e}[/red]")
        sys.exit(1)


@app.command()
def config_check():
    """
    Verifica la configuracion del sistema.
    """
    console.print("[cyan]Verificando configuracion...[/cyan]\n")

    # Validar
    errors = Config.validate()

    # Tabla de configuracion
    table = Table(title="Configuracion Actual", show_header=True)
    table.add_column("Variable", style="cyan")
    table.add_column("Valor", style="white")
    table.add_column("Estado", style="white")

    configs = [
        ("SEIA_BASE_URL", Config.SEIA_BASE_URL),
        ("SCRAPE_MODE", Config.SCRAPE_MODE),
        ("EMAIL_ENABLED", str(Config.EMAIL_ENABLED)),
        ("EMAIL_API_USER", Config.EMAIL_API_USER[:20] + "..." if Config.EMAIL_API_USER else None),
        ("EMAIL_TO", Config.EMAIL_TO[:50] + "..." if len(Config.EMAIL_TO) > 50 else Config.EMAIL_TO if Config.EMAIL_TO else None),
        ("DB_PATH", str(Config.get_db_path())),
        ("LOG_LEVEL", Config.LOG_LEVEL),
        ("MAX_PAGES", str(Config.MAX_PAGES)),
        ("TIMEZONE", Config.TIMEZONE),
        ("SCHEDULE_TIME", Config.SCHEDULE_TIME),
        ("ALERT_NEW_APPROVED_THRESHOLD", str(Config.ALERT_NEW_APPROVED_THRESHOLD)),
        ("APPROVED_MIN_RATIO", str(Config.APPROVED_MIN_RATIO)),
        ("STABILITY_INTERSECTION_MIN", str(Config.STABILITY_INTERSECTION_MIN)),
        ("BOOTSTRAP_STABLE_RUNS_REQUIRED", str(Config.BOOTSTRAP_STABLE_RUNS_REQUIRED)),
    ]

    for name, value in configs:
        if value:
            table.add_row(name, str(value), "[green]OK[/green]")
        else:
            table.add_row(name, "[dim]no configurado[/dim]", "[yellow]?[/yellow]")

    console.print(table)

    # Mostrar modo actual
    try:
        storage = SEIAStorage()
        mode = storage.get_monitor_mode()
        mode_color = {"NORMAL": "green", "BOOTSTRAP": "yellow", "QUARANTINE": "red"}.get(mode, "white")
        console.print(f"\nModo monitor: [{mode_color}]{mode}[/{mode_color}]")
    except Exception:
        pass

    # Errores
    if errors:
        console.print("\n[red]Errores de validacion:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)
    else:
        console.print("\n[green]Configuracion valida[/green]")


@app.command()
def version():
    """Muestra la version del sistema."""
    from seia_monitor import __version__
    console.print(f"SEIA Monitor v{__version__}")


def main():
    """Punto de entrada principal"""
    app()


if __name__ == "__main__":
    main()
