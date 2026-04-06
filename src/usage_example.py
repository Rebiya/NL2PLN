from pettachainer.pettachainer import PeTTaChainer
from nl2pln import NL2PLNModule
import dspy

model = "openrouter/deepseek/deepseek-chat"
dspy.configure(lm=dspy.LM(model, temperature=0.6, max_tokens=2000))
dspy.settings.configure(track_usage=True)

metta_handler = PeTTaChainer()
training_module = NL2PLNModule()
training_module.load("src/simba_all.json")
module = training_module.nl2pln

# Better context to help consistency
context = ["Use consistent predicate names. Use singular forms for types (dog, animal, bird). Always use $x for variables in rules."]

tests = [
    {"sentences": ["Fido is a dog.", "Dogs are animals."], "query": "Is Fido an animal?"},
    {"sentences": ["All birds can fly.", "Sparrows are birds."], "query": "Can sparrows fly?"},
    {"sentences": ["All men are mortal.", "Socrates is a man."], "query": "Is Socrates mortal?"},
]

for test in tests:
    print(f"\n{'='*60}\nTEST: {test['query']}\n{'='*60}")

    for s in test["sentences"]:
        result = module(sentences=[s], queries=[], context=context, pln_spec="")
        for stmt in result.statements:
            print(f"Adding → {stmt}")
            try:
                metta_handler.add_atom(stmt)
            except Exception as e:
                print(f"  → Add failed: {e}")

    print(f"\nQuery: {test['query']}")
    result = module(sentences=[test['query']], queries=[{"question": test['query']}], context=context, pln_spec="")

    for q_list in result.queries:
        for q in q_list:
            q_str = str(q).strip()
            if len(q_str) < 10: 
                continue
            print(f"Executing: {q_str}")
            try:
                res = metta_handler.query(q_str)
                print(f"Result: {res}")
            except Exception as e:
                print(f"Error: {e}")
