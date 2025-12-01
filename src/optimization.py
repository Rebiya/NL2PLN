import os
import shutil
import re
from datetime import datetime
import mlflow
import dspy

from dspy.teleprompt import GEPA
from nl2pln import NL2PLNModule , difficulty_metric , build_examples_from_file

import logging
logger = logging.getLogger(dspy.teleprompt.gepa.gepa.__name__)

SCORE_THRESHOLD = 0.9
MAX_COMPILATION_ATTEMPTS = 1

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))
#model = "openai/gpt-5"
#model = "openrouter/z-ai/glm-4.5"
model = "cerebras/gpt-oss-120b"
#model = "openrouter/openai/gpt-5"
#model = "openrouter/openai/gpt-5.1"
optmodel = model

dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))

tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
if tracking_uri:
    mlflow.set_tracking_uri(uri=tracking_uri)
    mlflow.set_experiment("DSPy-Optimization")
    mlflow.dspy.autolog(
        log_compiles=True,    # Track optimization process
        log_evals=True,       # Track evaluation results
        log_traces_from_compile=True  # Track program traces during optimization
    )

# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
#parser = argparse.ArgumentParser(
#    description="Optimize SampleGenerator using COCA train/val datasets"
#)
#parser.add_argument("--train-file", type=str, default="NL2PLN/COCA/train.txt",
#                    help="Path to training text file (one sentence per line)")
#parser.add_argument("--val-file", type=str, default="NL2PLN/COCA/val.txt",
#                    help="Path to validation text file (one sentence per line)")
#args = parser.parse_args()

dataset = build_examples_from_file("data/sentences.json")
#valset = build_examples_from_file(args.val_file)

shutil.rmtree('gepa_logs')
teleprompter = GEPA(metric=difficulty_metric
                   ,reflection_lm=dspy.LM(model=optmodel, temperature=1.0, max_tokens=32000)
                   ,num_threads=10
                   ,max_full_evals=9
                   ,track_stats=True
                   ,track_best_outputs=True
                   ,log_dir='gepa_logs'
                   )

module = NL2PLNModule(model=model)
#module.load("programs/sample_module_optimzied_17102025_1421.json")

print("Length of trainset: " + str(len(dataset)))

logger.setLevel(logging.WARNING)

print(module)
for i in range(1):
    print("====================================================================================")
    print("Iteration: " + str(i))
    print("====================================================================================")
    trainset = [dataset[i]]
    valset = dataset[:(i + 1)]

    compiled_successfully = False
    for attempt in range(1, MAX_COMPILATION_ATTEMPTS + 1):
        module = teleprompter.compile(
            module,
            trainset=trainset,
            valset=valset,
        )
        print("====================================================================================")
        print(module)
        print("====================================================================================")
        print(module.detailed_results.best_outputs_valset)
        print("====================================================================================")

        score = module.detailed_results.val_aggregate_scores[0] 
        if score > SCORE_THRESHOLD:
            compiled_successfully = True
            shutil.rmtree('gepa_logs')
            break

        if attempt < MAX_COMPILATION_ATTEMPTS:
            print(f"val_aggregate_scores {score} did not exceed {SCORE_THRESHOLD}, recompiling (attempt {attempt + 1})...")
            teleprompter.max_full_evals += 9
        else:
            print(f"val_aggregate_scores {score} did not exceed {SCORE_THRESHOLD} after {MAX_COMPILATION_ATTEMPTS} attempts.")

    if not compiled_successfully:
        print(f"Max compilation attempts reached without exceeding threshold; stopping outer loop at {i}.")
        break

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
dated_model_name = f"{re.sub(r'[^A-Za-z0-9_.-]', '_', model)}_{timestamp}"
save_path = f"programs/sample_module_optimzied_{dated_model_name}.json"

module.save(save_path)
print(f"Optimised generator saved to {save_path}")
