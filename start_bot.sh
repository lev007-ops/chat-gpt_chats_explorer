#!/bin/bash

if [ -d ".venv" ]; then
    echo "The .venv folder exists."
else
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
python3 bot.py