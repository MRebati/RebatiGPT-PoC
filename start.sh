#!/bin/bash

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
while ! curl -s http://ollama:11434/api/tags > /dev/null; do
    sleep 1
done

# Pull the model using curl
echo "Pulling model: ${OLLAMA_MODEL:-modashtizade/DeepSeek-R1-Distill-Llama-8B-Persian:Q4_K_M}"
curl -X POST http://ollama:11434/api/pull -d "{\"name\": \"${OLLAMA_MODEL:-modashtizade/DeepSeek-R1-Distill-Llama-8B-Persian:Q4_K_M}\", \"insecure\": true}"

# Start the application
exec chainlit run src/main.py --host 0.0.0.0 --port 8000 