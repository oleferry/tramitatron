"""Validadores deterministas de campos de identidad (PRD §6.3: la IA explica;
el sistema valida). Ningún dato extraído se usa sin pasar por aquí y sin
revisión visual del ciudadano."""

import re
from datetime import date

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}

_DNI_RE = re.compile(r"^(\d{8})([A-Z])$")
_NIE_RE = re.compile(r"^([XYZ])(\d{7})([A-Z])$")
_SIP_RE = re.compile(r"^\d{8}$")


def validate_dni_or_nie(value: str) -> bool:
    value = value.strip().upper()
    if match := _DNI_RE.match(value):
        number, letter = match.groups()
        return DNI_LETTERS[int(number) % 23] == letter
    if match := _NIE_RE.match(value):
        prefix, digits, letter = match.groups()
        number = int(_NIE_PREFIX[prefix] + digits)
        return DNI_LETTERS[number % 23] == letter
    return False


def validate_sip(value: str) -> bool:
    return bool(_SIP_RE.match(value.strip()))


def validate_birth_date(value: str) -> bool:
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        return False
    return date(1900, 1, 1) <= parsed <= date.today()


def validate_nonempty(value: str) -> bool:
    return bool(value.strip())


# Campo -> (id de validador para trazabilidad, función)
FIELD_VALIDATORS: dict[str, tuple[str, callable]] = {
    "dni_number": ("dni_or_nie_v1", validate_dni_or_nie),
    "sip_number": ("sip_format_v1", validate_sip),
    "birth_date": ("iso_date_v1", validate_birth_date),
    "full_name": ("nonempty_v1", validate_nonempty),
}


def validator_for(field: str) -> tuple[str, callable]:
    return FIELD_VALIDATORS.get(field, ("nonempty_v1", validate_nonempty))
