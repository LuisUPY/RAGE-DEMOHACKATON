# RAGE — OWASP Top 10 LLM 2025 y Estado del Arte

Documento de fundamentación técnica (responde al feedback de asesores del hackathon).

Fuente oficial: **OWASP Top 10 for LLM Applications 2025**, OWASP GenAI Security Project
(noviembre 2024). https://genai.owasp.org/llm-top-10/

---

## Parte A — OWASP Top 10 LLM 2025: qué resuelve RAGE

La lista oficial 2025 y la relación con RAGE:

| # | Riesgo OWASP 2025 | ¿RAGE lo aborda? | Cómo |
|---|---|---|---|
| **LLM01** | **Prompt Injection** | ✅ **Sí, hoy (núcleo)** | Clasificación de intención + RAG de amenazas + decisión bloquean inyecciones directas, indirectas, payload splitting, ofuscación |
| **LLM02** | **Sensitive Information Disclosure** | 🟡 Parcial / con cambios | Detecta intentos de extracción; con filtro de **salida** puede redactar/bloquear fugas (PII, secretos) |
| LLM03 | Supply Chain | ❌ Fuera de alcance | Es de cadena de suministro de modelos/deps, no de runtime de prompts |
| LLM04 | Data and Model Poisoning | ❌ Fuera de alcance | Ocurre en entrenamiento/fine-tuning |
| **LLM05** | **Improper Output Handling** | 🟡 Con un par de cambios | Agregar una **capa de validación/sanitización de salida** (la arquitectura ya tiene el "punto de intercepción") |
| **LLM06** | **Excessive Agency** | 🟡 Con un par de cambios | El **motor de decisión** puede exigir aprobación/bloquear acciones de herramientas de alto riesgo (allow/warn/block sobre tool-calls) |
| **LLM07** | **System Prompt Leakage** | ✅ **Sí, hoy** | Detecta ataques que buscan filtrar el system prompt (es justo lo que mide el harness con canarios) |
| **LLM08** | **Vector and Embedding Weaknesses** | ⚠️ **Riesgo que RAGE introduce** | RAGE usa un vector store → hay que protegerlo (ver abajo) |
| **LLM09** | **Misinformation** | 🟡 Con cambios | Con validación de groundedness (RAG Triad) se puede señalar respuestas no fundamentadas |
| LLM10 | Unbounded Consumption | 🟡 Parcial | El gateway puede aplicar rate limiting / cuotas, pero no es el foco |

### Lo que RAGE resuelve HOY (mensaje principal para el pitch)

- **LLM01 Prompt Injection** — es *el* riesgo #1 de OWASP y el corazón de RAGE.
  Importante: los **escenarios de ataque que documenta OWASP para LLM01** (inyección directa,
  inyección indirecta vía documento, payload splitting, sufijo adversarial, ataque
  multilingüe/ofuscado con Base64) **ya están cubiertos en el dataset del harness** (`io-*`,
  `pi-*`, `co-002`, `ob-*`). Es decir: ya medimos exactamente los casos que OWASP describe.
- **LLM07 System Prompt Leakage** — los canarios del harness simulan fuga de instrucciones/
  secretos del system prompt; RAGE detecta y bloquea esos intentos.

### Lo que RAGE resuelve "con un par de cambios"

- **LLM05 Improper Output Handling** y **LLM02 Sensitive Information Disclosure**: agregar un
  **filtro de salida** (revisar la respuesta del LLM antes de devolverla). La arquitectura ya
  intercepta el flujo, así que es extender el gateway al lado de salida.
- **LLM06 Excessive Agency**: aplicar el motor de decisión **sobre las llamadas a herramientas**
  (no solo al texto), exigiendo human-in-the-loop para acciones privilegiadas. OWASP lo
  recomienda explícitamente para LLM01/LLM06.
- **LLM09 Misinformation**: incorporar la **"RAG Triad"** (relevancia de contexto, groundedness,
  relevancia pregunta/respuesta) que el propio OWASP sugiere como mitigación.

### Honestidad técnica: el riesgo que RAGE INTRODUCE (LLM08)

Como RAGE se basa en embeddings + vector store de amenazas, **hereda LLM08 (Vector and
Embedding Weaknesses)**: el KB podría ser envenenado, o sufrir inversión de embeddings.
Mitigaciones a incluir: control de acceso al store, validación de integridad de lo que se indexa,
y no almacenar datos sensibles en los vectores. **Mencionar esto en el pitch demuestra madurez.**

### Costo/beneficio frente a otros métodos (resumen)

| Método | Reduce LLM01 | Adaptable sin reentrenar | Explicable | Costo runtime |
|---|---|---|---|---|
| Solo system prompt | Débil | n/a | No | ~0 |
| RLHF del modelo (de fábrica) | Medio | ❌ (reentrenar) | No | 0 en inferencia |
| Clasificador fine-tuneado (Llama/Prompt Guard) | Alto en conocidos | ❌ (reentrenar) | Limitado | 1 llamada chica |
| **RAGE (RAG de amenazas)** | Alto | ✅ **agregar al KB** | ✅ **"se parece a ataque X"** | embeddings + búsqueda (≈ +1–15%) |

Diferenciador de RAGE: **adaptabilidad (nuevas amenazas sin reentrenar) + explicabilidad
(auditoría/compliance, mapeo directo a OWASP)**, con sobrecosto bajo (~+1–15% del costo del LLM
en diseño eficiente; ver `REPORT.md`). No gana en precisión cruda a un clasificador dedicado;
gana en mantenibilidad y trazabilidad.

---

## Parte B — Estado del arte y justificación de la arquitectura

### Por qué esta arquitectura (qué nos llevó a ella)

El estado del arte en defensa de prompt injection combina varias familias:

1. **Endurecimiento de system prompt / jerarquía de instrucciones** — universal pero débil solo.
2. **RLHF / rechazo de fábrica** — fuerte pero caro de entrenar y no actualizable por ti.
3. **Clasificadores guard** (Llama Guard, Prompt Guard, Lakera) — buenos, pero requieren
   reentrenar para amenazas nuevas.
4. **Frameworks de guardrails** (NeMo, Guardrails AI, Rebuff).
5. **Defensas basadas en retrieval (RAG)** — emergentes; permiten actualizar sin reentrenar.

RAGE elige la vía **RAG** porque OWASP, en sus mitigaciones de LLM01, recomienda explícitamente
**filtros semánticos**, **segregar/identificar contenido externo** y **pruebas adversariales**;
un KB de amenazas vectorizado encaja directamente y aporta dos ventajas que faltan en las otras
vías: **actualización sin reentrenar** y **explicabilidad** (traza al ataque conocido).

### ¿El orden de las capas es correcto en relación costo/calidad?

Orden conceptual original: **(1) Clasificación de intención → (2) RAG de amenazas → (3) Decisión**.

**Análisis honesto:** el orden conceptual es razonable, pero **para optimizar costo/calidad
conviene implementarlo como una *cascada con salida temprana (early-exit)***, ordenando las
etapas de **más barata/precisa a más cara**:

| Orden recomendado | Etapa | Costo | Rol |
|---|---|---|---|
| 1 | **Pre-filtro determinista** (reglas, firmas, denylist, regex) | ~0 | Atrapa lo obvio y sale temprano |
| 2 | **RAG de amenazas** (embeddings + similitud) | bajo | "¿se parece a un ataque conocido?" |
| 3 | **Clasificador de intención (LLM)** — **condicional** | alto | Solo si 1+2 son **ambiguos** |
| 4 | **Motor de decisión** | ~0 | **Fusiona** todas las señales → score allow/warn/block |

**Por qué este orden es mejor costo/calidad:**

- El componente **más caro es el clasificador de intención si usa una llamada a un LLM**. Ponerlo
  **primero y en cada request** dispara el costo. Ejecutarlo **solo cuando las etapas baratas no
  deciden** mantiene el sobrecosto cerca de **+1–5%** (la mayoría del tráfico se resuelve barato).
- **Matiz importante**: si la "clasificación de intención" se implementa con un **clasificador
  pequeño fine-tuneado** (no una llamada a LLM grande), es barata y rápida, y entonces **sí puede
  ir primero**. O sea: *el orden correcto depende de con qué se implemente la capa 1*.
- **Calidad de output**: el orden de las etapas **no degrada** la calidad final mientras el
  **motor de decisión fusione todas las señales** al final (no decidir en la primera etapa que
  dispare). Para minimizar **falsos positivos** (el costo de calidad más caro), el motor debe
  exigir **señales corroborantes** antes de un bloqueo duro, y usar las bandas (warn vs block).

**Conclusión Parte B:** mantener las 3 capas conceptuales, pero implementarlas como cascada
con early-exit y clasificador LLM condicional. Así se respeta la intención del diseño y se
optimiza la relación costo/calidad.

---

## Referencias

- OWASP Top 10 for LLM Applications 2025 — https://genai.owasp.org/llm-top-10/
- LLM01 Prompt Injection (escenarios y mitigaciones) — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- LLM08 Vector and Embedding Weaknesses — https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/
- Análisis de costo/beneficio detallado: ver `REPORT.md`.
