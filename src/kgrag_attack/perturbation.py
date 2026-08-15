"""Construcción de las tripletas de perturbación que se insertan en el
grafo de conocimiento.

A partir de plantillas de caminos de relaciones, arma cadenas de
inferencia engañosas que conducen desde la entidad tema hasta una
respuesta adversaria, respetando un presupuesto máximo de inserciones
por respuesta y recurriendo a entidades puente elegidas al azar cuando
un camino no puede anclarse en el grafo existente.
"""

from __future__ import annotations

import random

from .kg import KnowledgeGraph, Triple

# Cap on fallback attempts so a pathological relation-path list (e.g. all
# empty) can never spin the loop forever.
_MAX_FALLBACK_ROUNDS_PER_PATH = 4


def build_perturbation_triples(
    kg: KnowledgeGraph,
    topic_entity: str,
    relation_paths: list[tuple[str, ...]],
    adversarial_answer: str,
    budget_k: int,
    rng: random.Random,
) -> list[Triple]:
    """Construye hasta ``budget_k`` tripletas de perturbación que dirigen
    ``topic_entity`` hacia ``adversarial_answer`` siguiendo ``relation_paths``.
    """
    triples: list[Triple] = []
    seen: set[Triple] = set()

    def add(triple: Triple) -> None:
        """Agrega ``triple`` al resultado si no se agregó antes en esta
        llamada ni ya existe en el grafo."""
        if triple not in seen and triple not in kg.triples:
            seen.add(triple)
            triples.append(triple)

    # Primary strategy (Eq. 7): ground each path's prefix w' = (r1..r{l-1})
    # from the topic entity, then attach the adversarial answer via the
    # final relation r_l.
    for path in relation_paths:
        if len(triples) >= budget_k or not path:
            continue
        prefix, last_relation = path[:-1], path[-1]
        grounded = kg.ground(topic_entity, prefix)
        for e in sorted(grounded):
            if len(triples) >= budget_k:
                break
            add((e, last_relation, adversarial_answer))

    if len(triples) >= budget_k or not relation_paths:
        return triples[:budget_k]

    # Fallback strategy: some paths fail to ground or yield too few triples,
    # so synthesize bridge entities to complete the chain instead.
    exclude = {topic_entity, adversarial_answer} | {h for h, _, _ in triples}
    path_idx = 0
    max_rounds = _MAX_FALLBACK_ROUNDS_PER_PATH * len(relation_paths)
    rounds = 0
    while len(triples) < budget_k and rounds < max_rounds:
        path = relation_paths[path_idx % len(relation_paths)]
        path_idx += 1
        rounds += 1
        if not path:
            continue

        current = topic_entity
        chain: list[Triple] = []
        grounded_ok = True
        for relation in path[:-1]:
            bridge = kg.random_entity(rng, exclude=exclude)
            if bridge is None:
                grounded_ok = False
                break
            chain.append((current, relation, bridge))
            exclude.add(bridge)
            current = bridge
        if not grounded_ok:
            continue

        chain.append((current, path[-1], adversarial_answer))
        for triple in chain:
            if len(triples) >= budget_k:
                break
            add(triple)

    return triples[:budget_k]


def poison_knowledge_graph(
    kg: KnowledgeGraph,
    topic_entity: str,
    relation_paths: list[tuple[str, ...]],
    adversarial_answers: list[str],
    budget_k: int,
    seed: int | None = None,
) -> tuple[KnowledgeGraph, dict[str, list[Triple]]]:
    """Aplica el ataque para cada respuesta adversaria y devuelve el grafo
    envenenado junto con las tripletas insertadas por cada respuesta.
    """
    rng = random.Random(seed)
    per_answer: dict[str, list[Triple]] = {}
    all_new_triples: list[Triple] = []
    for answer in adversarial_answers:
        triples = build_perturbation_triples(
            kg, topic_entity, relation_paths, answer, budget_k, rng
        )
        per_answer[answer] = triples
        all_new_triples.extend(triples)
    poisoned_kg = kg.with_triples(all_new_triples)
    return poisoned_kg, per_answer
