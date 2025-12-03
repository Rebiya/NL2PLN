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
from mm2chainer import MorkHandler

class NL2PLNModule(dspy.Module):
    def __init__(self):
        self.nl2pln : dspy.Module = dspy.ChainOfThought("sentences: list[str] , context: list[str] -> pln_light: list[str]")

    def forward(self, sentences : List[str], queries: List[dict]):
        stmts = self.nl2pln(sentences=sentences,context=[]).pln_light

        queries_pln = []
        for q in queries:
            pln_q = self.nl2pln(sentences=[q['question']],context=stmts)
            queries_pln.append(pln_q.pln_light)

        return dspy.Prediction(statements=stmts, queries=queries_pln)

pln_spec = """
A pln light statment has the following form:
(: PRF TYPE TRUTH_VALUE)
PRF can be either a specific name or a varaible $prf in the case of queries.
TYPE can be one of:
    A Predicate applied to on or more objects (Predicate x y)
    Which can be combined using And Or Implication.
        Example: (And (Predicate1 x) (Predicate2 x))
    Statments should have variables $var only inside Implications.
    Variables in the premises are universally quantified.
    Variables that appear only in the coclusion are existentially quantified.
        Example: (Implication (Predicate1 $x $y) (And (Predicate2 $y $z) (Predicate3 $z))) [$x $y are universally quantified, $z is existentially quantified]
    Queries can have variables at any location that a Predicate or Object could appear.
        Example: ($pred x) / (Pred $x)
TRUTH_VALUE can be either (STV strength confidence) with strenght and confidence between 0 and 1
            or a variable $tv in the case of queries.
"""

def format_result(q, proof, comp):
    return dedent(f"""
        Proof: {proof}
        for question: '{q['question']}'
        matched expected answer: {q['expected_answer']}
        with similarity: {comp.proof_exists_and_matches_expected_answer}
        Reasoning: {comp.reasoning}
    """)

def format_hint(gold_stmts, q):
    return dedent(f"""
        A possible representation (inspiration only):
        Statements: {gold_stmts}
        Queries: {q['query']}
    """)

def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None, pred_name=None, pred_trace=None):
    try: 
        metta_handler = MorkHandler()
        compare : dspy.Module = dspy.ChainOfThought("question, expected_answer, proof -> proof_exists_and_matches_expected_answer: float")

        log = False

        score = 0.0
        if pred.statements == [] or pred.statements is None:
            return dspy.Prediction(score=score, feedback="No pln statements found")

        for stmt in pred.statements:
            if checkStmt(stmt) == 0.0:
                return dspy.Prediction(score=score, feedback=
                    f"""The statement {stmt} did not follow the right syntax. Follow the pln light spec {pln_spec}""")
            score += 0.001
            metta_handler.add_atom(stmt,log=log)
        
        for query in pred.queries:
            #if len(query) != 1:
                #return dspy.Prediction(score=score, feedback="Found multiple queries where only one is expected.")
            #score += 0.001
            if checkQuery(query[0]) == 0.0:
                return dspy.Prediction(score=score, feedback=
                    f"""The query {query[0]} did not follow the right syntax. Follow the pln light spec {pln_spec}""")
            score += 0.001

        proofs = []
        for qr in pred.queries:
            proofs.append(metta_handler.query(qr[0],log=log))


        correct_matches = 0
        feedback_details = []
        for query, proof in zip(gold.queries, proofs):
            result = compare(
                question=query['question'],
                expected_answer=query['expected_answer'],
                proof=proof
            )
            match = 0.0 if result.proof_exists_and_matches_expected_answer is None else result.proof_exists_and_matches_expected_answer

            correct_matches += match
            feedback_details.append(format_result(query, proof, result))

            if match < 0.7:
                feedback_details.append(format_hint(gold.statements, query))

        n = len(pred.queries)
        score = max(correct_matches / n if n > 0 else 0.0,0.1)

        return dspy.Prediction(
            score=score,
            feedback=f"Score: {correct_matches}/{n} questions matched. \n" + "\n".join(feedback_details)
        )
    except Exception as e:
        print(pred)
        print("Error occured in difficulty_metric:",e)



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
    model = "openrouter/deepseek/deepseek-v3.2"
    #model = "cerebras/gpt-oss-120b"

    dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))
    dspy.settings.configure(track_usage=True)

    module = NL2PLNModule()
    module.load("programs/manual0.json")

    puzzle_data = build_examples_from_file("data/sentences.json")

    puzzle_data = [puzzle_data[0]]

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
