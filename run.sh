#!/usr/bin/env bash
set -e

# Trap SIGINT, SIGTERM, and EXIT to gracefully stop background processes
trap 'echo "Stopping services..."; kill 0 2>/dev/null' INT TERM EXIT

echo "=========================================="
echo "Starting Backend (docker compose up --build)..."
echo "=========================================="
(cd backend && make run) &

echo "=========================================="
echo "Starting Frontend (npm run dev)..."
echo "=========================================="
(cd frontend && npm run dev) &

wait
