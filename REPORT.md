# RAGE — Reporte de estado y plan de hackathon

> Retrieval-Augmented Governance Engine — capa de seguridad contra prompt injection,
> jailbreaks y uso malicioso de sistemas de IA.

## 1. Qué tenemos hoy

Un **harness de medición** (`rage_bench`) que cuantifica *qué tan grave* es el problema de
prompt injection / jailbreak. Es la base de evidencia del proyecto.

- **18 ataques** en 9 categorías: instruction override, role-play/DAN, inyección indirecta
  (en documentos y output de herramientas falsas), ofuscación (base64/leetspeak), supresión
  de rechazo, ingeniería social, indirección, sobrecarga de contexto, secuestro de comportamiento.
- **Métricas**: Attack Success Rate (ASR) por categoría + un **score de severidad 0–100** con
  bandas (`NONE` / `LOW` / `ELEVATED` / `CRITICAL`).
- **Método seguro**: medimos con *canarios inofensivos* (un código secreto que el modelo no
  debe revelar, o un token prohibido pero inocuo). Nunca se solicita ni produce contenido dañino real.
- **Proveedores**: `mock` (offline, sin API key) y `openai` / `anthropic` (modelo real).
- **Estado**: Python + uv, 19 tests pasando, lint limpio, CLI funcional.

Demo offline actual:

| Modelo simulado | ASR | Severidad |
|---|---|---|
| `vulnerable` | 100.0% | 100/100 CRÍTICO |
| `guarded` | 44.4% | 40.3/100 ELEVADO |
| `hardened` (estilo RAGE) | 0.0% | 0/100 NONE |

> Ya podemos demostrar el *problema* y el *objetivo*. Lo que falta es construir la defensa
> real que lleve a un LLM real de "vulnerable" a "hardened".

## 2. Qué falta para una demo funcional en "casos graves"

Un "caso grave" = un agente con herramientas conectadas a datos/acciones (DB, API, correo)
donde una inyección causa daño real (fuga de datos, acción no autorizada).

| Pieza | Qué es | Riesgo / dificultad |
|---|---|---|
| **Motor RAGE (3 capas)** | (1) clasificador de intención, (2) base RAG de amenazas con vector store, (3) motor de decisión riesgo→allow/warn/block | Núcleo del proyecto; el RAG + vector store es lo más invasivo |
| **Escenario grave demo** | Agente vulnerable de ejemplo (chatbot con "herramienta" que lee un dato sensible) que SÍ cae sin RAGE | Bajo; reutiliza la lógica de canarios del harness |
| **Evidencia antes/después** | Correr el harness contra un LLM real **sin** RAGE vs **con** RAGE en medio | Bajo una vez exista el gateway; requiere **API key** |
| **Gateway / middleware** | Capa que intercepta el prompt, lo pasa por RAGE y bloquea/deja pasar | Medio; conecta todo |
| **Capa de presentación** | CLI con tabla (ya existe) o mini-dashboard web mostrando score y bloqueo en vivo | Bajo / medio según si es web |
| **Infra / secretos** | `OPENAI_API_KEY` o `ANTHROPIC_API_KEY`; vector store (en memoria sirve para la demo) | Bajo |

**Bloqueante inmediato**: una **API key** (OpenAI o Anthropic) para medir modelos reales y
demostrar el caso grave end-to-end.

## 3. Reparto del flujo con Cursor (sábado y domingo)

Trabajar en **ramas separadas en paralelo**, lanzando **agentes de Cursor (cloud) por feature**,
cada uno con su PR.

### Sábado — construir el núcleo (en paralelo)

- **Track A — Decisión + Gateway**: motor de decisión (score→allow/warn/block) y middleware que
  envuelve al LLM. → rama `cursor/decision-engine`.
- **Track B — Capa RAG**: base de amenazas + vector store (en memoria está bien para demo) y
  cálculo de similitud. → rama `cursor/rag-threat-kb`.
- **Track C — Clasificador de intención**: clasificador (LLM pequeño o reglas) de las categorías.
  → rama `cursor/intent-classifier`.
- **Cierre del sábado**: integrar A+B+C tras un LLM real y correr el harness existente → primer
  número "con RAGE".

### Domingo — demo + evidencia + pulido

- **Escenario grave** (agente vulnerable de ejemplo) + **comparativa antes/después** usando el
  harness ya hecho.
- **Presentación**: tabla/dashboard del ASR cayendo de CRÍTICO a NONE con RAGE activo.
- **Buffer**: ajustar umbrales, casos extra de ataque, ensayar pitch.

### Cómo aprovechar Cursor en concreto

- Un **cloud agent por track**, cada quien revisa su PR → menos conflictos.
- El harness actual es el **test de regresión**: cada feature se valida corriendo
  `uv run rage-bench` contra el modelo real.
- Tareas chicas y bien descritas a los agentes (ej. "implementa la capa de decisión con estos
  umbrales y tests").

## Pendientes para arrancar

- [ ] Definir el **caso grave** a lucir (ej. fuga de dato de cliente vs acción no autorizada).
- [ ] Agregar **API key** (`OPENAI_API_KEY` o `ANTHROPIC_API_KEY`) para medir modelos reales.
- [ ] Crear ramas por track y asignar responsables.
