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
    Formatea un proyecto como HTML para el email siguiendo el diseño ejecutivo minimalista
    y compatible con Outlook (basado en tablas).
    """
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

    url_ficha = project.url_detalle or '#'

    return f"""
              <!-- INICIO BLOQUE PROYECTO -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0; padding:0;">
                <tr>
                  <td style="padding:0 0 24px 0; font-family:Arial, Helvetica, sans-serif;">
                    <div style="font-size:26px; font-weight:800; color:#111827; line-height:1.2;">
                      {project.nombre_proyecto}
                    </div>
                  </td>
                </tr>

                <!-- Key Facts Card (fondo gris) -->
                <tr>
                  <td bgcolor="#f9fafb" style="background-color:#f9fafb; padding:20px; border:1px solid #f3f4f6;">
                    <!-- Badge -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td bgcolor="#5FA91D" style="background-color:#5FA91D; padding:4px 10px;">
                          <div style="font-family:Arial, Helvetica, sans-serif; font-size:11px; font-weight:700; color:#ffffff; letter-spacing:0.02em; text-transform:uppercase;">
                            {project.estado}
                          </div>
                        </td>
                      </tr>
                    </table>

                    <!-- Spacer -->
                    <div style="height:12px; line-height:12px; font-size:12px;">&nbsp;</div>

                    <!-- Facts grid (2 columnas) -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td width="50%" valign="top" style="padding:0 8px 16px 0;">
                          <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;">
                            Monto Inversión
                          </div>
                          <div style="font-size:14px; color:#374151; padding-top:2px;">
                            {monto}
                          </div>
                        </td>
                        <td width="50%" valign="top" style="padding:0 0 16px 8px;">
                          <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;">
                            Región
                          </div>
                          <div style="font-size:14px; color:#374151; padding-top:2px;">
                            {project.region or 'N/A'}
                          </div>
                        </td>
                      </tr>

                      <tr>
                        <td width="50%" valign="top" style="padding:0 8px 0 0;">
                          <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;">
                            Tipo
                          </div>
                          <div style="font-size:14px; color:#374151; padding-top:2px;">
                            {project.tipo or 'N/A'}
                          </div>
                        </td>
                        <td width="50%" valign="top" style="padding:0 0 0 8px;">
                          <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;">
                            Fecha Ingreso
                          </div>
                          <div style="font-size:14px; color:#374151; padding-top:2px;">
                            {project.fecha_ingreso or 'N/A'}
                          </div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- Sección Resumen -->
                <tr>
                  <td style="padding:32px 0 12px 0;">
                    <div style="font-size:14px; font-weight:800; color:#4b5563; letter-spacing:0.10em; text-transform:uppercase; padding-bottom:6px; border-bottom:2px solid #f3f4f6; font-family:Arial, Helvetica, sans-serif;">
                      Resumen del Proyecto
                    </div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 0 8px 0; font-family:Arial, Helvetica, sans-serif;">
                    <div style="font-size:15px; color:#4b5563; white-space:pre-line;">
                      {resumen}
                    </div>
                  </td>
                </tr>

                <!-- Sección Contacto -->
                <tr>
                  <td style="padding:24px 0 12px 0;">
                    <div style="font-size:14px; font-weight:800; color:#4b5563; letter-spacing:0.10em; text-transform:uppercase; padding-bottom:6px; border-bottom:2px solid #f3f4f6; font-family:Arial, Helvetica, sans-serif;">
                      Información de Contacto
                    </div>
                  </td>
                </tr>

                <tr>
                  <td style="padding:0;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <!-- Titular -->
                        <td width="48%" valign="top" style="padding:0;">
                          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                 style="border:1px solid #f3f4f6; background-color:#ffffff;">
                            <tr>
                              <td style="padding:16px; font-family:Arial, Helvetica, sans-serif;">
                                <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; margin-bottom:4px;">
                                  Titular
                                </div>
                                <div style="font-size:14px; font-weight:800; color:#111827; margin-bottom:2px;">
                                  {titular_n}
                                </div>
                                <a href="mailto:{titular_e}" style="font-size:13px; color:#5FA91D; text-decoration:none;">
                                  {titular_e}
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>

                        <td width="4%">&nbsp;</td>

                        <!-- Rep Legal -->
                        <td width="48%" valign="top" style="padding:0;">
                          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                                 style="border:1px solid #f3f4f6; background-color:#ffffff;">
                            <tr>
                              <td style="padding:16px; font-family:Arial, Helvetica, sans-serif;">
                                <div style="font-size:11px; color:#6b7280; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; margin-bottom:4px;">
                                  Rep. Legal
                                </div>
                                <div style="font-size:14px; font-weight:800; color:#111827; margin-bottom:2px;">
                                  {rep_n}
                                </div>
                                <a href="mailto:{rep_e}" style="font-size:13px; color:#5FA91D; text-decoration:none;">
                                  {rep_e}
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

                <!-- CTA -->
                <tr>
                  <td align="center" style="padding:40px 0 20px 0;">
                    <!-- Botón bulletproof (Outlook VML) -->
                    <!--[if mso]>
                      <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="{url_ficha}"
                        style="height:44px;v-text-anchor:middle;width:260px;" arcsize="12%" strokecolor="#5FA91D" fillcolor="#5FA91D">
                        <w:anchorlock/>
                        <center style="color:#ffffff;font-family:Arial, Helvetica, sans-serif;font-size:14px;font-weight:bold;">
                          VER FICHA COMPLETA
                        </center>
                      </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-- -->
                    <a href="{url_ficha}"
                      style="display:inline-block; background-color:#5FA91D; border:1px solid #5FA91D; color:#ffffff;
                             font-family:Arial, Helvetica, sans-serif; font-size:14px; font-weight:800;
                             text-decoration:none; padding:12px 32px; border-radius:6px;">
                      VER FICHA COMPLETA
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>

                <!-- Separador entre proyectos -->
                <tr>
                  <td style="padding:0 0 24px 0;">
                    <div style="height:1px; background-color:#f3f4f6; line-height:1px; font-size:1px;">&nbsp;</div>
                  </td>
                </tr>
              </table>
              <!-- FIN BLOQUE PROYECTO -->
    """


def create_email_body(proyectos_nuevos: list[Project], timestamp: datetime) -> str:
    """
    Crea el cuerpo del email en HTML con diseño ejecutivo minimalista y compatible con Outlook.
    """
    proyectos_html = ""
    for p in proyectos_nuevos:
        proyectos_html += format_project_html(p)

    if not proyectos_nuevos:
        proyectos_html = """
        <div style="padding: 32px; text-align: center; color: #6b7280; font-family: Arial, Helvetica, sans-serif;">
            <p style="font-size: 16px; margin: 0;">No se detectaron proyectos aprobados nuevos en esta revisión.</p>
        </div>
        """

    return f"""
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta http-equiv="x-ua-compatible" content="ie=edge">
      <title>SEIA - Novedades</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f9fafb;">
      <!-- Wrapper fondo -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f9fafb" style="background-color:#f9fafb;">
        <tr>
          <td align="center" style="padding:24px 12px;">

            <!-- Container 600 -->
            <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
                   style="width:600px; max-width:600px; background-color:#ffffff; border:1px solid #e5e7eb;">
              <tr>
                <td style="padding:32px; font-family:Arial, Helvetica, sans-serif; color:#111827; line-height:1.5;">
                  {proyectos_html}
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td bgcolor="#f9fafb" style="background-color:#f9fafb; padding:24px; text-align:center; border-top:1px solid #e5e7eb;
                                           font-family:Arial, Helvetica, sans-serif; font-size:12px; color:#9ca3af;">
                  Este es un mensaje automático del sistema de monitoreo SEIA.<br>
                  No responder a este correo electrónico.<br>
                  <span style="font-size:10px; display:block; margin-top:8px;">v2026.02.02.1</span>
                </td>
              </tr>
            </table>
            <!-- /Container -->

          </td>
        </tr>
      </table>
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
