from kgrag_attack.kg import KnowledgeGraph

TRIPLES = [
    ("Manchester By The Sea", "filmPlace", "Manchester"),
    ("Manchester", "locatedIn", "Massachusetts"),
    ("Massachusetts", "stateOf", "United States"),
]


def test_ground_follows_exact_relation_sequence():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    assert kg.ground("Manchester By The Sea", ("filmPlace",)) == {"Manchester"}
    assert kg.ground(
        "Manchester By The Sea", ("filmPlace", "locatedIn", "stateOf")
    ) == {"United States"}


def test_ground_returns_empty_set_when_path_does_not_exist():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    assert kg.ground("Manchester By The Sea", ("locatedIn",)) == set()
    assert kg.ground("Nonexistent", ("filmPlace",)) == set()


def test_ground_empty_path_returns_start_entity():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    assert kg.ground("Manchester", ()) == {"Manchester"}


def test_with_triples_does_not_mutate_original_kg():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    poisoned = kg.with_triples([("Manchester", "cityOf", "England")])

    assert ("Manchester", "cityOf", "England") not in kg.triples
    assert ("Manchester", "cityOf", "England") in poisoned.triples
    assert len(poisoned) == len(kg) + 1


def test_add_triple_is_idempotent():
    kg = KnowledgeGraph()
    assert kg.add_triple("A", "r", "B") is True
    assert kg.add_triple("A", "r", "B") is False
    assert len(kg) == 1


def test_neighborhood_relations_respects_hop_limit():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    assert kg.neighborhood_relations("Manchester By The Sea", max_hops=1) == {"filmPlace"}
    assert kg.neighborhood_relations("Manchester By The Sea", max_hops=2) == {
        "filmPlace",
        "locatedIn",
    }
