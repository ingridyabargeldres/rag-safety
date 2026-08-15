from kgrag_attack.adversarial_answers import generate_adversarial_answers
from kgrag_attack.kg import KnowledgeGraph
from kgrag_attack.llm import StaticLLMClient


def test_filters_to_valid_kg_entities_via_fuzzy_matching():
    kg = KnowledgeGraph.from_triples(
        [
            ("Manchester By The Sea", "filmPlace", "Manchester"),
            ("England", "containedIn", "United Kingdom"),
        ]
    )
    llm = StaticLLMClient(["- United Kingdom\n- France\n- Narnia"])
    answers = generate_adversarial_answers(
        "Which country is Manchester By The Sea filmed in?", kg, llm, n=5, max_rounds=1
    )
    assert answers == ["United Kingdom"]


def test_stops_early_once_n_answers_found():
    kg = KnowledgeGraph.from_triples([("A", "r", "B"), ("C", "r", "D")])
    llm = StaticLLMClient(["- B\n- D\n- extra"])
    answers = generate_adversarial_answers("q", kg, llm, n=2, max_rounds=3)
    assert set(answers) == {"B", "D"}


def test_returns_empty_list_when_nothing_matches_after_max_rounds():
    kg = KnowledgeGraph.from_triples([("A", "r", "B")])
    llm = StaticLLMClient(["- Narnia", "- Atlantis"])
    answers = generate_adversarial_answers("q", kg, llm, n=3, max_rounds=2)
    assert answers == []
