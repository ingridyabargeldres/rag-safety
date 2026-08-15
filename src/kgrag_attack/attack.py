"""Orquestación completa del ataque en tres etapas: generación de
respuestas adversarias, extracción de caminos de relaciones e inserción
de las tripletas de perturbación.
"""

from __future__ import annotations

from dataclasses import dataclass

from .adversarial_answers import generate_adversarial_answers
from .kg import KnowledgeGraph, Triple
from .llm import LLMClient
from .perturbation import poison_knowledge_graph
from .relation_paths import generate_relation_paths


@dataclass
class AttackResult:
    question: str
    topic_entity: str
    adversarial_answers: list[str]
    relation_paths: list[tuple[str, ...]]
    perturbation_triples: dict[str, list[Triple]]
    clean_kg: KnowledgeGraph
    poisoned_kg: KnowledgeGraph

    @property
    def all_perturbation_triples(self) -> list[Triple]:
        return [t for triples in self.perturbation_triples.values() for t in triples]


def run_attack(
    kg: KnowledgeGraph,
    question: str,
    topic_entity: str,
    llm: LLMClient,
    n_answers: int = 5,
    budget_k: int = 4,
    n_paths: int = 3,
    max_hops: int = 3,
    seed: int | None = None,
) -> AttackResult:
    """Ejecuta el ataque de envenenamiento contra una única pregunta y
    devuelve el grafo envenenado junto con todo lo generado en el proceso:
    respuestas adversarias, caminos de relaciones y tripletas insertadas.

    Con los valores por defecto (n_answers=5, budget_k=4) se pueden
    insertar hasta 20 tripletas por pregunta.
    """
    adversarial_answers = generate_adversarial_answers(
        question, kg, llm, n=n_answers
    )
    relation_paths = generate_relation_paths(
        question, topic_entity, kg, llm, n_paths=n_paths, max_hops=max_hops
    )
    poisoned_kg, per_answer_triples = poison_knowledge_graph(
        kg, topic_entity, relation_paths, adversarial_answers, budget_k, seed=seed
    )
    return AttackResult(
        question=question,
        topic_entity=topic_entity,
        adversarial_answers=adversarial_answers,
        relation_paths=relation_paths,
        perturbation_triples=per_answer_triples,
        clean_kg=kg,
        poisoned_kg=poisoned_kg,
    )
