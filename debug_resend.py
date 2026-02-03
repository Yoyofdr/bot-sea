
import sys
from datetime import datetime
from seia_monitor.config import Config
from seia_monitor.storage import SEIAStorage
from seia_monitor.notifier_email import create_email_body, get_api_token, send_email_via_api
from seia_monitor.models import Project

def resend_today_test():
    config = Config()
    storage = SEIAStorage()
    
    # Destinatario de prueba
    test_email = "rfernandezdelrio@bye.cl"
    
    print(f"Buscando proyectos de hoy...")
    
    # Obtener proyectos cuya primera aparición fue hoy
    all_projects = storage.get_current_projects()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    today_projects = []
    for p in all_projects:
        if p.first_seen and p.first_seen.strftime("%Y-%m-%d") == today_str:
            # Cargar detalles si existen
            details = storage.get_project_details(p.project_id)
            p.details = details
            today_projects.append(p)
    
    print(f"Encontrados {len(today_projects)} proyectos nuevos hoy.")
    
    if not today_projects:
        print("No hay proyectos nuevos hoy para re-enviar, pero enviaré el reporte de 'Sin Cambios' para probar el diseño.")
    
    # Generar el cuerpo del email con el nuevo diseño
    html_body = create_email_body(today_projects, datetime.now())
    
    # Obtener token
    token = get_api_token(config)
    if not token:
        print("Error: No se pudo obtener el token de la API.")
        return

    subject = f"PRUEBA DISEÑO v6 - {len(today_projects)} Proyectos Nuevos" if today_projects else "PRUEBA DISEÑO v6 - Sin Cambios"
    
    print(f"Enviando correo a {test_email}...")
    success = send_email_via_api(test_email, subject, html_body, token, config)
    
    if success:
        print("✓ Correo de prueba enviado exitosamente.")
    else:
        print("✗ Error al enviar el correo.")

if __name__ == "__main__":
    resend_today_test()
