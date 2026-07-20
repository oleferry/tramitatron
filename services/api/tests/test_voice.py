"""Canal de voz (PRD §14.3 y §13.2).

Lo crítico: el audio y la transcripción NO pueden quedar en ningún sitio
(E2E-01: "no queda audio, texto libre ni PII"), y una transcripción dudosa no
puede presentarse como buena.
"""

import base64
import logging

import pytest

# El mock elige la frase por el tamaño del audio (tamaño % 4).
AUDIO_MEDICO = 64  # 64 % 4 == 0 -> "quiero pedir cita para el médico"
AUDIO_DNI = 65  # 65 % 4 == 1 -> "necesito renovar el dni"
AUDIO_ITV = 66  # 66 % 4 == 2 -> "tengo que pasar la itv del coche"
AUDIO_DUDOSO = 67  # 67 % 4 == 3 -> confianza baja


def _audio(size: int = AUDIO_MEDICO) -> str:
    # Exactamente `size` bytes: el mock elige la frase por el tamaño, así que
    # un byte de más o de menos cambia la transcripción esperada.
    return base64.b64encode((b"\x1a\x45" * size)[:size]).decode()


@pytest.fixture()
def session_id(client) -> str:
    return client.post("/api/session", json={"language": "es"}).json()["session_id"]


def _transcribe(client, session_id, size=AUDIO_MEDICO, language="es"):
    response = client.post(
        f"/api/session/{session_id}/voice/transcribe",
        json={"audio_base64": _audio(size), "language": language},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_transcription_returns_text_and_confidence(client, session_id):
    body = _transcribe(client, session_id)
    assert body["text"] == "quiero pedir cita para el médico"
    assert body["confidence"] > 0.6
    assert body["usable"] is True


def test_low_confidence_transcription_is_not_usable(client, session_id):
    """Una transcripción dudosa se marca para repetir, no para usarla."""
    body = _transcribe(client, session_id, size=AUDIO_DUDOSO)
    assert body["confidence"] < 0.6
    assert body["usable"] is False


def test_transcription_feeds_the_intent_search(client, session_id):
    """La voz no es un canal aparte: acaba en el mismo clasificador."""
    text = _transcribe(client, session_id, size=AUDIO_DNI)["text"]
    intent = client.post("/api/assistant/intent", json={"text": text}).json()
    assert intent["procedure_id"] == "mir.dni.renewal-appointment"


def test_transcription_in_valencian(client, session_id):
    body = _transcribe(client, session_id, language="ca-valencia")
    assert body["text"] == "vull demanar cita amb el metge"


def test_audio_and_transcript_are_never_stored(client, session_id):
    """PRD §13.2 y E2E-01: ni el audio ni el texto libre pueden persistir."""
    body = _transcribe(client, session_id)
    session = client.get(f"/api/session/{session_id}").json()

    # No aparece ninguna clave de voz ni el texto en el estado de la sesión.
    assert session["data_keys"] == []
    assert body["text"] not in str(session)


def test_no_audio_or_transcript_in_logs(client, caplog):
    audio = _audio()
    with caplog.at_level(logging.DEBUG):
        session_id = client.post("/api/session", json={"language": "es"}).json()["session_id"]
        client.post(
            f"/api/session/{session_id}/voice/transcribe",
            json={"audio_base64": audio},
        )
        client.delete(f"/api/session/{session_id}")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "quiero pedir cita" not in all_logs
    assert audio[:24] not in all_logs


def test_voice_requires_a_live_session(client):
    """La voz es un canal de una sesión viva, no un transcriptor abierto."""
    response = client.post(
        "/api/session/inexistente/voice/transcribe",
        json={"audio_base64": _audio()},
    )
    assert response.status_code == 404


def test_voice_rejects_invalid_audio(client, session_id):
    response = client.post(
        f"/api/session/{session_id}/voice/transcribe",
        json={"audio_base64": "esto-no-es-base64!!"},
    )
    assert response.status_code == 400


def test_voice_rejects_empty_audio(client, session_id):
    response = client.post(
        f"/api/session/{session_id}/voice/transcribe", json={"audio_base64": ""}
    )
    assert response.status_code == 400


def test_voice_rejects_oversized_audio(client, session_id):
    huge = base64.b64encode(b"x" * (4 * 1024 * 1024 + 1)).decode()
    response = client.post(
        f"/api/session/{session_id}/voice/transcribe", json={"audio_base64": huge}
    )
    assert response.status_code == 413
