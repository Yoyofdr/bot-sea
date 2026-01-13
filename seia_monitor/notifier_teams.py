"""
Notificador para Microsoft Teams usando Incoming Webhooks.
Envía mensajes formateados con proyectos nuevos y cambios relevantes.
"""

import json
import time
import requests
from datetime import datetime
from typing import Optional

from seia_monitor.config import Config
from seia_monitor.logger import get_logger
from seia_monitor.models import Project, ChangeEvent, ChangeResult

logger = get_logger("notifier_teams")


# Límite de tamaño de mensaje para Teams (aprox 28KB)
MAX_MESSAGE_SIZE = 28 * 1024


def format_teams_message(
    changes: ChangeResult,
    stats: Optional[dict] = None,
    date: Optional[datetime] = None
) -> dict:
    """
    Formatea un mensaje para Teams con Adaptive Card simple.
    
    Args:
        changes: Resultado de cambios detectados
        stats: Estadísticas adicionales (opcional)
        date: Fecha del reporte (default: hoy)
    
    Returns:
        Diccionario con el payload del mensaje
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    
    # Construir texto del mensaje
    lines = [
        f"📊 **SEIA - Monitoreo Diario ({date_str})**",
        "─" * 40,
        ""
    ]
    
    # Nuevos proyectos
    if changes.nuevos:
        lines.append(f"🆕 **Nuevos Proyectos ({len(changes.nuevos)})**")
        lines.append("")
        
        # Limitar a top N si hay muchos
        max_items = 20
        items_to_show = changes.nuevos[:max_items]
        
        for project in items_to_show:
            lines.append(f"• **{project.nombre_proyecto}**")
            if project.region:
                lines.append(f"  Región: {project.region} | Estado: {project.estado}")
            else:
                lines.append(f"  Estado: {project.estado}")
            
            if project.url_detalle:
                lines.append(f"  🔗 [Ver detalle]({project.url_detalle})")
            
            lines.append("")
        
        if len(changes.nuevos) > max_items:
            remaining = len(changes.nuevos) - max_items
            lines.append(f"_... y {remaining} proyectos nuevos más_")
            lines.append("")
    
    # Cambios relevantes de estado
    if changes.cambios_relevantes:
        lines.append(f"🔄 **Cambios Relevantes de Estado ({len(changes.cambios_relevantes)})**")
        lines.append("")
        
        max_items = 20
        items_to_show = changes.cambios_relevantes[:max_items]
        
        for change in items_to_show:
            lines.append(f"• **{change.nombre_proyecto}**")
            lines.append(f"  {change.estado_anterior} → **{change.estado_nuevo}**")
            
            if change.region:
                lines.append(f"  Región: {change.region}")
            
            # Si hay detalles disponibles, incluirlos
            if change.details:
                details = change.details
                
                # Tipo de proyecto
                if details.tipo_proyecto and details.tipo_proyecto != "No disponible":
                    lines.append(f"  📋 Tipo: {details.tipo_proyecto}")
                
                # Monto de inversión (destacado)
                if details.monto_inversion:
                    lines.append(f"  💰 **Monto: {details.monto_inversion}**")
                
                # Descripción (resumida)
                if details.descripcion_completa:
                    desc = details.descripcion_completa
                    if len(desc) > 500:
                        desc = desc[:500] + "..."
                    lines.append(f"  📄 Descripción: {desc}")
                
                # Titular
                if details.titular_nombre:
                    titular_info = f"  🏢 Titular: {details.titular_nombre}"
                    if details.titular_email:
                        titular_info += f" ({details.titular_email})"
                    lines.append(titular_info)
                
                # Representante Legal
                if details.rep_legal_nombre:
                    rep_info = f"  👤 Rep. Legal: {details.rep_legal_nombre}"
                    if details.rep_legal_email:
                        rep_info += f" ({details.rep_legal_email})"
                    lines.append(rep_info)
            
            if change.url_detalle:
                lines.append(f"  🔗 [Ver detalle completo]({change.url_detalle})")
            
            lines.append("")
        
        if len(changes.cambios_relevantes) > max_items:
            remaining = len(changes.cambios_relevantes) - max_items
            lines.append(f"_... y {remaining} cambios más_")
            lines.append("")
    
    # Sin cambios
    if not changes.has_changes():
        lines.append("✅ Sin cambios relevantes en esta corrida.")
        lines.append("")
    
    # Footer con estadísticas
    if stats:
        duration = stats.get('duration_seconds', 0)
        total = stats.get('total_projects', 0)
        pages = stats.get('pages_scraped', 0)
        method = stats.get('scrape_method', 'unknown')
        
        lines.append("─" * 40)
        lines.append(
            f"⏱️ Corrida completada en {duration:.1f}s | "
            f"{total} proyectos monitoreados | "
            f"{pages} página(s) | "
            f"Método: {method}"
        )
    
    message_text = "\n".join(lines)
    
    # Formato MessageCard (compatible con webhooks de Teams)
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"SEIA Monitoreo - {date_str}",
        "themeColor": "0078D4" if changes.has_changes() else "00AA00",
        "title": f"SEIA Monitoreo Diario - {date_str}",
        "text": message_text
    }
    
    return payload


def send_teams_notification(
    webhook_url: str,
    changes: ChangeResult,
    stats: Optional[dict] = None,
    retry: bool = True
) -> bool:
    """
    Envía notificación a Teams vía webhook.
    
    Args:
        webhook_url: URL del webhook de Teams
        changes: Resultado de cambios detectados
        stats: Estadísticas adicionales (opcional)
        retry: Si True, reintenta en caso de fallo
    
    Returns:
        True si se envió exitosamente
    """
    if not webhook_url:
        logger.error("No se configuró TEAMS_WEBHOOK_URL")
        return False
    
    if not changes.has_changes():
        logger.info("No hay cambios relevantes, omitiendo notificación")
        return True
    
    # Formatear mensaje
    try:
        payload = format_teams_message(changes, stats)
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        # Verificar tamaño
        if len(payload_json.encode('utf-8')) > MAX_MESSAGE_SIZE:
            logger.warning(
                f"Mensaje muy grande ({len(payload_json)} bytes), "
                "se truncará automáticamente"
            )
            # El formato ya limita a top 20, así que debería estar bien
    
    except Exception as e:
        logger.error(f"Error formateando mensaje: {e}")
        return False
    
    # Enviar con reintentos
    max_attempts = 3 if retry else 1
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Enviando notificación a Teams (intento {attempt + 1}/{max_attempts})")
            
            response = requests.post(
                webhook_url,
                headers={
                    'Content-Type': 'application/json; charset=utf-8'
                },
                data=payload_json.encode('utf-8'),
                timeout=30
            )
            
            # Manejar respuestas
            if response.status_code == 200:
                logger.info("✓ Notificación enviada exitosamente a Teams")
                return True
            
            elif response.status_code == 429:
                # Rate limit
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit (429), esperando {retry_after}s")
                if attempt < max_attempts - 1:
                    time.sleep(retry_after)
                    continue
            
            elif response.status_code >= 500:
                # Error del servidor
                logger.warning(f"Error del servidor ({response.status_code})")
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    time.sleep(wait_time)
                    continue
            
            else:
                # Otro error
                logger.error(
                    f"Error enviando a Teams: {response.status_code} - {response.text}"
                )
                return False
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout en intento {attempt + 1}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a Teams: {e}")
            if attempt < max_attempts - 1:
                time.sleep(2)
    
    logger.error("Falló el envío de notificación a Teams después de todos los intentos")
    return False


def test_teams_webhook(webhook_url: str) -> bool:
    """
    Envía un mensaje de prueba al webhook de Teams.
    
    Args:
        webhook_url: URL del webhook
    
    Returns:
        True si funciona correctamente
    """
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "SEIA Monitor - Test",
        "themeColor": "0078D4",
        "title": "🧪 SEIA Monitor - Test de Webhook",
        "text": "Este es un mensaje de prueba del sistema de monitoreo SEIA.\n\n✅ Si recibes este mensaje, el webhook está funcionando correctamente."
    }
    
    try:
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info("✓ Webhook de Teams funciona correctamente")
            return True
        else:
            logger.error(f"Error en webhook: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error probando webhook: {e}")
        return False

