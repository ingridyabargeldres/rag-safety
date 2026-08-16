# rag-safety

Reproducción del pipeline de ataque de envenenamiento de conocimiento en caja
negra contra sistemas KG-RAG (*Knowledge Graph–Retrieval-Augmented
Generation*), descrito en Zhao et al. (2025). El repositorio implementa las
tres etapas del ataque de forma ejecutable contra cualquier grafo de
conocimiento en memoria, documenta su fundamento teórico y valida cada etapa
mediante pruebas automatizadas.

## Autora

| Campo | Valor |
|---|---|
| Nombre | Ingrid Alicia Yábar Geldres |
| Universidad | Universidad Nacional de Ingeniería (UNI) |
| Facultad | Facultad de Ingeniería Económica, Estadística y Ciencias Sociales |
| Programa | Doctorado en Ciencias e Ingeniería Estadística |
| ORCID | [0009-0003-9729-3259](https://orcid.org/0009-0003-9729-3259) (Investigadora RENACYT) |
| Correo | ingrid.yabar.g@uni.pe |

## Alcance

Este repositorio implementa el **pipeline de ataque** de tres etapas
(generación de respuestas adversarias → extracción de caminos de relaciones →
inserción de tripletas de perturbación), ejecutable contra cualquier grafo de
conocimiento en memoria. No integra los cuatro sistemas KG-RAG objetivo
evaluados en el artículo (RoG, GCR, G-retriever, SubgraphRAG) ni los
benchmarks WebQSP/CWQ.

## Desviaciones frente al artículo

- **Extracción de caminos de relaciones** (Sección 3.2 del artículo): el
  artículo entrena un LLM específico de grafos de conocimiento (LLM_RoG). Esta
  reproducción, en cambio, prompea un LLM de propósito general (OpenAI) pero
  restringe su vocabulario de relaciones al que realmente existe cerca de la
  entidad tema en el grafo (`KnowledgeGraph.neighborhood_relations`), de modo
  que los caminos generados queden anclados sin requerir GPU ni un modelo
  ajustado. Ver [src/kgrag_attack/relation_paths.py](src/kgrag_attack/relation_paths.py).
- El resto del pipeline (generación de respuestas adversarias mediante
  coincidencia difusa, Sección 3.1; inserción de perturbación con la
  estrategia de respaldo, Sección 3.3) sigue el artículo directamente.

Detalle completo en [Desviaciones frente al método original y limitaciones](docs/proposal/05-desviaciones-limitaciones.md).

## Instalación

```bash
pip install -r requirements.txt
cp .env.example .env   # completar OPENAI_API_KEY
```

## Uso

### Ejecución rápida (demo)

`scripts/demo_manchester.py` construye a mano un grafo de conocimiento de 13
tripletas alrededor de la película *Manchester By The Sea* y ejecuta el
ataque completo de extremo a extremo:

```bash
python scripts/demo_manchester.py            # usa OPENAI_API_KEY
python scripts/demo_manchester.py --offline  # sin llamadas a la API, LLM simulado y determinista
python scripts/demo_manchester.py --n-answers 3 --budget-k 4
```

### Uso programático

`run_attack` acepta cualquier grafo propio como lista de tripletas
`(cabeza, relación, cola)`, una pregunta en lenguaje natural, la entidad tema
de esa pregunta y un cliente LLM. El siguiente ejemplo reproduce, de forma
reducida, el caso de "Manchester By The Sea" documentado en
[Réplica del experimento](docs/proposal/04-replicacion-experimentos.md):

```python
from kgrag_attack.attack import run_attack
from kgrag_attack.kg import KnowledgeGraph
from kgrag_attack.llm import OpenAIClient

question = 'Which country is the movie "Manchester By The Sea" filmed in?'
topic_entity = "Manchester By The Sea"

triples = [
    ("Manchester By The Sea", "filmPlace", "Manchester"),
    ("Manchester By The Sea", "starring", "Casey Affleck"),
    ("Manchester", "locatedIn", "Massachusetts"),
    ("Massachusetts", "stateOf", "United States"),
    ("Casey Affleck", "bornIn", "Massachusetts"),
    ("Miami", "locatedIn", "Florida"),
    ("Florida", "stateOf", "United States"),
]

kg = KnowledgeGraph.from_triples(triples)
result = run_attack(kg, question, topic_entity, llm=OpenAIClient())

result.adversarial_answers    # respuestas incorrectas candidatas, p. ej. ['Florida']
result.relation_paths         # caminos de relaciones anclables, p. ej. [('filmPlace', 'locatedIn')]
result.perturbation_triples   # {'Florida': [('Manchester', 'locatedIn', 'Florida')]}
result.poisoned_kg            # grafo original + tripletas de perturbación insertadas
```

`OpenAIClient` no es determinista (temperatura 0.7 por defecto), por lo que
`adversarial_answers`, `relation_paths` y `perturbation_triples` pueden variar
entre ejecuciones; para un resultado reproducible en pruebas o demostraciones,
sustituir `OpenAIClient()` por `StaticLLMClient([...])` (ver
[src/kgrag_attack/llm.py](src/kgrag_attack/llm.py)).

`run_attack` admite además los parámetros `n_answers` (respuestas adversarias
candidatas a generar, por defecto 5), `budget_k` (tripletas de perturbación
máximas por respuesta, por defecto 4), `n_paths` (caminos de relaciones a
generar, por defecto 3), `max_hops` (longitud máxima de esos caminos, por
defecto 3) y `seed` (semilla opcional para la estrategia de respaldo del
anclaje). Firma completa en [src/kgrag_attack/attack.py](src/kgrag_attack/attack.py).

## Tests

```bash
python -m pytest
```

Todas las pruebas son offline (sin llamadas a la API) y cubren la lógica
determinista del grafo y de la perturbación, además del parseo de prompts
mediante un cliente LLM simulado.

## Documentación

- [docs/proposal/](docs/proposal/) — documentación detallada de la
  implementación, en varios archivos:
  1. [00-introduccion.md](docs/proposal/00-introduccion.md) — motivación y objetivo.
  2. [01-marco-teorico.md](docs/proposal/01-marco-teorico.md) — definiciones y fórmulas del artículo, interpretadas.
  3. [02-metodo-de-ataque.md](docs/proposal/02-metodo-de-ataque.md) — las tres etapas, mapeadas a la implementación.
  4. [03-arquitectura-implementacion.md](docs/proposal/03-arquitectura-implementacion.md) — organización del código.
  5. [04-replicacion-experimentos.md](docs/proposal/04-replicacion-experimentos.md) — ejecución de extremo a extremo con salida real.
  6. [05-desviaciones-limitaciones.md](docs/proposal/05-desviaciones-limitaciones.md) — diferencias frente al método original.
- [docs/presentation/](docs/presentation/) — presentación en beamer
  (`presentacion.tex` / `presentacion.pdf`) para exposición en clase.

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
