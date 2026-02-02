To install, clone this repo as well as the dependencies:

```bash
git clone https://github.com/patham9/PeTTa.git
git clone https://github.com/rTreutlein/PeTTaChainer.git
git clone https://github.com/rTreutlein/NL2PLN.git
```

Have a look at `src/usage_example.py` for how to use the model, and
`src/usage_example_with_context.py` for a demo that retrieves top-k PLN
translations from a local vector DB as context.

## Running the context demo

Bring up the local services:

```bash
docker compose up -d
```

Pull an embedding model into Ollama:

```bash
docker exec -it $(docker ps -qf "name=ollama") ollama pull nomic-embed-text
```

Run the example:

```bash
python src/usage_example_with_context.py
```

- `nl2pln.py` is the main module that contains the NL2PLN model for training.
- `simba.py` contains training using the Simba optimizer.
- `gepa.py` contains training using the GEPA optimizer.
