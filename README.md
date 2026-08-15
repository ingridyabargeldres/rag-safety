# rag-safety

Reproducción del pipeline de ataque de envenenamiento de conocimiento en caja
negra contra sistemas KG-RAG, descrito en Zhao et al., *"RAG Safety: Exploring
Knowledge Poisoning Attacks to Retrieval-Augmented Generation"*
([arXiv:2507.08862](https://arxiv.org/abs/2507.08862)).

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

Este repositorio implementa el **pipeline de ataque** de tres etapas (generación
de respuestas adversarias → extracción de caminos de relaciones → inserción de
tripletas de perturbación), ejecutable contra cualquier grafo de conocimiento en
memoria. No integra los cuatro sistemas KG-RAG objetivo evaluados en el artículo
(RoG, GCR, G-retriever, SubgraphRAG) ni los benchmarks WebQSP/CWQ.

## Desviaciones frente al artículo

- **Extracción de caminos de relaciones** (Sección 3.2 del artículo): el
  artículo entrena un LLM específico de grafos de conocimiento (LLM_RoG). Esta
  reproducción, en cambio, prompea un LLM de propósito general (OpenAI) pero
  restringe su vocabulario de relaciones al que realmente existe cerca de la
  entidad tema en el grafo (`KnowledgeGraph.neighborhood_relations`), de modo que
  los caminos generados queden anclados sin requerir GPU ni un modelo
  ajustado. Ver `src/kgrag_attack/relation_paths.py`.
- El resto del pipeline (generación de respuestas adversarias mediante
  coincidencia difusa, Sección 3.1; inserción de perturbación con la estrategia
  de respaldo, Sección 3.3) sigue el artículo directamente.

Detalle completo en [docs/proposal/05-desviaciones-limitaciones.md](docs/proposal/05-desviaciones-limitaciones.md).

## Instalación

```bash
pip install -r requirements.txt
cp .env.example .env   # completar OPENAI_API_KEY
```

## Uso

Ejecutar el ataque contra un grafo pequeño construido a mano que reproduce el
ejemplo de "Manchester By The Sea" del artículo:

```bash
python scripts/demo_manchester.py            # usa OPENAI_API_KEY
python scripts/demo_manchester.py --offline  # sin llamadas a la API, LLM simulado y determinista
```

Para atacar un grafo propio, ver `src/kgrag_attack/attack.py::run_attack`:

```python
from kgrag_attack.attack import run_attack
from kgrag_attack.kg import KnowledgeGraph
from kgrag_attack.llm import OpenAIClient

kg = KnowledgeGraph.from_triples([...])
result = run_attack(kg, question="...", topic_entity="...", llm=OpenAIClient())
result.poisoned_kg           # grafo con las tripletas de perturbación insertadas
result.perturbation_triples  # tripletas insertadas por cada respuesta adversaria
```

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
