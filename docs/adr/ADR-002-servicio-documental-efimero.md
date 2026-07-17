# ADR-002 — Servicio documental efímero dentro de la sesión

**Estado:** aceptada
**Fecha:** 2026-07-17
**Contexto:** PRD §11 (gestión documental) y §13 (sesión anónima)

## Decisión

1. **La extracción documental se guarda como JSON dentro de los datos de la
   sesión** (clave `document_<id>`), no en un almacén propio. Consecuencia
   directa: hereda el TTL y la purga de la sesión sin código adicional, y es
   imposible que un documento sobreviva a la sesión que lo capturó.

2. **La imagen nunca se persiste.** Viaja del device-agent al kiosco y del
   kiosco a la API en el cuerpo de la petición, se pasa al gateway y se
   descarta. No hay rutas de fichero, ni caché, ni logs con cuerpos.

3. **Pipeline del PRD §11.2** implementado en `app/documents/`:
   `QUALITY_CHECK` (base64 válido, tamaño ≤ 8 MB) → `EXTRACT` (gateway,
   hoy mock sintético) → `VALIDATE` (deterministas) → `USER_CONFIRM`
   (el kiosco muestra todos los valores en campos editables) →
   `USE_IN_SESSION` (los valores confirmados pasan a `session.data`) →
   `PURGE` (con la sesión, o antes vía DELETE).

4. **Validadores deterministas separados de la IA** (`validators.py`): letra
   del DNI (mod 23) y NIE, formato SIP, fecha ISO acotada. En la confirmación
   la confianza del modelo deja de contar: solo validador + revisión humana.
   La IA nunca corrige silenciosamente un dato de identidad (PRD §11.4).

5. **Estados por campo** (PRD §11.5): `VALID`, `REVIEW_REQUIRED` (confianza
   < 0.80) o `INVALID`. El mock devuelve a propósito un campo con confianza
   baja para que el flujo de revisión del kiosco se ejercite siempre.

## Consecuencias

- El caso E2E-02 del PRD es reproducible hoy con datos sintéticos y quedará
  igual cuando el gateway mock se sustituya por un modelo de visión real:
  solo cambia la implementación de `extract_document`.
- Los tests de privacidad cubren también documentos: los valores extraídos
  no aparecen en logs ni en listados de sesión (solo las claves).
- Límite conocido: los datos de sesión viajan como un único JSON en Redis;
  si una sesión acumulara muchas capturas, convendría trocearlo. Irrelevante
  para el MVP (1–2 documentos por sesión).
