
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

# Critical: correct PYTHONPATH for the new structure
export PYTHONPATH=$PWD/src:$PWD/../PeTTa:$PWD/../PeTTaChainer

export OPENROUTER_API_KEY="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"

python src/usage_example.py "$@"