"""Propone caminos de relaciones que conectan de forma plausible la
entidad tema de una pregunta con su respuesta, para usarlos como
plantillas de las tripletas de perturbación.

Restringe las relaciones que puede elegir el LLM al vocabulario que
realmente existe a pocos saltos de la entidad tema
(``KnowledgeGraph.neighborhood_relations``) y descarta cualquier camino
que use una relación fuera de ese vocabulario.
"""

from __future__ import annotations

from .kg import KnowledgeGraph
from .llm import LLMClient

PROMPT_TEMPLATE = """You are given a question and the relation names that exist in a knowledge graph near the topic entity of the question.

Question: {question}
Topic entity: {topic_entity}
Available relations: {relations}

Propose up to {n_paths} short relation paths (chains of 1 to {max_hops} relations, using ONLY relations from the list above, spelled exactly as given) that would plausibly lead from the topic entity to the answer of the question.

Output exactly one path per line, relations separated by " -> ". Do not number the lines, do not include the topic entity name, and do not add any other text.
Example output for two 2-hop paths:
relationA -> relationB
relationC -> relationD"""

_SYSTEM_PROMPT = (
    "You are proposing structurally valid reasoning paths over a knowledge "
    "graph for RAG-safety research."
)


def _parse_paths(
    text: str, vocab: set[str], max_hops: int, topic_entity: str | None = None
) -> list[tuple[str, ...]]:
    """Extrae de ``text`` los caminos de relaciones válidos: uno por línea,
    con las relaciones separadas por ``->``. Descarta un primer token que
    coincida con ``topic_entity`` y cualquier camino vacío, más largo que
    ``max_hops`` o que use una relación fuera de ``vocab``."""
    paths: list[tuple[str, ...]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = [t.strip() for t in line.split("->") if t.strip()]
        # some LLMs prepend the topic entity despite instructions not to;
        # drop it rather than discarding an otherwise-valid path.
        if topic_entity and tokens and tokens[0].lower() == topic_entity.lower():
            tokens = tokens[1:]
        if not tokens or len(tokens) > max_hops:
            continue
        if any(t not in vocab for t in tokens):
            continue
        path = tuple(tokens)
        if path not in paths:
            paths.append(path)
    return paths


def generate_relation_paths(
    question: str,
    topic_entity: str,
    kg: KnowledgeGraph,
    llm: LLMClient,
    n_paths: int = 3,
    max_hops: int = 3,
    vocab_hops: int = 2,
) -> list[tuple[str, ...]]:
    """Devuelve hasta ``n_paths`` plantillas de caminos de relaciones
    ancladas en ``kg``."""
    vocab = kg.neighborhood_relations(topic_entity, max_hops=vocab_hops)
    if not vocab:
        return []
    prompt = PROMPT_TEMPLATE.format(
        question=question,
        topic_entity=topic_entity,
        relations=", ".join(sorted(vocab)),
        n_paths=n_paths,
        max_hops=max_hops,
    )
    raw = llm.complete(prompt, system=_SYSTEM_PROMPT)
    return _parse_paths(raw, vocab, max_hops, topic_entity)[:n_paths]
