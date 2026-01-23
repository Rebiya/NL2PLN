import os
import dspy
import json
import mlflow
from pprint import pformat
from dspy.teleprompt import SIMBA
from dspy.utils.callback import BaseCallback

from nl2pln import NL2PLNModule , difficulty_metric , build_examples_from_file

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#model = "openrouter/z-ai/glm-4.5"
#model = "cerebras/gpt-oss-120b"
#model = "openrouter/deepseek/deepseek-v3.2"
#model = "moonshotai/kimi-k2-0905:exacto"
#model = "openrouter/openai/gpt-5.1"
#model = "openrouter/google/gemini-3-pro-preview"
model = "openrouter/google/gemini-3-flash-preview"
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

#dataset = build_examples_from_file("data/sentences.json")
dataset = build_examples_from_file("data/andres.json")

module = NL2PLNModule()
module.load("programs/auto0_andres.json")

for i in range(0,2):

    teleprompter = SIMBA(
        metric=difficulty_metric,
        prompt_model=dspy.LM(optmodel, temperature=1.0),
        bsize=i+1,
        num_threads=10,
    )

    if i > 1:
        module.load(f"programs/sauto{i - 1}_andres.json")

    #trainset = [dataset[i]]
    trainset = dataset[:(i + 1)]
    module = teleprompter.compile(
        module,
        trainset=trainset,
    )

    module.save(f"programs/sauto{i}_andres.json")
