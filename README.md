# NL2PLN - RAG-based Natural Language to PLN 

This repository converts natural language sentences into **Probabilistic Logic Networks (PLN)** statements and queries, then performs symbolic reasoning using **MeTTa**.

**Current Architecture (RAG-based)**

## System Architecture

```
Natural Language Input
        ↓
RAG Preprocessor (NLTK lemmatization + concept extraction)
        ↓
Qdrant Vector DB (retrieves similar past examples)
        ↓
Rich System Prompt (from simba_all.json) + Retrieved Examples
        ↓
LLM (via OpenRouter - e.g. DeepSeek)
        ↓
Structured PLN Statements + Queries (JSON)
        ↓
PeTTaChainer → MeTTa (adds atoms + performs inference)
        ↓
Inference Results (transitivity, modus ponens, etc.)
```

**Key Components:**
- **RAG Preprocessor**: Normalizes text and extracts concepts to reduce singular/plural issues.
- **Qdrant**: Semantic search for few-shot examples (stored as vectors, not PLN).
- **LLM**: Generates PLN using retrieved examples + rich prompt from `simba_all.json`.
- **PeTTa + PeTTaChainer**: Symbolic reasoning engine (Prolog backend).
- **MeTTa**: Hypergraph knowledge base where real inference happens.

## Setup (Step-by-Step)

### 1. Clone All Required Repositories

```bash
mkdir -p ~/qwestor && cd ~/qwestor

git clone https://github.com/patham9/PeTTa.git
git clone https://github.com/rTreutlein/PeTTaChainer.git
git clone https://github.com/rTreutlein/NL2PLN.git   # or your fork
```

### 2. Start Qdrant (Docker - Recommended)

```bash
docker run -d -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/NL2PLN/data/qdrant_storage:/qdrant/storage \
  --name qdrant qdrant/qdrant
```

Check it's running:
```bash
docker ps
```

### 3. Setup the Environment (using uv - recommended)

```bash
cd NL2PLN

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync

# Install editable local dependencies
uv pip install -e ../PeTTaChainer
```

### 4. Set Your OpenRouter API Key

```bash
export OPENROUTER_API_KEY="sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 5. Run the Pipeline

```bash
./run.sh
```

Or manually:

```bash
python src/usage_example.py
```

## What to Expect

You should see:
- Qdrant indexing examples from `data/all.json`
- MeTTa library loading
- PLN statements being generated
- Real inference results from MeTTa (e.g., transitivity: "Fido is a dog" + "Dogs are animals" → "Fido is an animal")

## Project Structure (Important)

```
NL2PLN/
├── data/                  # all.json contains training examples
├── src/
│   ├── rag_nl2pln.py      # Main RAG pipeline
│   ├── qdrant_store.py    # Qdrant vector store
│   ├── rag_preprocessor.py # Text normalization
│   ├── pln_prompt.py      # Prompt builder (uses simba_all.json)
│   └── usage_example.py   # Easy test script
├── simba_all.json         # Rich system prompt for LLM
├── run.sh                 # Convenience launcher
└── pyproject.toml
```

## Troubleshooting

- **Qdrant not found**: Make sure Docker container is running (`docker ps`)
- **402 Payment Required**: Use a cheaper model (`deepseek/deepseek-v3.2`) and reduce `max_tokens`
- **Model not found**: Check OpenRouter model name (try `deepseek/deepseek-v3.2`)
- **Key error**: Ensure `OPENROUTER_API_KEY` is exported before running
