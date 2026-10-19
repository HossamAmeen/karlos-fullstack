#!/usr/bin/env bash
# Full automated QA: local backend + frontend suites, live API, live UI, report.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/qa"; mkdir -p reports
echo "== backend unit/API tests";  (cd "$ROOT/backend" && .venv/bin/python -m pytest -q --no-cov) | tee reports/backend-tests.txt
echo "== frontend unit/page tests"; (cd "$ROOT/frontend" && npx vitest run) 2>&1 | tee reports/frontend-tests.txt
echo "== live API";  python3 -m pytest api -q -p no:cacheprovider --junitxml=reports/api-results.xml
echo "== live UI";   npx playwright test
python3 generate_report.py
