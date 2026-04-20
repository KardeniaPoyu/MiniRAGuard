#!/bin/bash
# Qingju Environment Setup Script

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created from .env.example."
    echo "👉 PLEASE EDIT .env AND ADD YOUR API KEYS BEFORE DEPLOYING."
else
    echo "ℹ️ .env file already exists. Skipping copy."
fi
