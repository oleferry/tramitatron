"""Contrato del conector de trámites (PRD §12.3, simplificado para el hito 1).

Los conectores reales (GVA Salud, SITVAL) NO se implementan hasta que el núcleo
y las pruebas de privacidad estén completos. Solo existe el conector mock.
"""

from typing import Literal, Protocol

from pydantic import BaseModel


class ExecutionResult(BaseModel):
    status: Literal["completed", "failed", "user_handoff"]
    receipt: dict[str, str] | None = None
    # Mensaje PARA EL CIUDADANO: amable y genérico. Nunca lleva detalle técnico.
    message: str | None = None
    # Detalle TÉCNICO del fallo para soporte (código HTTP, tipo de excepción,
    # estado del worker). Alimenta el `technical_error` de la incidencia, que la
    # capa de redacción conserva de forma segura (PRD §13.4). El kiosco NO lo
    # muestra. Los conectores solo deben poner aquí info técnica, jamás datos de
    # la persona: es un canal de diagnóstico, no de negocio.
    technical_detail: str | None = None
    # Código de incidencia anónimo (TT-603, PRD §5): al fallar un trámite, el
    # servidor abre una incidencia y devuelve su código para que el kiosco lo
    # muestre y el ciudadano pueda citarlo en soporte.
    incident_code: str | None = None


class HealthcheckResult(BaseModel):
    connector: str
    healthy: bool
    detail: str | None = None


class TransactionConnector(Protocol):
    name: str

    async def execute(self, data: dict[str, str], confirmed: bool) -> ExecutionResult: ...

    async def healthcheck(self) -> HealthcheckResult: ...
