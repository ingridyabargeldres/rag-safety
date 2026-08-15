# Marco teórico

Este documento introduce las definiciones sobre las que se apoya el resto de la
documentación: qué es un grafo de conocimiento, cómo se representan los caminos
de razonamiento y de relaciones, y qué tarea resuelve un sistema KG-RAG (de
Grafo de conocimiento a Pipeline de un sistema KG-RAG). Sobre esa base se
formaliza el modelo de amenaza del atacante (Objetivo del atacante) y las dos
piezas matemáticas centrales del ataque: cómo se generan caminos de relaciones
plausibles (Formulación de la extracción de caminos de relaciones) y cómo se
construye la tripleta de perturbación a partir de ellos (Anclaje del prefijo y
construcción de la tripleta de perturbación). Las definiciones y fórmulas de
este documento siguen a Zhao et al. (2025).

## Grafo de conocimiento

Un grafo de conocimiento se define como una terna `G = (E, R, T)`, donde `E` es el
conjunto de entidades, `R` el conjunto de relaciones y `T ⊆ E × R × E` el conjunto
de tripletas fácticas. Cada tripleta `(e_h, r, e_t) ∈ T` representa una arista
dirigida y etiquetada: la relación `r` conecta la entidad cabeza `e_h` con la
entidad cola `e_t`. Por ejemplo, `(Manchester, locatedIn, Massachusetts)` afirma
que Manchester está ubicada en Massachusetts.

## Caminos de razonamiento y caminos de relaciones

Un **camino de razonamiento** es una secuencia de tripletas consecutivas en el
grafo:

```
p : e₀ →r₁ e₁ →r₂ ... →rₗ eₗ
```

donde cada `(e_{i-1}, r_i, e_i)` es una tripleta válida de `T` y `l` es la longitud
del camino. Un **camino de relaciones** conserva solo la secuencia de relaciones
del camino, descartando las entidades intermedias: `w = (r₁, r₂, …, rₗ)`. Por
ejemplo, el camino de razonamiento `Cardiff →locatedIn Wales →containedIn United
Kingdom` tiene como camino de relaciones asociado `(locatedIn, containedIn)`.

La operación inversa —encontrar, dentro de un grafo, las entidades alcanzables al
seguir un camino de relaciones dado a partir de una entidad de inicio— se llama
**anclaje** (*grounding*). Un camino de relaciones es solo una plantilla; anclarlo
en un grafo concreto produce las entidades reales que resultan de recorrer esa
secuencia de relaciones.

## Preguntas sobre grafos de conocimiento

Dada una pregunta en lenguaje natural `q` y un grafo `G`, responder la pregunta
consiste en construir una función `f` que, apoyándose en `G`, devuelva una entidad
respuesta `a ∈ E`: `a = f(q, G)`.

## Pipeline de un sistema KG-RAG

Un sistema KG-RAG típico resuelve una pregunta en dos etapas:

**Etapa de recuperación.** A partir de la pregunta `q` y el grafo completo `G`, se
extrae un subgrafo `G_q = (E_q, R_q, T_q)` que contiene solo la información
relevante para responder `q`:

```math
G_q = \text{Retriever}(q; G) \qquad (1)
```

**Etapa de generación.** El subgrafo recuperado se combina con la pregunta en un
prompt y se pasa a un modelo de lenguaje parametrizado por `θ`, que produce la
respuesta final:

```math
a = f_\theta(\text{Prompt}[q, G_q]) \qquad (2)
```

Esta separación es la que hace vulnerable al sistema frente a un ataque de
envenenamiento: si el grafo `G` contiene tripletas falsas pero bien conectadas a la
entidad tema de la pregunta, la etapa de recuperación puede incluirlas dentro de
`G_q` sin distinguirlas de las tripletas legítimas, y la etapa de generación puede
terminar apoyándose en ellas para construir la respuesta.

## Objetivo del atacante

Dada una pregunta `q`, el atacante busca insertar un conjunto pequeño de tripletas
adversarias `T̂` en el grafo, de modo que el sistema KG-RAG, operando sobre el
grafo modificado `Ĝ = {E, R, T ∪ T̂}`, produzca un conjunto de respuestas `Â` que
no incluya la respuesta correcta `a*` (Zhao et al., 2025):

```math
\hat{A} = \text{KG-RAG}(q; \hat{G}), \qquad a^{*} \notin \hat{A} \qquad (3)
```

El atacante opera en **modo caja negra**: no tiene acceso al recuperador, al modelo
de lenguaje ni a ningún parámetro interno del sistema KG-RAG objetivo, y tampoco
conoce la respuesta correcta de la pregunta que está atacando. Su única capacidad
es insertar tripletas nuevas en el grafo —no puede borrar ni modificar las
existentes—, y para mantener el ataque difícil de detectar, cada tripleta insertada
debe reutilizar entidades y relaciones que ya existen en el grafo, y el número de
tripletas insertadas por respuesta adversaria está acotado por un presupuesto `K`.

## Formulación de la extracción de caminos de relaciones

Zhao et al. (2025) plantean la generación de caminos de relaciones plausibles
para una pregunta como un problema de optimización: dado `q`, se busca
maximizar la probabilidad de generar un camino de relaciones `w` que esté
anclado en el grafo y que sea semánticamente coherente con `q`. Usando como
supervisión débil el conjunto `W*` de caminos de relaciones más cortos entre la
entidad tema de la pregunta y la entidad respuesta correcta en el grafo, el
objetivo es:

```math
\max_{\theta} \; \mathbb{E}_{w \sim W^{*}}\big[\log P_\theta(w \mid q)\big] \qquad (4)
```

Asumiendo una distribución uniforme sobre `W*`, esta esperanza se aproxima
promediando sobre todos los caminos del conjunto:

```math
\operatorname*{arg\,max}_{\theta} \; \frac{1}{|W^{*}|} \sum_{w \in W^{*}} \log P_\theta(w \mid q) \qquad (5)
```

Como un camino de relaciones es en sí mismo una secuencia, la probabilidad de
generarlo se descompone en el producto de las probabilidades de generar cada
relación condicionada a las anteriores y a la pregunta:

```math
\frac{1}{|W^{*}|} \sum_{w \in W^{*}} \log \prod_{i=1}^{|w|} P_\theta(r_i \mid r_{<i}, q) \qquad (6)
```

En otras palabras: entrenar un modelo para proponer buenos caminos de relaciones
equivale a entrenarlo para predecir, relación por relación, la siguiente relación
más plausible dada la pregunta y las relaciones ya elegidas. Esta implementación no
entrena un modelo con este objetivo (ver
[Desviaciones frente al método original y limitaciones](05-desviaciones-limitaciones.md));
en su lugar logra el mismo efecto —caminos anclables y coherentes— restringiendo el
vocabulario de relaciones que un modelo de propósito general puede elegir al que
realmente existe cerca de la entidad tema en el grafo.

## Anclaje del prefijo y construcción de la tripleta de perturbación

Dado un camino de relaciones `w = (r₁, r₂, …, rₗ)`, su prefijo `w' = (r₁, …,
r_{l-1})` se ancla en el grafo a partir de la entidad tema `e_q` de la pregunta,
obteniendo el conjunto de entidades alcanzadas tras `l-1` saltos (Zhao et al., 2025):

```math
E_{l-1} = \text{Grounding}(e_q, w'; G) \qquad (7)
```

donde cada `e_{l-1} ∈ E_{l-1}` es una entidad real, alcanzable siguiendo
`e_q →r₁ e₁ →r₂ ... →r_{l-1} e_{l-1}`. La tripleta de perturbación se completa
adjuntando la última relación del camino y la respuesta adversaria: `(e_{l-1}, r_l,
â)`. La intuición es que, si un sistema KG-RAG ya seguiría el prefijo `w'` al
razonar sobre la pregunta, basta con una única arista adicional —`r_l` hacia `â`—
para que la cadena de razonamiento termine en la respuesta incorrecta en lugar de
la correcta.

Cuando el prefijo no se puede anclar en el grafo (por ejemplo, porque la entidad
tema no tiene salidas con la primera relación del camino), se recurre a una
**estrategia de respaldo**: se muestrean entidades puente al azar del grafo para
completar la cadena manteniendo el mismo patrón de relaciones. Por ejemplo, para un
camino de dos saltos `(r₁, r₂)`, se insertan juntas las tripletas `(e_q, r₁, e')` y
`(e', r₂, â)`, donde `e'` es una entidad puente elegida al azar.

# Referencias

Zhao, T., Chen, J., Ru, Y., Zhu, H., Hu, N., Liu, J., & Lin, Q. (2025). *RAG safety: Exploring knowledge poisoning attacks to retrieval-augmented generation*. arXiv. https://arxiv.org/abs/2507.08862
