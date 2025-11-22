#!/bin/bash
set -e

echo "Running Backend Tests..."
pytest backend/test_backend.py

echo "Running Frontend Tests..."
cd frontend
# Pass CI=true to avoid watch mode
CI=true npm test

echo "End-to-End Validation Passed!"
