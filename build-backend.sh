#!/usr/bin/env bash

# Delete backend_dist if exists
if [ -d src/main/backend_dist ]; then
  rm -rf src/main/backend_dist
fi

# Run pyinstaller
pyinstaller src/main/backend/br_processor.py --distpath src/main/backend_dist

# Clean up
rm -rf src/main/br_processor.spec
rm -rf src/main/build
rm -rf br_processor.spec