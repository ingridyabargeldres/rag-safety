from kgrag_attack.kg import KnowledgeGraph
from kgrag_attack.llm import StaticLLMClient
from kgrag_attack.relation_paths import generate_relation_paths

TRIPLES = [
    ("Manchester By The Sea", "filmPlace", "Manchester"),
    ("Manchester", "locatedIn", "Massachusetts"),
]


def test_keeps_only_paths_using_vocabulary_relations():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    llm = StaticLLMClient(
        ["filmPlace -> locatedIn\nfilmPlace -> madeUpRelation\nfilmPlace"]
    )
    paths = generate_relation_paths(
        "q", "Manchester By The Sea", kg, llm, n_paths=5, max_hops=3, vocab_hops=2
    )
    assert paths == [("filmPlace", "locatedIn"), ("filmPlace",)]


def test_drops_paths_longer_than_max_hops():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    llm = StaticLLMClient(["filmPlace -> locatedIn"])
    paths = generate_relation_paths(
        "q", "Manchester By The Sea", kg, llm, n_paths=5, max_hops=1, vocab_hops=2
    )
    assert paths == []


def test_returns_empty_when_topic_entity_has_no_outgoing_edges():
    kg = KnowledgeGraph.from_triples(TRIPLES)
    llm = StaticLLMClient(["should not matter"])
    paths = generate_relation_paths("q", "Nonexistent", kg, llm)
    assert paths == []
