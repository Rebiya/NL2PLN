from pettachainer.pettachainer import PeTTaChainer
from nl2pln import NL2PLNModule

import dspy

data = ["Fido is a dog."
       ,"Dogs are Animals."
       ]

query = "What is Fido?"

model = "openrouter/google/gemini-3-flash-preview"

dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))
dspy.settings.configure(track_usage=True)

metta_handler = PeTTaChainer()

training_module = NL2PLNModule()
training_module.load("src/nl2plnModuleJan2026.json")

module = training_module.nl2pln

for elem in data:
    stmts = module(sentences=[elem], context=[]).pln_light
    for stmt in stmts:
        print(f"Adding statement: {stmt}")
        metta_handler.add_atom(stmt)

pln_querys = module(sentences=[query], context=[]).pln_light
for pln_query in pln_querys:
    print(f"Query: {pln_query} Result:")
    print(metta_handler.query(pln_query))

#Notes:
#For larger systems we should provide a context here of sentnences and their pln representation using the same or similar concepts
#Retrived from the knowledge base using Embeddings or similar. This ensures that the representations stay consistent making the reasoning simpler.
