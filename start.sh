#!/bin/bash
# Start the Claude Bridge server

cd "$(dirname "$0")"
source venv/bin/activate
python server.py
