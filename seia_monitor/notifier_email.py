"""
Notificador por email para nuevos proyectos aprobados.
Envía emails con formato HTML limpio y profesional usando la API de Bye.cl.
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
    Formatea un proyecto como HTML para el email.
    
    Args:
        project: Proyecto a formatear
    
    Returns:
        HTML del proyecto
    """
    details_html = ""
    if project.details:
        d = project.details
        
        # Preparar secciones solo si tienen contenido
        resumen = d.descripcion_completa or 'Resumen no disponible para este proyecto.'
        monto = d.monto_inversion or 'No especificado'
        
        titular_n = d.titular_nombre or 'No disponible'
        titular_e = d.titular_email or 'N/A'
        rep_n = d.rep_legal_nombre or 'No disponible'
        rep_e = d.rep_legal_email or 'N/A'

        details_html = f"""
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px dashed #2563eb;">
            
            <!-- Resumen -->
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0 0 4px 0; color: #1e40af; font-size: 14px;">📝 Resumen del Proyecto</h4>
                <p style="margin: 0; font-size: 13px; color: #444; line-height: 1.5; max-height: 250px; overflow-y: auto; white-space: pre-line; background: #fff; padding: 8px; border-radius: 4px; border: 1px solid #e5e7eb;">
                    {resumen}
                </p>
            </div>
            
            <!-- Inversión -->
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0 0 4px 0; color: #1e40af; font-size: 14px;">💰 Inversión</h4>
                <p style="margin: 0; font-size: 15px; color: #059669; font-weight: bold;">
                    {monto}
                </p>
            </div>
            
            <!-- Contacto -->
            <div>
                <h4 style="margin: 0 0 4px 0; color: #1e40af; font-size: 14px;">👤 Información de Contacto</h4>
                <div style="background-color: #f8fafc; padding: 12px; border-radius: 6px; font-size: 13px; border: 1px solid #e2e8f0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="color: #64748b; width: 100px; padding: 4px 0;"><strong>Titular:</strong></td>
                            <td style="font-weight: 500; color: #334155;">{titular_n}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 4px 0;"><strong>Email:</strong></td>
                            <td><a href="mailto:{titular_e}" style="color: #2563eb; text-decoration: underline;">{titular_e}</a></td>
                        </tr>
                        <tr style="border-top: 1px solid #f1f5f9;">
                            <td style="color: #64748b; padding: 4px 0; padding-top: 8px;"><strong>Rep. Legal:</strong></td>
                            <td style="font-weight: 500; color: #334155; padding-top: 8px;">{rep_n}</td>
                        </tr>
                        <tr>
                            <td style="color: #64748b; padding: 4px 0;"><strong>Email RL:</strong></td>
                            <td><a href="mailto:{rep_e}" style="color: #2563eb; text-decoration: underline;">{rep_e}</a></td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        """

    return f"""
    <div style="border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 16px 0; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h3 style="color: #1e40af; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px;">{project.nombre_proyecto}</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr>
                <td style="padding: 6px 0; color: #6b7280; width: 140px;"><strong>ID Proyecto:</strong></td>
                <td style="padding: 6px 0; color: #111827; font-family: monospace;">{project.project_id}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #6b7280;"><strong>Titular:</strong></td>
                <td style="padding: 6px 0; color: #111827;">{project.titular or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #6b7280;"><strong>Región:</strong></td>
                <td style="padding: 6px 0; color: #111827;">{project.region or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #6b7280;"><strong>Tipo:</strong></td>
                <td style="padding: 6px 0; color: #111827;"><span style="background-color: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{project.tipo or 'N/A'}</span></td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #6b7280;"><strong>Fecha Ingreso:</strong></td>
                <td style="padding: 6px 0; color: #111827;">{project.fecha_ingreso or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #6b7280;"><strong>Estado:</strong></td>
                <td style="padding: 6px 0;"><span style="background-color: #22c55e; color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{project.estado}</span></td>
            </tr>
        </table>
        
        {details_html}
        
        <div style="margin-top: 20px; text-align: right;">
            {f'<a href="{project.url_detalle}" style="display: inline-block; background-color: #2563eb; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 500;">Ver Ficha en SEIA →</a>' if project.url_detalle else ''}
        </div>
    </div>
    """


def create_email_body(proyectos_nuevos: list[Project], timestamp: datetime) -> str:
    """
    Crea el cuerpo del email en HTML.
    
    Args:
        proyectos_nuevos: Lista de proyectos nuevos aprobados (puede estar vacía)
        timestamp: Timestamp de la corrida
    
    Returns:
        HTML completo del email
    """
    tiene_proyectos = len(proyectos_nuevos) > 0
    
    # Header
    if tiene_proyectos:
        header_title = "🎉 Nuevos Proyectos Aprobados - SEIA"
        header_color = "#2563eb"
        summary_bg = "#dbeafe"
        summary_border = "#2563eb"
        summary_text = f"Se detectaron <strong>{len(proyectos_nuevos)}</strong> nuevo(s) proyecto(s) aprobado(s)"
    else:
        header_title = "✅ Monitoreo SEIA - Sin Cambios"
        header_color = "#059669"
        summary_bg = "#d1fae5"
        summary_border = "#059669"
        summary_text = "No se detectaron proyectos aprobados nuevos"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, {header_color} 0%, #1e40af 100%); color: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; }}
            .footer {{ margin-top: 32px; padding: 16px; background-color: #f3f4f6; border-radius: 8px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0 0 8px 0; font-size: 28px;">{header_title}</h1>
                <p style="margin: 0; opacity: 0.9;">Monitoreo automático del Sistema de Evaluación de Impacto Ambiental</p>
            </div>
            
            <div style="background-color: {summary_bg}; border-left: 4px solid {summary_border}; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <p style="margin: 0;"><strong>📊 Resumen:</strong> {summary_text}</p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #1e40af;">Fecha: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
    """
    
    if tiene_proyectos:
        html += '<h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Proyectos Detectados</h2>'
        # Proyectos
        for proyecto in proyectos_nuevos:
            html += format_project_html(proyecto)
    else:
        html += """
            <div style="padding: 24px; text-align: center; color: #6b7280;">
                <p style="font-size: 16px; margin: 0;">El sistema ha verificado la página del SEIA correctamente.</p>
                <p style="font-size: 14px; margin: 8px 0 0 0;">No hay proyectos aprobados nuevos desde la última verificación.</p>
            </div>
        """
    
    # Footer
    html += f"""
            <div class="footer">
                <p style="margin: 0;">Este es un mensaje automático del sistema de monitoreo SEIA</p>
                <p style="margin: 8px 0 0 0;">No responder a este correo</p>
                <p style="margin: 8px 0 0 0; font-size: 10px; color: #9ca3af;">v2026.01.27.1</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def get_api_token(config: Config) -> Optional[str]:
    """
    Obtiene el token de autenticación de la API de Bye.cl.
    
    Args:
        config: Configuración con credenciales
    
    Returns:
        Token de autenticación o None si falla
    """
    try:
        login_url = f"{config.EMAIL_API_BASE_URL}/Cuentas/login"
        payload = {
            "email": config.EMAIL_API_USER,
            "password": config.EMAIL_API_PASSWORD
        }
        
        logger.debug(f"Autenticando en API: {login_url}")
        response = requests.post(login_url, json=payload, timeout=10)
        response.raise_for_status()
        
        token = response.json().get("token")
        if token:
            logger.info("✓ Token de API obtenido exitosamente")
            return token
        else:
            logger.error("La respuesta de login no contiene token")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error obteniendo token de API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado obteniendo token: {e}")
        return None


def send_email_via_api(
    to_address: str,
    subject: str,
    html_body: str,
    token: str,
    config: Config,
    cc: str = ""
) -> bool:
    """
    Envía un email usando la API de Bye.cl.
    
    Args:
        to_address: Email del destinatario
        subject: Asunto del email
        html_body: Cuerpo HTML del email
        token: Token de autenticación
        config: Configuración
        cc: Emails en copia (opcional)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
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
            "cc": cc,
            "htmlBody": html_body
        }
        
        logger.debug(f"Enviando email a: {to_address}")
        response = requests.post(send_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"✓ Email enviado exitosamente a {to_address}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error enviando email via API: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado enviando email: {e}")
        return False


def send_email_notification(
    proyectos_nuevos: list[Project],
    config: Optional[Config] = None
) -> bool:
    """
    Envía notificación por email sobre nuevos proyectos aprobados.
    
    Args:
        proyectos_nuevos: Lista de proyectos nuevos a notificar
        config: Configuración (usa Config por defecto si no se provee)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    if config is None:
        config = Config()
    
    # Verificar que esté habilitado
    if not config.EMAIL_ENABLED:
        logger.info("Notificaciones por email deshabilitadas")
        return False
    
    # Verificar configuración
    if not config.EMAIL_API_BASE_URL or not config.EMAIL_API_USER or not config.EMAIL_API_PASSWORD:
        logger.warning("Configuración de email API incompleta")
        return False
    
    if not config.EMAIL_TO:
        logger.warning("EMAIL_TO no configurado")
        return False
    
    try:
        # Obtener token
        token = get_api_token(config)
        if not token:
            logger.error("No se pudo obtener token de autenticación")
            return False
        
        # Crear cuerpo HTML y subject
        timestamp = datetime.now()
        html_body = create_email_body(proyectos_nuevos, timestamp)
        
        if proyectos_nuevos:
            subject = f"🎉 {len(proyectos_nuevos)} Nuevo(s) Proyecto(s) Aprobado(s) - SEIA"
        else:
            subject = "✅ Monitoreo SEIA - Sin Cambios"
        
        # Enviar a cada destinatario
        recipients = [email.strip() for email in config.EMAIL_TO.split(",")]
        all_success = True
        
        for recipient in recipients:
            if not recipient:
                continue
            
            success = send_email_via_api(
                to_address=recipient,
                subject=subject,
                html_body=html_body,
                token=token,
                config=config
            )
            
            if not success:
                all_success = False
        
        if all_success:
            if proyectos_nuevos:
                logger.info(f"✓ Emails enviados exitosamente a {len(recipients)} destinatario(s) con {len(proyectos_nuevos)} proyecto(s)")
            else:
                logger.info(f"✓ Emails de confirmación enviados exitosamente a {len(recipients)} destinatario(s) (sin proyectos nuevos)")
            return True
        else:
            logger.warning("⚠ Algunos emails no se pudieron enviar")
            return False
        
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False





