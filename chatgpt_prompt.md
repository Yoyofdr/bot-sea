
# Contexto
Tengo un bot en Python (hosteado en un Droplet de Digital Ocean) que monitorea el SEIA (Sistema de Evaluación de Impacto Ambiental de Chile).
El flujo es:
1. Scrapea la lista de proyectos aprobados recientes usando `playwright`.
2. Para cada proyecto nuevo, entra a su ficha detallada (`fichaPrincipal.php`) para extraer: Resumen (Descripción), Monto de Inversión y Contactos (Titular/Rep. Legal).
3. Envía un email con estos detalles.

# El Problema
En mi entorno local (Mac), el script de scraping funciona **perfectamente**. Extrae todos los detalles, el monto y los correos de los titulares.
Sin embargo, en Producción (el servidor), el usuario final reporta que los correos siguen llegando **sin** esta información detallada (llegan vacíos o con datos faltantes), a pesar de que ya subí el código que arregla esto.

# Código Relevante
Esta es la función de scraping que funciona local pero falla en prod:

```python
def scrape_project_details(url: str, retry_count: int = 2) -> ProjectDetails:
    # ... configuración de playwright ...
    
    # FORZAR URL DE FICHA PRINCIPAL (Más robusta)
    if 'id_expediente=' in url:
        project_id_raw = url.split('id_expediente=')[1].split('&')[0]
        # Transformamos la URL a la vista "Ficha Principal" que tiene toda la info
        detail_url = f"https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php?modo=normal&id_expediente={project_id_raw}"
    
    page.goto(detail_url, wait_until='networkidle')
    
    # ESTRATEGIA DE EXTRACCIÓN
    # 1. Monto de Inversión (busca etiqueta h6 o texto cercano)
    monto_inversion = _extract_field_value(soup, "Monto de Inversión")
    
    # 2. Descripción (busca div con clase sg-description-file o contenedores de texto justificado)
    descripcion_completa = _extract_description(soup)
    
    # 3. Contactos (busca en acordeones o tablas)
    titular_info = _extract_contact_section(soup, "Titular")
    rep_legal_info = _extract_contact_section(soup, "Representante Legal")
    
    return ProjectDetails(...)
```

# Logs de Prueba Local (Exitosa)
Esto es lo que obtengo al correr el script de debug en mi máquina para un proyecto de HOY:
```
DETAILS_START_2167639261
Nombre: Conjunto Habitacional Altos de Valdivia
Monto: 16,7000 Millones de Dólares
Desc: El proyecto Conjunto Habitacional” Altos de Valdivia... (texto completo)
Titular: Constructora e Inmobiliaria DADELCO SPA
Email: fdd@dadelco.cl
RL Nombre: Fernando Ignacio Daettwyler De Laire
DETAILS_END_2167639261
```

# Pregunta
¿Por qué razón este scraper funcionaría 10/10 en local pero fallaría silenciosamente (o no extraería los datos) al correr en un servidor Linux (Digital Ocean)?
Considera:
1. ¿Podría el SEIA estar entregando un HTML diferente a las IPs de data centers (WAF/Anti-bot)?
2. ¿Hay alguna diferencia conocida en cómo `playwright` renderiza en modo `headless` en Linux vs Mac que afecte selectores de texto?
3. ¿Qué pasos de debugging me recomiendas para validar qué está viendo exactamente el servidor?
