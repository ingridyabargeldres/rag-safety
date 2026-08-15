# Introducción y motivación

Este documento presenta la motivación del proyecto, su objetivo concreto, el
alcance de lo implementado y la estructura del resto de la documentación.
Primero se explica por qué los sistemas KG-RAG son vulnerables a la inserción de
conocimiento falso ([Motivación](#motivación)); luego se precisa qué reproduce
esta implementación ([Objetivo de la implementación](#objetivo-de-la-implementación));
a continuación se delimita qué queda fuera de ese alcance
([Alcance de esta reproducción](#alcance-de-esta-reproducción)); y finalmente
se ofrece un mapa de los demás documentos
([Estructura de esta documentación](#estructura-de-esta-documentación)).

## Motivación

Los sistemas de generación aumentada por recuperación (RAG) permiten que un modelo de
lenguaje responda apoyándose en una fuente de conocimiento externa en lugar de
depender únicamente de lo que memorizó durante el entrenamiento. Cuando esa fuente
externa es un grafo de conocimiento (KG), el sistema puede seguir caminos de
razonamiento explícitos —entidad por entidad, relación por relación— en vez de
recuperar simples fragmentos de texto. Esto se conoce como KG-RAG y resulta
especialmente atractivo en dominios donde la trazabilidad de la respuesta importa
(por ejemplo, diagnóstico médico o análisis legal), porque el camino de razonamiento
recuperado sirve como justificación interpretable de la respuesta final.

Esa misma propiedad que hace atractivo a KG-RAG —la posibilidad de editar el grafo
para mantenerlo actualizado— es también su punto débil. Un grafo de conocimiento
editable puede ser alterado por un tercero con acceso de escritura, insertando un
pequeño número de hechos falsos pero plausibles. A diferencia de un documento de
texto libre, una tripleta `(cabeza, relación, cola)` es una unidad de información
muy compacta y estructurada: basta con insertar una sola arista falsa en el lugar
correcto del grafo para desviar un camino de razonamiento multi-salto completo
hacia una conclusión incorrecta, sin que el resto del grafo se vea alterado ni la
manipulación resulte evidente a simple vista (Zhao et al., 2025).

Este proyecto documenta una implementación propia del ataque de envenenamiento
de conocimiento contra sistemas KG-RAG propuesto por Zhao et al. (2025): dado un grafo de
conocimiento limpio y una pregunta, el ataque identifica primero
qué respuestas incorrectas conviene inducir, luego determina qué patrón de
relaciones seguiría un sistema KG-RAG al razonar sobre esa pregunta, y finalmente
inserta el número mínimo de tripletas necesario para completar una cadena de
inferencia engañosa que termine en esas respuestas incorrectas. Todo el proceso
opera en modo caja negra: el atacante no necesita conocer ni la arquitectura del
sistema KG-RAG objetivo, ni sus parámetros internos, ni las respuestas correctas de
la pregunta que está atacando; su única vía de acción es el propio grafo de
conocimiento.

## Objetivo de la implementación

Reproducir el pipeline de ataque de tres etapas —[generación de respuestas
adversarias](02-metodo-de-ataque.md#etapa-1--generación-de-respuestas-adversarias),
[extracción de caminos de relaciones](02-metodo-de-ataque.md#etapa-2--extracción-de-caminos-de-relaciones)
e [inserción de tripletas de
perturbación](02-metodo-de-ataque.md#etapa-3--inserción-de-tripletas-de-perturbación)—
de forma ejecutable contra cualquier grafo de conocimiento en
memoria, validando cada etapa con pruebas automatizadas y con una demostración de
extremo a extremo sobre un caso concreto y verificable a mano.

## Alcance de esta reproducción

Esta implementación cubre el **pipeline de ataque** en su totalidad, pero no
integra ninguno de los cuatro sistemas KG-RAG objetivo (RoG, GCR, G-retriever,
SubgraphRAG) ni los benchmarks WebQSP/CWQ. En su lugar, el ataque se valida
insertando las tripletas de perturbación en un grafo de conocimiento propio y
verificando —por inspección directa del grafo— que las nuevas aristas completan
efectivamente un camino de razonamiento hacia la respuesta adversaria. El detalle de
esta y otras desviaciones respecto al método original se documenta en
[Desviaciones frente al método original y limitaciones](05-desviaciones-limitaciones.md).

## Estructura de esta documentación

1. [Marco teórico](01-marco-teorico.md) — definiciones y fórmulas que sustentan el ataque, interpretadas.
2. [Método de ataque: las tres etapas](02-metodo-de-ataque.md) — las tres etapas del ataque, mapeadas a la implementación.
3. [Arquitectura de la implementación](03-arquitectura-implementacion.md) — organización del código, módulo por módulo.
4. [Réplica del experimento](04-replicacion-experimentos.md) — réplica ejecutable del ataque con salida real.
5. [Desviaciones frente al método original y limitaciones](05-desviaciones-limitaciones.md) — diferencias frente al método original y trabajo futuro.

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
