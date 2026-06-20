# Prompt para Track B — RAG Threat Knowledge Base (pegar en chat/repo nuevo)

> Copia TODO el bloque de abajo y pégalo como primer mensaje en el chat nuevo (con el repo en
> blanco). Es autosuficiente: lleva el contexto, la arquitectura, el alcance y los criterios de
> aceptación.

---

Eres un agente de ingeniería. Vamos a construir, **desde cero y en un repo en blanco**, el
**Track B** del proyecto **RAGE**. Lee todo este contexto antes de empezar y trabaja de forma
autónoma: configura el entorno, implementa, **ejecuta y prueba end-to-end**, y muéstrame
evidencia real (no asumas que algo funciona sin correrlo).

## Contexto del proyecto (RAGE)

- **RAGE (Retrieval-Augmented Governance Engine)** es una **capa de seguridad que se coloca
  delante de un LLM** (chatbots y, sobre todo, agentes conectados a APIs/bases de datos) para
  **detectar y contener prompt injection y jailbreaks** — el riesgo nº1 del **OWASP Top 10 para
  LLM 2025 (LLM01)**.
- **Honestidad técnica (importante):** la idea de detección por *retrieval* de amenazas **ya
  existe** (papers RAD [arXiv 2508.16406], RePD; herramientas Vigil, Rebuff). **No** lo presentes
  como un algoritmo nuevo. El valor de RAGE es de **integración, gobernanza, explicabilidad,
  actualización en caliente y medición**.
- **Metodología SEGURA de medición:** la susceptibilidad se mide con **canarios inofensivos**
  (p. ej. un código secreto que el modelo no debe revelar, o un token prohibido pero inocuo).
  **Nunca** se solicita ni produce contenido dañino real.

## Arquitectura de RAGE (cascada con salida temprana / early-exit)

El tráfico pasa por capas ordenadas de **más barata/precisa a más cara** (la mayoría se resuelve
barato; el LLM solo se invoca en casos ambiguos):

1. **Capa 1 — Pre-filtro determinista** (reglas/firmas/regex) · costo ~0
2. **Capa 2 — RAG de amenazas (KB)** ← **ESTO ES LO QUE CONSTRUIMOS EN TRACK B**
3. **Capa 3 — Filtro semántico dinámico** (intención, con estado / multi-turno)
4. **Capa 4 — Motor de decisión** (fusiona señales → score 0–100, bandas allow/warn/block, umbral ajustable)
5. **Gateway de acciones + verificación de salida** (gatea tool-calls; valida la respuesta)

Track B debe **exponer una señal limpia** que las capas 3 y 4 (otros tracks) puedan consumir.
**No** construyas el motor de decisión, el filtro de intención ni el gateway aquí.

## Alcance de Track B (qué construir)

Un módulo de **base de conocimiento de amenazas basada en RAG** que, dado un texto de entrada
(prompt del usuario y/o contenido recuperado/documento), devuelva una **señal de amenaza**:
puntaje de similitud con ataques conocidos + metadatos del ataque coincidente (categoría,
técnica, mapeo OWASP, severidad) para **explicabilidad**.

Componentes:

1. **Corpus de amenazas (KB):** dataset curado de patrones de ataque conocidos, etiquetados con
   `category`, `technique`, `owasp_id`, `severity`. Semilla con familias de **OWASP LLM01**:
   override directo ("ignore previous instructions"), inyección indirecta (en documento / tool
   output), payload splitting, ofuscación (base64/leetspeak), roleplay/DAN, supresión de rechazo,
   ingeniería social, indirección/traducción. Formato **JSON o YAML**, fácil de extender.
2. **Embeddings (interfaz intercambiable):** provee un **embedder offline por defecto, SIN API
   key** (p. ej. `sentence-transformers` local, o un fallback TF-IDF/hashing si no quieres
   descargar modelos) **y** un proveedor opcional de **OpenAI embeddings** (detrás de
   `OPENAI_API_KEY`). El camino offline DEBE funcionar sin clave.
3. **Vector store:** **en memoria** (numpy + similitud coseno) para la demo, detrás de una
   interfaz para poder cambiarlo luego (Chroma/FAISS).
4. **Recuperación + scoring:** top-k por similitud, agregado a un **score 0–1 (o 0–100)** con
   **umbral ajustable**; devuelve los ejemplos coincidentes (para explicabilidad).
5. **Actualización en caliente (`add_threat`)**: agregar un ejemplo al KB mejora la detección
   **sin reentrenar** — este es un diferenciador clave (hipótesis H4).

## Contrato de interfaz (para integrar con otros tracks después)

Define una API clara y estable, por ejemplo:

- `ThreatRetriever.score(text: str) -> ThreatSignal`
- `ThreatSignal{ score: float, band: str, matches: list[ThreatMatch], latency_ms: float }`
- `ThreatMatch{ id, category, technique, owasp_id, severity, similarity }`
- `ThreatRetriever.add_threat(example) -> None`  (hot update, sin reentrenar)

## Stack y convenciones

- **Python 3.10+**, gestionado con **uv** (uv-native: `pyproject.toml` + `uv.lock`,
  `[dependency-groups] dev`, y extras). Deben funcionar: `uv sync`, `uv run pytest`,
  `uv run ruff check .`. (Nota: `[dependency-groups]` requiere uv ≥ 0.4.27; expón también un
  extra `dev` para compatibilidad: `uv sync --extra dev`.)
- Lint con **ruff**, tests con **pytest** (usa `pythonpath = ["."]`, sin editable install).
- **Offline-first:** todo debe correr end-to-end **sin API key**; los embeddings por API son
  opcionales.
- **Seguridad (OWASP LLM08):** trata el **contenido del KB y el texto recuperado como NO
  confiables**; escanea/sanitiza lo que se indexa (el vector store es un vector de ataque).

## Entregables

- Paquete `rage_rag/` (o nombre similar) con los componentes anteriores.
- **CLI/demo**: dado un prompt, imprime el score de amenaza + los ataques conocidos coincidentes.
- **Tests pytest**: validez del dataset; determinismo del embedder; correctitud de recuperación
  (un ataque conocido puntúa alto; un prompt benigno puntúa bajo); la **actualización en caliente**
  mejora la detección de una familia nueva.
- **README** con setup/run, esquema del KB y cómo extenderlo.

## Criterios de aceptación

- Ataques conocidos (de un set held-out) obtienen **score alto**; prompts benignos, **score bajo**
  (reporta separación / precisión-recall básica).
- Mide y expón **latencia** por consulta (y costo si se usa API).
- **Demuestra H4:** agregar un ataque nuevo al KB hace que una variante antes no detectada de esa
  familia pase a puntuar alto, **sin reentrenar**.

## Fuera de alcance (otros tracks)

Motor de decisión/bandas y gateway (Track A), filtro de intención con estado (Track C), métrica
**AUC de degradación multi-turno**. Aquí solo expón la señal de amenaza.

## Forma de trabajar

1. Explora/planifica, crea el `pyproject.toml` y el layout.
2. Implementa por partes, **corriendo tests** conforme avanzas.
3. Al final, ejecuta la demo y **muéstrame la salida real** (CLI + pytest + ruff).
4. Pídeme una API key **solo** si la quieres para los embeddings opcionales; el camino offline
   debe funcionar sin ella.

Empieza confirmando brevemente tu plan y luego procede.
