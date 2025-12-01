"""
Validate the gold-standard outputs in data/sentences.json by feeding them
directly into the evaluation metric (no model generation).

Usage:
  python -m NL2PLN.test_gold_examples --data data/sentences.json
"""

import argparse
from statistics import mean
from typing import List

import dspy

from nl2pln import build_examples_from_file, difficulty_metric


def evaluate_gold_only(model_name: str, data_path: str, index: int | None) -> None:
    """
    Treat the gold statements/queries as the prediction and score them with the
    existing difficulty_metric. This checks that the provided solutions are
    internally consistent and pass the evaluation logic.
    """
    dspy.configure(lm=dspy.LM(model_name, temperature=1.0, max_tokens=20000))

    examples: List[dspy.Example] = build_examples_from_file(data_path)

    if index is not None:
        if index < 0 or index >= len(examples):
            raise IndexError(f"Index {index} out of range; dataset has {len(examples)} examples.")
        examples = [examples[index]]
    scores: List[float] = []

    for idx, example in enumerate(examples):
        print(f"\n=== Example {idx} ===")
        print("Sentences:", example.sentences)

        # Use gold statements and queries as the prediction input.
        pred = dspy.Prediction(statements=example.statements, queries=example.queries)
        metric = difficulty_metric(example, pred)
        scores.append(metric.score)

        print(f"Score: {metric.score:.3f}")
        print(metric.feedback)

    if scores:
        print("\n=== Aggregate ===")
        print(f"Average score across {len(scores)} examples: {mean(scores):.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate gold-standard outputs directly against the metric."
    )
    parser.add_argument(
        "--data",
        default="data/sentences.json",
        help="Path to JSON file containing gold examples.",
    )
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-oss-120b",
        help="Model id to use for DSPy LM configuration (used by validation chains).",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="If provided, only evaluate the example at this zero-based index.",
    )
    args = parser.parse_args()

    evaluate_gold_only(
        model_name=args.model,
        data_path=args.data,
        index=args.index,
    )


if __name__ == "__main__":
    main()
