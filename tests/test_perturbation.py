import random

from kgrag_attack.kg import KnowledgeGraph
from kgrag_attack.perturbation import build_perturbation_triples, poison_knowledge_graph

TRIPLES = [
    ("Manchester By The Sea", "filmPlace", "Manchester"),
    ("Manchester", "locatedIn", "Massachusetts"),
    ("Massachusetts", "stateOf", "United States"),
    ("Manchester By The Sea", "starring", "Casey Affleck"),
    ("Casey Affleck", "bornIn", "Massachusetts"),
]


def test_primary_grounding_produces_expected_triple():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    rng = random.Random(0)
    triples = build_perturbation_triples(
        kg,
        "Manchester By The Sea",
        [("filmPlace", "locatedIn")],
        "United Kingdom",
        budget_k=1,
        rng=rng,
    )
    assert triples == [("Manchester", "locatedIn", "United Kingdom")]


def test_budget_is_never_exceeded():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    rng = random.Random(1)
    triples = build_perturbation_triples(
        kg,
        "Manchester By The Sea",
        [("filmPlace", "locatedIn"), ("starring", "bornIn")],
        "United Kingdom",
        budget_k=1,
        rng=rng,
    )
    assert len(triples) == 1


def test_fallback_bridges_when_path_does_not_ground():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    rng = random.Random(42)
    triples = build_perturbation_triples(
        kg,
        "Manchester By The Sea",
        [("nonexistentRelation", "locatedIn")],
        "United Kingdom",
        budget_k=2,
        rng=rng,
    )
    # a 2-hop path with a failed prefix falls back to one bridge chain:
    # (topic, r1, bridge) then (bridge, r2, adversarial_answer)
    assert len(triples) == 2
    head, r1, bridge = triples[0]
    assert head == "Manchester By The Sea" and r1 == "nonexistentRelation"
    assert bridge in kg.entities
    assert triples[1] == (bridge, "locatedIn", "United Kingdom")


def test_fallback_may_fall_short_when_kg_too_small_for_bridges():
    kg = KnowledgeGraph.from_triples([("A", "r", "B")])
    rng = random.Random(0)
    triples = build_perturbation_triples(
        kg, "A", [("missing1", "missing2", "missing3")], "Z", budget_k=3, rng=rng
    )
    assert len(triples) <= 3


def test_never_reinserts_an_existing_triple():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    rng = random.Random(0)
    # "Manchester" already has locatedIn -> Massachusetts; asking to poison
    # toward that very same entity must not duplicate the existing triple.
    triples = build_perturbation_triples(
        kg,
        "Manchester By The Sea",
        [("filmPlace", "locatedIn")],
        "Massachusetts",
        budget_k=1,
        rng=rng,
    )
    assert ("Manchester", "locatedIn", "Massachusetts") not in triples


def test_poison_knowledge_graph_aggregates_across_answers_without_mutating_input():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    poisoned, per_answer = poison_knowledge_graph(
        kg,
        "Manchester By The Sea",
        [("filmPlace", "locatedIn")],
        ["United Kingdom", "France"],
        budget_k=1,
        seed=7,
    )
    assert per_answer["United Kingdom"] == [("Manchester", "locatedIn", "United Kingdom")]
    assert per_answer["France"] == [("Manchester", "locatedIn", "France")]
    assert len(poisoned) == len(kg) + 2
    assert len(kg) == len(TRIPLES)  # clean KG left untouched (insertion-only attack)
