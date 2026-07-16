def _intent(client, text, language="es"):
    response = client.post("/api/assistant/intent", json={"text": text, "language": language})
    assert response.status_code == 200
    return response.json()


def test_health_intent_spanish(client):
    result = _intent(client, "Quiero pedir cita para el médico")
    assert result["intent"] == "BOOK_HEALTH_APPOINTMENT"
    assert result["procedure_id"] == "gva.health.primary-care.appointment"
    assert result["next_action"] == "SHOW_PROCEDURE"


def test_health_intent_valencian(client):
    result = _intent(client, "Vull demanar cita amb el metge", language="ca-valencia")
    assert result["procedure_id"] == "gva.health.primary-care.appointment"


def test_itv_intent(client):
    result = _intent(client, "necesito pasar la ITV del coche")
    assert result["procedure_id"] == "sitval.itv.appointment"


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
