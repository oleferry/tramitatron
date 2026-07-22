def _intent(client, text, language="es"):
    response = client.post("/api/assistant/intent", json={"text": text, "language": language})
    assert response.status_code == 200
    return response.json()


def test_health_intent_spanish(client):
    result = _intent(client, "Quiero pedir cita para el médico")
    assert result["intent"] == "BOOK_HEALTH_APPOINTMENT"
    assert result["procedure_id"] == "sacyl.health.primary-care"
    assert result["next_action"] == "SHOW_PROCEDURE"


def test_health_intent_valencian(client):
    result = _intent(client, "Vull demanar cita amb el metge", language="ca-valencia")
    assert result["procedure_id"] == "sacyl.health.primary-care"


def test_itv_intent(client):
    result = _intent(client, "necesito pasar la ITV del coche")
    assert result["procedure_id"] == "jcyl.itv.info"


def test_expanded_intents_route_to_new_procedures(client):
    """Cada trámite nuevo del catálogo ampliado es alcanzable desde el buscador."""
    cases = [
        ("quiero renovar el dni", "mir.dni.renewal-appointment"),
        ("cita con hacienda para la renta", "aeat.cita-previa"),
        ("necesito mi informe de vida laboral", "seg-social.tgss.vida-laboral"),
        ("cita para la pensión de jubilación", "seg-social.inss.cita-previa"),
        ("he perdido la tarjeta sanitaria", "sacyl.health.card"),
        ("estoy en el paro y necesito cita", "sepe.cita-previa"),
        ("renovar el carné de conducir", "dgt.cita-previa"),
        ("cita de extranjería para huellas", "mir.extranjeria.cita-previa"),
        ("certificado de empadronamiento", "padron.certificado"),
        ("certificado de nacimiento", "mjusticia.certificado-nacimiento"),
        ("antecedentes penales", "mjusticia.antecedentes-penales"),
    ]
    for text, expected in cases:
        result = _intent(client, text)
        assert result["procedure_id"] == expected, f"{text!r} -> {result['procedure_id']}"
        assert result["next_action"] == "SHOW_PROCEDURE", text


def test_expanded_intents_in_valencian(client):
    cases = [
        ("vull renovar el dni", "mir.dni.renewal-appointment"),
        ("cita amb hisenda per a la renda", "aeat.cita-previa"),
        ("estic a l'atur", "sepe.cita-previa"),
        ("certificat d'empadronament", "padron.certificado"),
    ]
    for text, expected in cases:
        result = _intent(client, text, language="ca-valencia")
        assert result["procedure_id"] == expected, f"{text!r} -> {result['procedure_id']}"


def test_specific_rules_win_over_generic(client):
    """'Vida laboral' no debe caer en la regla genérica de Seguridad Social."""
    result = _intent(client, "vida laboral de la seguridad social")
    assert result["procedure_id"] == "seg-social.tgss.vida-laboral"
    # Y la tarjeta sanitaria no debe caer en la cita médica.
    result = _intent(client, "renovar la tarjeta sanitaria")
    assert result["procedure_id"] == "sacyl.health.card"


def test_unknown_intent_asks_clarification(client):
    result = _intent(client, "xyzzy plugh")
    assert result["intent"] == "UNKNOWN"
    assert result["next_action"] == "ASK_CLARIFICATION"
    assert result["clarification"]


def test_clarification_in_valencian(client):
    result = _intent(client, "xyzzy plugh", language="ca-valencia")
    assert "tràmit" in result["clarification"]


def test_text_too_long_rejected(client):
    response = client.post("/api/assistant/intent", json={"text": "a" * 501})
    assert response.status_code == 422
