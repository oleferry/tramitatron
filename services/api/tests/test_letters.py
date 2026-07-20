"""Explicación de cartas administrativas (TT-404, PRD §5.2 caso D y E2E-04).

Lo crítico aquí no es el resumen bonito, sino que el riesgo se detecte SIEMPRE
y que nunca se invente un plazo. Ante la duda, el sistema debe derivar a una
persona.
"""

import base64

import pytest

from app.letters.analysis import assess, detect_deadlines, detect_risk_terms, detect_sensitive_data

CARTA_EMBARGO = (
    "AGENCIA TRIBUTARIA\nPROVIDENCIA DE APREMIO\n"
    "No habiéndose satisfecho la deuda, se inicia la vía ejecutiva por importe "
    "de 1.240,50 €. Podrá interponer recurso en el plazo de un mes. De no "
    "atenderlo se procederá al embargo de bienes. DNI 12345678Z."
)
CARTA_RUTINARIA = (
    "CONSELLERIA DE SANIDAD\nSu cita de revisión ha quedado asignada. "
    "Debe presentarse hasta el 30/09/2026 aportando su tarjeta SIP."
)
CARTA_PLAZO_AMBIGUO = (
    "AYUNTAMIENTO DE CASTELLÓ DE LA PLANA\nDebe aportar la documentación que "
    "falta a la mayor brevedad, conforme a la normativa vigente."
)


# El mock elige la carta sintética por el tamaño en bytes de la imagen
# (tamaño % 4). Estos alias fijan qué carta llega en cada test.
CARTA_APREMIO_BYTES = 64  # 64 % 4 == 0 -> providencia de apremio (riesgo alto)
CARTA_CITA_BYTES = 65  # 65 % 4 == 1 -> cita sanitaria (rutinaria)
CARTA_AMBIGUA_BYTES = 66  # 66 % 4 == 2 -> plazo "a la mayor brevedad"
CARTA_ILEGIBLE_BYTES = 67  # 67 % 4 == 3 -> transcripción de baja confianza


def _image(size: int = CARTA_APREMIO_BYTES) -> str:
    return base64.b64encode(b"x" * size).decode()


def _upload(client, session_id, image=None, language="es"):
    body = {"image_base64": image or _image(), "language": language}
    response = client.post(f"/api/session/{session_id}/letters", json=body)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def session_id(client) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


# --- Análisis determinista (sin API) ---------------------------------------


def test_high_risk_terms_detected():
    terms = detect_risk_terms(CARTA_EMBARGO)
    assert "embargo" in terms
    assert "apremio" in terms
    assert "via_ejecutiva" in terms
    assert "recurso" in terms


def test_routine_letter_is_not_high_risk():
    assert detect_risk_terms(CARTA_RUTINARIA) == []
    assert assess(CARTA_RUTINARIA)["risk_level"] == "normal"
    assert assess(CARTA_RUTINARIA)["recommend_human"] is False


def test_risk_detection_ignores_accents_and_case():
    assert "sancion" in detect_risk_terms("Expediente SANCIONADOR por INFRACCIÓN grave")


def test_explicit_relative_deadline():
    deadlines, ambiguous = detect_deadlines("Podrá recurrir en el plazo de 15 días hábiles.")
    assert deadlines == ["15 días hábiles"]
    assert ambiguous is False


def test_explicit_deadline_with_number_word():
    deadlines, _ = detect_deadlines("Dispone de un plazo de un mes para alegar.")
    assert deadlines == ["1 mes"]


def test_explicit_absolute_deadlines():
    numeric, _ = detect_deadlines("Debe presentarse antes del 30/09/2026.")
    assert numeric == ["30/09/2026"]
    textual, _ = detect_deadlines("Tiene hasta el 5 de octubre de 2026 para responder.")
    assert textual == ["05/10/2026"]


def test_vague_deadline_is_never_reported_as_a_date():
    """PRD §5.2: los plazos solo se dan si aparecen inequívocamente."""
    deadlines, ambiguous = detect_deadlines(CARTA_PLAZO_AMBIGUO)
    assert deadlines == []
    assert ambiguous is True


def test_ambiguous_deadline_escalates_to_human():
    """Un plazo dudoso basta para derivar, aunque no haya términos de riesgo."""
    analysis = assess(CARTA_PLAZO_AMBIGUO)
    assert analysis["risk_level"] == "high"
    assert analysis["recommend_human"] is True


def test_sensitive_data_types_detected():
    found = detect_sensitive_data(
        "DNI 12345678Z, cuenta ES9121000418450200051332, "
        "teléfono 612345678, correo persona@ejemplo.es, importe 1.240,50 €"
    )
    assert {"dni", "iban", "telefono", "email", "importe"} <= set(found)


def test_sensitive_values_are_never_returned():
    """Se informa del TIPO de dato, jamás del valor (PRD §13.2)."""
    analysis = assess(CARTA_EMBARGO)
    serialized = repr(analysis)
    assert "12345678Z" not in serialized
    assert "1.240,50" not in serialized
    assert "dni" in analysis["sensitive_data"]


def test_organismo_detected():
    assert "AGENCIA TRIBUTARIA" in (assess(CARTA_EMBARGO)["organismo"] or "")


# --- API -------------------------------------------------------------------


def test_letter_separates_facts_from_explanation(client, session_id):
    body = _upload(client, session_id)
    assert set(body) == {"letter_id", "transcription_confidence", "facts", "explanation"}
    assert "excerpt" in body["facts"]
    assert "summary" in body["explanation"]
    assert body["explanation"]["disclaimer"]


def test_high_risk_letter_recommends_human_and_gives_no_legal_advice(client, session_id):
    """E2E-04: resume hechos, destaca organismo, deriva a humano y NO
    recomienda un recurso jurídico concreto."""
    body = _upload(client, session_id, image=_image(CARTA_APREMIO_BYTES))
    facts, explanation = body["facts"], body["explanation"]

    assert explanation["risk_level"] == "high"
    assert explanation["recommend_human"] is True
    assert explanation["human_advice"]
    assert {"embargo", "apremio", "via_ejecutiva"} <= set(explanation["risk_terms"])
    assert "agencia" in (facts["organismo"] or "").lower()
    assert facts["deadlines"] == ["1 mes"]
    assert "dni" in facts["sensitive_data"]

    summary = explanation["summary"].lower()
    # No debe indicar CÓMO recurrir ni prometer un resultado.
    for forbidden in ("debes recurrir", "presenta un recurso", "recomendamos recurrir",
                      "no tienes que pagar", "puedes ignorar"):
        assert forbidden not in summary


def test_routine_letter_does_not_alarm(client, session_id):
    """Una cita médica no debe derivarse a atención humana ni marcarse en rojo."""
    body = _upload(client, session_id, image=_image(CARTA_CITA_BYTES))
    assert body["explanation"]["risk_level"] == "normal"
    assert body["explanation"]["recommend_human"] is False
    assert body["explanation"]["human_advice"] is None
    assert body["facts"]["deadlines"] == ["30/09/2026"]


def test_ambiguous_deadline_letter_escalates(client, session_id):
    body = _upload(client, session_id, image=_image(CARTA_AMBIGUA_BYTES))
    assert body["facts"]["deadlines"] == []
    assert body["explanation"]["ambiguous_deadline"] is True
    assert body["explanation"]["recommend_human"] is True


def test_summary_never_contradicts_itself(client, session_id):
    """Con un plazo ambiguo se avisa; NO se puede rematar diciendo que no hay
    plazos, porque tranquilizaría justo a quien debe darse prisa."""
    body = _upload(client, session_id, image=_image(CARTA_AMBIGUA_BYTES))
    summary = body["explanation"]["summary"].lower()
    assert "menciona un plazo" in summary
    assert "no se han detectado plazos" not in summary


def test_unreadable_letter_is_not_interpreted(client, session_id):
    """Con transcripción de baja confianza no se explica nada: se pide repetir.
    Explicar mal una carta es peor que admitir que no se ha podido leer."""
    body = _upload(client, session_id, image=_image(CARTA_ILEGIBLE_BYTES))
    assert body["transcription_confidence"] < 0.55
    assert body["facts"]["excerpt"] == ""
    assert body["facts"]["organismo"] is None
    assert body["explanation"]["recommend_human"] is True
    assert "no se ha podido leer" in body["explanation"]["summary"].lower()


def test_letter_is_stored_in_session_and_purgeable(client, session_id):
    body = _upload(client, session_id)
    letter_id = body["letter_id"]

    assert client.get(f"/api/session/{session_id}/letters/{letter_id}").status_code == 200
    assert client.delete(f"/api/session/{session_id}/letters/{letter_id}").status_code == 204
    assert client.get(f"/api/session/{session_id}/letters/{letter_id}").status_code == 404


def test_letter_dies_with_the_session(client, session_id):
    letter_id = _upload(client, session_id)["letter_id"]
    client.delete(f"/api/session/{session_id}")
    assert client.get(f"/api/session/{session_id}/letters/{letter_id}").status_code == 404


def test_letters_are_isolated_between_sessions(client, session_id):
    letter_id = _upload(client, session_id)["letter_id"]
    other = client.post("/api/session", json={"language": "es"}).json()["session_id"]
    assert client.get(f"/api/session/{other}/letters/{letter_id}").status_code == 404


def test_letter_requires_existing_session(client):
    response = client.post(
        "/api/session/inexistente/letters", json={"image_base64": _image()}
    )
    assert response.status_code == 404


def test_letter_rejects_invalid_image(client, session_id):
    response = client.post(
        f"/api/session/{session_id}/letters", json={"image_base64": "no-es-base64!!"}
    )
    assert response.status_code == 400


def test_letter_explanation_in_valencian(client, session_id):
    body = _upload(client, session_id, language="ca-valencia")
    assert "assessorament jurídic" in body["explanation"]["disclaimer"]
