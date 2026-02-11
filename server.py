#!/usr/bin/env python3
"""
Claude Bridge Server
Receives commands from ChatGPT Actions and executes them via Claude Code.
"""

import os
import subprocess
import logging
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get('CLAUDE_BRIDGE_API_KEY', 'change-me-set-CLAUDE_BRIDGE_API_KEY-env-var')
CLAUDE_PATH = os.path.expanduser('~/.local/bin/claude')
DEFAULT_TIMEOUT = 300  # 5 minutes max for Claude execution


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = request.headers.get('X-API-Key', '')

        if not token or token != API_KEY:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (no auth required)."""
    return jsonify({'status': 'ok', 'service': 'claude-bridge'})


@app.route('/run-claude', methods=['POST'])
@require_api_key
def run_claude():
    """
    Execute a prompt using Claude Code.

    Request body:
    {
        "prompt": "Your instruction for Claude",
        "working_directory": "/optional/path/to/project",
        "skip_permissions": true,
        "continue_conversation": true,
        "timeout": 120
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'JSON body required'}), 400

        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Bad Request', 'message': 'prompt field is required'}), 400

        working_dir = data.get('working_directory', os.path.expanduser('~'))
        skip_permissions = data.get('skip_permissions', True)
        continue_conversation = data.get('continue_conversation', True)  # Default to continuing
        timeout = min(data.get('timeout', DEFAULT_TIMEOUT), DEFAULT_TIMEOUT)

        # Build the command
        cmd = [CLAUDE_PATH, '-p', prompt]

        # Continue previous conversation by default
        if continue_conversation:
            cmd.append('--continue')

        if skip_permissions:
            cmd.append('--dangerously-skip-permissions')

        logger.info(f"Executing Claude command in {working_dir}")
        logger.info(f"Continue conversation: {continue_conversation}")
        logger.info(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

        # Execute
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'PATH': f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"}
        )

        response = {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'exit_code': result.returncode,
            'continued': continue_conversation
        }

        logger.info(f"Command completed with exit code {result.returncode}")
        return jsonify(response)

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return jsonify({
            'success': False,
            'error': f'Command timed out after {timeout} seconds',
            'output': None
        }), 504

    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'output': None
        }), 500


@app.route('/new-session', methods=['POST'])
@require_api_key
def new_session():
    """Start a fresh Claude session (don't continue previous)."""
    try:
        data = request.json or {}
        prompt = data.get('prompt', 'Hello, starting a new session.')
        working_dir = data.get('working_directory', os.path.expanduser('~'))
        skip_permissions = data.get('skip_permissions', True)
        timeout = min(data.get('timeout', DEFAULT_TIMEOUT), DEFAULT_TIMEOUT)

        cmd = [CLAUDE_PATH, '-p', prompt]
        if skip_permissions:
            cmd.append('--dangerously-skip-permissions')

        logger.info(f"Starting NEW Claude session in {working_dir}")

        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'PATH': f"{os.path.expanduser('~/.local/bin')}:{os.environ.get('PATH', '')}"}
        )

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.stderr else None,
            'exit_code': result.returncode,
            'new_session': True
        })

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/list-projects', methods=['GET'])
@require_api_key
def list_projects():
    """List available project directories."""
    dev_dir = os.path.expanduser('~/Developer')
    try:
        projects = []
        if os.path.exists(dev_dir):
            for item in os.listdir(dev_dir):
                path = os.path.join(dev_dir, item)
                if os.path.isdir(path) and not item.startswith('.'):
                    projects.append({
                        'name': item,
                        'path': path
                    })
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Claude Bridge Server on port 5050")
    logger.info(f"Claude path: {CLAUDE_PATH}")
    app.run(host='0.0.0.0', port=5050)
