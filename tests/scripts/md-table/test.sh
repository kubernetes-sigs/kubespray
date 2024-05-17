#!/bin/bash
set -euxo pipefail

echo "Install requirements..."
pip install -r ./tests/scripts/md-table/requirements.txt

echo "Generate current file..."
./tests/scripts/md-table/main.py > tmp.md

echo "Compare docs/developers/ci.md with actual tests in tests/files/*.yml ..."
cmp docs/developers/ci.md tmp.md
