from rag_nl2pln import RAGNL2PLN
from pettachainer.pettachainer import PeTTaChainer

rag = RAGNL2PLN(
    data_file="data/all.json",
    model="deepseek/deepseek-v3.2"   # Best current cheap & capable model
)

metta_handler = PeTTaChainer()

sentences = ["Good students study hard.", "Students who study hard go to library.", "Abebe is a good student."]
queries = [{"question": "Do abebe go to library?"}]

result = rag.convert(sentences=sentences, queries=queries)

print("Statements:", result.statements)
print("Queries:", result.queries)

for stmt in result.statements:
    metta_handler.add_atom(stmt)

for q_list in result.queries:
    for q in q_list:
        print("Query:", q)
        try:
            print("Result:", metta_handler.query(q))
        except Exception as e:
            print("Query error:", e)