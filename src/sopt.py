import os
import dspy
import json
import mlflow
from pprint import pformat
from dspy.teleprompt import GEPA
from dspy.utils.callback import BaseCallback

from nl2pln import NL2PLNModule , difficulty_metric , build_examples_from_file

import logging
logger = logging.getLogger(dspy.teleprompt.gepa.gepa.__name__)

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#model = "openrouter/z-ai/glm-4.5"
#model = "cerebras/gpt-oss-120b"
#model = "openrouter/deepseek/deepseek-v3.2"
model = "openrouter/moonshotai/kimi-k2-0905:exacto"
#model = "openrouter/openai/gpt-5.1"
optmodel = model

lm = dspy.LM(model)

class PromptDumpCallback(BaseCallback):
    def on_lm_start(self, **event):
        call_id  = event.get("call_id")
        messages   = event.get("inputs").get("messages")

        record = {
            "call_id": call_id,
            "messages": messages,
        }

        with open("dspy_prompts.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

dspy.configure(lm=lm,callbacks=[PromptDumpCallback()])

tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
if tracking_uri:
    mlflow.set_tracking_uri(uri=tracking_uri)
    mlflow.set_experiment("DSPy-Optimization")
    mlflow.dspy.autolog(
        log_compiles=True,    # Track optimization process
        log_evals=True,       # Track evaluation results
        log_traces_from_compile=True  # Track program traces during optimization
    )

dataset = build_examples_from_file("data/sentences.json")

#shutil.rmtree('gepa_logs')
teleprompter = GEPA(metric=difficulty_metric
                   ,reflection_lm=dspy.LM(model,temperature=1.0)
                   ,num_threads=10
                   ,max_full_evals=6
                   ,reflection_minibatch_size=1
                   ,track_stats=True
                   ,track_best_outputs=True
                    #,log_dir='gepa_logs'
                   )

module = NL2PLNModule()

i = 3
module.load(f"programs/manualng{i - 1}.json")

trainset = dataset[:(i + 1)]
valset = dataset[:(i + 1)]
module = teleprompter.compile(
    module,
    trainset=trainset,
    valset=valset,
)
print(pformat(module.detailed_results, width=100, indent=2))

module.save(f"programs/manualng{i}.json")
