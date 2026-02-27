"""
Seeds para el panel de monitoreo.
"""

from seia_monitor.storage import SEIAStorage

# Fuente: https://www.bye.cl/equipo/?laywer=&position=abogado_socio (páginas 1 y 2)
BYE_SOCIOS = [
    ("Errázuriz Grez, José Tomás", "jerrazuriz@bye.cl"),
    ("Barros Tocornal, Cristián", "cbarros@bye.cl"),
    ("Guerrero Valenzuela, Pablo", "pguerrero@bye.cl"),
    ("Ovalle Irarrázaval, José Ignacio", "jiovalle@bye.cl"),
    ("Ducci González, Carlos", "cducci@bye.cl"),
    ("Toro Bossay, Luis Eduardo", "ltoro@bye.cl"),
    ("Vásquez Maldonado, Emilio", "evasquez@bye.cl"),
    ("Letelier Herrera, Luis Alberto", "lletelier@bye.cl"),
    ("Balmaceda Jimeno, Nicolás", "nbalmaceda@bye.cl"),
    ("Simian Soza, Bernardo", "bsimian@bye.cl"),
    ("Trucco Horwitz, Carola", "ctrucco@bye.cl"),
    ("Barros Echeverría, Víctor", "vbarros@bye.cl"),
    ("Ruiz-Tagle Ramírez, Oscar", "oruiztagle@bye.cl"),
    ("Solórzano Báez, Patricio", "psolorzano@bye.cl"),
    ("Iturrate Alvarado, Juan Cristóbal", "jiturrate@bye.cl"),
    ("Garrido Capdevila, Fernando", "fgarrido@bye.cl"),
    ("Díaz Velásquez, Javier", "jdiaz@bye.cl"),
    ("Cademartori Gamboa, David", "dcademartori@bye.cl"),
    ("San Martín Arjona, Javier", "jsanmartin@bye.cl"),
    ("De la Barra Gili, Francisco", "fdelabarra@bye.cl"),
    ("Eguiguren Ebensperger, Sergio", "seguiguren@bye.cl"),
    ("Barros Vial, Enrique", "ebarros@bye.cl"),
    ("Cordero Becker, Vicente", "vcordero@bye.cl"),
    ("Corvalán Pérez, José Luis", "jcorvalan@bye.cl"),
    ("Bórquez Electorat, Francisco", "fborquez@bye.cl"),
    ("Allende Destuet, Felipe", "fallende@bye.cl"),
    ("Pellegrini Munita, Cristóbal", "cpellegrini@bye.cl"),
    ("Rivera Ruz, María Olga", "mrivera@bye.cl"),
    ("Kovacevic Yáñez, Tomás", "tkovacevic@bye.cl"),
    ("Marinovic Carrasco, Lucas", "lmarinovic@bye.cl"),
    ("Espinosa Meza, María Fernanda", "mfespinosa@bye.cl"),
    ("Rodríguez Ariztía, Andrés", "arodriguez@bye.cl"),
    ("Ovalle Vergara, Diego", "dovalle@bye.cl"),
]


def seed_bye_socios(storage: SEIAStorage) -> int:
    """
    Inserta/actualiza socios de ByE en la tabla de responsables.
    Retorna cantidad de registros procesados.
    """
    for nombre, email in BYE_SOCIOS:
        storage.upsert_lawyer(nombre=nombre, email=email, active=True)
    return len(BYE_SOCIOS)
