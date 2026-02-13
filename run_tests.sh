#!/bin/bash
set -e

echo "Running unit tests..."
pytest tests/ -v

echo ""
echo "All tests passed!"
echo ""
echo "To run integration test:"
echo "1. Set up credentials.json and .env"
echo "2. Follow tests/integration_test.md"
