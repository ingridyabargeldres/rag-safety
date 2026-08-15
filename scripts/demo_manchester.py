"""Demo del ataque de envenenamiento sobre un grafo de conocimiento
pequeño construido a mano: ejecuta las tres etapas del ataque y muestra
cómo una sola arista engañosa redirige la recuperación multi-salto hacia
un país incorrecto.

Uso:
    python scripts/demo_manchester.py            # usa OPENAI_API_KEY si está definida
    python scripts/demo_manchester.py --offline  # LLM simulado y determinista, sin llamadas a la API
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from kgrag_attack.attack import run_attack  # noqa: E402
from kgrag_attack.kg import KnowledgeGraph  # noqa: E402
from kgrag_attack.llm import LLMClient, OpenAIClient, StaticLLMClient  # noqa: E402

QUESTION = 'Which country is the movie "Manchester By The Sea" filmed in?'
TOPIC_ENTITY = "Manchester By The Sea"

CLEAN_TRIPLES = [
    ("Manchester By The Sea", "filmPlace", "Manchester"),
    ("Manchester By The Sea", "starring", "Casey Affleck"),
    ("Manchester By The Sea", "director", "Kenneth Lonergan"),
    ("Manchester", "locatedIn", "Massachusetts"),
    ("Manchester", "locatedIn", "Essex County"),
    ("Massachusetts", "stateOf", "United States"),
    ("Essex County", "stateOf", "United States"),
    ("Casey Affleck", "bornIn", "Massachusetts"),
    ("David Beckham", "bornIn", "England"),
    ("David Beckham", "playedFor", "Los Angeles"),
    ("England", "containedIn", "United Kingdom"),
    ("Miami", "locatedIn", "Florida"),
    ("Florida", "stateOf", "United States"),
]

# Canned replies for --offline mode: an adversarial-answer bullet list
# (Figure 3 prompt) followed by two relation paths (Figure 4 prompt),
# standing in for what GPT-4 plausibly returns for this question.
_OFFLINE_ADVERSARIAL_ANSWERS_REPLY = (
    "- United Kingdom\n- France\n- Canada\n- Germany\n- Australia"
)
_OFFLINE_RELATION_PATHS_REPLY = "filmPlace -> locatedIn\nstarring -> bornIn"


def build_llm(offline: bool) -> LLMClient:
    if offline or not os.environ.get("OPENAI_API_KEY"):
        if not offline:
            print("[!] OPENAI_API_KEY not set - falling back to --offline stub LLM.\n")
        return StaticLLMClient(
            [_OFFLINE_ADVERSARIAL_ANSWERS_REPLY, _OFFLINE_RELATION_PATHS_REPLY]
        )
    return OpenAIClient(model="gpt-4o-mini")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true", help="use a deterministic stub LLM instead of OpenAI"
    )
    parser.add_argument("--n-answers", type=int, default=1)
    parser.add_argument("--budget-k", type=int, default=2)
    args = parser.parse_args()

    kg = KnowledgeGraph.from_triples(CLEAN_TRIPLES)
    llm = build_llm(args.offline)

    print(f"Question: {QUESTION}")
    print(f"Topic entity: {TOPIC_ENTITY}")
    print(f"Clean KG: {len(kg)} triples\n")

    result = run_attack(
        kg,
        QUESTION,
        TOPIC_ENTITY,
        llm,
        n_answers=args.n_answers,
        budget_k=args.budget_k,
        n_paths=2,
    )

    print(f"Adversarial target answers: {result.adversarial_answers}")
    print(f"Relation path templates: {result.relation_paths}\n")

    print("Injected perturbation triples:")
    for answer, triples in result.perturbation_triples.items():
        for h, r, t in triples:
            print(f"  ({h}, {r}, {t})   [target: {answer}]")

    print(f"\nPoisoned KG: {len(result.poisoned_kg)} triples "
          f"(+{len(result.poisoned_kg) - len(result.clean_kg)} vs. clean)")

    print("\n--- Retrieval simulation: outgoing edges near the topic entity ---")
    for label, g in (("Before attack", result.clean_kg), ("After attack", result.poisoned_kg)):
        print(f"{label}:")
        for source in (TOPIC_ENTITY, "Manchester", "Casey Affleck"):
            for relation, tail in sorted(g.out_edges(source)):
                print(f"  {source} --{relation}--> {tail}")


if __name__ == "__main__":
    main()
