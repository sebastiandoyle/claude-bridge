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

## Usage Examples

### Basic prompt

```bash
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What files are in this directory?"}'
```

### Work in a specific project

```bash
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Run the tests and tell me which ones fail",
    "working_directory": "~/Developer/my-project"
  }'
```

### Start a new session (clear previous context)

```bash
curl -X POST http://localhost:5050/new-session \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Start fresh. What is this project?", "working_directory": "~/Developer/my-app"}'
```

### Multi-step conversation

```bash
# Step 1: Ask Claude to read the codebase
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Read the main application file and summarize the architecture",
    "working_directory": "~/Developer/my-app"
  }'

# Step 2: Follow up (context is preserved automatically)
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Now refactor the database module to use connection pooling",
    "working_directory": "~/Developer/my-app"
  }'
```

### List available projects

```bash
curl http://localhost:5050/list-projects \
  -H "X-API-Key: your-secret-key-here"
```

### Python client

```python
import requests

BRIDGE = "http://localhost:5050"
HEADERS = {
    "Authorization": "Bearer your-secret-key-here",
    "Content-Type": "application/json"
}

# Send a prompt
resp = requests.post(f"{BRIDGE}/run-claude", headers=HEADERS, json={
    "prompt": "Add error handling to the API routes",
    "working_directory": "~/Developer/my-app",
    "timeout": 120
})

result = resp.json()
if result["success"]:
    print(result["output"])
else:
    print(f"Error: {result['error']}")
```

### Custom timeout

```bash
# Long-running task with 5-minute timeout (max)
curl -X POST http://localhost:5050/run-claude \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Run the full test suite and fix any failures",
    "working_directory": "~/Developer/my-app",
    "timeout": 300
  }'
```

## ChatGPT Integration

Import `openapi.yaml` as a ChatGPT Action schema. Update the server URL to your machine's address (e.g., via Tailscale Funnel). This lets ChatGPT delegate coding tasks to Claude Code running on your local machine.

## Requirements

- Python 3.8+
- Flask
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed at `~/.local/bin/claude`
