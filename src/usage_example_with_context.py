import json
import uuid
import urllib.error
import urllib.request

from pettachainer.pettachainer import PeTTaChainer
from nl2pln import NL2PLNModule

import dspy

OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "nomic-embed-text"

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "nl2pln_examples"


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_embed(text: str) -> list[float]:
    resp = http_json("POST", OLLAMA_URL, {"model": OLLAMA_MODEL, "prompt": text})
    return resp["embedding"]


def qdrant_collection_exists() -> bool:
    try:
        http_json("GET", f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}")
        return True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def qdrant_ensure_collection(vector_size: int) -> None:
    if qdrant_collection_exists():
        return
    http_json(
        "PUT",
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}",
        {"vectors": {"size": vector_size, "distance": "Cosine"}},
    )


def qdrant_upsert(point_id: str, vector: list[float], payload: dict) -> None:
    http_json(
        "PUT",
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points?wait=true",
        {"points": [{"id": point_id, "vector": vector, "payload": payload}]},
    )


def qdrant_search(vector: list[float], limit: int = 5) -> list[dict]:
    resp = http_json(
        "POST",
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search",
        {"vector": vector, "limit": limit, "with_payload": True},
    )
    return resp.get("result", [])


def qdrant_delete_collection() -> None:
    try:
        http_json("DELETE", f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise


def retrieve_context(sentence: str, top_k: int = 5) -> tuple[list[str], list[float]]:
    vector = ollama_embed(sentence)
    qdrant_ensure_collection(len(vector))
    results = qdrant_search(vector, limit=top_k)
    context: list[str] = []
    for item in results:
        payload = item.get("payload", {})
        pln = payload.get("pln", [])
        if isinstance(pln, list):
            context.extend(pln)
    return context, vector


def store_example(sentence: str, pln: list[str], vector: list[float] | None = None) -> None:
    if vector is None:
        vector = ollama_embed(sentence)
        qdrant_ensure_collection(len(vector))
    payload = {"nl": sentence, "pln": pln}
    qdrant_upsert(str(uuid.uuid4()), vector, payload)


data = [
    "Fido is a dog.",
    "Dogs are Animals.",
]

query = "What is Fido?"

model = "openrouter/google/gemini-3-flash-preview"

dspy.configure(lm=dspy.LM(model, temperature=1.0, max_tokens=20000))
dspy.settings.configure(track_usage=True)

metta_handler = PeTTaChainer()

training_module = NL2PLNModule()
training_module.load("src/nl2plnModuleJan2026.json")

module = training_module.nl2pln

for elem in data:
    context, vector = retrieve_context(elem, top_k=5)
    print(f"Converting sentence: {elem} with context: {context}")
    stmts = module(sentences=[elem], context=context).pln_light
    store_example(elem, stmts, vector=vector)
    for stmt in stmts:
        print(f"Adding statement: {stmt}")
        metta_handler.add_atom(stmt)
        print("\n")

context, _ = retrieve_context(query, top_k=5)
pln_querys = module(sentences=[query], context=context).pln_light
for pln_query in pln_querys:
    print(f"Query: {pln_query} Result:")
    print(metta_handler.query(pln_query))

qdrant_delete_collection()

# Notes:
# - This example embeds the NL sentence, stores nl -> pln in Qdrant, and retrieves
#   top-k PLN translations as context for consistency on every NL2PLN call.
# - Requires a local Ollama server with an embedding model and a local Qdrant instance.
