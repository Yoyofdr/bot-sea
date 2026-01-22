
from seia_monitor.models import Project, ProjectDetails
from seia_monitor.notifier_email import create_email_body
from datetime import datetime

def generate_preview():
    # 1. Datos del proyecto
    project = Project(
        project_id="seia_2167572524",
        nombre_proyecto="Instalación de oficinas para Faena Minera",
        titular="Safka Elizabeth Abse Ávila",
        region="Región de Coquimbo",
        tipo="EIA",
        fecha_ingreso="Ingreso voluntario",
        estado="En Admisión",
        url_detalle="https://seia.sea.gob.cl/expediente/expedientesDetalle.php?id_expediente=2167572524"
    )
    
    # 2. Detalles (Simulados basados en la ficha real del SEIA)
    project.details = ProjectDetails(
        project_id="2167572524",
        nombre_completo="Instalación de oficinas para Faena Minera",
        tipo_proyecto="EIA",
        monto_inversion="0,0150 Millones de Dólares",
        descripcion_completa="El proyecto corresponde exclusivamente a la instalación de faenas consistentes en oficinas administrativas provisorias y servicios higiénicos para el personal que laborará en la construcción del proyecto minero, además de un área de almacenamiento de insumos y materiales. La instalación de faena ocupará una superficie de 0,5 hectáreas aproximadamente y contará con suministro de energía eléctrica mediante generador y agua potable mediante camión aljibe.",
        titular_nombre="Safka Elizabeth Abse Ávila",
        titular_email="absesafka@gmail.com",
        rep_legal_nombre=None,
        rep_legal_email=None
    )

    # 3. Generar HTML
    html = create_email_body([project], datetime.now())
    
    # 4. Guardar para previsualización
    with open("previsualizacion_correo.html", "w") as f:
        f.write(html)
    
    print("✅ Previsualización generada en 'previsualizacion_correo.html'")

if __name__ == "__main__":
    generate_preview()
