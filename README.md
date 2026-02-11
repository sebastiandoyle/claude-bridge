# Claude Bridge

A Flask server that lets ChatGPT (or any HTTP client) talk to Claude Code CLI — because sometimes you need your AIs to have a conversation.

## What It Does

Exposes Claude Code as an HTTP API. Send a prompt, get Claude's response back as JSON. Supports:

- **Continuing conversations** — keeps context between calls
- **New sessions** — start fresh when needed
- **Project listing** — see available projects in `~/Developer`
- **API key auth** — Bearer token or X-API-Key header

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install flask

# Set your API key
export CLAUDE_BRIDGE_API_KEY="your-secret-key-here"

# Run
./start.sh
```

Server starts on port 5050.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/run-claude` | Yes | Send prompt (continues conversation) |
| POST | `/new-session` | Yes | Start fresh conversation |
| GET | `/list-projects` | Yes | List ~/Developer projects |

## Example

```bash
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What files are in this directory?", "working_directory": "~/Developer/my-project"}'
```

## ChatGPT Integration

Import `openapi.yaml` as a ChatGPT Action schema. Update the server URL to your machine's address (e.g., via Tailscale Funnel).

## Requirements

- Python 3.8+
- Flask
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed at `~/.local/bin/claude`
