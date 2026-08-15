# Arquitectura de la implementación

Este documento describe cómo está organizado el código de la implementación y
qué responsabilidad tiene cada módulo. Primero se presenta el árbol de
directorios del proyecto (Organización del proyecto); luego se detallan los dos
módulos de infraestructura que comparten las tres etapas del ataque —el grafo
de conocimiento y el cliente de modelo de lenguaje— (`kg.py` y `llm.py`); a
continuación se describe la orquestación que las combina (`attack.py`); y
finalmente se resume la cobertura de las pruebas automatizadas (Pruebas
automatizadas). Los tres módulos que implementan cada etapa del ataque
(`adversarial_answers.py`, `relation_paths.py`, `perturbation.py`) se describen
en [Método de ataque: las tres etapas](02-metodo-de-ataque.md), no en este
documento.

## Organización del proyecto

```
rag-safety/
├── src/kgrag_attack/
│   ├── kg.py                  # grafo de conocimiento en memoria
│   ├── llm.py                 # cliente de LLM (OpenAI real + stub determinista)
│   ├── adversarial_answers.py # etapa 1
│   ├── relation_paths.py      # etapa 2
│   ├── perturbation.py        # etapa 3
│   └── attack.py              # orquestación de las tres etapas
├── scripts/
│   └── demo_manchester.py     # réplica ejecutable de extremo a extremo
├── tests/                     # 18 pruebas, totalmente offline
└── docs/proposal/, docs/presentation/
```

La fuente teórica de esta implementación es Zhao et al. (2025).

## `kg.py` — grafo de conocimiento

`KnowledgeGraph` es una estructura mínima en memoria: un conjunto de tripletas
`(cabeza, relación, cola)` más un índice de adyacencia (`_out`) para resolver
aristas salientes en tiempo constante. Expone las operaciones que el resto del
ataque necesita:

- `add_triple` / `with_triples` — inserción de tripletas (esta última devuelve un
  grafo nuevo, sin mutar el original — así el grafo "limpio" original queda
  siempre disponible para comparar contra el grafo "envenenado").
- `neighborhood_relations` — recorrido en anchura que acumula el vocabulario de
  relaciones alcanzables en, como máximo, `max_hops` saltos desde una entidad; usado
  para restringir qué relaciones puede proponer el modelo en la etapa 2.
- `ground` — sigue una secuencia de relaciones desde una entidad de inicio y
  devuelve el conjunto de entidades alcanzadas; es la operación de anclaje
  descrita en el marco teórico, usada en la etapa 3.
- `random_entity` — muestreo aleatorio de una entidad del grafo (con exclusiones),
  usado por la estrategia de respaldo de la etapa 3.

## `llm.py` — cliente de modelo de lenguaje

Define el protocolo `LLMClient` (`complete(prompt, *, system=None) -> str`) con dos
implementaciones intercambiables:

- `OpenAIClient` — llama a la API de chat de OpenAI (modelo `gpt-4o-mini` por
  defecto). Carga `OPENAI_API_KEY` desde el entorno o desde un archivo `.env`.
- `StaticLLMClient` — devuelve una lista de respuestas predefinidas, una por
  llamada. Permite ejecutar el pipeline completo y las pruebas automatizadas sin
  ninguna llamada de red, fijando de antemano qué "respondería" el modelo en cada
  etapa.

Que ambas etapas 1 y 2 dependan únicamente del protocolo `LLMClient` —y no de
`OpenAIClient` directamente— es lo que permite sustituir el modelo real por el stub
determinista sin tocar el código de las etapas.

## `attack.py` — orquestación

`run_attack` llama a las tres etapas en orden y empaqueta todo lo producido en un
`AttackResult`: la pregunta y entidad tema originales, las respuestas adversarias
generadas, los caminos de relaciones generados, las tripletas de perturbación
insertadas (agrupadas por respuesta adversaria) y ambos grafos —el limpio y el
envenenado— para poder compararlos directamente.

## Pruebas automatizadas

Las 18 pruebas del proyecto (`tests/`) se ejecutan íntegramente sin acceso a red,
usando `StaticLLMClient` para fijar las respuestas del modelo:

| Archivo | Qué verifica |
|---|---|
| `test_kg.py` | Inserción de tripletas, anclaje (`ground`), vocabulario de vecindad (`neighborhood_relations`), inmutabilidad de `with_triples`. |
| `test_adversarial_answers.py` | Parseo de listas con viñetas, coincidencia difusa contra el vocabulario del grafo, reintento en múltiples rondas hasta reunir `n` respuestas válidas. |
| `test_relation_paths.py` | Parseo de caminos, descarte de relaciones fuera del vocabulario permitido, descarte de caminos que exceden `max_hops`. |
| `test_perturbation.py` | Construcción de tripletas por la estrategia principal, activación de la estrategia de respaldo cuando un camino no se puede anclar, respeto del presupuesto `budget_k`, no duplicación de tripletas ya existentes. |

Ejecución:

```bash
python -m pytest -q
```

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
