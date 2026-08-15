# Desviaciones frente al método original y limitaciones

Este documento contrasta la implementación con el método original de Zhao et
al. (2025) y delimita hasta dónde llega esta reproducción. Primero se detallan
las [desviaciones deliberadas](#desviaciones-deliberadas) frente al artículo;
luego se acotan las [limitaciones de alcance](#limitaciones-de-alcance) que
quedan fuera de esta implementación; y finalmente se proponen los pasos
naturales para cerrar esa brecha en el [trabajo futuro](#trabajo-futuro).

## Desviaciones deliberadas

Esta implementación se aparta del artículo original en un único punto
deliberado: la
[extracción de caminos de relaciones sin modelo especializado](#extracción-de-caminos-de-relaciones-sin-modelo-especializado),
que aquí no requiere entrenar ningún modelo. El resto del pipeline
[sigue el método original directamente](#todo-lo-demás-sigue-el-método-original-directamente),
sin modificaciones de fondo.

### Extracción de caminos de relaciones sin modelo especializado

El artículo original entrena un modelo de lenguaje específico para grafos de
conocimiento (denominado LLM_RoG en el artículo, basado en LLaMA-2-7B) siguiendo el
objetivo de las ecuaciones 4 a 6 (ver
[Formulación de la extracción de caminos de relaciones](01-marco-teorico.md#formulación-de-la-extracción-de-caminos-de-relaciones)):
maximizar la probabilidad de generar,
dada una pregunta, los caminos de relaciones más cortos entre la entidad tema y la
respuesta correcta en el grafo. Entrenar un modelo así requiere una GPU y un
conjunto de entrenamiento específico del grafo objetivo.

Esta implementación logra un efecto equivalente sin entrenamiento: en lugar de
optimizar los parámetros de un modelo para que prefiera relaciones anclables, se
calcula de antemano el vocabulario de relaciones que existen a pocos saltos de la
entidad tema (`KnowledgeGraph.neighborhood_relations`) y se restringe al modelo de
propósito general a elegir únicamente relaciones de ese vocabulario, descartando en
el post-procesamiento cualquier camino que use una relación fuera de él
(`_parse_paths` en `relation_paths.py`). El resultado —caminos garantizados
anclables en el grafo real— es el mismo que persigue el objetivo de entrenamiento
original, pero logrado por restricción de vocabulario en tiempo de inferencia en
lugar de por ajuste de parámetros.

### Todo lo demás sigue el método original directamente

La generación de respuestas adversarias mediante coincidencia difusa contra el
vocabulario de entidades del grafo, y la inserción de tripletas de perturbación con
su estrategia de respaldo mediante entidades puente, se implementan siguiendo
directamente la descripción del artículo, sin modificaciones de fondo.

## Limitaciones de alcance

- **No se integra ningún sistema KG-RAG objetivo.** El artículo evalúa el ataque
  contra cuatro sistemas (RoG, GCR, G-retriever, SubgraphRAG) sobre los benchmarks
  WebQSP y CWQ, midiendo la caída de métricas de desempeño (Hit, F1, Hits@1, EM) y
  el éxito de la manipulación adversaria (A-Precision, A-H@1, A-MRR). Esta
  implementación se detiene en la construcción del grafo envenenado: no incluye
  ningún recuperador ni generador que consuma ese grafo para producir una
  respuesta final, así que ninguna de esas métricas puede calcularse aquí. La
  validación se limita a inspeccionar directamente las tripletas insertadas.
- **Sin benchmarks a gran escala.** La demostración usa un único grafo construido a
  mano con 13 tripletas, en lugar de los subgrafos de WebQSP/CWQ (miles de
  preguntas, con un promedio de más de 4000 tripletas por subgrafo). Esto permite
  verificar el comportamiento del ataque paso a paso, pero no dice nada sobre su
  efectividad agregada a la escala evaluada en el artículo.
- **Modelo de lenguaje distinto.** El artículo usa GPT-4 para generar respuestas
  adversarias; esta implementación usa `gpt-4o-mini` por defecto (configurable en
  `OpenAIClient`), lo que puede producir candidatos de menor calidad o con menor
  diversidad semántica.

## Trabajo futuro

- Integrar un recuperador simple (por ejemplo, un algoritmo de anchura acotada
  sobre el grafo envenenado) y un generador basado en LLM, para poder medir el
  efecto del ataque sobre una respuesta final y no solo sobre la estructura del
  grafo.
- Ejecutar el ataque sobre un subconjunto real de WebQSP o CWQ para obtener cifras
  de degradación comparables, aunque sea a pequeña escala, con las reportadas en el
  artículo (Tabla 3 y Tabla 4 del artículo original).
- Explorar si un modelo de propósito general, guiado con la misma restricción de
  vocabulario pero con ejemplos de caminos correctos en el prompt (aprendizaje en
  contexto), puede acercarse a la calidad de un modelo específico de grafos como
  LLM_RoG sin necesidad de ajuste de parámetros.

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
