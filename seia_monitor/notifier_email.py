"""
Notificador por email para nuevos proyectos aprobados.
Envía emails con formato HTML limpio y profesional.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    return f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 12px 0; background-color: #f9f9f9;">
        <h3 style="color: #2563eb; margin-top: 0;">{project.nombre_proyecto}</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 4px 0; color: #666; width: 150px;"><strong>ID:</strong></td>
                <td style="padding: 4px 0;">{project.project_id}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666;"><strong>Titular:</strong></td>
                <td style="padding: 4px 0;">{project.titular or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666;"><strong>Región:</strong></td>
                <td style="padding: 4px 0;">{project.region or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666;"><strong>Tipo:</strong></td>
                <td style="padding: 4px 0;">{project.tipo or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666;"><strong>Fecha Ingreso:</strong></td>
                <td style="padding: 4px 0;">{project.fecha_ingreso or 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0; color: #666;"><strong>Estado:</strong></td>
                <td style="padding: 4px 0;"><span style="background-color: #22c55e; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{project.estado}</span></td>
            </tr>
        </table>
        {f'<p style="margin-top: 12px;"><a href="{project.url_detalle}" style="color: #2563eb; text-decoration: none;">Ver detalles del proyecto →</a></p>' if project.url_detalle else ''}
    </div>
    """


def create_email_body(proyectos_nuevos: list[Project], timestamp: datetime) -> str:
    """
    Crea el cuerpo del email en HTML.
    
    Args:
        proyectos_nuevos: Lista de proyectos nuevos aprobados
        timestamp: Timestamp de la corrida
    
    Returns:
        HTML completo del email
    """
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); color: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; }}
            .footer {{ margin-top: 32px; padding: 16px; background-color: #f3f4f6; border-radius: 8px; text-align: center; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0 0 8px 0; font-size: 28px;">🎉 Nuevos Proyectos Aprobados - SEIA</h1>
                <p style="margin: 0; opacity: 0.9;">Monitoreo automático del Sistema de Evaluación de Impacto Ambiental</p>
            </div>
            
            <div style="background-color: #dbeafe; border-left: 4px solid #2563eb; padding: 16px; margin-bottom: 24px; border-radius: 4px;">
                <p style="margin: 0;"><strong>📊 Resumen:</strong> Se detectaron <strong>{len(proyectos_nuevos)}</strong> nuevo(s) proyecto(s) aprobado(s)</p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #1e40af;">Fecha: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Proyectos Detectados</h2>
    """
    
    # Proyectos
    for proyecto in proyectos_nuevos:
        html += format_project_html(proyecto)
    
    # Footer
    html += f"""
            <div class="footer">
                <p style="margin: 0;">Este es un mensaje automático del sistema de monitoreo SEIA</p>
                <p style="margin: 8px 0 0 0;">No responder a este correo</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


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
    if not config.EMAIL_HOST or not config.EMAIL_USER:
        logger.warning("Configuración de email incompleta")
        return False
    
    if not proyectos_nuevos:
        logger.info("No hay proyectos nuevos para notificar")
        return True
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = config.EMAIL_FROM
        msg['To'] = config.EMAIL_TO
        msg['Subject'] = f"🎉 {len(proyectos_nuevos)} Nuevo(s) Proyecto(s) Aprobado(s) - SEIA"
        
        # Crear cuerpo HTML
        timestamp = datetime.now()
        html_body = create_email_body(proyectos_nuevos, timestamp)
        
        # Crear parte texto plano (fallback)
        text_body = f"""
Nuevos Proyectos Aprobados - SEIA

Se detectaron {len(proyectos_nuevos)} nuevo(s) proyecto(s) aprobado(s)
Fecha: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}

Proyectos:
"""
        for i, proyecto in enumerate(proyectos_nuevos, 1):
            text_body += f"\n{i}. {proyecto.nombre_proyecto}\n"
            text_body += f"   - Titular: {proyecto.titular or 'N/A'}\n"
            text_body += f"   - Región: {proyecto.region or 'N/A'}\n"
            text_body += f"   - Estado: {proyecto.estado}\n"
        
        # Adjuntar ambas partes
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # Conectar y enviar
        logger.info(f"Conectando a servidor SMTP: {config.EMAIL_HOST}:{config.EMAIL_PORT}")
        
        with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT, timeout=30) as server:
            if config.EMAIL_USE_TLS:
                logger.debug("Iniciando TLS")
                server.starttls()
            
            # Autenticación (solo si se proporciona password)
            if config.EMAIL_PASSWORD:
                logger.debug(f"Autenticando como {config.EMAIL_USER}")
                server.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            
            # Enviar
            logger.info(f"Enviando email a: {config.EMAIL_TO}")
            server.send_message(msg)
        
        logger.info(f"✓ Email enviado exitosamente con {len(proyectos_nuevos)} proyecto(s)")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Error de autenticación SMTP: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False

