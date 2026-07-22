"""Redacción del error técnico de una incidencia (TT-603, PRD §13.3/§13.4).

Una incidencia guarda el error técnico para que soporte pueda diagnosticar,
pero el PRD prohíbe persistir datos personales (§13.4). Un mensaje de error
podría arrastrar PII sin querer ("fallo al enviar el DNI 12345678Z"), así que
antes de guardar NADA se redacta de forma determinista: se sustituyen los
patrones que huelen a dato personal por una etiqueta del tipo, nunca el valor.

Es defensa en profundidad: la fuente normal (mensajes de conector, excepciones
controladas) no debería llevar PII; esto garantiza que, si la lleva, no se
persiste. Ante la duda, redacta de más.
"""

import re

_MAX_LEN = 300

# El orden importa: primero los patrones específicos (email, IBAN, DNI/NIE),
# luego las secuencias largas de dígitos genéricas (teléfono, SIP, expediente).
# Los códigos de estado HTTP y tiempos cortos (3–4 cifras) se conservan: son
# útiles para diagnosticar y no identifican a nadie.
_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[correo]"),
    (re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?\d{4}){3,}\b"), "[iban]"),
    (re.compile(r"\b[XYZ]\d{7}[A-Za-z]\b", re.IGNORECASE), "[nie]"),
    (re.compile(r"\b\d{7,8}[A-Za-z]\b"), "[dni]"),
    (re.compile(r"\+\d[\d ]{7,}\d"), "[telefono]"),
    (re.compile(r"\b\d{9,}\b"), "[numero]"),
]


def redact(text: str | None) -> str:
    """Devuelve el mensaje sin datos personales, colapsado y acotado."""
    if not text:
        return "(sin detalle)"
    clean = " ".join(str(text).split())
    for pattern, replacement in _RULES:
        clean = pattern.sub(replacement, clean)
    if len(clean) > _MAX_LEN:
        clean = clean[:_MAX_LEN].rstrip() + "…"
    return clean or "(sin detalle)"
