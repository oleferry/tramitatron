"""Gateway mock: clasificación de intención por palabras clave, determinista.

Sirve para desarrollar y probar el kiosco sin ningún proveedor de IA. El texto
del ciudadano no se registra ni se conserva: entra, se clasifica y se descarta.
"""

import re
import unicodedata

from .base import (
    DocumentRequest,
    DocumentResult,
    IntentRequest,
    IntentResult,
    RawExtractedField,
)

_RULES: list[tuple[str, str, str]] = [
    # (patrón, intent, procedure_id)
    (
        r"\b(medic\w*|metge\w*|salud|salut|doctor\w*|ambulatori\w*|centro de salud)\b",
        "BOOK_HEALTH_APPOINTMENT",
        "gva.health.primary-care.appointment",
    ),
    (
        r"\b(itv|vehicul\w*|vehicle|coche|cotxe|moto|inspeccion tecnica)\b",
        "BOOK_ITV_APPOINTMENT",
        "sitval.itv.appointment",
    ),
    (
        r"\b(demo|demostracion|demostracio|prueba|prova)\b",
        "DEMO_PROCEDURE",
        "demo.mock.appointment",
    ),
]

_CLARIFICATION = {
    "es": "No he entendido qué trámite necesitas. ¿Puedes decirlo con otras palabras?",
    "ca-valencia": "No he entés quin tràmit necessites. Pots dir-ho amb altres paraules?",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class MockModelGateway:
    async def classify_intent(self, request: IntentRequest) -> IntentResult:
        normalized = _normalize(request.text)
        for pattern, intent, procedure_id in _RULES:
            if re.search(pattern, normalized):
                return IntentResult(
                    intent=intent,
                    confidence=0.92,
                    procedure_id=procedure_id,
                    next_action="SHOW_PROCEDURE",
                )
        return IntentResult(
            intent="UNKNOWN",
            confidence=0.2,
            procedure_id=None,
            next_action="ASK_CLARIFICATION",
            clarification=_CLARIFICATION[request.language],
        )

    async def extract_document(self, request: DocumentRequest) -> DocumentResult:
        """Extracción SINTÉTICA: ignora la imagen y devuelve siempre los mismos
        datos ficticios. El campo birth_date llega con confianza baja a propósito
        para ejercitar el flujo de revisión obligatoria del kiosco."""
        name = RawExtractedField(
            field="full_name", value="PERSONA SINTÉTICA DEMO", confidence=0.95
        )
        synthetic: dict[str, list[RawExtractedField]] = {
            "dni": [
                RawExtractedField(field="dni_number", value="12345678Z", confidence=0.97),
                name,
                RawExtractedField(field="birth_date", value="1957-03-14", confidence=0.62),
            ],
            "sip_card": [
                RawExtractedField(field="sip_number", value="01234567", confidence=0.93),
                name,
            ],
        }
        return DocumentResult(
            document_class=request.document_class,
            fields=synthetic[request.document_class],
        )
