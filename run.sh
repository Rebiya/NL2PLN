
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

# Critical: correct PYTHONPATH for the new structure
export PYTHONPATH=$PWD/src:$PWD/../PeTTa:$PWD/../PeTTaChainer

OPENROUTER_API_KEY="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"
python src/usage_example.py "$@"