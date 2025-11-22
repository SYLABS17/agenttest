#!/bin/bash
set -e

echo "Building Frontend..."

cd frontend
npm install
npm run build

echo "Moving build artifacts to backend/static..."
rm -rf ../backend/static
mkdir -p ../backend/static
cp -r build/* ../backend/static/

echo "Frontend built and moved to backend/static"
