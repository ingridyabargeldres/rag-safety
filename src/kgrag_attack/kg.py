"""Representación mínima de un grafo de conocimiento dirigido.

Las tripletas son tuplas de cadenas ``(cabeza, relación, cola)`` que
representan aristas dirigidas y etiquetadas entre entidades.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

Triple = tuple[str, str, str]


@dataclass
class KnowledgeGraph:
    triples: set[Triple] = field(default_factory=set)
    _out: dict[str, list[tuple[str, str]]] = field(default_factory=lambda: defaultdict(list), repr=False)

    @classmethod
    def from_triples(cls, triples: list[Triple]) -> "KnowledgeGraph":
        kg = cls()
        for h, r, t in triples:
            kg.add_triple(h, r, t)
        return kg

    def add_triple(self, head: str, relation: str, tail: str) -> bool:
        """Inserta una tripleta. Devuelve False si ya existía (no hace nada)."""
        triple = (head, relation, tail)
        if triple in self.triples:
            return False
        self.triples.add(triple)
        self._out[head].append((relation, tail))
        return True

    def contains(self, head: str, relation: str, tail: str) -> bool:
        return (head, relation, tail) in self.triples

    @property
    def entities(self) -> set[str]:
        ents: set[str] = set()
        for h, _, t in self.triples:
            ents.add(h)
            ents.add(t)
        return ents

    @property
    def relations(self) -> set[str]:
        return {r for _, r, _ in self.triples}

    def out_edges(self, entity: str) -> list[tuple[str, str]]:
        """Pares (relación, cola) de las aristas que salen de ``entity``."""
        return list(self._out.get(entity, []))

    def relations_from(self, entity: str) -> set[str]:
        return {r for r, _ in self._out.get(entity, [])}

    def neighborhood_relations(self, entity: str, max_hops: int = 2) -> set[str]:
        """Vocabulario de relaciones alcanzables en, como máximo, ``max_hops``
        saltos desde ``entity``.

        Recorre el grafo en anchura desde ``entity``, acumulando cada
        relación de salida encontrada hasta agotar los saltos permitidos o
        quedarse sin nuevas entidades por explorar.
        """
        seen_entities = {entity}
        frontier = {entity}
        rels: set[str] = set()
        for _ in range(max_hops):
            next_frontier: set[str] = set()
            for e in frontier:
                for r, t in self.out_edges(e):
                    rels.add(r)
                    if t not in seen_entities:
                        next_frontier.add(t)
            seen_entities |= next_frontier
            frontier = next_frontier
            if not frontier:
                break
        return rels

    def ground(self, start: str, relation_path: tuple[str, ...]) -> set[str]:
        """Entidades alcanzadas al seguir, en orden, la secuencia de
        relaciones ``relation_path`` a partir de ``start``.

        Si ``relation_path`` está vacía, devuelve ``{start}``. Si en algún
        paso no existe ninguna arista con la relación esperada, devuelve el
        conjunto vacío.
        """
        frontier = {start}
        for relation in relation_path:
            next_frontier: set[str] = set()
            for e in frontier:
                for r, t in self.out_edges(e):
                    if r == relation:
                        next_frontier.add(t)
            frontier = next_frontier
            if not frontier:
                return set()
        return frontier

    def random_entity(self, rng: random.Random, exclude: set[str] | None = None) -> str | None:
        candidates = self.entities - (exclude or set())
        if not candidates:
            return None
        return rng.choice(sorted(candidates))

    def with_triples(self, new_triples: list[Triple]) -> "KnowledgeGraph":
        """Devuelve un nuevo grafo formado por este grafo más ``new_triples``,
        sin modificar el original."""
        poisoned = KnowledgeGraph.from_triples(list(self.triples))
        for h, r, t in new_triples:
            poisoned.add_triple(h, r, t)
        return poisoned

    def __len__(self) -> int:
        return len(self.triples)
