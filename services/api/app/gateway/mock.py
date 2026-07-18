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
    # (patrón, intent, procedure_id). El orden importa: gana la primera regla,
    # así que los patrones más específicos van antes que los genéricos.
    (
        r"\b(vida laboral|informe laboral|cotizacion\w*|cotitzacio\w*)\b",
        "REQUEST_WORK_HISTORY",
        "seg-social.tgss.vida-laboral",
    ),
    (
        r"\b(antecedentes|antecedents|penales|penals)\b",
        "REQUEST_CRIMINAL_RECORD",
        "mjusticia.antecedentes-penales",
    ),
    (
        r"\b(nacimiento|naixement|registro civil|registre civil)\b",
        "REQUEST_BIRTH_CERTIFICATE",
        "mjusticia.certificado-nacimiento",
    ),
    (
        r"\b(empadronamiento|empadronament|padron|padro|volante|volant)\b",
        "REQUEST_CENSUS_CERTIFICATE",
        "castello.padron.certificado",
    ),
    (
        r"\b(tarjeta sanitaria|targeta sanitaria|sip)\b",
        "RENEW_HEALTH_CARD",
        "gva.health.sip-renewal",
    ),
    (
        r"\b(medic\w*|metge\w*|salud|salut|doctor\w*|ambulatori\w*|centro de salud)\b",
        "BOOK_HEALTH_APPOINTMENT",
        "gva.health.primary-care.appointment",
    ),
    (
        r"\b(itv|inspeccion tecnica|inspeccio tecnica)\b",
        "BOOK_ITV_APPOINTMENT",
        "sitval.itv.appointment",
    ),
    (
        r"\b(carne\w? de conducir|carnet de conduir|permiso de conducir|permis de conduir"
        r"|trafico|transit|dgt|canje\w*|bescanvi\w*)\b",
        "BOOK_DGT_APPOINTMENT",
        "dgt.cita-previa",
    ),
    (
        r"\b(coche|cotxe|moto|vehicul\w*|vehicle)\b",
        "BOOK_ITV_APPOINTMENT",
        "sitval.itv.appointment",
    ),
    (
        r"\b(extranjeria|estrangeria|nie|tie|huellas|empremtes|residencia)\b",
        "BOOK_IMMIGRATION_APPOINTMENT",
        "mir.extranjeria.cita-previa",
    ),
    (
        r"\b(dni|documento nacional|pasaporte|passaport)\b",
        "BOOK_DNI_APPOINTMENT",
        "mir.dni.renewal-appointment",
    ),
    (
        r"\b(hacienda|hisenda|renta|renda|irpf|declaracion|declaracio|impuesto\w*"
        r"|impost\w*|agencia tributaria|tributari\w*)\b",
        "BOOK_TAX_APPOINTMENT",
        "aeat.cita-previa",
    ),
    (
        r"\b(paro|atur|desempleo|desocupacio|sepe|subsidio|subsidi)\b",
        "BOOK_SEPE_APPOINTMENT",
        "sepe.cita-previa",
    ),
    (
        r"\b(pension\w*|pensio\w*|jubilacion|jubilacio|viudedad|viudetat|viduitat"
        r"|incapacidad|incapacitat|seguridad social|seguretat social)\b",
        "BOOK_INSS_APPOINTMENT",
        "seg-social.inss.cita-previa",
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
