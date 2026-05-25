#!/bin/bash
set -e

echo "Starting Career Agent Backend..."

# Start the application
exec uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
