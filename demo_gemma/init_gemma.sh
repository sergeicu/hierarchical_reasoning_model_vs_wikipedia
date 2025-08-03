#!/bin/bash

# Start Ollama server
export CUDA_VISIBLE_DEVICES=0
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# Wait for server to start
sleep 3

# Pull required models
ollama pull gemma3:1b
ollama pull gemma3:4b
ollama pull gemma3:27b

echo "Setup complete. Run: python get_gemma_responses.py" 
