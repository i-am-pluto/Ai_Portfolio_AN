#!/usr/bin/env bash
# Start the MCP server in SSE mode for Claude mobile / remote access.
#
# Usage:
#   ./start_mobile_server.sh              # port 8000 (default)
#   MCP_PORT=9000 ./start_mobile_server.sh
#
# Then expose publicly (development):
#   ngrok http 8000
#
# Add to Claude.ai → Settings → Integrations → MCP Servers:
#   URL: https://<your-ngrok-id>.ngrok-free.app/sse
#
# Required env vars (set in .env or export before running):
#   GROQ_API_KEY=<your-key>
#   KITE_SSE_URL=https://mcp.kite.trade/sse   (default)
#   USE_KITE=true                              (default)
#   AI_BACKEND=langgraph                       (default)

set -euo pipefail

cd "$(dirname "$0")"

export MCP_TRANSPORT=sse
export MCP_HOST="${MCP_HOST:-0.0.0.0}"
export MCP_PORT="${MCP_PORT:-8000}"

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "Starting MCP SSE server on ${MCP_HOST}:${MCP_PORT} ..."
echo "Connect Claude mobile to: http://localhost:${MCP_PORT}/sse"
echo "(Use ngrok or a cloud deployment for remote access)"
echo ""

exec uv run python -m stocks_fetch
