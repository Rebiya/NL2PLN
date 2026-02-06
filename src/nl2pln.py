import os
import dspy
import json
import logging
import mlflow
import traceback

logger = logging.getLogger(__name__)

from typing import List
from textwrap import dedent
from cleanPLN import checkStmt, checkQuery, checkImpl, balance_parentheses
from pettachainer.pettachainer import PeTTaChainer

class NL2PLNSingature(dspy.Signature):
    """
    You convert Natural Language sentences to **PLN light statements** following the exact syntax and semantic rules below. Always produce valid, well-formed statements.
    When possible try to reuse predicates and structures from the context.

    ### 1. General Form

    A PLN light statement has the form:

    ```
    (: PRF TYPE TRUTH_VALUE)
    ```

    ### 2. PRF (Proof Reference)

    * Either a concrete identifier (symbol/name), or
    * A variable `$prf` **only in queries**

    ### 3. TYPE

    TYPE describes the logical content and must follow these rules:

    #### 3.1 Predicates

    * A predicate is written as:

    ```
    (Predicate arg1 arg2 ...)
    ```

    * Arguments may be objects or variables.

    #### 3.2 Logical Connectives

    Predicates can be combined using:

    * `And`
    * `Or`
    * `Implication`
    * `LikelierThan`

    Example:

    ```
    (And (Predicate1 x) (Predicate2 x))
    ```

    #### 3.3 Variables and Quantification

    * Variables are written as `$var`
    * **Variables may only appear inside Implications**, except in queries.
    * In an Implication:

      * Variables appearing in the **Premises** are **universally quantified**
      * Variables appearing **only in the Conclusions** are **existentially quantified**

    Example:

    ```
    (Implication
        (Premises
            (Predicate1 $x $y))
        (Conclusions
            (Predicate2 $y $z)
            (Predicate3 $z)))
    ```

    Here:

    * `$x`, `$y` are universally quantified
    * `$z` is existentially quantified

    #### 3.4 Queries

    * Queries may contain variables **anywhere** a predicate name or argument can appear
    * Queries typically use `$prf` and/or `$tv`

    Examples:

    ```
    ($pred x)
    (Predicate $x)
    ```

    ### 4. Compute Predicate

    There exists a special hardcoded predicate:

    ```
    (Compute operator args -> result)
    ```

    Rules:

    * `operator` is one of: `< <= + - * /`
    * `Compute` **may only appear in the premises of an Implication**
    * Unlike normal predicates, `Compute` is evaluated by executing the operator, not by checking the knowledge base

    Example:

    ```
    (Implication
        (Premises
            (Cardinality dogs $x)
            (Cardinality cats $y)
            (Compute + ($x $y) -> $t))
        (Conclusions
            (Cardinality dogsPlusCats $t)))
    ```

    Filtering example:

    ```
    (Compute > ($x $y) -> True)
    ```

    ### 5. FoldAll Predicate

    There exists a special aggregation predicate:

    ```
    (FoldAll pattern value init fun -> out)
    ```

    Rules:

    * `FoldAll` **may only appear in the Premises of an Implication**
    * It finds all matches of `pattern` under current bindings
    * For each match it evaluates `value` and folds that into an accumulator starting from `init`
    * If there are no matches, the result is `init`
    * Only `out` is exported to later premises/conclusions
    * Prefer inline lambdas for fold functions, e.g. `(|-> ($acc $x) (+ $acc $x))`

    Example:

    ```
    (Implication
        (Premises
            (FoldAll (Count $name $n) $n 0 (|-> ($acc $x) (+ $acc $x)) -> $total))
        (Conclusions
            (Count Total $total)))
    ```

    ### 6. TRUTH_VALUE

    TRUTH_VALUE is either:

    * A concrete truth value:

    ```
    (STV strength confidence)
    ```

    where `strength` and `confidence` are real numbers in `[0, 1]`, or

    * A variable `$tv` **only in queries**

    ### 7. Output Constraints

    * Always follow the exact syntax
    * Do not introduce undeclared constructs
    * Do not place variables outside allowed positions
    * Do not use `Compute` outside implication premises
    * Do not use `FoldAll` outside implication premises
    * Ensure quantification rules are respected

    Produce only valid PLN light statements / queries.
    """
    #Inputs
    sentences: List[str] = dspy.InputField(desc="Original natural language sentences")
    context: List[str] = dspy.InputField(desc="Contextual information")

    #Outputs
    pln_light: List[str] = dspy.OutputField(desc="PLN light statements")

class NL2PLNModule(dspy.Module):

    def __init__(self):
        self.nl2pln : dspy.Module = dspy.ChainOfThought(NL2PLNSingature)

    def forward(self, sentences : List[str], queries: List[dict]):
        stmts = self.nl2pln(sentences=sentences,context=[]).pln_light

        queries_pln = []
        for q in queries:
            pln_q = self.nl2pln(sentences=[q['question']],context=stmts)
            queries_pln.append(pln_q.pln_light)

        return dspy.Prediction(statements=stmts, queries=queries_pln)

class ProofEvaluatorSignature(dspy.Signature):
    """Evaluate how well a proof answers a question and suggest improvements.

    You are evaluating PLN (Probabilistic Logic Networks) proofs generated from natural language.
    Assess whether the proof correctly answers the question and provide constructive feedback.
    """
    # Inputs
    sentences: List[str] = dspy.InputField(desc="Original natural language sentences")
    question: str = dspy.InputField(desc="The question being asked")
    expected_answer: str = dspy.InputField(desc="The expected answer to the question")
    statements: List[str] = dspy.InputField(desc="PLN statements generated from sentences")
    query: List[str] = dspy.InputField(desc="PLN query generated for the question")
    proof: str = dspy.InputField(desc="The proof result from running the query")

    # Outputs
    score: float = dspy.OutputField(desc="Score from 0.0 to 1.0 indicating how well the proof answers the question")
    feedback: str = dspy.OutputField(desc="Detailed feedback on what went wrong and how to improve the PLN statements/query")
    improved_statements: List[str] = dspy.OutputField(desc="Improved PLN statements that would produce a better proof")
    improved_query: List[str] = dspy.OutputField(desc="Improved PLN query that would better capture the question")


class ProofEvaluator(dspy.Module):
    def __init__(self):
        self.evaluate = dspy.ChainOfThought(ProofEvaluatorSignature)

    def forward(self, sentences, question, expected_answer, statements, query, proof):
        return self.evaluate(
            sentences=sentences,
            question=question,
            expected_answer=expected_answer,
            statements=statements,
            query=query,
            proof=proof
        )

pln_spec = """
A pln light statment has the following form:
(: PRF TYPE TRUTH_VALUE)
PRF can be either a specific name or a varaible $prf in the case of queries.
TYPE can be one of:
    A Predicate applied to on or more objects (Predicate x y)
    Which can be combined using And Or Implication LikelierThan.
        Example: (And (Predicate1 x) (Predicate2 x))
    Statments should have variables $var only inside Implications.
    Variables in the Premises are universally quantified.
    Variables that appear only in the Conclusions are existentially quantified.
        Example: (Implication (Premises (Predicate1 $x $y)) (Conclusions (Predicate2 $y $z) (Predicate3 $z))) [$x $y are universally quantified, $z is existentially quantified]
    Queries can have variables at any location that a Predicate or Object could appear.
        Example: ($pred x) / (Pred $x)
TRUTH_VALUE can be either (STV strength confidence) with strenght and confidence between 0 and 1
            or a variable $tv in the case of queries.

There exists a hardcoded (Compute $f $args -> $res) Predicate whose first argument is an arithmetic operator like < <= + - * /
which should only be used in the Premises of an Implication.
Example: (Implication (Premises (Cardinality dogs $x) (Cardinality cats $y) (Compute + ($x $y) -> $t)) (Conclusions (Cardinality dogsPlusCats $t)))
Compared to normal predicetes who's existed is check in the knowledge base the Compute predicate is checked by running the function/operator.

There also exists (FoldAll $pattern $value $init $fun -> $out) for aggregations in Premises.
`$value` controls what gets passed into the folding function for each match.
Example: (Implication (Premises (FoldAll (Count $name $n) $n 0 (|-> ($acc $x) (+ $acc $x)) -> $total)) (Conclusions (Count Total $total)))
"""

def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None, pred_name=None, pred_trace=None):
    try:
        metta_handler = PeTTaChainer()
        evaluator = ProofEvaluator()

        log = False

        score = 0.0
        if pred.statements == [] or pred.statements is None:
            return dspy.Prediction(score=score, feedback="No pln statements found")

        for stmt in pred.statements:
            if checkStmt(stmt) == 0.0:
                return dspy.Prediction(
                    score=score,
                    feedback=f"""The statement {stmt} did not follow the right syntax. Follow the pln light spec {pln_spec}"""
                )
            score += 0.001
            metta_handler.add_atom(stmt)

        for query in pred.queries:
            if checkQuery(query[0]) == 0.0:
                return dspy.Prediction(
                    score=score,
                    feedback=f"""The query {query[0]} did not follow the right syntax. Follow the pln light spec {pln_spec}"""
                )
            score += 0.001

        proofs = []
        for qr in pred.queries:
            proofs.append(metta_handler.query(qr[0]))

        total_score = 0.0
        feedback_details = []

        for q, query_pln, proof in zip(gold.queries, pred.queries, proofs):
            evaluation = evaluator(
                sentences=gold.sentences,
                question=q['question'],
                expected_answer=q['expected_answer'],
                statements=pred.statements,
                query=query_pln,
                proof=str(proof)
            )

            eval_score = 0.0 if evaluation.score is None else float(evaluation.score)
            total_score += eval_score

            feedback_details.append(dedent(f"""
                Question: '{q['question']}'
                Expected: {q['expected_answer']}
                Proof: {proof}
                Score: {eval_score}
                Feedback: {evaluation.feedback}
                Improved statements: {evaluation.improved_statements}
                Improved query: {evaluation.improved_query}
            """))

        n = len(pred.queries)
        final_score = max(total_score / n if n > 0 else 0.0, 0.1)

        return dspy.Prediction(
            score=final_score,
            feedback=f"Score: {total_score:.2f}/{n} questions. \n" + "\n".join(feedback_details)
        )
    except Exception as e:
        print(pred)
        print("Error occured in difficulty_metric:", e)
        traceback.print_exc()
        return dspy.Prediction(score=0.0, feedback=f"Error: {e}")



def build_examples_from_file(filepath: str) -> List[dspy.Example]:
    """
    Load a JSON file containing a list of puzzle data and convert each item into a
    dspy.Example that provides 'sentences' (list[str]) and 'questions' (list[dict]) as inputs.
    """
    examples: List[dspy.Example] = []
    with open(filepath, "r", encoding="utf-8") as f:
        puzzle_data = json.load(f)
    for item in puzzle_data:
        examples.append(
            dspy.Example(item).with_inputs("sentences", "queries")
        )
    return examples

tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
if tracking_uri:
    mlflow.set_tracking_uri(uri=tracking_uri)
    mlflow.set_experiment("DSPy-Optimization")
    mlflow.dspy.autolog(
        log_compiles=True,    # Track optimization process
        log_evals=True,       # Track evaluation results
        log_traces_from_compile=True  # Track program traces during optimization
    )

if __name__ == '__main__':
    #model = "openrouter/openai/gpt-5.1"
    #model = "openrouter/deepseek/deepseek-v3.2"
    #model = "cerebras/gpt-oss-120b"
    #model = "openrouter/google/gemini-3-flash-preview"
    model = "openai/gpt-5.2"

    dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))
    dspy.settings.configure(track_usage=True)

    module = NL2PLNModule()
    #module.load("src/nl2plnModuleJan2026.json")

    #puzzle_data = build_examples_from_file("data/andres.json")
    puzzle_data = build_examples_from_file("data/counting.json")
    #puzzle_data = build_examples_from_file("data/sentences.json")

    #puzzle_data = puzzle_data[0:17]

    score_sum = 0
    for puzzle in puzzle_data:
        res = module(sentences=puzzle.sentences, queries=puzzle.queries)
        print("------------------------------------------------------------------------------------------------------------------------------")
        print(res)
        metric = difficulty_metric(puzzle, res)
        print("------------------------------------------------------------------------------------------------------------------------------")
        print(metric.score)
        print(metric.feedback)
        score_sum += metric.score
    print(score_sum/len(puzzle_data))
