#!/bin/bash
set -e

# If GROQ_API_KEY environment variable is set, use it with --api-key
if [[ -n "${GROQ_API_KEY}" ]]; then
    API_KEY_ARG="--api-key ${GROQ_API_KEY}"
else
    API_KEY_ARG=""
fi

# Execute the Python script with arguments
python main.py $API_KEY_ARG "$@"