"""Gateway mock: clasificación de intención por palabras clave, determinista.

Sirve para desarrollar y probar el kiosco sin ningún proveedor de IA. El texto
del ciudadano no se registra ni se conserva: entra, se clasifica y se descarta.
"""

import base64
import binascii
import re
import unicodedata

from .base import (
    AudioRequest,
    DocumentRequest,
    DocumentResult,
    ExplainRequest,
    ExplainResult,
    IntentRequest,
    IntentResult,
    RawExtractedField,
    TranscriptResult,
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
        "padron.certificado",
    ),
    (
        r"\b(tarjeta sanitaria|targeta sanitaria|sip)\b",
        "RENEW_HEALTH_CARD",
        "sacyl.health.card",
    ),
    (
        r"\b(medic\w*|metge\w*|salud|salut|doctor\w*|ambulatori\w*|centro de salud)\b",
        "BOOK_HEALTH_APPOINTMENT",
        "sacyl.health.primary-care",
    ),
    (
        r"\b(itv|inspeccion tecnica|inspeccio tecnica)\b",
        "BOOK_ITV_APPOINTMENT",
        "jcyl.itv.info",
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
        "jcyl.itv.info",
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


# Transcripciones sintéticas para el flujo de voz. Frases que un ciudadano
# diría de verdad ante el tótem, para que el buscador tenga algo que clasificar.
_SYNTHETIC_TRANSCRIPTS: dict[str, list[dict]] = {
    "es": [
        {"text": "quiero pedir cita para el médico", "confidence": 0.94},
        {"text": "necesito renovar el dni", "confidence": 0.91},
        {"text": "tengo que pasar la itv del coche", "confidence": 0.89},
        # Confianza baja a propósito: ejercita el aviso de repetir.
        {"text": "eeeh… no sé… una cosa del…", "confidence": 0.38},
    ],
    "ca-valencia": [
        {"text": "vull demanar cita amb el metge", "confidence": 0.93},
        {"text": "necessite renovar el dni", "confidence": 0.90},
        {"text": "he de passar la itv del cotxe", "confidence": 0.88},
        {"text": "eeeh… no sé… una cosa del…", "confidence": 0.36},
    ],
}

# Cartas sintéticas para el explicador (TT-404). Todos los datos son
# inventados: NIF de prueba, expedientes ficticios e importes de ejemplo.
_SYNTHETIC_LETTERS: list[dict] = [
    {
        # Riesgo alto + plazo relativo explícito.
        "organismo": "Agencia Tributaria",
        "confidence": 0.88,
        "text": (
            "AGENCIA ESTATAL DE ADMINISTRACIÓN TRIBUTARIA\n"
            "Delegación de Castellón\n\n"
            "Expediente: 2026/EJ/004521\n"
            "Interesado: PERSONA SINTÉTICA DEMO, DNI 12345678Z\n\n"
            "PROVIDENCIA DE APREMIO\n\n"
            "Se comunica que, no habiéndose satisfecho la deuda en periodo "
            "voluntario, se ha dictado providencia de apremio por importe de "
            "1.240,50 €, iniciándose la vía ejecutiva.\n\n"
            "Podrá interponer recurso de reposición en el plazo de un mes "
            "contado desde el día siguiente a la notificación. De no atender "
            "este requerimiento se procederá al embargo de bienes.\n"
        ),
    },
    {
        # Carta rutinaria: sin riesgo, con fecha explícita de cita.
        "organismo": "Conselleria de Sanidad",
        "confidence": 0.91,
        "text": (
            "CONSELLERIA DE SANIDAD UNIVERSAL Y SALUD PÚBLICA\n"
            "Departamento de Salud de Castellón\n\n"
            "Estimado usuario:\n\n"
            "Le informamos de que su cita de revisión ha quedado asignada en el "
            "Centro de Salud Gran Vía. Debe presentarse hasta el 30/09/2026 "
            "aportando su tarjeta SIP.\n\n"
            "Si no puede acudir, puede anular la cita por teléfono en el "
            "960 123 456 o a través del Portal del Paciente.\n"
        ),
    },
    {
        # Plazo ambiguo: menciona plazo pero sin fecha -> debe derivar a humano.
        "organismo": "Ayuntamiento de Castelló de la Plana",
        "confidence": 0.83,
        "text": (
            "AYUNTAMIENTO DE CASTELLÓ DE LA PLANA\n"
            "Servicio de Gestión Tributaria\n\n"
            "Expediente: 2026/URB/00871\n\n"
            "Se le comunica que debe aportar la documentación que falta en su "
            "solicitud a la mayor brevedad, conforme a la normativa vigente.\n\n"
            "Puede presentarla en el registro municipal o en la sede "
            "electrónica del Ayuntamiento.\n"
        ),
    },
    {
        # Foto ilegible: confianza por debajo del umbral -> no se interpreta.
        "organismo": None,
        "confidence": 0.31,
        "text": "...ilegible...",
    },
]


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

    async def transcribe(self, request: AudioRequest) -> TranscriptResult:
        """Transcripción SINTÉTICA: ignora el audio (no hay STT sin proveedor).

        Rota entre frases típicas para poder ejercitar el flujo completo
        —grabar, ver la transcripción, confirmarla o borrarla— y para que el
        buscador reciba texto que sus reglas sí reconocen. Una de las frases
        llega con confianza baja a propósito, para probar el aviso de repetir.
        """
        try:
            size = len(base64.b64decode(request.audio_base64, validate=True))
        except (binascii.Error, ValueError):
            size = len(request.audio_base64)
        samples = _SYNTHETIC_TRANSCRIPTS[request.language]
        return TranscriptResult(**samples[size % len(samples)])

    async def explain_official_content(self, request: ExplainRequest) -> ExplainResult:
        """Transcripción SINTÉTICA: ignora la imagen (no hay OCR sin modelo de
        visión). Rota entre cartas de ejemplo según el tamaño en bytes de la
        imagen, para poder ejercitar los distintos caminos del análisis
        —riesgo alto, rutinaria, plazo ambiguo e ilegible— sin depender de un
        proveedor. Se usa la longitud DECODIFICADA y no la del base64 porque
        esta última es siempre múltiplo de 4 y devolvería siempre la misma."""
        try:
            size = len(base64.b64decode(request.image_base64, validate=True))
        except (binascii.Error, ValueError):
            size = len(request.image_base64)
        sample = _SYNTHETIC_LETTERS[size % len(_SYNTHETIC_LETTERS)]
        return ExplainResult(
            text=sample["text"],
            organismo=sample["organismo"],
            confidence=sample["confidence"],
        )
