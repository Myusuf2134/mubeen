#!/bin/bash

# Test script for MB-017 TV display WebSocket connectivity
# Usage: ./scripts/test-mb017-display.sh [masjid_uuid]

set -e

MASJID_ID="${1:-550e8400-e29b-41d4-a716-446655440000}"
HOST="${2:-localhost:8000}"

echo "════════════════════════════════════════════════════════════════"
echo "MB-017 Display WebSocket Test"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Testing WebSocket connection to: ws://$HOST/api/khutbah/$MASJID_ID/live"
echo ""

# Test 1: Check if backend is running
echo "✓ Test 1: Backend connectivity..."
if ! curl -s -f "http://$HOST/api/health" > /dev/null; then
  echo "✗ Backend is not running at http://$HOST"
  echo "  Start with: docker-compose up backend (or uvicorn mubeen.main:app)"
  exit 1
fi
echo "  ✓ Backend responding to HTTP requests"
echo ""

# Test 2: WebSocket connection (requires websocat or similar)
echo "✓ Test 2: WebSocket connectivity..."
if ! command -v websocat &> /dev/null; then
  echo "  ⚠ websocat not installed; install with: brew install websocat (or your package manager)"
  echo "  Skipping WebSocket test"
  echo ""
  echo "  To test manually, open in browser:"
  echo "    http://localhost:5173/display/$MASJID_ID"
  echo "  (assuming frontend is running on port 5173)"
else
  # Test connection (will timeout after 2s, which is expected if no publisher is active)
  echo "  Testing connection with 2-second timeout..."
  timeout 2 websocat "ws://$HOST/api/khutbah/$MASJID_ID/live" || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
      echo "  ✓ WebSocket accepted connection (timed out waiting for messages, which is normal)"
    else
      echo "  ✗ WebSocket connection failed with code $EXIT_CODE"
      exit 1
    fi
  }
fi
echo ""

# Test 3: Frontend display page
echo "✓ Test 3: Display page availability..."
FRONTEND_HOST="${3:-localhost:5173}"
if ! curl -s -f "http://$FRONTEND_HOST/display/$MASJID_ID" > /dev/null 2>&1; then
  echo "  ⚠ Frontend not running at http://$FRONTEND_HOST"
  echo "  Start with: cd frontend && npm run dev"
  echo ""
  echo "  Display page URL: http://$FRONTEND_HOST/display/$MASJID_ID"
else
  echo "  ✓ Display page responding"
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "MB-017 Tests Complete"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "1. Open the display page: http://localhost:5173/display/$MASJID_ID"
echo "2. Header should show 'Connecting...' then 'LIVE' (if backend/WS is working)"
echo "3. Start a khutbah session and publisher to see captions appear"
echo ""
echo "To start a test khutbah session:"
echo "  curl -X POST http://localhost:8000/api/khutbah/$MASJID_ID/start \\"
echo "    -H 'Authorization: Bearer YOUR_OPERATOR_TOKEN'"
echo ""
