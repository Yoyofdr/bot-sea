"""
Notificador por email para nuevos proyectos aprobados.
Envía emails con formato HTML ejecutivo minimalista usando la API de Bye.cl.
"""

import requests
from datetime import datetime
from typing import Optional

from seia_monitor.config import Config
from seia_monitor.models import Project
from seia_monitor.logger import get_logger

logger = get_logger("notifier_email")


def format_project_html(project: Project) -> str:
    """
    Formatea un proyecto como HTML para el email siguiendo el diseño ejecutivo minimalista.
    """
    details_html = ""
    resumen = "Resumen no disponible para este proyecto."
    monto = "No especificado"
    titular_n = project.titular or 'N/A'
    titular_e = 'N/A'
    rep_n = 'No disponible'
    rep_e = 'N/A'

    if project.details:
        d = project.details
        resumen = d.descripcion_completa or resumen
        monto = d.monto_inversion or monto
        titular_n = d.titular_nombre or titular_n
        titular_e = d.titular_email or titular_e
        rep_n = d.rep_legal_nombre or rep_n
        rep_e = d.rep_legal_email or rep_e

    return f"""
    <!-- Bloque de Proyecto -->
    <div style="margin-bottom: 48px;">
        <h1 style="font-size: 26px; font-weight: 800; color: #111827; margin: 0 0 24px 0; line-height: 1.2;">
            {project.nombre_proyecto}
        </h1>

        <!-- Key Facts Card -->
        <div style="background-color: #f9fafb; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                    <td valign="top" style="padding-bottom: 12px;">
                        <span style="display: inline-block; background-color: #5FA91D; color: #ffffff; font-size: 11px; font-weight: bold; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.02em;">
                            {project.estado}
                        </span>
                    </td>
                </tr>
            </table>
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top: 12px;">
                <tr>
                    <td width="50%" style="padding-bottom: 16px;">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Monto Inversión</div>
                        <div style="font-size: 14px; color: #374151; padding-top: 2px;">{monto}</div>
                    </td>
                    <td width="50%" style="padding-bottom: 16px;">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Región</div>
                        <div style="font-size: 14px; color: #374151; padding-top: 2px;">{project.region or 'N/A'}</div>
                    </td>
                </tr>
                <tr>
                    <td width="50%">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Tipo</div>
                        <div style="font-size: 14px; color: #374151; padding-top: 2px;">{project.tipo or 'N/A'}</div>
                    </td>
                    <td width="50%">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Fecha Ingreso</div>
                        <div style="font-size: 14px; color: #374151; padding-top: 2px;">{project.fecha_ingreso or 'N/A'}</div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Summary -->
        <h2 style="font-size: 14px; font-weight: 700; color: #4b5563; text-transform: uppercase; letter-spacing: 0.1em; margin: 32px 0 12px 0; border-bottom: 2px solid #f3f4f6; padding-bottom: 6px;">
            Resumen del Proyecto
        </h2>
        <div style="font-size: 15px; color: #4b5563; margin-bottom: 24px; white-space: pre-line;">
            {resumen}
        </div>

        <!-- Contact -->
        <h2 style="font-size: 14px; font-weight: 700; color: #4b5563; text-transform: uppercase; letter-spacing: 0.1em; margin: 32px 0 12px 0; border-bottom: 2px solid #f3f4f6; padding-bottom: 6px;">
            Información de Contacto
        </h2>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td width="48%" valign="top">
                    <div style="background-color: #ffffff; border: 1px solid #f3f4f6; border-radius: 6px; padding: 16px;">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 4px;">Titular</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 2px;">{titular_n}</div>
                        <a href="mailto:{titular_e}" style="font-size: 13px; color: #5FA91D; text-decoration: none;">{titular_e}</a>
                    </div>
                </td>
                <td width="4%"></td>
                <td width="48%" valign="top">
                    <div style="background-color: #ffffff; border: 1px solid #f3f4f6; border-radius: 6px; padding: 16px;">
                        <div style="font-size: 11px; color: #6b7280; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 4px;">Rep. Legal</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 2px;">{rep_n}</div>
                        <a href="mailto:{rep_e}" style="font-size: 13px; color: #5FA91D; text-decoration: none;">{rep_e}</a>
                    </div>
                </td>
            </tr>
        </table>

        <!-- CTA -->
        <div style="margin-top: 40px; margin-bottom: 20px; text-align: center;">
            <a href="{project.url_detalle or '#'}" style="display: inline-block; background-color: #5FA91D; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold;">
                VER FICHA COMPLETA
            </a>
        </div>
    </div>
    """


def create_email_body(proyectos_nuevos: list[Project], timestamp: datetime) -> str:
    """
    Crea el cuerpo del email en HTML con diseño ejecutivo minimalista.
    """
    proyectos_html = ""
    for p in proyectos_nuevos:
        proyectos_html += format_project_html(p)

    if not proyectos_nuevos:
        proyectos_html = """
        <div style="padding: 32px; text-align: center; color: #6b7280;">
            <p style="font-size: 16px; margin: 0;">No se detectaron proyectos aprobados nuevos en esta revisión.</p>
        </div>
        """

    return f"""
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style type="text/css">
        body {{ margin: 0; padding: 0; background-color: #f9fafb; font-family: Arial, Helvetica, sans-serif; color: #111827; line-height: 1.5; }}
      </style>
    </head>
    <body>
      <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
        <div style="padding: 32px;">
          {proyectos_html}
        </div>
        <div style="padding: 32px; background-color: #f9fafb; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb;">
          Este es un mensaje automático del sistema de monitoreo SEIA.<br>
          No responder a este correo electrónico.<br>
          <span style="font-size: 10px; margin-top: 8px; display: block;">v2026.01.30.1</span>
        </div>
      </div>
    </body>
    </html>
    """


def get_api_token(config: Config) -> Optional[str]:
    """
    Obtiene el token de autenticación de la API de Bye.cl.
    """
    try:
        login_url = f"{config.EMAIL_API_BASE_URL}/Cuentas/login"
        payload = {
            "email": config.EMAIL_API_USER,
            "password": config.EMAIL_API_PASSWORD
        }
        response = requests.post(login_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        logger.error(f"Error obteniendo token de API: {e}")
        return None


def send_email_via_api(to_address: str, subject: str, html_body: str, token: str, config: Config) -> bool:
    """
    Envía un email usando la API de Bye.cl.
    """
    try:
        send_url = f"{config.EMAIL_API_BASE_URL}/Email/SendEmailByE"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "toAddress": to_address,
            "subject": subject,
            "htmlBody": html_body
        }
        response = requests.post(send_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Error enviando email via API: {e}")
        return False


def send_email_notification(proyectos_nuevos: list[Project], config: Optional[Config] = None) -> bool:
    """
    Envía notificación por email sobre nuevos proyectos aprobados.
    """
    if config is None:
        config = Config()
    
    if not config.EMAIL_ENABLED:
        return False
    
    if not config.EMAIL_API_BASE_URL or not config.EMAIL_API_USER or not config.EMAIL_API_PASSWORD or not config.EMAIL_TO:
        logger.warning("Configuración de email incompleta")
        return False
    
    try:
        token = get_api_token(config)
        if not token:
            return False
        
        html_body = create_email_body(proyectos_nuevos, datetime.now())
        
        if proyectos_nuevos:
            subject = f"{len(proyectos_nuevos)} Nuevo(s) Proyecto(s) Aprobado(s) - SEIA"
        else:
            subject = "Monitoreo SEIA - Sin Cambios"
        
        recipients = [email.strip() for email in config.EMAIL_TO.split(",")]
        all_success = True
        
        for recipient in recipients:
            if recipient and not send_email_via_api(recipient, subject, html_body, token, config):
                all_success = False
        
        if all_success:
            logger.info(f"✓ Emails enviados exitosamente")
        return all_success
        
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False
