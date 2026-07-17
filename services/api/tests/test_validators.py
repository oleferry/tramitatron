from app.documents.validators import (
    validate_birth_date,
    validate_dni_or_nie,
    validate_sip,
)


def test_dni_valid_letter():
    assert validate_dni_or_nie("12345678Z")
    assert validate_dni_or_nie("00000000T")
    # minúsculas y espacios se toleran
    assert validate_dni_or_nie(" 12345678z ")


def test_dni_wrong_letter_rejected():
    assert not validate_dni_or_nie("12345678A")
    assert not validate_dni_or_nie("12345678")
    assert not validate_dni_or_nie("1234567Z")


def test_nie_valid():
    # X0000000T: 00000000 % 23 = 0 -> T
    assert validate_dni_or_nie("X0000000T")
    assert not validate_dni_or_nie("X0000000A")


def test_sip_format():
    assert validate_sip("01234567")
    assert not validate_sip("1234567")
    assert not validate_sip("123456789")
    assert not validate_sip("12A45678")


def test_birth_date():
    assert validate_birth_date("1957-03-14")
    assert not validate_birth_date("2999-01-01")  # futuro
    assert not validate_birth_date("1857-01-01")  # anterior a 1900
    assert not validate_birth_date("14/03/1957")  # formato no ISO
