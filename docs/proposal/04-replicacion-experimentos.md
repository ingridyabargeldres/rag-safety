# Réplica del experimento

Esta sección documenta la ejecución real del ataque implementado en este
repositorio, de extremo a extremo, sobre un caso de prueba construido a mano y
verificable por inspección directa.

## Preparación del entorno

```bash
pip install -r requirements.txt
cp .env.example .env   # completar OPENAI_API_KEY si se quiere usar el modelo real
```

## Caso de prueba: "Manchester By The Sea"

`scripts/demo_manchester.py` construye a mano un grafo de conocimiento pequeño con
13 tripletas alrededor de la película *Manchester By The Sea*, y ataca la pregunta
`"Which country is the movie \"Manchester By The Sea\" filmed in?"` con la entidad
tema `Manchester By The Sea`. El grafo limpio incluye, entre otras, las tripletas:

```
(Manchester By The Sea, filmPlace, Manchester)
(Manchester By The Sea, starring, Casey Affleck)
(Manchester, locatedIn, Massachusetts)
(Casey Affleck, bornIn, Massachusetts)
(David Beckham, bornIn, England)
(England, containedIn, United Kingdom)
```

La respuesta correcta a la pregunta es "Estados Unidos" (por la cadena
`Manchester By The Sea → filmPlace → Manchester → locatedIn → Massachusetts →
stateOf → United States`), pero el grafo también contiene, sin relación con la
película, hechos verídicos sobre otra persona (David Beckham) que mencionan
"England" y "United Kingdom" — el tipo de coincidencia superficial que el ataque
puede explotar para construir una respuesta adversaria plausible.

El script se puede ejecutar en dos modos:

```bash
python scripts/demo_manchester.py            # usa OPENAI_API_KEY si está definida
python scripts/demo_manchester.py --offline  # LLM simulado y determinista, sin llamadas a la API
```

En modo `--offline`, el modelo de lenguaje se reemplaza por `StaticLLMClient` con
dos respuestas fijas: una lista de países como respuestas adversarias (imitando lo
que un modelo real propondría para esta pregunta) y dos caminos de relaciones
(`filmPlace -> locatedIn` y `starring -> bornIn`). Esto hace que la ejecución sea
determinista y reproducible sin depender de una clave de API.

## Salida real de la ejecución (`--offline`)

```
Question: Which country is the movie "Manchester By The Sea" filmed in?
Topic entity: Manchester By The Sea
Clean KG: 13 triples

Adversarial target answers: ['United Kingdom']
Relation path templates: [('filmPlace', 'locatedIn'), ('starring', 'bornIn')]

Injected perturbation triples:
  (Manchester, locatedIn, United Kingdom)   [target: United Kingdom]
  (Casey Affleck, bornIn, United Kingdom)   [target: United Kingdom]

Poisoned KG: 15 triples (+2 vs. clean)

--- Retrieval simulation: outgoing edges near the topic entity ---
Before attack:
  Manchester By The Sea --director--> Kenneth Lonergan
  Manchester By The Sea --filmPlace--> Manchester
  Manchester By The Sea --starring--> Casey Affleck
  Manchester --locatedIn--> Essex County
  Manchester --locatedIn--> Massachusetts
  Casey Affleck --bornIn--> Massachusetts
After attack:
  Manchester By The Sea --director--> Kenneth Lonergan
  Manchester By The Sea --filmPlace--> Manchester
  Manchester By The Sea --starring--> Casey Affleck
  Manchester --locatedIn--> Essex County
  Manchester --locatedIn--> Massachusetts
  Manchester --locatedIn--> United Kingdom
  Casey Affleck --bornIn--> Massachusetts
  Casey Affleck --bornIn--> United Kingdom
```

## Interpretación del resultado

De la lista de países candidatos, solo "United Kingdom" ya existía como entidad en
el grafo: aparece como cola de la tripleta `(England, containedIn, United
Kingdom)`, ajena a la película y alcanzable solo indirectamente desde David
Beckham (`David Beckham --bornIn--> England --containedIn--> United Kingdom`).
Es la única candidata que sobrevive la coincidencia difusa contra el vocabulario
de entidades, así que es la única respuesta adversaria válida para este caso —de
ahí que la lista final tenga un solo elemento en lugar de cinco.

Con esa única respuesta adversaria y los dos caminos de relaciones propuestos, la
etapa de anclaje resuelve el prefijo de un salto de cada camino
(`Manchester By The Sea --filmPlace--> Manchester` y
`Manchester By The Sea --starring--> Casey Affleck`) directamente sobre el grafo
existente, y adjunta la última relación de cada camino hacia la respuesta
adversaria. El resultado son exactamente dos tripletas nuevas:

- `(Manchester, locatedIn, United Kingdom)`
- `(Casey Affleck, bornIn, United Kingdom)`

Ninguna de las dos requirió la estrategia de respaldo, porque ambos caminos se
anclaron directamente en el grafo original.

El efecto sobre el grafo es mínimo en tamaño —2 tripletas insertadas sobre 13
originales— pero suficiente para introducir dos rutas de razonamiento alternativas
y con apariencia legítima: `Manchester By The Sea → filmPlace → Manchester →
locatedIn → United Kingdom` y `Manchester By The Sea → starring → Casey Affleck →
bornIn → United Kingdom`. Un sistema KG-RAG que recorra el grafo desde la entidad
tema encontraría estas dos rutas hacia "United Kingdom" junto a la ruta legítima
hacia "United States", sin ninguna señal estructural que distinga la información
insertada de la original — exactamente el mecanismo descrito en el marco teórico
para el ejemplo original del artículo (Zhao et al., 2025): insertar
`(Manchester, containedIn, England)` para engañar al sistema hacia "United
Kingdom".

## Ejecución con la API real de OpenAI

La ejecución `--offline` documentada arriba usa respuestas fijas para que el
resultado sea reproducible sin clave de API. Esta sección documenta, en cambio,
una ejecución real contra la API de OpenAI (`gpt-4o-mini`, temperatura 0.7):

```bash
python scripts/demo_manchester.py
```

```
Question: Which country is the movie "Manchester By The Sea" filmed in?
Topic entity: Manchester By The Sea
Clean KG: 13 triples

Adversarial target answers: ['Florida']
Relation path templates: [('filmPlace', 'locatedIn'), ('filmPlace', 'starring')]

Injected perturbation triples:
  (Manchester, locatedIn, Florida)   [target: Florida]
  (Manchester, starring, Florida)   [target: Florida]

Poisoned KG: 15 triples (+2 vs. clean)

--- Retrieval simulation: outgoing edges near the topic entity ---
Before attack:
  Manchester By The Sea --director--> Kenneth Lonergan
  Manchester By The Sea --filmPlace--> Manchester
  Manchester By The Sea --starring--> Casey Affleck
  Manchester --locatedIn--> Essex County
  Manchester --locatedIn--> Massachusetts
  Casey Affleck --bornIn--> Massachusetts
After attack:
  Manchester By The Sea --director--> Kenneth Lonergan
  Manchester By The Sea --filmPlace--> Manchester
  Manchester By The Sea --starring--> Casey Affleck
  Manchester --locatedIn--> Essex County
  Manchester --locatedIn--> Florida
  Manchester --locatedIn--> Massachusetts
  Manchester --starring--> Florida
  Casey Affleck --bornIn--> Massachusetts
```

Con el modelo real, la respuesta adversaria que sobrevivió la coincidencia
difusa fue "Florida" en lugar de "United Kingdom": el modelo propone en cada
llamada un conjunto distinto de países plausibles pero incorrectos, y solo se
conserva como respuesta adversaria el que coincide con una entidad ya presente
en el grafo. En este grafo, "Florida" existe únicamente por dos tripletas
ajenas a la película (`Miami, locatedIn, Florida` y `Florida, stateOf, United
States`), así que la coincidencia vuelve a ser accidental, del mismo tipo que
la de "United Kingdom" en la ejecución offline, pero sobre una entidad
distinta.

De los dos caminos de relaciones propuestos, `(filmPlace, locatedIn)` reproduce
el patrón canónico del artículo (lugar de filmación → ubicado en). El segundo,
`(filmPlace, starring)`, es estructuralmente válido —`starring` existe como
relación saliente dentro del vocabulario de dos saltos alrededor de la entidad
tema— pero semánticamente incoherente: adjuntar `starring` a "Manchester" (una
ubicación) no corresponde a ninguna relación real con sentido, aunque el
resultado, `(Manchester, starring, Florida)`, sigue siendo una tripleta que un
sistema KG-RAG podría recuperar sin señales estructurales de manipulación. Esto
ilustra un límite real de restringir el vocabulario de relaciones (ver
[Extracción de caminos de relaciones sin modelo especializado](05-desviaciones-limitaciones.md#extracción-de-caminos-de-relaciones-sin-modelo-especializado)):
garantiza que el camino sea anclable en el grafo, pero no garantiza que sea
semánticamente plausible.

Esta ejecución no es reproducible byte a byte: al no fijarse una semilla para
el muestreo del modelo de lenguaje, cada corrida contra la API real puede
generar respuestas adversarias y caminos de relaciones distintos. La ejecución
`--offline` es la que se mantiene fija como referencia reproducible; esta
sección documenta una muestra real, no un resultado canónico.

## Verificación con pruebas automatizadas

```bash
python -m pytest -q
```

```
..................                                                       [100%]
18 passed in 0.07s
```

Las 18 pruebas cubren cada etapa del ataque de forma aislada (ver
[Arquitectura de la implementación](03-arquitectura-implementacion.md)) y no
requieren acceso a red, por lo que su resultado es reproducible en cualquier
entorno con las dependencias instaladas.

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
