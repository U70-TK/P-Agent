#!/usr/bin/env bash

echo "--- MacOS/Linux Environment Setup ---"

if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv already installed."
fi

if [ ! -d "venv" ]; then
    echo "Creating uv virtual environment (Python 3.12)"
    uv venv --python 3.12 venv
else
    echo "venv already exists."
fi

echo "Activating environment..."
source venv/bin/activate

if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found."
    exit 1
fi

echo "Installing dependencies..."
uv pip install -r requirements.txt

echo "Setup complete."
echo "To activate the environment, run:"
echo "    source venv/bin/activate"
