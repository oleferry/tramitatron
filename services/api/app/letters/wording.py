"""Textos del explicador de cartas, en castellano y valenciano.

Están aquí y no en el modelo de IA a propósito: el mensaje que decide si una
persona busca ayuda ante un embargo no puede depender de una generación.
Ninguno de estos textos recomienda una actuación jurídica concreta.
"""

_RISK_LABELS: dict[str, dict[str, str]] = {
    "embargo": {"es": "un embargo", "ca-valencia": "un embargament"},
    "apremio": {
        "es": "un procedimiento de apremio",
        "ca-valencia": "un procediment de constrenyiment",
    },
    "via_ejecutiva": {"es": "la vía ejecutiva", "ca-valencia": "la via executiva"},
    "sancion": {"es": "una sanción o multa", "ca-valencia": "una sanció o multa"},
    "recurso": {"es": "un recurso", "ca-valencia": "un recurs"},
    "alegaciones": {"es": "alegaciones", "ca-valencia": "al·legacions"},
    "requerimiento": {"es": "un requerimiento", "ca-valencia": "un requeriment"},
    "desahucio": {"es": "un desahucio", "ca-valencia": "un desnonament"},
    "denuncia": {"es": "una denuncia", "ca-valencia": "una denúncia"},
    "via_judicial": {"es": "un asunto judicial", "ca-valencia": "un assumpte judicial"},
    "deuda": {"es": "una deuda", "ca-valencia": "un deute"},
    "providencia": {"es": "una providencia", "ca-valencia": "una provisió"},
    "diligencia": {"es": "una diligencia", "ca-valencia": "una diligència"},
}

_SENSITIVE_LABELS: dict[str, dict[str, str]] = {
    "dni": {"es": "tu DNI", "ca-valencia": "el teu DNI"},
    "nie": {"es": "tu NIE", "ca-valencia": "el teu NIE"},
    "iban": {"es": "un número de cuenta", "ca-valencia": "un número de compte"},
    "telefono": {"es": "un teléfono", "ca-valencia": "un telèfon"},
    "email": {"es": "un correo electrónico", "ca-valencia": "un correu electrònic"},
    "importe": {"es": "un importe de dinero", "ca-valencia": "un import de diners"},
    "expediente": {"es": "un número de expediente", "ca-valencia": "un número d'expedient"},
}

DISCLAIMER = {
    "es": (
        "Esta es una lectura automática y puede contener errores. No es "
        "asesoramiento jurídico. Consulta siempre el documento original."
    ),
    "ca-valencia": (
        "Esta és una lectura automàtica i pot contindre errors. No és "
        "assessorament jurídic. Consulta sempre el document original."
    ),
}

HUMAN_ADVICE = {
    "es": (
        "Por su contenido, es mejor que te ayude una persona. Pide ayuda al "
        "personal del centro o acude a la oficina del organismo que firma la carta."
    ),
    "ca-valencia": (
        "Pel seu contingut, és millor que t'ajude una persona. Demana ajuda al "
        "personal del centre o acudix a l'oficina de l'organisme que firma la carta."
    ),
}

_AMBIGUOUS_DEADLINE = {
    "es": (
        "La carta menciona un plazo pero no dice una fecha clara: confírmalo con "
        "una persona para no quedarte sin tiempo."
    ),
    "ca-valencia": (
        "La carta menciona un termini però no diu una data clara: confirma-ho amb "
        "una persona per a no quedar-te sense temps."
    ),
}

_UNREADABLE = {
    "es": (
        "No se ha podido leer bien el documento. Prueba a hacer la foto con más "
        "luz y sin sombras, o pide ayuda al personal del centro."
    ),
    "ca-valencia": (
        "No s'ha pogut llegir bé el document. Prova a fer la foto amb més llum i "
        "sense ombres, o demana ajuda al personal del centre."
    ),
}


def unreadable_summary(language: str) -> str:
    return _UNREADABLE[language]


def build_summary(language: str, analysis: dict) -> str:
    """Resumen en lenguaje claro, construido con plantillas deterministas."""
    es = language == "es"
    parts: list[str] = []

    organismo = analysis["organismo"]
    if organismo:
        parts.append(
            f"Esta carta la envía {organismo}." if es else f"Esta carta l'envia {organismo}."
        )
    else:
        parts.append(
            "No se ha podido identificar con seguridad qué organismo envía la carta."
            if es
            else "No s'ha pogut identificar amb seguretat quin organisme envia la carta."
        )

    risk_terms = analysis["risk_terms"]
    if risk_terms:
        labels = [_RISK_LABELS[t][language] for t in risk_terms if t in _RISK_LABELS]
        if labels:
            listed = ", ".join(labels[:-1]) + (
                (" y " if es else " i ") + labels[-1] if len(labels) > 1 else ""
            )
            listed = listed if len(labels) > 1 else labels[0]
            parts.append(
                f"Menciona {listed}. Es un asunto importante."
                if es
                else f"Menciona {listed}. És un assumpte important."
            )

    deadlines = analysis["deadlines"]
    if deadlines:
        listed = ", ".join(deadlines)
        parts.append(
            f"Aparece un plazo: {listed}." if es else f"Apareix un termini: {listed}."
        )
    if analysis["ambiguous_deadline"]:
        parts.append(_AMBIGUOUS_DEADLINE[language])

    sensitive = analysis["sensitive_data"]
    if sensitive:
        labels = [_SENSITIVE_LABELS[s][language] for s in sensitive if s in _SENSITIVE_LABELS]
        if labels:
            listed = ", ".join(labels)
            parts.append(
                f"El documento contiene datos personales ({listed}): no lo dejes olvidado aquí."
                if es
                else f"El document conté dades personals ({listed}): no el deixes oblidat ací."
            )

    # Solo se dice "no hay nada urgente" si de verdad no hay NADA: si la carta
    # menciona un plazo vago ya se ha avisado arriba, y rematar con "no se han
    # detectado plazos" se contradice y tranquiliza a quien no debe.
    if not risk_terms and not deadlines and not analysis["ambiguous_deadline"]:
        parts.append(
            "No se han detectado plazos ni avisos urgentes, pero léela entera por si acaso."
            if es
            else "No s'han detectat terminis ni avisos urgents, però llig-la sencera per si de cas."
        )

    return " ".join(parts)
