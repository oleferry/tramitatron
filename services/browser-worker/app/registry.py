"""Registro de portales y allowlist (TT-502: allowlist; regla 7 del §30).

Un conector solo puede navegar los hosts declarados aquí. El worker nunca
abre una URL arbitraria: si el host de la URL no está en `hosts`, se rechaza.

Los conectores de portales reales (GVA Salud, SITVAL) se declaran para dejar
la estructura lista, pero nacen DESACTIVADOS: dirigir la automatización a un
portal real de la administración está sujeto a las pruebas de privacidad y a la
EIPD (CLAUDE.md y PRD §5.4), y además esos portales exigen CAPTCHA/Cl@ve, que no
se automatizan. Mientras `enabled` sea falso, `prepare` responde "unavailable".
"""

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True)
class PortalSpec:
    connector: str
    # Host(s) permitidos para este conector. Allowlist estricta.
    hosts: tuple[str, ...]
    # URL de inicio del trámite (dentro de la allowlist).
    start_url: str
    # Campo lógico (el que usa Tramitatrón) -> nombre del campo en el formulario.
    field_map: dict[str, str] = field(default_factory=dict)
    # Señales de que toca ceder a la persona: texto/atributo que, si aparece,
    # marca el punto de handoff (CAPTCHA, botón de envío…).
    handoff_signals: tuple[str, ...] = ()
    enabled: bool = False

    def allows(self, url: str) -> bool:
        return urlparse(url).hostname in self.hosts


# La autoridad del portal de pruebas (host o host:port) se inyecta al construir
# el registro, para que funcione con servidor real (Playwright) o con transporte
# ASGI en tests. La allowlist compara por hostname, sin puerto.
def build_registry(portal_authority: str) -> dict[str, PortalSpec]:
    portal_host = urlparse(f"http://{portal_authority}").hostname or portal_authority
    demo = PortalSpec(
        connector="demo.worker.appointment",
        hosts=(portal_host,),
        start_url=f"http://{portal_authority}/portal/cita",
        # Campo lógico de Tramitatrón -> nombre del campo en el asistente. Cubre
        # los cuatro pasos (servicio, oficina, fecha/hora, datos personales). El
        # worker rellena en cada página los que estén presentes y avanza.
        field_map={
            "service": "servicio",
            "office": "oficina",
            "date": "fecha",
            "time": "hora",
            "full_name": "nombre",
            "dni_number": "dni",
            "phone": "telefono",
        },
        handoff_signals=("captcha", "cl@ve", "clave"),
        enabled=True,
    )
    # Portal real: declarado y DESACTIVADO (ver docstring). Sacyl (cita de
    # atención primaria en Castilla y León); se habilitará tras la EIPD.
    sacyl = PortalSpec(
        connector="sacyl.health.primary-care",
        hosts=("www.saludcastillayleon.es", "cita.saludcastillayleon.es"),
        start_url="https://cita.saludcastillayleon.es/",
        field_map={"health_card_number": "tarjeta", "birth_date": "fnac"},
        handoff_signals=("captcha", "cl@ve", "clave"),
        enabled=False,
    )
    return {s.connector: s for s in (demo, sacyl)}
