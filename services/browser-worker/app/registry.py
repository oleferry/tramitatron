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
        field_map={"license_plate": "matricula", "vehicle_type": "tipo"},
        handoff_signals=("captcha", "name=\"enviar\""),
        enabled=True,
    )
    # Portales reales: declarados y DESACTIVADOS (ver docstring).
    sitval = PortalSpec(
        connector="sitval.itv.appointment",
        hosts=("sitval.com", "www.sitval.com"),
        start_url="https://sitval.com/",
        field_map={"license_plate": "matricula", "vehicle_type": "tipo"},
        handoff_signals=("captcha",),
        enabled=False,
    )
    gva = PortalSpec(
        connector="gva.health.primary-care.appointment",
        hosts=("www.san.gva.es", "sede.gva.es"),
        start_url="https://www.san.gva.es/es/web/portal-del-paciente",
        field_map={"sip_number": "sip", "birth_date": "fnac"},
        handoff_signals=("captcha", "cl@ve", "clave"),
        enabled=False,
    )
    return {s.connector: s for s in (demo, sitval, gva)}
