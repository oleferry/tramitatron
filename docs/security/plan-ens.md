# Plan de adecuación al ENS — Tramitatrón (BORRADOR)

- **Ticket:** TT-704 (EPIC 7)
- **Estado:** BORRADOR técnico para el Responsable de Seguridad de la
  administración contratante y su equipo de sistemas
- **Fecha:** 2026-07-21
- **Marco:** Real Decreto 311/2022, Esquema Nacional de Seguridad (ENS).
- **Documentos hermanos:** [threat model (TT-702)](threat-model.md) y
  [EIPD técnica (TT-703)](eipd-tecnica.md).

> **Quién es responsable del ENS.** El ENS obliga a la **entidad del sector
> público** que presta el servicio (el ayuntamiento u organismo contratante),
> que es quien **categoriza el sistema y aprueba la Declaración de
> Aplicabilidad**. Tramitatrón, como solución/encargado del tratamiento, debe
> **facilitar** esa adecuación y cumplir las medidas aplicables al servicio que
> presta. Este documento es un **insumo técnico** para esa adecuación, no la
> adecuación misma. La categorización propuesta aquí es una recomendación a
> validar por el Responsable de Seguridad.

---

## 1. Alcance

Sistema de información "Tramitatrón": tótems de asistencia digital + backend
(API, worker de navegación, gateway de IA) + conocimiento oficial. Ámbito:
micro-piloto en 1–3 municipios de Castellón.

Quedan fuera de este plan (responsabilidad de la administración y del
integrador de hardware): la red municipal, el directorio de usuarios de
soporte, el MDM y el bastionado del sistema operativo del tótem, más allá de las
recomendaciones que aquí se hacen.

---

## 2. Categorización del sistema (Anexo I RD 311/2022)

Valoración por dimensión del **impacto de un incidente** (Bajo/Medio/Alto):

| Dimensión | Nivel propuesto | Justificación |
|---|---|---|
| **Confidencialidad** | **Medio** | Trata datos A2, incluidas categorías especiales (salud vía SIP, contenido de cartas). Atenúa el impacto que sea **anónimo, efímero y sin acumulación**: una brecha afecta, como mucho, a los datos de la sesión en curso, no a un fichero de muchas personas. **El Responsable puede elevarlo a Alto** si pondera las categorías especiales como impacto alto |
| **Integridad** | **Medio** | Alterar requisitos o plazos mostrados puede perjudicar a la persona. Atenúa: catálogo y conocimiento versionados, reglas deterministas y cita de fuente |
| **Trazabilidad** | **Bajo** (ciudadano) / **Medio** (operación) | Por diseño **no hay traza por ciudadano** (anonimato, privacidad por diseño). La traza relevante es la de acciones de administración/soporte y cambios de configuración |
| **Autenticidad** | **Medio** | El sistema **no autentica al ciudadano** (anónimo). Sí importa autenticar al personal de soporte y garantizar que el tótem habla con el backend legítimo |
| **Disponibilidad** | **Bajo-Medio** | Un tótem caído degrada con alternativa humana (personal del centro, teléfono, web oficial). No es infraestructura crítica |

**Categoría del sistema propuesta: MEDIA** (la mayor dimensión es Media).

Consecuencia: aplican las medidas de nivel **MEDIO** del Anexo II. Para categoría
MEDIA suele bastar **autoevaluación**; si el Responsable eleva Confidencialidad a
Alto, el sistema pasaría a **categoría ALTA** y requeriría **auditoría formal y
certificación de conformidad** (art. 38).

---

## 3. Tensión privacidad ↔ trazabilidad

El ENS valora la trazabilidad; el diseño de Tramitatrón la **minimiza a
propósito** en la cara del ciudadano (sin identificadores, sin expediente,
purga). No es una carencia: es la medida de protección de datos (EIPD, TT-703).

Resolución propuesta: la trazabilidad del ENS se satisface en el plano
**operativo** (acceso de soporte, cambios de configuración, despliegues,
healthchecks del worker), **sin** reintroducir traza de PII del ciudadano. El
log de acceso ya registra método/ruta/estado sin PII; el worker emite eventos
sin valores.

---

## 4. Estado de las medidas (Anexo II, nivel MEDIO)

Leyenda: **✅ implementado** (con evidencia en el repo) · **◑ parcial** ·
**🏗 despliegue** (responsabilidad de la administración/integrador) ·
**⏳ pendiente**.

### 4.1 Marco organizativo (org)

| Medida | Estado | Evidencia / nota |
|---|---|---|
| org.1 Política de seguridad | 🏗 | La aprueba la administración contratante |
| org.2 Normativa de seguridad | 🏗 | Idem |
| org.3 Procedimientos de seguridad | ◑ | Existen ADRs y estos documentos; falta el cuerpo procedimental formal |
| org.4 Proceso de autorización | 🏗 | De la administración |

### 4.2 Marco operacional (op)

| Medida | Estado | Evidencia / nota |
|---|---|---|
| op.pl.1 Análisis de riesgos | ✅ | Threat model (TT-702) + EIPD (TT-703) |
| op.pl.2 Arquitectura de seguridad | ✅ | Monolito modular + worker separado (regla 8); límites de confianza documentados (ADR-001, TT-702) |
| op.pl.3 Adquisición de nuevos componentes | ◑ | Dependencias fijadas; falta SBOM formal |
| op.acc Control de acceso (identificación, autenticación, autorización) | ◑/🏗 | El ciudadano es anónimo por diseño; el acceso de **soporte/administración** debe autenticarse (fuerte) — pendiente de la política de operación. El device-agent aún no autentica al frontend (deuda conocida) |
| op.exp.1 Inventario de activos | ◑ | Componentes descritos aquí y en el PRD §9.3 |
| op.exp.2 Configuración de seguridad | 🏗 | Bastionado del tótem (usuario sin privilegios, puertos bloqueados) — §15.4 |
| op.exp.3 Gestión de la configuración | ✅ | Todo por variables de entorno; sin secretos en código; catálogo/conocimiento versionados en git |
| op.exp.8 Registro de actividad | ✅ | Log de acceso sin PII (`main.py`); eventos del worker sin valores |
| op.exp.10 Protección de claves criptográficas | 🏗/◑ | Secretos por entorno; **vault pendiente** (§15.4); `.env` ignorado y escaneo de secretos en CI (gitleaks) |
| op.ext.1 Contratación y acuerdos de nivel de servicio | 🏗 | Con proveedores (cloud, IA, soporte) — jurídica |
| op.ext.2 Gestión diaria de servicios externos | ◑ | Healthchecks de conectores; degradación ante caída del proveedor de IA (ADR-006) |
| op.nub Servicios en la nube | 🏗/◑ | Backend en región UE (Render/Frankfurt, `render.yaml`); contrato de encargado pendiente |
| op.cont Continuidad del servicio | 🏗 | Alternativa humana siempre disponible; plan de continuidad formal pendiente |
| op.mon Monitorización (detección, métricas) | ⏳ | Alertas/logs centralizados pendientes (§15.4) |

### 4.3 Medidas de protección (mp)

| Medida | Estado | Evidencia / nota |
|---|---|---|
| mp.if Protección de las instalaciones | 🏗 | Ubicación del tótem, acceso físico — administración |
| mp.per Gestión del personal | 🏗 | Personal de soporte — administración |
| mp.eq Protección de los equipos | 🏗 | Bastionado del tótem, bloqueo de sesión, cifrado de disco — §15.4 |
| mp.com.1 Perímetro seguro | ◑/🏗 | CORS restringido; **allowlist de dominios del worker** (regla 7, ADR-007); firewall del tótem pendiente |
| mp.com.2 Protección de la confidencialidad (cifrado en tránsito) | 🏗 | HTTPS de extremo a extremo — despliegue |
| mp.com.3 Protección de la autenticidad e integridad | ◑ | Salidas de IA tipadas y validadas; mTLS/pinning pendiente |
| mp.si Protección de los soportes de información | ✅ | **No hay soportes con PII**: datos efímeros, sin base de datos de PII, sin imágenes/audio en disco (ADR-002/004/005) |
| mp.sw.1 Desarrollo seguro | ✅ | Revisión por ADR; tests (incl. privacidad y aislamiento); CI con lint y escaneo de secretos |
| mp.sw.2 Aceptación y puesta en servicio | ◑ | CI (tests + build + a11y); falta pipeline de despliegue firmado (§15.4) |
| mp.info.1 Datos de carácter personal | ✅ | Minimización, efímero, informar del tipo y no del valor, revisión del usuario; alineado con la EIPD (TT-703) |
| mp.info.3 Cifrado de la información | ◑/🏗 | En tránsito (HTTPS) y en reposo efímero; el PRD pide "cifrado efímero" para A2 — **verificar** que la sesión en Redis va cifrada en reposo si Redis persiste |
| mp.info.6 Limpieza de documentos | ✅ | Purga de documentos/cartas/voz; sin metadatos retenidos |
| mp.s.2 Protección de servicios y aplicaciones web | ◑ | Validación de entrada, límites de tamaño, sin PII en URLs; **rate limiting pendiente** |
| mp.s.mon Protección frente a denegación de servicio | ◑ | Timeouts y límites de tamaño; anti-DoS de red pendiente |

---

## 5. Perfil de la brecha (gap) principal

Lo que el software **ya aporta** a la adecuación:

- Arquitectura por niveles con worker separado y allowlist (op.pl.2, mp.com.1).
- Minimización y no persistencia de PII (mp.info, mp.si) — el punto más fuerte.
- Gestión de configuración sin secretos en código (op.exp.3, op.exp.10 parcial).
- Registro de actividad sin PII (op.exp.8).
- Análisis de riesgos hecho (op.pl.1).
- Desarrollo seguro con tests y CI (mp.sw.1).

Lo que **depende de la administración/integrador** (no del código):

- Política, normativa y procedimientos de seguridad (org.*).
- Bastionado del tótem: arranque seguro, cifrado de disco, usuario sin
  privilegios, puertos, MDM, VPN de administración (mp.eq, op.exp.2, §15.4).
- Autenticación fuerte de soporte y **prohibición de acceso remoto silencioso**
  a una sesión ciudadana (op.acc).
- Contratos de encargado con proveedores y op.nub (op.ext, jurídica).
- Monitorización y alertas centralizadas (op.mon).

Deuda **del código** — estado:

- ✅ Autenticar el device-agent al frontend (op.acc): token `X-Device-Token`.
- ✅ Rate limiting en la API (mp.s.2): middleware por cliente y ventana.
- ✅ SBOM y escaneo de dependencias en CI (op.pl.3): job `deps` con pip-audit,
  `npm audit --omit=dev` y SBOM CycloneDX del kiosco.
- ⏳ Verificar cifrado en reposo de la sesión si Redis persiste (mp.info.3):
  depende de la configuración de Redis en el despliegue (infra).

---

## 6. Recomendaciones y siguientes pasos

1. El Responsable de Seguridad **valida la categorización** (§2) y decide si
   Confidencialidad es Media o Alta (determina autoevaluación vs. auditoría).
2. Elaborar la **Declaración de Aplicabilidad** a partir de la tabla §4.
3. Cerrar la deuda de código listada en §5 (auth device-agent, rate limiting,
   SBOM, cifrado en reposo).
4. La administración aborda el marco organizativo y el bastionado del tótem.
5. Integrar con la **EIPD (TT-703)** y el **threat model (TT-702)**: comparten
   riesgos y medidas; deben mantenerse coherentes.
6. Si la categoría resulta ALTA, planificar **auditoría y certificación de
   conformidad** (art. 38) antes del despliegue institucional.

---

## 7. Control de versiones

Cada cambio de arquitectura, categoría de datos o medida de seguridad debe
actualizar este plan junto con el threat model y la EIPD. Versión inicial:
borrador técnico 2026-07-21, categoría propuesta MEDIA (a validar).
