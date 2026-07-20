"""Análisis determinista de cartas administrativas (TT-404).

Deliberadamente NO usa IA. El modelo solo transcribe (`explain_official_content`);
la clasificación de riesgo, la detección de plazos y la de datos sensibles se
hacen con reglas auditables aquí. Motivo (PRD §6.3 y §5.2 caso D): una
alucinación jamás debe poder rebajar el riesgo de un embargo ni inventar un
plazo. Ante la duda, este módulo escala el riesgo, nunca lo baja.
"""

import re
import unicodedata

# Términos que obligan a derivar a atención humana (PRD §5.2 caso D). No se
# ofrece nunca un recurso jurídico concreto: solo se avisa y se deriva.
_HIGH_RISK_TERMS = {
    "embargo": "embargo",
    "embargar": "embargo",
    "apremio": "apremio",
    "ejecutiva": "via_ejecutiva",
    "sancion": "sancion",
    "sancionador": "sancion",
    "multa": "sancion",
    "infraccion": "sancion",
    "recurso": "recurso",
    "alegaciones": "alegaciones",
    "requerimiento": "requerimiento",
    "desahucio": "desahucio",
    "denuncia": "denuncia",
    "juzgado": "via_judicial",
    "judicial": "via_judicial",
    "deuda": "deuda",
    "providencia": "providencia",
    "diligencia": "diligencia",
}

# Trámites ordinarios: no elevan el riesgo por sí solos.
_ROUTINE_TERMS = {"cita", "certificado", "renovacion", "informativa", "resolucion favorable"}

_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

_NUMBER_WORDS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "quince": 15,
    "veinte": 20, "treinta": 30,
}

# Plazo relativo explícito: "en el plazo de 15 días hábiles", "plazo de un mes".
_RELATIVE_DEADLINE_RE = re.compile(
    r"plazo\s+(?:m[aá]ximo\s+)?de\s+(\d{1,3}|" + "|".join(_NUMBER_WORDS) + r")\s+"
    r"(d[ií]as?|meses?|mes|a[nñ]os?)"
    r"(?:\s+(h[aá]biles?|naturales?))?",
    re.IGNORECASE,
)

# Fecha límite explícita: "antes del 30/09/2026", "hasta el 5 de octubre de 2026".
_ABSOLUTE_NUMERIC_RE = re.compile(
    r"(?:antes\s+del|hasta\s+el|fecha\s+l[ií]mite:?|no\s+m[aá]s\s+tarde\s+del)\s+"
    r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
    re.IGNORECASE,
)
_ABSOLUTE_TEXT_RE = re.compile(
    r"(?:antes\s+del|hasta\s+el|fecha\s+l[ií]mite:?|no\s+m[aá]s\s+tarde\s+del)\s+"
    r"(\d{1,2})\s+de\s+(" + "|".join(_MONTHS) + r")\s+de\s+(\d{4})",
    re.IGNORECASE,
)

# Menciones vagas de plazo: se avisa de que existe, pero NO se da una fecha.
_VAGUE_DEADLINE_RE = re.compile(
    r"(?:a\s+la\s+mayor\s+brevedad|lo\s+antes\s+posible|plazo\s+establecido|"
    r"plazo\s+legalmente\s+previsto|en\s+breve|plazo\s+reglamentario|"
    r"conforme\s+a\s+la\s+normativa)",
    re.IGNORECASE,
)

# Datos sensibles: se detecta su PRESENCIA y su tipo, nunca el valor.
_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("dni", re.compile(r"\b\d{8}[A-Za-z]\b")),
    ("nie", re.compile(r"\b[XYZxyz]\d{7}[A-Za-z]\b")),
    ("iban", re.compile(r"\b[A-Za-z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,5}\b")),
    ("telefono", re.compile(r"\b(?:\+34[\s-]?)?[6-9]\d{2}[\s-]?\d{3}[\s-]?\d{3}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("importe", re.compile(r"\b\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?\s?€")),
    (
        "expediente",
        re.compile(r"\bexpediente\s*(?:n[ºo°]\.?|n[uú]mero)?\s*[:\s]\s*[\w/-]{4,}", re.I),
    ),
]

# Palabras de membrete. Se recorren las líneas en orden y gana la primera que
# contenga alguna: en una carta oficial el emisor va en la cabecera. Los
# términos genéricos ("delegación") van al final porque suelen ser la segunda
# línea ("Agencia Estatal…" / "Delegación de Castellón") y no el emisor.
_ORGANISMO_TERMS = [
    "ayuntamiento",
    "generalitat",
    "conselleria",
    "agencia estatal",
    "agencia tributaria",
    "seguridad social",
    "tesoreria",
    "diputacion",
    "ministerio",
    "direccion general",
    "instituto nacional",
    "servicio publico",
    "jefatura",
    "subdelegacion",
    "delegacion",
]
_MAX_ORGANISMO_CHARS = 120


def _normalize(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in lowered if not unicodedata.combining(c))


def detect_sensitive_data(text: str) -> list[str]:
    """Tipos de dato sensible presentes. NUNCA devuelve los valores."""
    return sorted({name for name, pattern in _SENSITIVE_PATTERNS if pattern.search(text)})


def detect_organismo(text: str) -> str | None:
    """Emisor de la carta: primera línea del membrete con un término oficial."""
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line or len(line) > _MAX_ORGANISMO_CHARS:
            continue
        normalized = _normalize(line)
        if any(term in normalized for term in _ORGANISMO_TERMS):
            return line
    return None


def detect_deadlines(text: str) -> tuple[list[str], bool]:
    """Plazos inequívocos y si además hay menciones vagas de plazo.

    Solo se devuelve un plazo cuando el texto lo dice de forma explícita
    (PRD §5.2: "identifica plazos solo cuando aparecen inequívocamente").
    Un "a la mayor brevedad" no es un plazo: se marca como ambiguo para que
    la interfaz recomiende confirmarlo con una persona.
    """
    deadlines: list[str] = []

    for match in _ABSOLUTE_NUMERIC_RE.finditer(text):
        day, month, year = match.groups()
        deadlines.append(f"{int(day):02d}/{int(month):02d}/{year}")

    for match in _ABSOLUTE_TEXT_RE.finditer(text):
        day, month_name, year = match.groups()
        month = _MONTHS[_normalize(month_name)]
        deadlines.append(f"{int(day):02d}/{month:02d}/{year}")

    for match in _RELATIVE_DEADLINE_RE.finditer(text):
        amount_raw, unit, qualifier = match.groups()
        amount = (
            int(amount_raw)
            if amount_raw.isdigit()
            else _NUMBER_WORDS[_normalize(amount_raw)]
        )
        unit_norm = _normalize(unit)
        if unit_norm.startswith("dia"):
            unit_label = "días"
        elif unit_norm.startswith("mes"):
            unit_label = "meses" if amount > 1 else "mes"
        else:
            unit_label = "años" if amount > 1 else "año"
        text_deadline = f"{amount} {unit_label}"
        if qualifier:
            text_deadline += f" {_normalize(qualifier).replace('habiles', 'hábiles')}"
        deadlines.append(text_deadline)

    has_vague = bool(_VAGUE_DEADLINE_RE.search(text))
    # Dedup conservando el orden de aparición.
    return list(dict.fromkeys(deadlines)), has_vague


def detect_risk_terms(text: str) -> list[str]:
    """Categorías de riesgo presentes, deduplicadas."""
    normalized = _normalize(text)
    found = {
        category
        for term, category in _HIGH_RISK_TERMS.items()
        if re.search(rf"\b{term}\w*\b", normalized)
    }
    return sorted(found)


def assess(text: str) -> dict:
    """Análisis completo y determinista de la carta.

    Devuelve riesgo alto si aparece cualquier término de la lista o si hay un
    plazo ambiguo (PRD §5.2 incluye "plazos dudosos" como motivo de derivar).
    """
    risk_terms = detect_risk_terms(text)
    deadlines, ambiguous_deadline = detect_deadlines(text)
    sensitive = detect_sensitive_data(text)

    high_risk = bool(risk_terms) or ambiguous_deadline
    return {
        "risk_level": "high" if high_risk else "normal",
        "risk_terms": risk_terms,
        "deadlines": deadlines,
        "ambiguous_deadline": ambiguous_deadline,
        "sensitive_data": sensitive,
        "organismo": detect_organismo(text),
        "recommend_human": high_risk,
    }
